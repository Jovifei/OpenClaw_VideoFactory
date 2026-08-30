"""Validated visual-only Phase 1 technical-explainer orchestration."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from third_party.openmontage.slideshow_risk import score_slideshow_risk
from third_party.openmontage.verify_scene_pacing import verify_scene_pacing

VISUAL_TYPES = frozenset({"kinetic_typography", "system_diagram", "timeline", "comparison_card", "checklist"})
CANVASES = {"16:9": {"width": 1920, "height": 1080}, "9:16": {"width": 1080, "height": 1920}}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("visual_input_not_object")
    return value


def validate_visual_inputs(scene_plan_path: Path, timing_manifest_path: Path, *, aspect: str) -> dict[str, Any]:
    if aspect not in CANVASES:
        raise ValueError("aspect_invalid")
    plan, timing = _load(scene_plan_path), _load(timing_manifest_path)
    if plan.get("schema_version") != "1.0" or timing.get("schema_version") != "1.0":
        raise ValueError("schema_version_invalid")
    if timing.get("scene_plan", {}).get("sha256") != _sha256(scene_plan_path):
        raise ValueError("scene_plan_hash_mismatch")
    if plan.get("script_sha256") != timing.get("script", {}).get("sha256"):
        raise ValueError("script_hash_mismatch")
    promise = plan.get("delivery_promise", "teacher_explainer")
    if promise not in {"data_explainer", "teacher_explainer"}:
        raise ValueError("delivery_promise_invalid")
    scenes, segments = plan.get("scenes"), timing.get("segments")
    if not isinstance(scenes, list) or not isinstance(segments, list) or len(scenes) != len(segments):
        raise ValueError("scene_timing_count_mismatch")
    previous_end = 0
    paced: list[dict[str, float]] = []
    for index, (scene, segment) in enumerate(zip(scenes, segments, strict=True), 1):
        if scene.get("scene_index") != index or segment.get("index") != index:
            raise ValueError("scene_index_invalid")
        start, end = int(segment.get("scene_start_microseconds", -1)), int(segment.get("scene_end_microseconds", -1))
        if start != previous_end or end <= start:
            raise ValueError("scene_boundaries_not_contiguous")
        previous_end = end
        if scene.get("visual_type") not in VISUAL_TYPES:
            raise ValueError("visual_type_invalid")
        if not str(scene.get("on_screen_knowledge", "")).strip():
            raise ValueError("visible_knowledge_required")
        if not scene.get("source_refs"):
            raise ValueError("source_refs_required")
        paced.append({"duration_seconds": (end - start) / 1_000_000})
    if previous_end != round(float(timing.get("visual_duration_seconds", 0)) * 1_000_000):
        raise ValueError("scene_duration_mismatch")
    for window in (scenes[i:i + 3] for i in range(max(0, len(scenes) - 2))):
        if len({scene["visual_type"] for scene in window}) == 1:
            raise ValueError("visual_type_repetition")
    directed = [{"type": scene["visual_type"], "description": scene["on_screen_knowledge"],
                 "information_role": scene["information_role"], "shot_intent": scene["shot_intent"],
                 "shot_language": {"shot_size": ("wide", "medium", "close", "detail", "wide")[i % 5],
                                   "camera_movement": scene["motion"]}} for i, scene in enumerate(scenes)]
    slideshow = score_slideshow_risk(directed, renderer_family="technical_explainer", render_runtime="remotion")
    if slideshow["verdict"] == "revise":
        raise ValueError("one_revision_required")
    if slideshow["verdict"] == "fail":
        raise ValueError("slideshow_risk_failed")
    pacing = verify_scene_pacing(paced, target_duration_seconds=float(timing["visual_duration_seconds"]))
    if not pacing["valid"]:
        raise ValueError("scene_pacing_invalid")
    return {"scene_plan": plan, "timing": timing, "delivery_promise": promise, "slideshow": slideshow,
            "pacing": pacing, "canvas": CANVASES[aspect], "renderer": "remotion", "visual_only": True}


def _e_drive(path: Path, field: str) -> str:
    resolved = str(path.resolve())
    if Path(resolved).drive.upper() != "E:":
        raise ValueError(f"{field}_must_use_e_drive")
    return resolved


def build_renderer_command(*, node: str, scene_plan: Path, timing_manifest: Path, output: Path, report: Path,
                           stills_dir: Path, clips_dir: Path, renderer: Path) -> list[str]:
    return [node, str(renderer.resolve()), "--scene-plan", str(scene_plan.resolve()), "--timing-manifest", str(timing_manifest.resolve()),
            "--output", _e_drive(output, "renderer_output"), "--report", _e_drive(report, "renderer_report"),
            "--stills-dir", _e_drive(stills_dir, "renderer_stills"), "--clips-dir", _e_drive(clips_dir, "renderer_clips")]


def assemble_contact_sheet(stills: list[Path], output: Path) -> dict[str, Any]:
    from PIL import Image, ImageDraw
    if not stills:
        raise ValueError("contact_sheet_stills_required")
    images = [Image.open(path).convert("RGB") for path in stills]
    thumb_w, thumb_h = 480, 270
    sheet = Image.new("RGB", (thumb_w * 2, thumb_h * ((len(images) + 1) // 2)), "#eceff3")
    draw = ImageDraw.Draw(sheet)
    for index, image in enumerate(images):
        image.thumbnail((thumb_w, thumb_h))
        x, y = index % 2 * thumb_w, index // 2 * thumb_h
        sheet.paste(image, (x, y))
        draw.text((x + 12, y + 12), f"SCENE {index + 1}", fill="white", stroke_width=2, stroke_fill="black")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    for image in images:
        image.close()
    return {"path": str(output), "scene_count": len(stills), "sha256": _sha256(output)}


def render_and_review(*, scene_plan: Path, timing_manifest: Path, output: Path, report: Path, stills_dir: Path,
                      clips_dir: Path, review_report: Path, contact_sheet: Path, aspect: str = "16:9") -> dict[str, Any]:
    validation = validate_visual_inputs(scene_plan, timing_manifest, aspect=aspect)
    renderer = Path(__file__).resolve().parents[2] / "scripts" / "render_phase1_topic_visual.mjs"
    command = build_renderer_command(node="node", scene_plan=scene_plan, timing_manifest=timing_manifest, output=output,
        report=report, stills_dir=stills_dir, clips_dir=clips_dir, renderer=renderer)
    subprocess.run(command, check=True, shell=False, timeout=900)
    sheet = assemble_contact_sheet(sorted(stills_dir.glob("scene_*.png")), contact_sheet)
    post_report = review_report.with_name("post_render_check.json")
    post_script = Path(__file__).resolve().parents[2] / "scripts" / "phase1_post_render_check.py"
    subprocess.run([sys.executable, str(post_script), "--visual", str(output), "--render-report", str(report),
                    "--output-report", str(post_report)], check=True, shell=False, timeout=600)
    post_render = _load(post_report)
    result = {"schema_version": "1.0", "status": "passed", "validation": validation, "contact_sheet": sheet,
              "render_report_sha256": _sha256(report), "visual_sha256": _sha256(output),
              "post_render": post_render["checks"], "human_review_required": True}
    review_report.parent.mkdir(parents=True, exist_ok=True)
    review_report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
