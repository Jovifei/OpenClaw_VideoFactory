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
