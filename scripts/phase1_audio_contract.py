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
from video_factory.pipeline.narration_timing import plan_source_aligned_narration
from video_factory.pipeline.registry import load_pink_pig_registry
from video_factory.pipeline.storyboard import compile_storyboard


TAIL_MARGIN_SECONDS = 0.2
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


def run_fixture(brief_path: Path, output_root: Path) -> dict[str, Any]:
    brief = load_local_brief(brief_path)
    plan = build_local_plan(brief, repo_root=ROOT)
    topic_slug = str(plan["job_id"])
    fixture_root = output_root / topic_slug
    fixture_root.mkdir(parents=True, exist_ok=True)
    original_timeline = compile_storyboard(
        plan["storyboard"], load_pink_pig_registry(repo_root=ROOT), repo_root=ROOT
    )
    result = plan_source_aligned_narration(
        storyboard=plan["storyboard"],
        script=plan["script"],
        factual_brief=plan["factual_brief"],
        registry=load_pink_pig_registry(repo_root=ROOT),
        repo_root=ROOT,
        work_dir=fixture_root,
        voice=str(VOICE_CONFIG["voice"]),
        provider=str(VOICE_CONFIG["provider"]),
        tail_margin_seconds=TAIL_MARGIN_SECONDS,
    )
    passes = result["passes"]
    final_pass = passes[-1]
    aligned = dict(final_pass["aligned_audio"])
    audio_path = Path(str(aligned["path"]))
    aligned["sha256"] = _sha(audio_path)
    aligned["duration_seconds"] = round(_probe_duration(audio_path), 3)
    aligned["volume"] = _volume(audio_path)
    final_pass["aligned_audio"] = aligned
    return {
        "status": "AUDIO_ONLY_READY_FOR_LISTENING_REVIEW",
        "topic": plan["topic"],
        "topic_digest": plan["topic_digest"],
        "original_timeline_duration_seconds": original_timeline["total_duration_seconds"],
        "passes": passes,
        "rewrite": "one_pass_used" if int(result["rewrite_count"]) else "not_needed",
        "listening_review": "PENDING_HUMAN_AUDIO_REVIEW",
    }


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
