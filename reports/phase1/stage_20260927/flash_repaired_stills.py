"""Five real-cue stills after scoped Flash asset repair; no full video job."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageChops

from generate_video import _local_brief_subtitle_style
from src.factory.phase1_local import build_local_plan, load_local_brief
from video_factory.pipeline.registry import load_pink_pig_registry
from video_factory.pipeline.storyboard import compile_storyboard
from video_factory.pipeline.subtitle import build_srt_from_timeline

from flash_preflight import OUTPUT as OLD_OUTPUT, ROOT, short_render, sha


OUTPUT = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_flash_geometry_20260927")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    brief = load_local_brief(ROOT / "examples/phase1_local_flash_watchdog/brief.json")
    plan = build_local_plan(brief, repo_root=ROOT)
    timeline = compile_storyboard(plan["storyboard"], load_pink_pig_registry(repo_root=ROOT), repo_root=ROOT)
    srt = OUTPUT / "subtitle_37_8.srt"
    cues = build_srt_from_timeline(timeline, srt)
    old_report = json.loads((OLD_OUTPUT / "flash_preflight_report.json").read_text(encoding="utf-8"))
    assert timeline["total_duration_seconds"] == old_report["planned_duration_seconds"] == 37.8
    assert sha(srt) == old_report["srt_sha256"]
    profile = plan["render_profile"]
    style = _local_brief_subtitle_style(1920, 1080)
    results = []
    for index, scene in enumerate(timeline["scenes"], start=1):
        result = short_render(
            f"repaired_scene_{index}", [scene], [str(cues[index - 1]["text"])],
            style, profile, (15,), output_dir=OUTPUT,
        )
        results.append(result)
        print(f"[{index}/5] {result['frames'][0]['path']}", flush=True)
    old_scene4 = OLD_OUTPUT / "scene_4_frame_15.png"
    new_scene4 = OUTPUT / "repaired_scene_4_frame_15.png"
    with Image.open(old_scene4) as original, Image.open(new_scene4) as current:
        original.load()
        current.load()
        scene4_pixels_unchanged = ImageChops.difference(original.convert("RGB"), current.convert("RGB")).getbbox() is None
    assert scene4_pixels_unchanged
    (OUTPUT / "flash_repaired_stills_report.json").write_text(
        json.dumps({"status": "stills_rendered_visual_review_pending", "source_preflight_report": str(OLD_OUTPUT / "flash_preflight_report.json"),
                    "timeline_duration_seconds": 37.8, "srt_sha256": sha(srt),
                    "scene4_control_pixels_unchanged": scene4_pixels_unchanged,
                    "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
