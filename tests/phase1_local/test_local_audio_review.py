from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import jsonschema
import pytest

from video_factory.pipeline import audio_planner, review_package, voice_generator
from video_factory.pipeline.errors import FactoryContractError


def test_windows_sapi_uses_stdin_for_narration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    observed: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        observed["command"] = command
        observed["input"] = kwargs.get("input")
        environment = kwargs.get("env")
        assert isinstance(environment, dict)
        Path(str(environment["PINK_PIG_SAPI_OUTPUT"])).write_bytes(b"RIFFfake")
        observed["voice"] = environment["PINK_PIG_SAPI_VOICE"]
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(voice_generator.shutil, "which", lambda _: "powershell.exe")
    monkeypatch.setattr(voice_generator.subprocess, "run", fake_run)

    text = "本地旁白不可出现在命令行"
    output = voice_generator.generate_voice(text, tmp_path / "scene.wav", provider="windows-sapi", voice="Microsoft Huihui")

    assert output.is_file()
    assert observed["input"] == text
    assert text not in " ".join(observed["command"])
    assert "-NoProfile" in observed["command"]
    assert observed["voice"] == "Microsoft Huihui"


def test_local_sapi_tts_is_allowed_when_network_is_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    called: dict[str, object] = {}

    def fake_tts(*args: object, **kwargs: object) -> audio_planner.AudioPlan:
        called["provider"] = args[3]
        return audio_planner.AudioPlan("tts", tmp_path / "audio.wav", False, None, ({"actual_duration": 1.0},))

    monkeypatch.setattr(audio_planner, "_plan_tts", fake_tts)
    plan = audio_planner.plan_audio(
        {"scenes": [{"duration": 1.0}]},
        work_dir=tmp_path,
        audio_config={"strategy": "tts_with_offline_fallback", "allow_network": False, "tts": {"provider": "windows-sapi"}},
        repo_root=tmp_path,
    )

    assert plan.mode == "tts"
    assert called["provider"] == "windows-sapi"


def _write_evidence(work_dir: Path, output: Path) -> None:
    output.write_bytes(b"fake-mp4")
    (work_dir / "subtitle.srt").write_text("1\n00:00:00,000 --> 00:00:05,000\n字幕\n", encoding="utf-8")
    (work_dir / "timeline.json").write_text(json.dumps({"scenes": [{}, {}, {}, {}, {}]}), encoding="utf-8")
    (work_dir / "run_report.json").write_text(json.dumps({
        "job_id": "phase1_modbus", "status": "success", "audio_plan": {"mode": "tts", "segments_count": 5},
    }), encoding="utf-8")
    (work_dir / "render_report.json").write_text(json.dumps({
        "resolution": {"width": 1080, "height": 1920}, "fps": 30.0, "codec": "h264",
        "audio": {"codec": "aac"}, "subtitle": {"present": True, "mode": "burned_in", "cue_count": 5},
        "layout_mode": "knowledge_illustration", "style_profile": {"status": "pass"},
        "subtitle_region": {"x": 90, "y": 1120, "width": 900, "height": 460},
    }), encoding="utf-8")


def test_build_review_package_writes_relative_hashed_artifacts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    work_dir = tmp_path / "job"
    work_dir.mkdir()
    output = work_dir / "final_master.mp4"
    _write_evidence(work_dir, output)
    media = {"duration_seconds": 28.0, "width": 1080, "height": 1920, "fps": 30.0, "video_codec": "h264", "audio_codec": "aac"}
    monkeypatch.setattr(review_package, "_probe_media", lambda _: media)
    monkeypatch.setattr(review_package, "_decode_media", lambda _: None)
    monkeypatch.setattr(review_package, "_extract_cover", lambda _source, target: target.write_bytes(b"png"))

    result = review_package.build_review_package(
        work_dir=work_dir,
        output_path=output,
        job_id="phase1_modbus",
        input_mode="topic",
        title="小粉猪讲 Modbus",
        scene_count=5,
        asset_selection={"asset_ids": ["pink_pig.knowledge_summary.v1"]},
    )

    assert result["quality"]["status"] == "passed"
    manifest = json.loads((work_dir / "review_package.json").read_text(encoding="utf-8"))
    quality = json.loads((work_dir / "quality_report.json").read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[2]
    jsonschema.Draft202012Validator(json.loads((root / "schemas/video/phase1_review_package.schema.json").read_text(encoding="utf-8"))).validate(manifest)
    jsonschema.Draft202012Validator(json.loads((root / "schemas/video/phase1_quality_report.schema.json").read_text(encoding="utf-8"))).validate(quality)
    assert manifest["status"] == "ready_for_human_review"
    assert all(":" not in item["path"] and not Path(item["path"]).is_absolute() for item in manifest["artifacts"])
    assert len(manifest["artifacts"]) == 6
    assert (work_dir / "quality_report.json").is_file()


def test_review_package_rejects_incomplete_narration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    work_dir = tmp_path / "job"
    work_dir.mkdir()
    output = work_dir / "final_master.mp4"
    _write_evidence(work_dir, output)
    report = json.loads((work_dir / "run_report.json").read_text(encoding="utf-8"))
    report["audio_plan"]["segments_count"] = 4
    (work_dir / "run_report.json").write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(FactoryContractError) as caught:
        review_package.build_review_package(
            work_dir=work_dir, output_path=output, job_id="phase1_modbus", input_mode="topic",
            title="小粉猪讲 Modbus", scene_count=5, asset_selection={},
        )
    assert caught.value.code == "phase1_review_narration_incomplete"


def test_local_reference_review_package_requires_five_evidence_documents(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    work_dir = tmp_path / "job"
    work_dir.mkdir()
    output = work_dir / "final_master.mp4"
    _write_evidence(work_dir, output)
    run_report = json.loads((work_dir / "run_report.json").read_text(encoding="utf-8"))
    run_report["job_id"] = "phase1_ref_test"
    (work_dir / "run_report.json").write_text(json.dumps(run_report), encoding="utf-8")
    source_sha = "a" * 64
    topic = "测试主题"
    topic_digest = __import__("hashlib").sha256(topic.encode("utf-8")).hexdigest()
    evidence = {
        "reference_receipt.json": {
            "schema_version": "1.0", "reference_id": "ref_" + "a" * 24,
            "source_mode": "owned_or_licensed_local_video", "source_name": "source.mp4",
            "source_sha256": source_sha, "stored_path": "input/reference_videos/" + source_sha + ".mp4",
            "stored_sha256": source_sha, "bytes": 10, "duration_seconds": 1.0,
            "resolution": {"width": 320, "height": 180}, "has_audio": False,
            "processing_timestamp": "2026-08-21T00:00:00Z", "analyzer_policy_version": "reference-analysis-v1",
        },
        "reference_rights.json": {
            "schema_version": "1.0", "rights_basis": "owned", "source_owner": "Jovi",
            "license_reference": "local-test", "source_sha256": source_sha, "processing_timestamp": "2026-08-21T00:00:00Z",
        },
        "reference_report.json": {
            "schema_version": "1.0", "reference_id": "ref_" + "a" * 24, "source_sha256": source_sha,
            "duration_seconds": 1.0, "resolution": {"width": 320, "height": 180},
            "scenes": [{"scene_id": "s01", "start_seconds": 0.0, "end_seconds": 1.0, "duration_seconds": 1.0,
                        "representative_frame_time_seconds": 0.5, "visual_description": "unavailable",
                        "caption_summary": "not extracted", "audio_summary": "no audio"}],
            "style_fingerprint": {"pace": "fast", "shot_density_per_second": 1.0, "median_shot_duration_seconds": 1.0,
                                  "scene_count": 1, "structure_summary": "single_scene"},
            "transcript": [], "asr": {"status": "unavailable", "model": None, "reason": "no_audio_track"},
        },
        "original_brief.json": {
            "schema_version": "1.0", "input_mode": "local_reference", "topic": topic,
            "factual_brief": {
                "schema_version": "1.0", "topic_digest": topic_digest, "review_status": "verified",
                "facts": [{"fact_id": "fact_one", "claim": "A claim.", "source_ids": ["source_a"]}],
                "sources": [
                    {"source_id": "source_a", "title": "A", "publisher": "A", "url": "https://example.test/a", "kind": "standard"},
                    {"source_id": "source_b", "title": "B", "publisher": "B", "url": "https://example.test/b", "kind": "official_document"},
                ],
            },
            "reference_sha256": source_sha,
            "reference_abstraction": {"pace": "fast", "scene_count_band": "1", "median_shot_duration_seconds": 1.0,
                                       "shot_density_per_second": 1.0, "structure": ["hook", "explain", "evidence", "repair", "summary"],
                                       "duration_target_seconds": 30},
        },
        "difference_report.json": {
            "schema_version": "1.0", "job_id": "phase1_ref_test", "status": "ready_for_human_review",
            "reference_sha256": source_sha, "output_sha256": "b" * 64,
            "checks": {"source_output_sha_distinct": "passed", "reference_path_absent": "passed", "registry_assets_only": "passed",
                       "local_sapi_audio": "passed", "source_audio_absent": "passed",
                       "text_similarity": {"status": "unavailable", "score": None, "threshold": 0.3, "method": "unavailable"}},
            "human_review": {"logo_watermark": "human_review_required", "faces": "human_review_required",
                             "perceptual_frame_similarity": "human_review_required", "shot_sequence_similarity": "human_review_required"},
        },
    }
    for name, value in evidence.items():
        (work_dir / name).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(review_package, "_probe_media", lambda _: {"duration_seconds": 28.0, "width": 1080, "height": 1920, "fps": 30.0, "video_codec": "h264", "audio_codec": "aac"})
    monkeypatch.setattr(review_package, "_decode_media", lambda _: None)
    monkeypatch.setattr(review_package, "_extract_cover", lambda _source, target: target.write_bytes(b"png"))

    result = review_package.build_review_package(
        work_dir=work_dir, output_path=output, job_id="phase1_ref_test", input_mode="local_reference",
        title=topic, scene_count=5, asset_selection={"asset_ids": ["pink_pig.knowledge_summary.v1"]},
    )
    manifest = result["manifest"]
    assert len(manifest["artifacts"]) == 11
    assert manifest["reference_evidence"]["difference_report"] == "difference_report.json"
