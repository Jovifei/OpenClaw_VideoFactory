from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.factory.phase1_topic import build_director_script, build_research_brief, build_scene_plan, build_topic_request
from src.factory.phase1_topic_visual import assemble_contact_sheet, build_renderer_command, validate_visual_inputs, verify_report_artifacts


def _task2_outputs(aspect: str = "16:9") -> tuple[dict, dict]:
    research = build_research_brief(topic="看门狗", sources=[{"id":"s1","url":"https://vendor.example/a","title":"手册","kind":"official_document"},{"id":"s2","url":"https://lab.example/b","title":"研究","kind":"research_paper"}], facts=[{"id":"f1","claim":"看门狗检测软件失去响应。","source_ids":["s1"]},{"id":"f2","claim":"窗口由最坏执行时间决定。","source_ids":["s1","s2"]}])
    request = build_topic_request(subject="看门狗窗口", duration=40, aspect=aspect)
    script = build_director_script(request, research, {"script":"为什么系统复位？看门狗检测软件失去响应。窗口由最坏执行时间决定。"})
    return script, build_scene_plan(script, research)


def _timing(script_bytes: bytes, plan_bytes: bytes, count: int) -> dict:
    return {"schema_version": "1.0", "scene_plan": {"sha256": hashlib.sha256(plan_bytes).hexdigest()},
            "script": {"sha256": hashlib.sha256(script_bytes).hexdigest()}, "visual_duration_seconds": count, "timing": {"fps": 30},
            "segments": [{"index": i + 1, "scene_start_microseconds": i * 1_000_000,
                          "scene_end_microseconds": (i + 1) * 1_000_000} for i in range(count)]}


def _write_inputs(tmp_path: Path, aspect: str = "16:9") -> tuple[Path, Path, Path]:
    script, plan = _task2_outputs(aspect)
    script_path = tmp_path / "director_script.json"
    script_path.write_text(json.dumps(script), encoding="utf-8")
    plan_path = tmp_path / "scene_plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    timing_path = tmp_path / "timing.json"
    timing_path.write_text(json.dumps(_timing(script_path.read_bytes(), plan_path.read_bytes(), len(plan["scenes"]))), encoding="utf-8")
    return script_path, plan_path, timing_path


@pytest.mark.parametrize(("aspect", "canvas"), [("16:9", {"width":1920,"height":1080}), ("9:16", {"width":1080,"height":1920})])
def test_visual_inputs_accept_genuine_task2_outputs(tmp_path: Path, aspect: str, canvas: dict) -> None:
    script, plan, timing = _write_inputs(tmp_path, aspect)
    result = validate_visual_inputs(script, plan, timing, aspect=aspect)
    assert result["delivery_promise"] == "teacher_explainer"
    assert result["slideshow"]["verdict"] in {"strong", "acceptable"}
    assert result["pacing"]["valid"] is True
    assert result["canvas"] == canvas
    assert set(result["scene_plan"]) == {"schema_version", "script_id", "scenes"}


@pytest.mark.parametrize(("mutation", "error"), [
    ("knowledge", "visible_knowledge_required"), ("source", "source_refs_required"),
    ("variety", "visual_type_repetition"), ("promise", "information_role_invalid")])
def test_visual_inputs_reject_semantic_contract_violations(tmp_path: Path, mutation: str, error: str) -> None:
    script_value, value = _task2_outputs("9:16")
    if mutation == "knowledge": value["scenes"][1]["on_screen_knowledge"] = ""
    if mutation == "source": value["scenes"][1]["source_refs"] = []
    if mutation == "variety":
        for scene in value["scenes"][:3]: scene["visual_type"] = "checklist"
    if mutation == "promise": value["scenes"][1]["information_role"] = "cinematic_motion"
    script_path = tmp_path / "director_script.json"
    script_path.write_text(json.dumps(script_value), encoding="utf-8")
    plan_path = tmp_path / "scene_plan.json"
    plan_path.write_text(json.dumps(value), encoding="utf-8")
    timing_path = tmp_path / "timing.json"
    timing_path.write_text(json.dumps(_timing(script_path.read_bytes(), plan_path.read_bytes(), len(value["scenes"]))), encoding="utf-8")
    with pytest.raises(ValueError, match=error): validate_visual_inputs(script_path, plan_path, timing_path, aspect="9:16")


def test_visual_inputs_reject_hash_and_boundary_mismatch(tmp_path: Path) -> None:
    script, plan, timing = _write_inputs(tmp_path)
    value = json.loads(timing.read_text(encoding="utf-8"))
    value["segments"][2]["scene_start_microseconds"] += 1
    timing.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="scene_boundaries_not_contiguous"): validate_visual_inputs(script, plan, timing, aspect="16:9")
    value["segments"][2]["scene_start_microseconds"] -= 1
    value["scene_plan"]["sha256"] = "0" * 64
    timing.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="scene_plan_hash_mismatch"): validate_visual_inputs(script, plan, timing, aspect="16:9")


def test_renderer_command_is_argument_safe_and_e_drive_only(tmp_path: Path) -> None:
    script, plan, timing = _write_inputs(tmp_path)
    output = Path("E:/runtime/job one/visual_master.mp4")
    command = build_renderer_command(node="node", script=script, scene_plan=plan, timing_manifest=timing, aspect="16:9", output=output,
        report=Path("E:/runtime/job one/render_report.json"), stills_dir=Path("E:/runtime/job one/stills"),
        clips_dir=Path("E:/runtime/job one/clips"), renderer=Path("E:/repo/scripts/render_phase1_topic_visual.mjs"))
    assert command[command.index("--output") + 1] == str(output.resolve())
    assert command[command.index("--script") + 1] == str(script.resolve())
    assert command[command.index("--aspect") + 1] == "16:9"
    with pytest.raises(ValueError, match="renderer_output_must_use_e_drive"):
        build_renderer_command(node="node", script=script, scene_plan=plan, timing_manifest=timing, aspect="16:9", output=Path("C:/bad.mp4"),
            report=Path("E:/r.json"), stills_dir=Path("E:/s"), clips_dir=Path("E:/c"), renderer=Path("E:/r.mjs"))


def test_long_variable_text_fails_layout_preflight(tmp_path: Path) -> None:
    script, plan, timing = _write_inputs(tmp_path)
    value = json.loads(plan.read_text(encoding="utf-8"))
    value["scenes"][1]["on_screen_knowledge"] = "超长技术知识" * 40
    plan.write_text(json.dumps(value), encoding="utf-8")
    timing_value = json.loads(timing.read_text(encoding="utf-8"))
    timing_value["scene_plan"]["sha256"] = hashlib.sha256(plan.read_bytes()).hexdigest()
    timing.write_text(json.dumps(timing_value), encoding="utf-8")
    with pytest.raises(ValueError, match="layout_text_overflow_preflight"):
        validate_visual_inputs(script, plan, timing, aspect="16:9")


def test_remotion_layout_measurement_uses_pinned_layout_utils() -> None:
    source = (Path(__file__).resolve().parents[2] / "remotion" / "src" / "TechnicalExplainer.tsx").read_text(encoding="utf-8")
    package = json.loads((Path(__file__).resolve().parents[2] / "remotion" / "package.json").read_text(encoding="utf-8"))
    assert package["dependencies"]["@remotion/layout-utils"] == "4.0.500"
    assert all(name in source for name in ("measureText", "fitText", "fillTextBox"))
    assert "getBoundingClientRect" not in source
    assert "delayRender" not in source


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


def _artifact_report(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    stills, clips = tmp_path / "stills", tmp_path / "clips"
    stills.mkdir(); clips.mkdir()
    entries = []
    for index in range(2):
        still = stills / f"scene_{index + 1:02d}_mid.png"; still.write_bytes(f"still{index}".encode())
        clip = clips / f"scene_{index + 1:02d}.mp4"; clip.write_bytes(f"clip{index}".encode())
        entries.append({"scene_index": index + 1, "still": {"filename": still.relative_to(tmp_path).as_posix(), "sha256": hashlib.sha256(still.read_bytes()).hexdigest()}, "clip": {"filename": clip.relative_to(tmp_path).as_posix(), "sha256": hashlib.sha256(clip.read_bytes()).hexdigest()}})
    output = tmp_path / "visual_master.mp4"; output.write_bytes(b"master")
    report = tmp_path / "render_report.json"
    report.write_text(json.dumps({"visual": {"filename": output.name, "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "scene_timing": entries}}), encoding="utf-8")
    return report, output, stills, clips


def test_report_artifacts_verify_declared_current_set(tmp_path: Path) -> None:
    report, output, stills, clips = _artifact_report(tmp_path)
    result = verify_report_artifacts(report, output, stills, clips, scene_count=2)
    assert [path.name for path in result["stills"]] == ["scene_01_mid.png", "scene_02_mid.png"]


@pytest.mark.parametrize(("mutation", "error"), [("stale", "artifact_directory_contaminated"), ("hash", "artifact_hash_mismatch"), ("escape", "artifact_path_escape")])
def test_report_artifacts_reject_stale_tamper_and_escape(tmp_path: Path, mutation: str, error: str) -> None:
    report, output, stills, clips = _artifact_report(tmp_path)
    value = json.loads(report.read_text(encoding="utf-8"))
    if mutation == "stale": (stills / "scene_99_mid.png").write_bytes(b"stale")
    if mutation == "hash": value["visual"]["scene_timing"][0]["still"]["sha256"] = "0" * 64
    if mutation == "escape": value["visual"]["scene_timing"][0]["still"]["filename"] = "../escape.png"
    report.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match=error): verify_report_artifacts(report, output, stills, clips, scene_count=2)
