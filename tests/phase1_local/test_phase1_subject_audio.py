from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.factory import phase1_subject_audio
from src.factory.phase1_topic import build_director_script, build_scene_plan, build_topic_request
from src.factory.assets.pink_pig.loader import load_registry
from video_factory.pipeline.narration_timing import validate_narration_claims
from scripts.phase1_jianying_timing import load_manifest


ROOT = Path(__file__).resolve().parents[2]


def _i2c_plan(tmp_path: Path) -> tuple[Path, Path, Path, dict]:
    research = json.loads((ROOT / "examples/phase1_subject_i2c/research_brief.json").read_text(encoding="utf-8"))
    request = build_topic_request(subject=research["topic"], duration=40, aspect="9:16")
    prose = (
        "为什么I2C总线要上拉？I2C线路通常采用开漏结构；器件主动拉低，释放后由上拉电阻恢复高电平。"
        "上拉电阻与总线电容决定上升沿；电阻过大可能使线路来不及达到有效高电平。"
        "电阻过小则增加低电平灌电流，可能超出器件的拉低能力；阻值必须兼顾两端限制。"
    )
    script = build_director_script(request, research, {"script": prose})
    plan = build_scene_plan(script, research)
    request_path = tmp_path / "topic_request.json"; request_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
    script_path = tmp_path / "director_script.json"; script_path.write_text(json.dumps(script, ensure_ascii=False), encoding="utf-8")
    plan_path = tmp_path / "scene_plan.json"; plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    return script_path, plan_path, request_path, research


def test_subject_audio_storyboard_is_timing_only_and_technical_cut(tmp_path: Path) -> None:
    script_path, _, _, _ = _i2c_plan(tmp_path)
    script = json.loads(script_path.read_text(encoding="utf-8"))
    registry = load_registry(repo_root=ROOT)
    storyboard = phase1_subject_audio.build_subject_audio_storyboard(script, registry=registry, aspect="9:16")
    assert storyboard["globals"]["transition_mode"] == "technical_cut"
    assert [scene["scene_id"] for scene in storyboard["scenes"]] == [f"s{i:02d}" for i in range(1, 6)]
    assert all(scene["asset_id"] == registry.default_asset_id for scene in storyboard["scenes"])


def test_shared_narration_claim_contract_accepts_i2c_source_facts(tmp_path: Path) -> None:
    script_path, _, _, research = _i2c_plan(tmp_path)
    script = json.loads(script_path.read_text(encoding="utf-8"))
    factual = phase1_subject_audio.build_subject_audio_factual_brief(research)
    result = validate_narration_claims(script, factual)
    assert result["status"] == "passed"
    assert {item["fact_id"] for item in result["checks"]} == {"open_drain", "rise_time", "sink_current"}


def test_shared_narration_claim_contract_rejects_contradictory_i2c_prose(tmp_path: Path) -> None:
    script_path, _, _, research = _i2c_plan(tmp_path)
    script = json.loads(script_path.read_text(encoding="utf-8"))
    script["beats"][1]["narration"] = "I2C使用推挽输出，不需要上拉电阻。"
    factual = phase1_subject_audio.build_subject_audio_factual_brief(research)
    import pytest

    with pytest.raises(ValueError, match="narration_fact_claim_missing"):
        validate_narration_claims(script, factual)


def test_subject_source_aligned_adapter_persists_manifest_and_integrity_without_render(
    tmp_path: Path, monkeypatch
) -> None:
    script_path, plan_path, request_path, research = _i2c_plan(tmp_path)
    aligned_root = tmp_path / "source_aligned" / "narration_pass_0" / "aligned"
    audio_root = tmp_path / "source_aligned" / "narration_pass_0"
    aligned_root.mkdir(parents=True)
    (audio_root / "audio.wav").write_bytes(b"concatenated")
    segments = []
    offsets = []
    integrity = {"status": "passed", "segments_in_order": True, "expected_endpoint_seconds": 40.0, "actual_endpoint_seconds": 40.0}
    for index in range(1, 6):
        filename = f"aligned_{index-1:03d}.wav"
        (aligned_root / filename).write_bytes(f"aligned-{index}".encode())
        segments.append({
            "scene_id": f"s{index:02d}",
            "aligned_audio_file": filename,
            "raw_audio_sha256": hashlib.sha256(f"raw-{index}".encode()).hexdigest(),
            "audio_integrity": {"status": "passed", "prefix_match": True, "tail_is_silence": True},
        })
        offsets.append({"scene_id": f"s{index:02d}", "start_seconds": float((index - 1) * 8), "end_seconds": float(index * 8)})

    captured = {}

    def fake_planner(**kwargs):
        captured.update(kwargs)
        return {
            "timeline": {"total_duration_seconds": 40.0},
            "audio_path": audio_root / "audio.wav",
            "segments": tuple(segments),
            "objective_audio_integrity": {**integrity, "scene_offsets": offsets},
            "original_script_sha256": "a" * 64,
            "final_script_sha256": "b" * 64,
            "final_timeline_sha256": "c" * 64,
            "final_srt_sha256": "d" * 64,
        }

    monkeypatch.setattr(phase1_subject_audio, "plan_source_aligned_narration", fake_planner)
    result = phase1_subject_audio.build_subject_source_aligned_audio(
        script_path=script_path,
        scene_plan_path=plan_path,
        topic=json.loads(request_path.read_text(encoding="utf-8")),
        research=research,
        repo_root=ROOT,
        work_dir=tmp_path / "media",
        timing_root=tmp_path / "media" / "timing",
    )
    manifest = json.loads(result["manifest_path"].read_text(encoding="utf-8"))
    persisted = json.loads(result["audio_integrity_path"].read_text(encoding="utf-8"))
    loaded = load_manifest(result["manifest_path"], drafts_root=result["timing_root"])
    assert captured["factual_brief"]["facts"][0]["fact_id"] == "open_drain"
    assert {item["source_id"] for item in captured["factual_brief"]["sources"]} == {"nxp_um10204", "ti_slva689"}
    assert all(source_id in {item["source_id"] for item in captured["factual_brief"]["sources"]} for fact in captured["factual_brief"]["facts"] for source_id in fact["source_ids"])
    assert captured["storyboard"]["globals"]["transition_mode"] == "technical_cut"
    assert manifest["source_aligned_narration"] is True
    assert manifest["voice"]["source_kind"] == "shared_source_aligned_narration"
    assert manifest["source_aligned_audio"]["audio_integrity_ref"] == "audio_integrity.json"
    assert loaded["voice"]["source_kind"] == "shared_source_aligned_narration"
    assert persisted["objective"]["status"] == "passed"
    assert len(manifest["segments"]) == 5
    assert not list((tmp_path / "media").glob("*.mp4"))
