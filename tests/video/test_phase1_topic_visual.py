from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.factory.phase1_topic_visual import assemble_contact_sheet, build_renderer_command, validate_visual_inputs


def _scene_plan() -> dict:
    kinds = ["kinetic_typography", "system_diagram", "timeline", "comparison_card", "checklist"]
    return {"schema_version": "1.0", "script_id": "script_0123456789abcdef", "script_sha256": "a" * 64,
            "delivery_promise": "teacher_explainer", "scenes": [
        {"scene_index": i + 1, "scene_type": "technical_fact", "narration": f"narration {i}",
         "on_screen_knowledge": f"knowledge {i}", "information_role": "explain_verified_fact",
         "narrative_role": "explain", "shot_intent": "reveal evidence progressively", "visual_type": kind,
         "motion": "progressive_reveal", "transition": "cut", "fallback_visual": "accessible_text_card",
         "source_refs": [f"fact{i}"]} for i, kind in enumerate(kinds)]}


def _timing(plan_bytes: bytes) -> dict:
    return {"schema_version": "1.0", "scene_plan": {"sha256": hashlib.sha256(plan_bytes).hexdigest()},
            "script": {"sha256": "a" * 64}, "visual_duration_seconds": 5, "timing": {"fps": 30},
            "segments": [{"index": i + 1, "scene_start_microseconds": i * 1_000_000,
                          "scene_end_microseconds": (i + 1) * 1_000_000} for i in range(5)]}


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    plan_path = tmp_path / "scene_plan.json"
    plan_path.write_text(json.dumps(_scene_plan()), encoding="utf-8")
    timing_path = tmp_path / "timing.json"
    timing_path.write_text(json.dumps(_timing(plan_path.read_bytes())), encoding="utf-8")
    return plan_path, timing_path


def test_visual_inputs_accept_five_scene_technical_explainer(tmp_path: Path) -> None:
    plan, timing = _write_inputs(tmp_path)
    result = validate_visual_inputs(plan, timing, aspect="16:9")
    assert result["delivery_promise"] == "teacher_explainer"
    assert result["slideshow"]["verdict"] in {"strong", "acceptable"}
    assert result["pacing"]["valid"] is True
    assert result["canvas"] == {"width": 1920, "height": 1080}


@pytest.mark.parametrize(("mutation", "error"), [
    ("knowledge", "visible_knowledge_required"), ("source", "source_refs_required"),
    ("variety", "visual_type_repetition"), ("promise", "delivery_promise_invalid")])
def test_visual_inputs_reject_semantic_contract_violations(tmp_path: Path, mutation: str, error: str) -> None:
    value = _scene_plan()
    if mutation == "knowledge": value["scenes"][0]["on_screen_knowledge"] = ""
    if mutation == "source": value["scenes"][0]["source_refs"] = []
    if mutation == "variety":
        for scene in value["scenes"][:3]: scene["visual_type"] = "checklist"
    if mutation == "promise": value["delivery_promise"] = "motion_led"
    plan_path = tmp_path / "scene_plan.json"
    plan_path.write_text(json.dumps(value), encoding="utf-8")
    timing_path = tmp_path / "timing.json"
    timing_path.write_text(json.dumps(_timing(plan_path.read_bytes())), encoding="utf-8")
    with pytest.raises(ValueError, match=error): validate_visual_inputs(plan_path, timing_path, aspect="9:16")


def test_visual_inputs_reject_hash_and_boundary_mismatch(tmp_path: Path) -> None:
    plan, timing = _write_inputs(tmp_path)
    value = json.loads(timing.read_text(encoding="utf-8"))
    value["segments"][2]["scene_start_microseconds"] += 1
    timing.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="scene_boundaries_not_contiguous"): validate_visual_inputs(plan, timing, aspect="16:9")
    value["segments"][2]["scene_start_microseconds"] -= 1
    value["scene_plan"]["sha256"] = "0" * 64
    timing.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="scene_plan_hash_mismatch"): validate_visual_inputs(plan, timing, aspect="16:9")


def test_renderer_command_is_argument_safe_and_e_drive_only(tmp_path: Path) -> None:
    plan, timing = _write_inputs(tmp_path)
    output = Path("E:/runtime/job one/visual_master.mp4")
    command = build_renderer_command(node="node", scene_plan=plan, timing_manifest=timing, output=output,
        report=Path("E:/runtime/job one/render_report.json"), stills_dir=Path("E:/runtime/job one/stills"),
        clips_dir=Path("E:/runtime/job one/clips"), renderer=Path("E:/repo/scripts/render_phase1_topic_visual.mjs"))
    assert command[command.index("--output") + 1] == str(output.resolve())
    with pytest.raises(ValueError, match="renderer_output_must_use_e_drive"):
        build_renderer_command(node="node", scene_plan=plan, timing_manifest=timing, output=Path("C:/bad.mp4"),
            report=Path("E:/r.json"), stills_dir=Path("E:/s"), clips_dir=Path("E:/c"), renderer=Path("E:/r.mjs"))


def test_contact_sheet_is_created_from_midpoint_stills(tmp_path: Path) -> None:
    from PIL import Image
    stills = []
    for index in range(5):
        path = tmp_path / f"scene_{index + 1}.png"
        Image.new("RGB", (160, 90), (20 + index * 20, 40, 80)).save(path)
        stills.append(path)
    output = tmp_path / "contact_sheet.png"
    result = assemble_contact_sheet(stills, output)
    assert output.is_file() and result["scene_count"] == 5
    assert result["sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
