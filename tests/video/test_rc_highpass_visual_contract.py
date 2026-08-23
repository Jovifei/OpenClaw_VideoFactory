from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_rc_brief_is_original_and_portrait() -> None:
    brief = json.loads((ROOT / "reports/phase1/douyin_7676032444876819739_rc_highpass_reconstruction_script.json").read_text(encoding="utf-8"))
    assert brief["style"]["aspect_ratio"] == "9:16"
    assert brief["style"]["background_policy"] == "theme_driven_not_global_pink"
    assert len(brief["beats"]) == 5
    assert brief["originality"]["source_audio_reused"] is False
    assert brief["originality"]["source_frames_reused"] is False
    assert brief["originality"]["source_transcript_reused"] is False
    forbidden = {"source_path", "frame_path", "audio_path", "asset_id", "provider", "render"}
    assert not forbidden.intersection(brief)


def test_storyboard_declares_safe_area_and_single_subtitle_authority() -> None:
    storyboard = json.loads((ROOT / "reports/phase1/douyin_7676032444876819739_rc_highpass_storyboard.json").read_text(encoding="utf-8"))
    assert storyboard["canvas"] == {"width": 1080, "height": 1920, "fps": 30}
    assert storyboard["safe_area"] == {"left": 72, "right": 72, "top": 68, "bottom": 180}
    assert storyboard["subtitle_reserve"]["authority"] == "jianying_native"
    assert storyboard["layout_contract"]["no_burned_in_subtitles"] is True


def test_component_uses_bounded_text_and_theme_driven_canvas() -> None:
    source = (ROOT / "remotion/src/ReferenceRcHighPassVisual.tsx").read_text(encoding="utf-8")
    assert "data-layout-box" in source
    assert "WebkitLineClamp" in source
    assert "overflow: 'hidden'" in source
    assert "THEME.canvas" in source
    assert "pink" not in source.lower()
