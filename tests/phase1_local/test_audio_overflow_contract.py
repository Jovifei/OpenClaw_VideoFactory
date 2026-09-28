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


def test_objective_audio_integrity_accepts_complete_prefix_and_silence_tail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    raw = tmp_path / "raw.wav"
    aligned = tmp_path / "aligned.wav"
    raw.write_bytes(b"raw-container")
    aligned.write_bytes(b"aligned-container")
    raw_pcm = b"\x01\x02\x03\x04"
    aligned_pcm = raw_pcm + b"\x00\x00\x00\x00"
    monkeypatch.setattr(audio_planner, "_probe_pcm_layout", lambda _path: (16000, 1))
    monkeypatch.setattr(
        audio_planner,
        "_decode_pcm_for_integrity",
        lambda path, *, sample_rate, channels: raw_pcm if path == raw else aligned_pcm,
    )

    evidence, layout, decoded = audio_planner._verify_complete_aligned_segment(
        raw, aligned, scene_id="s01"
    )

    assert evidence["status"] == "passed"
    assert evidence["prefix_match"] is True
    assert evidence["tail_is_silence"] is True
    assert evidence["padding_pcm_bytes"] == 4
    assert layout == (16000, 1)
    assert decoded == aligned_pcm


@pytest.mark.parametrize(
    ("aligned_pcm", "reason"),
    [
        (b"\x01\x02", "aligned_pcm_shorter_than_raw"),
        (b"\x01\x09\x03\x04", "aligned_pcm_prefix_mismatch"),
        (b"\x01\x02\x03\x04\x05\x06", "aligned_tail_not_silence"),
    ],
)
def test_objective_audio_integrity_rejects_truncation_or_non_silent_tail(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    aligned_pcm: bytes,
    reason: str,
) -> None:
    raw = tmp_path / "raw.wav"
    aligned = tmp_path / "aligned.wav"
    raw.write_bytes(b"raw-container")
    aligned.write_bytes(b"aligned-container")
    raw_pcm = b"\x01\x02\x03\x04"
    monkeypatch.setattr(audio_planner, "_probe_pcm_layout", lambda _path: (16000, 1))
    monkeypatch.setattr(
        audio_planner,
        "_decode_pcm_for_integrity",
        lambda path, *, sample_rate, channels: raw_pcm if path == raw else aligned_pcm,
    )

    with pytest.raises(audio_planner.AudioNarrationIntegrityError, match=reason):
        audio_planner._verify_complete_aligned_segment(raw, aligned, scene_id="s01")


def test_align_complete_segments_rejects_scene_reordering_and_duplicate_identity(tmp_path: Path) -> None:
    segments = (
        {"scene_id": "s02", "audio_path": str(tmp_path / "s02.wav"), "actual_duration": 1.0},
        {"scene_id": "s01", "audio_path": str(tmp_path / "s01.wav"), "actual_duration": 1.0},
    )
    timeline = {"transition_mode": "technical_cut", "scenes": [{"scene_id": "s01"}, {"scene_id": "s02"}]}
    with pytest.raises(audio_planner.AudioNarrationIntegrityError, match="scene_identity_mismatch"):
        audio_planner.align_complete_segments(
            segments, timeline, output_dir=tmp_path / "aligned", output_path=tmp_path / "audio.wav"
        )


def test_align_complete_segments_rejects_xfade_endpoint_ambiguity(tmp_path: Path) -> None:
    segment = {"scene_id": "s01", "audio_path": str(tmp_path / "s01.wav"), "actual_duration": 1.0}
    timeline = {"transition_mode": "xfade", "scenes": [{"scene_id": "s01"}]}
    with pytest.raises(audio_planner.AudioNarrationIntegrityError, match="transition_mode_not_supported"):
        audio_planner.align_complete_segments(
            (segment,), timeline, output_dir=tmp_path / "aligned", output_path=tmp_path / "audio.wav"
        )


def test_review_package_rejects_overflow_evidence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    work = tmp_path / "job"
    work.mkdir()
    output = work / "final_master.mp4"
    output.write_bytes(b"fake-mp4")
    (work / "subtitle.srt").write_text("1\n00:00:00,000 --> 00:00:05,000\n字幕\n", encoding="utf-8")
    (work / "timeline.json").write_text(json.dumps({"scenes": [{}]}), encoding="utf-8")
    (work / "run_report.json").write_text(json.dumps({
        "job_id": "phase1_modbus", "status": "success",
        "mascot": {"mode": "required"},
        "audio_plan": {"mode": "tts", "segments_count": 1, "segments": [{
            "actual_duration": 6.0, "scene_duration": 5.0, "overflow": True,
        }]},
    }), encoding="utf-8")
    (work / "render_report.json").write_text(json.dumps({
        "resolution": {"width": 1080, "height": 1920}, "fps": 30.0, "codec": "h264",
        "audio": {"codec": "aac"}, "subtitle": {"present": True, "mode": "burned_in", "cue_count": 1},
        "layout_mode": "knowledge_illustration", "style_profile": {"status": "pass"},
        "subtitle_region": {"x": 90, "y": 1400, "width": 900, "height": 300},
    }), encoding="utf-8")
    with pytest.raises(FactoryContractError, match="phase1_review_narration_incomplete"):
        review_package.build_review_package(
            work_dir=work, output_path=output, job_id="phase1_modbus", input_mode="topic",
            title="测试", scene_count=1, asset_selection={},
        )


def test_review_package_accepts_source_aligned_duration_evidence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    work = tmp_path / "job"
    work.mkdir()
    output = work / "final_master.mp4"
    output.write_bytes(b"fake-mp4")
    (work / "subtitle.srt").write_text("1\n00:00:00,000 --> 00:00:28,000\n字幕\n", encoding="utf-8")
    (work / "timeline.json").write_text(json.dumps({"scenes": [{}]}), encoding="utf-8")
    (work / "run_report.json").write_text(json.dumps({
        "job_id": "phase1_modbus", "status": "success",
        "mascot": {"mode": "required"},
        "audio_plan": {"mode": "tts", "segments_count": 1, "segments": [{
            "actual_duration": 7.8, "scene_duration": 4.0, "allocated_scene_duration": 8.0,
            "aligned_duration": 8.0, "overflow": False,
        }]},
    }), encoding="utf-8")
    (work / "render_report.json").write_text(json.dumps({
        "resolution": {"width": 1080, "height": 1920}, "fps": 30.0, "codec": "h264",
        "audio": {"codec": "aac"}, "subtitle": {"present": True, "mode": "burned_in", "cue_count": 1},
        "layout_mode": "knowledge_illustration", "style_profile": {"status": "pass"},
        "subtitle_region": {"x": 90, "y": 1400, "width": 900, "height": 300},
    }), encoding="utf-8")
    monkeypatch.setattr(review_package, "_probe_media", lambda _: {"duration_seconds": 28.0, "width": 1080, "height": 1920, "fps": 30.0, "video_codec": "h264", "audio_codec": "aac"})
    monkeypatch.setattr(review_package, "_decode_media", lambda _: None)
    monkeypatch.setattr(review_package, "_extract_cover", lambda _source, target: target.write_bytes(b"png"))
    result = review_package.build_review_package(
        work_dir=work, output_path=output, job_id="phase1_modbus", input_mode="topic",
        title="测试", scene_count=1, asset_selection={},
    )
    assert result["quality"]["status"] == "passed"


def test_review_package_rejects_source_aligned_without_objective_integrity() -> None:
    run_report = {
        "job_id": "phase1_modbus",
        "status": "success",
        "audio_plan": {
            "mode": "tts",
            "segments_count": 1,
            "segments": [{
                "actual_duration": 1.0,
                "allocated_scene_duration": 1.2,
                "scene_duration": 1.0,
                "overflow": False,
            }],
        },
        "narration_alignment": {
            "mode": "source_aligned_measured_tts",
            "objective_audio_integrity": {"status": "failed"},
        },
    }
    render_report = {
        "subtitle": {"present": True, "mode": "burned_in", "cue_count": 1},
        "mascot": {"mode": "off"},
    }
    with pytest.raises(FactoryContractError, match="phase1_review_narration_incomplete"):
        review_package._validate_evidence_documents(
            run_report=run_report,
            render_report=render_report,
            timeline={"scenes": [{}]},
            job_id="phase1_modbus",
            scene_count=1,
        )


def test_review_package_rejects_source_aligned_without_segment_integrity() -> None:
    run_report = {
        "job_id": "phase1_modbus",
        "status": "success",
        "audio_plan": {
            "mode": "tts",
            "source_aligned_narration": True,
            "segments_count": 1,
            "segments": [{
                "actual_duration": 1.0,
                "allocated_scene_duration": 1.2,
                "scene_duration": 1.0,
                "overflow": False,
            }],
        },
        "narration_alignment": {
            "mode": "source_aligned_measured_tts",
            "objective_audio_integrity": {"status": "passed"},
        },
    }
    with pytest.raises(FactoryContractError, match="phase1_review_narration_incomplete"):
        review_package._validate_evidence_documents(
            run_report=run_report,
            render_report={"subtitle": {"present": True, "mode": "burned_in", "cue_count": 1}, "mascot": {"mode": "off"}},
            timeline={"scenes": [{}]},
            job_id="phase1_modbus",
            scene_count=1,
        )
