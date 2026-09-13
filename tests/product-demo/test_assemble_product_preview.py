from __future__ import annotations

import hashlib

import pytest

from scripts.assemble_product_preview import (
    build_ass,
    build_srt,
    escape_subtitle_path,
    _subtitle_filter,
    wrap_subtitle,
)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_wrap_subtitle_is_two_lines_and_bounded() -> None:
    result = wrap_subtitle("逐星，把找机位、看天气、挑时间，放进同一个地图工作台。")
    lines = result.splitlines()
    assert len(lines) == 2
    assert all(len(line) <= 18 for line in lines)


def test_build_srt_uses_measured_voice_range() -> None:
    text = "实测字幕"
    timing = {
        "segments": [
            {
                "index": 1,
                "start_microseconds": 1_200_000,
                "end_microseconds": 3_400_000,
                "scene_end_microseconds": 5_000_000,
                "subtitle_sha256": _sha(text),
            }
        ]
    }
    script = {"beats": [{"subtitle": text}]}
    srt = build_srt(timing, script)
    assert "00:00:01,200 --> 00:00:03,400" in srt
    assert "实测字幕" in srt


def test_build_srt_rejects_tampered_subtitle() -> None:
    timing = {
        "segments": [
            {
                "index": 1,
                "start_microseconds": 0,
                "end_microseconds": 1_000_000,
                "scene_end_microseconds": 2_000_000,
                "subtitle_sha256": "0" * 64,
            }
        ]
    }
    with pytest.raises(ValueError, match="subtitle_hash_mismatch"):
        build_srt(timing, {"beats": [{"subtitle": "不可伪造"}]})


def test_subtitle_path_escapes_windows_drive_colon() -> None:
    assert escape_subtitle_path("E:\\promo\\captions.srt") == "E\\:/promo/captions.srt"


def test_ass_captions_bind_portrait_playres() -> None:
    text = "字幕"
    timing = {"segments": [{"index": 1, "start_microseconds": 0, "end_microseconds": 1_000_000, "scene_end_microseconds": 2_000_000, "subtitle_sha256": _sha(text)}]}
    ass = build_ass(timing, {"beats": [{"subtitle": text}]})
    assert "PlayResX: 1080" in ass and "PlayResY: 1920" in ass
    assert "Dialogue: 0,0:00:00.00,0:00:01.00" in ass


def test_subtitle_filter_uses_explicit_ass_playres() -> None:
    assert _subtitle_filter(__import__("pathlib").Path("E:/promo/captions.ass")).startswith("ass='")
