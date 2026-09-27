from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from video_factory.pipeline import audio_planner, review_package
from video_factory.pipeline.errors import FactoryContractError


def test_align_audio_rejects_overflow_instead_of_trimming(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source = tmp_path / "seg.wav"
    source.write_bytes(b"source")
    monkeypatch.setattr(audio_planner, "_get_audio_duration", lambda _path: 3.0)
    with pytest.raises(audio_planner.AudioNarrationOverflowError, match="audio_narration_overflow"):
        audio_planner._align_audio(source, tmp_path / "aligned.wav", target_duration=2.0)


def test_plan_tts_rejects_overflow_before_alignment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_voice(_text: str, output: Path, *, voice: str, provider: str) -> Path:
        output.write_bytes(b"wav")
        return output

    monkeypatch.setattr(audio_planner, "generate_voice", fake_voice)
    monkeypatch.setattr(audio_planner, "_get_audio_duration", lambda _path: 3.0)
    with pytest.raises(audio_planner.AudioNarrationOverflowError, match="audio_narration_overflow"):
        audio_planner._plan_tts(
            {"scenes": [{"scene_id": "s01", "narration": "旁白", "duration": 2.0}], "total_duration_seconds": 2.0},
            tmp_path,
            "voice",
            "windows-sapi",
        )
    assert not (tmp_path / "audio.wav").exists()


def test_review_package_rejects_overflow_evidence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    work = tmp_path / "job"
    work.mkdir()
    output = work / "final_master.mp4"
    output.write_bytes(b"fake-mp4")
    (work / "subtitle.srt").write_text("1\n00:00:00,000 --> 00:00:05,000\n字幕\n", encoding="utf-8")
    (work / "timeline.json").write_text(json.dumps({"scenes": [{}]}), encoding="utf-8")
    (work / "run_report.json").write_text(json.dumps({
        "job_id": "phase1_modbus", "status": "success",
        "audio_plan": {"mode": "tts", "segments_count": 1, "segments": [{
            "actual_duration": 6.0, "scene_duration": 5.0, "overflow": True,
        }]},
    }), encoding="utf-8")
    (work / "render_report.json").write_text(json.dumps({
        "resolution": {"width": 1080, "height": 1920}, "fps": 30.0, "codec": "h264",
        "audio": {"codec": "aac"}, "subtitle": {"present": True, "mode": "burned_in", "cue_count": 1},
        "layout_mode": "plain_vertical", "subtitle_region": {"x": 90, "y": 1400, "width": 900, "height": 300},
    }), encoding="utf-8")
    with pytest.raises(FactoryContractError, match="phase1_review_narration_incomplete"):
        review_package.build_review_package(
            work_dir=work, output_path=output, job_id="phase1_modbus", input_mode="topic",
            title="测试", scene_count=1, asset_selection={},
        )
