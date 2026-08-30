from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path); assert spec and spec.loader
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value


def test_timing_topic_binding_rejects_script_scene_and_voice_mismatch(tmp_path: Path) -> None:
    timing = _module("scripts/phase1_jianying_timing_probe.py", "topic_timing_probe")
    script = {"script_id":"s1","beats":[{}] * 5}
    plan = {"script_id":"s1","scenes":[{}] * 5}
    timing.validate_scene_plan_binding(script, plan, target_duration_seconds=30, voice_end_microseconds=29_000_000)
    plan["script_id"] = "other"
    with pytest.raises(ValueError, match="scene_plan_script_id_mismatch"): timing.validate_scene_plan_binding(script, plan, target_duration_seconds=30, voice_end_microseconds=29_000_000)
    plan["script_id"] = "s1"; plan["scenes"].pop()
    with pytest.raises(ValueError, match="scene_plan_scene_count_mismatch"): timing.validate_scene_plan_binding(script, plan, target_duration_seconds=30, voice_end_microseconds=29_000_000)
    plan["scenes"].append({})
    with pytest.raises(ValueError, match="voice_exceeds_visual_target"): timing.validate_scene_plan_binding(script, plan, target_duration_seconds=30, voice_end_microseconds=31_000_000)


def test_timing_parser_keeps_scene_plan_optional() -> None:
    timing = _module("scripts/phase1_jianying_timing_probe.py", "topic_timing_parser")
    parsed = timing.build_parser().parse_args(["--script","s.json","--name","n","--manifest","E:/m.json","--skill-root","E:/skill"])
    assert parsed.scene_plan is None


def test_render_report_clip_binding_rejects_tamper_extra_escape_and_duration(tmp_path: Path) -> None:
    draft = _module("scripts/phase1_jianying_tts_draft.py", "topic_draft_contract")
    root = tmp_path / "job"; clips = root / "clips"; clips.mkdir(parents=True)
    entries = []
    for index in range(1, 3):
        clip = clips / f"scene_{index:02d}.mp4"; clip.write_bytes(str(index).encode())
        entries.append({"scene_index":index,"start_seconds":index-1,"end_seconds":index,"clip":{"filename":f"clips/{clip.name}","sha256":draft.sha256(clip),"duration_microseconds":1_000_000}})
    report = root / "render.json"; report.write_text(json.dumps({"visual":{"scene_timing":entries}}), encoding="utf-8")
    segments = [{"index":1,"scene_start_microseconds":0,"scene_end_microseconds":1_000_000},{"index":2,"scene_start_microseconds":1_000_000,"scene_end_microseconds":2_000_000}]
    assert len(draft.verify_scene_clips(report, clips, segments, duration_probe=lambda _: 1_000_000)) == 2
    (clips / "scene_99.mp4").write_bytes(b"x")
    with pytest.raises(ValueError, match="visual_clip_directory_contaminated"): draft.verify_scene_clips(report, clips, segments, duration_probe=lambda _: 1_000_000)
    (clips / "scene_99.mp4").unlink(); entries[0]["clip"]["sha256"] = "0" * 64; report.write_text(json.dumps({"visual":{"scene_timing":entries}}), encoding="utf-8")
    with pytest.raises(ValueError, match="visual_clip_hash_mismatch"): draft.verify_scene_clips(report, clips, segments, duration_probe=lambda _: 1_000_000)
    entries[0]["clip"]["sha256"] = draft.sha256(clips / "scene_01.mp4")
    report.write_text(json.dumps({"visual":{"scene_timing":entries}}), encoding="utf-8")
    with pytest.raises(ValueError, match="visual_clip_duration_drift"): draft.verify_scene_clips(report, clips, segments, duration_probe=lambda _: 2_000_000)
    entries[0]["end_seconds"] = 1.2
    report.write_text(json.dumps({"visual":{"scene_timing":entries}}), encoding="utf-8")
    with pytest.raises(ValueError, match="visual_clip_declaration_timing_mismatch"): draft.verify_scene_clips(report, clips, segments, duration_probe=lambda _: 1_000_000)


@pytest.mark.parametrize("declared", [None, 900_000])
def test_render_report_clip_duration_field_is_required_and_bound(tmp_path: Path, declared: int | None) -> None:
    draft = _module("scripts/phase1_jianying_tts_draft.py", f"topic_clip_duration_{declared}")
    clips = tmp_path / "clips"; clips.mkdir(); clip = clips / "scene_01.mp4"; clip.write_bytes(b"clip")
    clip_value = {"filename":"clips/scene_01.mp4", "sha256":draft.sha256(clip)}
    if declared is not None: clip_value["duration_microseconds"] = declared
    report = tmp_path / "render.json"
    report.write_text(json.dumps({"visual":{"scene_timing":[{"scene_index":1,"start_seconds":0,"end_seconds":1,"clip":clip_value}]}}), encoding="utf-8")
    segment = [{"index":1,"scene_start_microseconds":0,"scene_end_microseconds":1_000_000}]
    with pytest.raises(ValueError, match="visual_clip_declared_duration_invalid"):
        draft.verify_scene_clips(report, clips, segment, duration_probe=lambda _: 1_000_000)


def test_renderer_emits_microsecond_clip_duration_contract() -> None:
    source = (ROOT / "scripts" / "render_phase1_topic_visual.mjs").read_text(encoding="utf-8")
    assert "duration_microseconds:Math.round((scene.end_seconds-scene.start_seconds)*1e6)" in source


def test_preview_render_report_binds_visual_hash(tmp_path: Path) -> None:
    preview = _module("scripts/assemble_jianying_voice_preview.py", "topic_preview_contract")
    visual = tmp_path / "visual.mp4"; visual.write_bytes(b"visual")
    report = tmp_path / "render.json"; report.write_text(json.dumps({"visual":{"filename":"visual.mp4","sha256":preview.sha256(visual)}}), encoding="utf-8")
    preview.verify_visual_report(visual, report)
    visual.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="visual_render_report_hash_mismatch"): preview.verify_visual_report(visual, report)


def test_preview_report_binding_is_exact() -> None:
    preview = _module("scripts/assemble_jianying_voice_preview.py", "topic_preview_report")
    binding = preview.render_report_binding(Path("E:/job/render_report.json"), "a" * 64)
    assert binding == {"filename":"render_report.json", "sha256":"a" * 64}
