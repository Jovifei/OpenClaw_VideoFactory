from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _load_module(relative_path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _manifest() -> dict:
    segments = []
    cursor = 0
    gap = 100_000
    for index, duration in enumerate((7_800_000, 6_420_000, 8_420_000, 5_800_000, 8_700_000), start=1):
        start = cursor
        end = start + duration
        next_start = end + gap if index < 5 else 50_000_000
        segments.append(
            {
                "index": index,
                "start_microseconds": start,
                "end_microseconds": end,
                "duration_microseconds": duration,
                "scene_start_microseconds": start,
                "scene_end_microseconds": next_start,
                "audio_relative_path": f"probe/temp_assets/tts_{index}.ogg",
                "audio_sha256": "a" * 64,
            }
        )
        cursor = next_start if index < 5 else end
    return {
        "schema_version": "1.0",
        "timing": {"fps": 30, "inter_segment_gap_microseconds": gap},
        "voice": {"segment_count": 5, "voice_end_microseconds": segments[-1]["end_microseconds"]},
        "visual_duration_seconds": 50,
        "segments": segments,
    }


def test_manifest_requires_contiguous_scene_windows() -> None:
    timing = _load_module("scripts/phase1_jianying_timing.py", "timing_manifest_test")
    value = _manifest()
    assert timing.validate_manifest(value)["segments"][1]["scene_start_microseconds"] == 7_900_000

    value["segments"][1]["scene_end_microseconds"] += 1
    with pytest.raises(ValueError, match="timing_scene_gap_invalid"):
        timing.validate_manifest(value)


def test_manifest_rejects_absolute_audio_paths() -> None:
    timing = _load_module("scripts/phase1_jianying_timing.py", "timing_manifest_path_test")
    value = _manifest()
    value["segments"][0]["audio_relative_path"] = "E:/private/audio.ogg"
    with pytest.raises(ValueError, match="audio_relative_path_must_be_relative"):
        timing.validate_manifest(value)


def test_timing_helpers_accept_the_director_contract_six_beat_subject(tmp_path: Path) -> None:
    timing = _load_module("scripts/phase1_jianying_timing.py", "timing_six_beat_subject")
    script = {"beats":[{"narration":"旁白","subtitle":"字幕"} for _ in range(6)]}
    source = tmp_path / "script.json"; source.write_text(__import__("json").dumps(script), encoding="utf-8")
    assert len(timing.load_script(source)[1]) == 6


def test_manifest_allows_explicit_long_form_tail() -> None:
    timing = _load_module("scripts/phase1_jianying_timing.py", "timing_manifest_long_form_test")
    value = _manifest()
    value["visual_duration_seconds"] = 120
    value["segments"][-1]["scene_end_microseconds"] = 120_000_000
    assert timing.validate_manifest(value)["visual_duration_seconds"] == 120


def test_manifest_rejects_visual_cue_outside_summary_audio() -> None:
    timing = _load_module("scripts/phase1_jianying_timing.py", "timing_manifest_cues_test")
    value = _manifest()
    value["visual_cues"] = [
        {"cue_id": "watershed", "start_microseconds": 29_000_000, "end_microseconds": 30_000_000},
        {"cue_id": "phase_lead", "start_microseconds": 30_100_000, "end_microseconds": 31_000_000},
        {"cue_id": "time_scale", "start_microseconds": 31_100_000, "end_microseconds": 32_000_000},
        {"cue_id": "design_fc", "start_microseconds": 32_100_000, "end_microseconds": 33_000_000},
        {"cue_id": "design_validate", "start_microseconds": 33_100_000, "end_microseconds": 34_000_000},
        {"cue_id": "next_preview", "start_microseconds": 34_100_000, "end_microseconds": 55_000_000},
    ]
    with pytest.raises(ValueError, match="visual_cue_range_invalid"):
        timing.validate_manifest(value)
