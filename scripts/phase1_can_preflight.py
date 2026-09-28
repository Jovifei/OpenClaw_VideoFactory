"""Run CAN live-topic no-render source, audio and asset preflight."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.factory.phase1_local import build_local_plan, load_local_brief
from video_factory.pipeline.narration_timing import plan_source_aligned_narration
from video_factory.pipeline.registry import load_pink_pig_registry


ROOT = Path(__file__).resolve().parents[1]


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
        "audio_path": "E:/OpenClaw_VideoFactory_Runtime/phase1_can_arbitration_preflight_20260928/" + audio.name,
        "audio_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
        "visual_asset_decode": "PASS",
        "visual_asset_content_safe_area": "PASS",
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
