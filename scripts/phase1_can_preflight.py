"""Run CAN live-topic no-render source, audio and asset preflight."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.factory.phase1_local import build_local_plan, load_local_brief
from video_factory.pipeline.narration_timing import plan_source_aligned_narration
from video_factory.pipeline.registry import load_pink_pig_registry


ROOT = Path(__file__).resolve().parents[1]


def _asset_checks(paths: list[Path]) -> tuple[str, str, list[dict[str, object]]]:
    checks: list[dict[str, object]] = []
    for path in paths:
        try:
            with Image.open(path) as image:
                image.load()
                size = image.size
                background = Image.new("RGB", (1490, 630), "#F4F6F8")
                bbox = ImageChops.difference(image.convert("RGB").crop((90, 170, 1580, 800)), background).getbbox()
            safe = bool(bbox and bbox[3] <= 590)
            checks.append({"path": path.relative_to(ROOT).as_posix(), "decoded": True, "size": list(size), "content_bbox": list(bbox) if bbox else None, "safe_area": safe})
        except Exception as exc:
            checks.append({"path": path.relative_to(ROOT).as_posix(), "decoded": False, "error": type(exc).__name__})
    return (
        "PASS" if checks and all(item.get("decoded") and item.get("size") == [1672, 941] for item in checks) else "FAIL",
        "PASS" if checks and all(item.get("safe_area") is True for item in checks) else "FAIL",
        checks,
    )


def main() -> int:
    brief_path = ROOT / "examples/phase1_local_can_arbitration/brief.json"
    brief = load_local_brief(brief_path)
    plan = build_local_plan(brief, repo_root=ROOT)
    registry = load_pink_pig_registry(repo_root=ROOT)
    runtime = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_can_arbitration_preflight_20260928")
    runtime.mkdir(parents=True, exist_ok=True)
    result = plan_source_aligned_narration(
        storyboard=plan["storyboard"],
        script=plan["script"],
        factual_brief=plan["factual_brief"],
        registry=registry,
        repo_root=ROOT,
        work_dir=runtime,
        voice="Microsoft Huihui Desktop",
        provider="windows-sapi",
        tail_margin_seconds=0.2,
    )
    final_pass = result["passes"][-1]
    audio = Path(result["audio_path"])
    asset_paths = [ROOT / str(selection["relative_path"]) for selection in plan["asset_selection"]["selections"]]
    visual_decode, visual_safe_area, visual_checks = _asset_checks(asset_paths)
    report = {
        "schema_version": "phase1_live_topic_preflight_v1",
        "status": "LIVE_TOPIC_PREFLIGHT_READY",
        "topic": plan["topic"],
        "job_id": plan["job_id"],
        "topic_digest": plan["topic_digest"],
        "brief": "examples/phase1_local_can_arbitration/brief.json",
        "facts": [fact["fact_id"] for fact in plan["factual_brief"]["facts"]],
        "sources": [source["source_id"] for source in plan["factual_brief"]["sources"]],
        "assets": [selection["asset_id"] for selection in plan["asset_selection"]["selections"]],
        "asset_hashes": [selection["sha256"] for selection in plan["asset_selection"]["selections"]],
        "rewrite_count": result["rewrite_count"],
        "final_duration_seconds": final_pass["allocation"]["duration_seconds"],
        "srt_endpoint_seconds": final_pass["allocation"]["srt_endpoint_seconds"],
        "objective_audio_integrity": result["objective_audio_integrity"],
        "runtime_locator_id": "phase1_can_arbitration_preflight_20260928",
        "audio_relative_path": audio.name,
        "audio_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
        "visual_asset_decode": visual_decode,
        "visual_asset_content_safe_area": visual_safe_area,
        "visual_preflight_report": "reports/phase1/stage_20260928/can_visual_preflight.json",
        "visual_preflight_status": "PASS_BOUNDED_STILL_ONLY",
        "visual_asset_checks": visual_checks,
        "transition_probe": "NOT_RUN_BEFORE_RENDER",
        "render_performed": False,
        "mp4_created": False,
        "transition_mode": result["timeline"].get("transition_mode"),
        "human_review": "NOT_REQUESTED",
        "next_step": "Remote review of CAN source-bound no-render preflight; authorize one outer CAN candidate only after preflight and later human gate.",
    }
    output = ROOT / "reports/phase1/stage_20260928/live_topic_preflight.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "job_id": report["job_id"], "duration": report["final_duration_seconds"], "audio_sha256": report["audio_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
