"""Render CAN production-style stills with the real preflight subtitle cues."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.factory.phase1_local import build_local_plan, load_local_brief
from video_factory.pipeline.registry import load_pink_pig_registry
from video_factory.pipeline.renderer import build_render_command
from video_factory.pipeline.storyboard import compile_storyboard

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_can_arbitration_preflight_20260928")
_CAN_VISUAL_TAGS = {"dominant_recessive", "two_node_bits", "id_compare", "loser_stops", "checklist"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_srt(path: Path) -> list[dict[str, object]]:
    blocks = re.split(r"\r?\n\r?\n", path.read_text(encoding="utf-8").strip())
    result = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            continue
        match = re.search(r"(\d+):(\d{2}):(\d{2}),(\d{3})\s+-->\s+(\d+):(\d{2}):(\d{2}),(\d{3})", lines[1])
        if not match:
            raise ValueError("srt_cue_invalid")
        values = [int(item) for item in match.groups()]
        start = values[0] * 3600 + values[1] * 60 + values[2] + values[3] / 1000
        end = values[4] * 3600 + values[5] * 60 + values[6] + values[7] / 1000
        result.append({"start_seconds": start, "end_seconds": end, "text": " ".join(lines[2:])})
    return result


def _safe_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    background = Image.new("RGB", (1490, 630), "#F4F6F8")
    return ImageChops.difference(image.convert("RGB").crop((90, 170, 1580, 800)), background).getbbox()


def _ffmpeg_decode(path: Path) -> dict[str, object]:
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1", "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "returncode": result.returncode,
        "error": result.stderr.strip()[-240:] if result.returncode else None,
    }


def _transition_probe(plan: dict[str, object], registry: object, subtitle_path: Path, cues: list[dict[str, object]]) -> dict[str, object]:
    compiled = compile_storyboard(plan["storyboard"], registry, repo_root=ROOT)
    timeline = deepcopy(compiled["scenes"])
    if len(timeline) != len(cues):
        return {"status": "FAIL", "reason": "scene_cue_count_mismatch", "scene_count": len(timeline), "cue_count": len(cues)}
    for scene, cue in zip(timeline, cues):
        scene["duration"] = round(float(cue["end_seconds"]) - float(cue["start_seconds"]), 3)
    try:
        command, duration = build_render_command(
            asset_dir=ROOT / "assets",
            timeline=timeline,
            subtitle_path=subtitle_path,
            output_path=ROOT / "reports/phase1/stage_20260928/can_transition_probe_not_rendered.mp4",
            transition_seconds=float(compiled["transition_seconds"]),
            audio_path=None,
            transition_mode=str(compiled.get("transition_mode", "")),
            repo_root=ROOT,
            burn_in_subtitles=False,
            canvas_width=int(compiled["width"]),
            canvas_height=int(compiled["height"]),
            fps=int(compiled["fps"]),
        )
    except Exception as exc:
        return {"status": "FAIL", "reason": type(exc).__name__, "detail": str(exc)}
    command_text = " ".join(command)
    filter_graph = command[command.index("-filter_complex") + 1] if "-filter_complex" in command else ""
    hard_cut = str(compiled.get("transition_mode")) == "technical_cut" and "xfade=" not in filter_graph and f"concat=n={len(timeline)}" in filter_graph
    contiguous = all(
        abs(float(cues[index]["end_seconds"]) - float(cues[index + 1]["start_seconds"])) <= 0.001
        for index in range(len(cues) - 1)
    )
    return {
        "status": "PASS_BOUNDED_TIMELINE_ONLY" if hard_cut and contiguous else "FAIL",
        "mode": compiled.get("transition_mode"),
        "scene_count": len(timeline),
        "cue_boundaries_contiguous": contiguous,
        "filter_graph_contains_xfade": "xfade=" in filter_graph,
        "filter_graph_contains_concat": f"concat=n={len(timeline)}" in filter_graph,
        "duration_seconds": duration,
        "frame_count": round(float(duration) * int(compiled["fps"])),
        "command_sha256": hashlib.sha256(command_text.encode("utf-8")).hexdigest(),
        "encoded_transition_frames": False,
        "rendered_output": False,
    }


def main() -> int:
    brief_path = ROOT / "examples/phase1_local_can_arbitration/brief.json"
    plan = build_local_plan(load_local_brief(brief_path), repo_root=ROOT)
    registry = load_pink_pig_registry(repo_root=ROOT)
    subtitle_path = RUNTIME / "narration_pass_0" / "subtitle.srt"
    cues = _parse_srt(subtitle_path)
    still_root = RUNTIME / "visual_preflight" / "stills"
    still_root.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 42)
    except OSError:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 42)
    checks = []
    for index, selection in enumerate(plan["asset_selection"]["selections"]):
        asset = registry.get(str(selection["asset_id"]))
        source_path = ROOT / str(asset.source_svg or "") if asset and asset.source_svg else None
        image_path = ROOT / str(selection["relative_path"])
        source_kind = "generator" if source_path and source_path.suffix == ".py" else "svg"
        ffmpeg_decode = _ffmpeg_decode(image_path)
        with Image.open(image_path) as image:
            image.load()
            image = image.convert("RGB")
            bbox = _safe_bbox(image)
            source_ok = bool(source_path and source_path.is_file())
            decode_ok = image.size == (1672, 941)
            safe_ok = bool(bbox and bbox[3] <= 590)
            canvas = image.copy()
            draw = ImageDraw.Draw(canvas, "RGBA")
            draw.rounded_rectangle((90, 760, 1580, 910), radius=18, fill=(22, 50, 79, 235), outline=(242, 193, 78, 255), width=3)
            cue_text = str(cues[index]["text"]) if index < len(cues) else ""
            draw.text((130, 805), cue_text, font=font, fill=(255, 255, 255, 255))
            still_path = still_root / f"scene_{index + 1:02d}.png"
            canvas.save(still_path)
        asset_tags = set(selection["tags"])
        visual_tags = sorted(asset_tags & _CAN_VISUAL_TAGS)
        semantic_mapping = {
            "scene_id": selection["scene_id"],
            "storyboard_asset_id_matches": plan["storyboard"]["scenes"][index]["asset_id"] == selection["asset_id"],
            "required_tags": plan["script"]["beats"][index]["required_tags"],
            "asset_tags": selection["tags"],
            "visual_semantic_tags": visual_tags,
            "semantic_match": "can_arbitration" in asset_tags and bool(visual_tags),
        }
        checks.append({
            "scene_index": index + 1,
            "asset_id": selection["asset_id"],
            "source_svg": source_path.relative_to(ROOT).as_posix() if source_ok else None,
            "asset_png": image_path.relative_to(ROOT).as_posix(),
            "registry_sha256": selection["sha256"],
            "actual_png_sha256": _sha(image_path),
            "source_binding": source_ok,
            "source_kind": source_kind if source_ok else None,
            "source_sha256": _sha(source_path) if source_ok else None,
            "pillow_decode_and_dimensions": decode_ok,
            "ffmpeg_decode": ffmpeg_decode,
            "decode_and_dimensions": decode_ok and ffmpeg_decode["status"] == "PASS",
            "safe_area": safe_ok,
            "semantic_mapping": semantic_mapping,
            "subtitle_text": cue_text,
            "still_sha256": _sha(still_path),
        })
    transition_probe = _transition_probe(plan, registry, subtitle_path, cues)
    status = "PASS_BOUNDED_STILL_ONLY" if all(
        item["source_binding"]
        and item["decode_and_dimensions"]
        and item["safe_area"]
        and item["registry_sha256"] == item["actual_png_sha256"]
        and item["semantic_mapping"]["storyboard_asset_id_matches"]
        and item["semantic_mapping"]["semantic_match"]
        for item in checks
    ) and transition_probe["status"] == "PASS_BOUNDED_TIMELINE_ONLY" else "CHANGES_REQUIRED"
    report = {
        "schema_version": "phase1_can_visual_preflight_v1",
        "status": status,
        "runtime_locator_id": "phase1_can_arbitration_preflight_20260928",
        "subtitle_source": "narration_pass_0/subtitle.srt",
        "checks": checks,
        "transition_probe": transition_probe,
        "outer_render_authorization": "NOT_AUTHORIZED",
    }
    output = ROOT / "reports/phase1/stage_20260928/can_visual_preflight.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "scenes": len(checks), "output": str(output)}))
    return 0 if status == "PASS_BOUNDED_STILL_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())

