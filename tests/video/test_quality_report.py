from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.render_report import build_render_report

from . import ROOT


def _probe(*, audio: bool = True) -> dict:
    return {
        "duration": 12.5,
        "has_audio": audio,
        "video": {"codec": "h264", "width": 1080, "height": 1920, "fps": "30/1"},
        "audio": {"codec": "aac", "sample_rate": "24000"} if audio else {},
    }


def _timeline() -> dict:
    return {
        "scenes": [
            {"asset_id": "pink_pig.normal.v1"},
            {"asset_id": "pink_pig.normal.v1"},
            {"asset_id": "pink_pig.success.v1"},
        ]
    }


def test_report_contains_required_quality_fields(tmp_path: Path) -> None:
    subtitle = tmp_path / "subtitle.srt"
    subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\n字幕\n", encoding="utf-8")
    report = build_render_report(
        ffprobe_meta=_probe(),
        timeline=_timeline(),
        subtitle_path=subtitle,
        captions_count=3,
    )
    assert report["duration"] == 12.5
    assert report["resolution"] == {"width": 1080, "height": 1920}
    assert report["fps"] == 30.0
    assert report["codec"] == "h264"
    assert report["audio"] == {"present": True, "codec": "aac", "sample_rate": 24000}
    assert report["subtitle"] == {"present": True, "mode": "burned_in", "cue_count": 3}
    assert report["asset_ids"] == [
        "pink_pig.normal.v1",
        "pink_pig.normal.v1",
        "pink_pig.success.v1",
    ]


def test_report_handles_video_without_audio(tmp_path: Path) -> None:
    report = build_render_report(
        ffprobe_meta=_probe(audio=False),
        timeline=_timeline(),
        subtitle_path=tmp_path / "missing.srt",
        captions_count=0,
    )
    assert report["audio"] == {"present": False, "codec": "", "sample_rate": None}
    assert report["subtitle"] == {"present": False, "mode": "disabled", "cue_count": 0}


def test_invalid_probe_fails_without_a_success_report(tmp_path: Path) -> None:
    with pytest.raises(FactoryContractError) as excinfo:
        build_render_report(
            ffprobe_meta={"error": "ffprobe_failed"},
            timeline=_timeline(),
            subtitle_path=tmp_path / "subtitle.srt",
            captions_count=1,
        )
    assert excinfo.value.code == "render_report_probe_failed"
    assert set(excinfo.value.to_dict()) == {"code", "message", "context"}


def test_report_is_json_serializable(tmp_path: Path) -> None:
    subtitle = tmp_path / "subtitle.srt"
    subtitle.write_text("字幕", encoding="utf-8")
    report = build_render_report(
        ffprobe_meta=_probe(),
        timeline=_timeline(),
        subtitle_path=subtitle,
        captions_count=1,
    )
    json.dumps(report, ensure_ascii=False)


def test_generated_offline_render_report_matches_real_mp4() -> None:
    report_path = ROOT / "dist" / "story_demo_offline" / "render_report.json"
    mp4_path = ROOT / "dist" / "pink_pig_story_demo_offline.mp4"
    assert report_path.is_file()
    assert mp4_path.is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(mp4_path)],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    data = json.loads(probe.stdout)
    video = next(stream for stream in data["streams"] if stream.get("codec_type") == "video")
    audio = next(stream for stream in data["streams"] if stream.get("codec_type") == "audio")
    assert report["codec"] == video["codec_name"]
    assert report["resolution"] == {"width": video["width"], "height": video["height"]}
    assert report["audio"]["codec"] == audio["codec_name"]
    assert report["audio"]["sample_rate"] == int(audio["sample_rate"])
    assert report["duration"] == pytest.approx(float(data["format"]["duration"]), abs=0.2)
