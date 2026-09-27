"""Bounded, audio-only Phase 1 narration contract proof.

This script measures the real local TTS output for Flash and FreeRTOS, performs
at most one deterministic concise rewrite when the 60-second budget requires
it, rebuilds the technical-cut timeline/SRT, and pads complete audio segments
without trimming.  It never renders a video or mutates a candidate job.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.factory.phase1_local import build_local_plan, load_local_brief
from video_factory.pipeline.audio_planner import (
    NarrationDurationBudgetError,
    allocate_scene_durations,
    align_complete_segments,
    synthesize_tts_segments,
)
from video_factory.pipeline.narration_timing import rewrite_narration_once, storyboard_with_narration
from video_factory.pipeline.registry import load_pink_pig_registry
from video_factory.pipeline.storyboard import compile_storyboard
from video_factory.pipeline.subtitle import build_srt_from_timeline


TAIL_MARGIN_SECONDS = 0.2
MAX_TOTAL_SECONDS = 60.0
MIN_TOTAL_SECONDS = 25.0
VOICE_CONFIG = {"provider": "windows-sapi", "voice": "Microsoft Huihui Desktop"}


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _probe_duration(path: Path) -> float:
    value = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True, timeout=20,
    )
    return float(json.loads(value.stdout)["format"]["duration"])


def _volume(path: Path) -> dict[str, float]:
    value = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(path), "-af", "volumedetect", "-f", "null", "NUL"],
        capture_output=True, text=True, check=False, timeout=60,
    )
    result: dict[str, float] = {}
    for line in (value.stdout + value.stderr).splitlines():
        if "mean_volume:" in line or "max_volume:" in line:
            name, raw = line.split(":", 1)
            result[name.strip()] = float(raw.strip().split()[0])
    return result


def _timeline_for(plan: dict[str, Any], script: dict[str, Any]) -> dict[str, Any]:
    storyboard = storyboard_with_narration(plan["storyboard"], script)
    return compile_storyboard(storyboard, load_pink_pig_registry(repo_root=ROOT), repo_root=ROOT)


def run_fixture(brief_path: Path, output_root: Path) -> dict[str, Any]:
    brief = load_local_brief(brief_path)
    plan = build_local_plan(brief, repo_root=ROOT)
    topic_slug = str(plan["job_id"])
    fixture_root = output_root / topic_slug
    fixture_root.mkdir(parents=True, exist_ok=True)
    original_timeline = _timeline_for(plan, plan["script"])

    passes: list[dict[str, Any]] = []
    current_script = plan["script"]
    original_fact_refs = [list(beat.get("fact_refs", [])) for beat in current_script.get("beats", [])]
    rewritten = False
    for pass_index in range(2):
        timeline = _timeline_for(plan, current_script)
        raw_dir = fixture_root / f"pass_{pass_index}" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        segments = synthesize_tts_segments(
            timeline, work_dir=raw_dir, voice=str(VOICE_CONFIG["voice"]), provider=str(VOICE_CONFIG["provider"])
        )
        raw_total = round(sum(float(segment["actual_duration"]) for segment in segments), 3)
        pass_record: dict[str, Any] = {
            "pass": pass_index,
            "rewritten": rewritten,
            "narration": [str(beat["narration"]) for beat in current_script["beats"]],
            "segments": [dict(segment, audio_sha256=_sha(Path(str(segment["audio_path"])))) for segment in segments],
            "raw_total_seconds": raw_total,
        }
        try:
            allocated = allocate_scene_durations(
                timeline,
                segments,
                tail_margin_seconds=TAIL_MARGIN_SECONDS,
                min_total_seconds=MIN_TOTAL_SECONDS,
                max_total_seconds=MAX_TOTAL_SECONDS,
            )
        except NarrationDurationBudgetError as exc:
            pass_record["allocation"] = {"status": "budget_exceeded", "error": str(exc)}
            passes.append(pass_record)
            if rewritten:
                return {
                    "status": "BLOCKED_NARRATION_DURATION_BUDGET",
                    "topic": plan["topic"],
                    "topic_digest": plan["topic_digest"],
                    "original_timeline_duration_seconds": original_timeline["total_duration_seconds"],
                    "passes": passes,
                    "rewrite": "one_pass_used",
                }
            current_script, rewrite_meta = rewrite_narration_once(current_script, plan["factual_brief"])
            rewritten = True
            pass_record["rewrite_reason"] = "narration_duration_budget_exceeded"
            pass_record["rewrite_meta"] = rewrite_meta
            pass_record["fact_refs_preserved"] = original_fact_refs == [
                list(beat.get("fact_refs", [])) for beat in current_script.get("beats", [])
            ]
            if not pass_record["fact_refs_preserved"]:
                raise ValueError("narration_rewrite_fact_bindings_changed")
            continue

        subtitle = fixture_root / f"pass_{pass_index}" / "subtitle.srt"
        cues = build_srt_from_timeline(allocated, subtitle)
        aligned_dir = fixture_root / f"pass_{pass_index}" / "aligned"
        audio_path = fixture_root / f"pass_{pass_index}" / "audio_only.wav"
        aligned = align_complete_segments(segments, allocated, output_dir=aligned_dir, output_path=audio_path)
        pass_record["allocation"] = {
            "status": "passed",
            "duration_seconds": allocated["total_duration_seconds"],
            "scene_durations": [scene["duration"] for scene in allocated["scenes"]],
            "srt_sha256": _sha(subtitle),
            "srt_end_seconds": cues[-1]["end"],
        }
        pass_record["aligned_audio"] = {
            "path": str(audio_path),
            "sha256": _sha(audio_path),
            "duration_seconds": round(_probe_duration(audio_path), 3),
            "volume": _volume(audio_path),
            "segments": aligned["segments"],
        }
        pass_record["scene_boundary_markers"] = [
            {"scene_id": scene["scene_id"], "start_seconds": round(sum(float(item["duration"]) for item in allocated["scenes"][:index]), 3),
             "end_seconds": round(sum(float(item["duration"]) for item in allocated["scenes"][: index + 1]), 3)}
            for index, scene in enumerate(allocated["scenes"])
        ]
        passes.append(pass_record)
        return {
            "status": "AUDIO_ONLY_READY_FOR_LISTENING_REVIEW",
            "topic": plan["topic"],
            "topic_digest": plan["topic_digest"],
            "original_timeline_duration_seconds": original_timeline["total_duration_seconds"],
            "passes": passes,
            "rewrite": "one_pass_used" if rewritten else "not_needed",
            "listening_review": "PENDING_HUMAN_AUDIO_REVIEW",
        }

    raise AssertionError("narration_pass_loop_exhausted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=Path("E:/OpenClaw_VideoFactory_Runtime/phase1_audio_contract_20260927"))
    parser.add_argument("briefs", nargs="+", type=Path)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"status": "completed", "fixtures": []}
    for index, brief in enumerate(args.briefs, start=1):
        result = run_fixture(brief.resolve(), args.output_root)
        result["brief"] = str(brief)
        report["fixtures"].append(result)
        print(f"[{index}/{len(args.briefs)}] {result['topic']} -> {result['status']}", flush=True)
    if any(item["status"] != "AUDIO_ONLY_READY_FOR_LISTENING_REVIEW" for item in report["fixtures"]):
        report["status"] = "CHANGES_REQUIRED"
    output = args.output_root / "audio_contract_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0 if report["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
