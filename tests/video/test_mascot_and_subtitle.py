from __future__ import annotations

from pathlib import Path

import pytest

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.mascot import load_mascot_contract
from video_factory.pipeline.renderer import build_render_command
from video_factory.pipeline.subtitle import build_srt


def _timeline() -> list[dict[str, object]]:
    return [
        {"order": 1, "image": "01.png", "duration": 5.0, "transition": "none"},
    ]


def test_required_mascot_loads_skill_and_style_profile() -> None:
    contract = load_mascot_contract(Path.cwd(), {"mode": "required"})
    assert contract["mode"] == "required"
    assert contract["skill_loaded"] is True


def test_mascot_off_is_explicit_escape_hatch() -> None:
    assert load_mascot_contract(Path.cwd(), {"mode": "off"}) == {"mode": "off", "skill_loaded": False}


def test_missing_required_mascot_skill_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(FactoryContractError) as caught:
        load_mascot_contract(tmp_path, {"mode": "required"})
    assert caught.value.code == "mascot_skill_unavailable"


def test_knowledge_subtitle_style_is_small_and_bottom_safe(tmp_path: Path) -> None:
    subtitle = tmp_path / "subtitle.srt"
    subtitle.write_text("1\n00:00:00,000 --> 00:00:05,000\n短字幕\n", encoding="utf-8")
    command, _ = build_render_command(
        asset_dir=tmp_path,
        timeline=_timeline(),
        subtitle_path=subtitle,
        output_path=tmp_path / "out.mp4",
        transition_seconds=0.4,
        audio_path=None,
    )
    graph = command[command.index("-filter_complex") + 1]
    # Public style is 44 final-video pixels; renderer maps it to the SRT
    # 384x288 libass canvas (7 virtual pixels) before invoking FFmpeg.
    assert "FontSize=7" in graph
    assert "Alignment=2" in graph
    assert "MarginV=38" in graph
    assert "FontSize=96" not in graph


def test_caption_wrap_limits_knowledge_text_to_two_lines(tmp_path: Path) -> None:
    script = tmp_path / "script.txt"
    subtitle = tmp_path / "subtitle.srt"
    script.write_text("参数一致，帧序正确，CRC 通过，数据才能可靠到站。\n", encoding="utf-8")
    captions = build_srt(
        script,
        _timeline(),
        subtitle,
        max_chars_per_line=18,
        max_lines=2,
    )
    assert len(captions) == 1
    assert captions[0]["text"].count("\n") == 1


def test_subtitle_cues_do_not_stack_during_scene_crossfade(tmp_path: Path) -> None:
    script = tmp_path / "script.txt"
    script.write_text("第一幕\n第二幕\n", encoding="utf-8")
    target = tmp_path / "subtitle.srt"
    captions = build_srt(
        script,
        [
            {"duration": 2.0},
            {"duration": 2.0},
        ],
        target,
        transition_seconds=0.4,
    )
    assert captions[0]["end"] <= captions[1]["start"]


def test_audio_gain_is_explicit_in_render_command(tmp_path: Path) -> None:
    subtitle = tmp_path / "subtitle.srt"
    subtitle.write_text("1\n00:00:00,000 --> 00:00:05,000\n短字幕\n", encoding="utf-8")
    # The command contract validates the path via ffprobe, so use the real demo audio.
    from tests.video import ROOT

    command, _ = build_render_command(
        asset_dir=ROOT,
        timeline=_timeline(),
        subtitle_path=subtitle,
        output_path=tmp_path / "out.mp4",
        transition_seconds=0.4,
        audio_path=ROOT / "assets" / "pink_pig" / "demo_music.wav",
        audio_gain=2.0,
    )
    assert "volume=2.000" in command


def test_audio_normalization_is_explicit_in_render_command(tmp_path: Path) -> None:
    subtitle = tmp_path / "subtitle.srt"
    subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\n测试\n", encoding="utf-8")
    output = tmp_path / "out.mp4"
    root = Path.cwd()
    command, _ = build_render_command(
        asset_dir=root / "assets" / "pink_pig",
        timeline=[{"image": "pig01.png", "duration": 1.0, "transition": "fade"}],
        subtitle_path=subtitle,
        output_path=output,
        transition_seconds=0.1,
        audio_path=root / "assets" / "pink_pig" / "demo_music.wav",
        audio_normalize=True,
        audio_sample_rate=48000,
    )
    assert any("loudnorm=I=-18:TP=-1.5:LRA=11" in item for item in command)
    assert any("aresample=48000" in item for item in command)
