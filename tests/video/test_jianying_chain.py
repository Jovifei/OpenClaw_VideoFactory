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


def test_visual_helper_rejects_c_drive_outputs() -> None:
    helper = _load_module("scripts/prepare_jianying_visual.py", "prepare_jianying_visual_test")
    with pytest.raises(ValueError, match="output_must_not_use_c_drive"):
        helper._reject_c_drive(Path("C:/Users/Admin/video.mp4"), "output")


def test_jianying_draft_defaults_to_e_drive_and_rejects_c_drive() -> None:
    draft = _load_module("scripts/phase1_jianying_tts_draft.py", "phase1_jianying_tts_draft_test")
    assert draft.DEFAULT_DRAFTS_ROOT.drive.upper() == "E:"
    parsed = draft.build_parser().parse_args(
        [
            "--visual", "visual.mp4", "--script", "script.json", "--timing-manifest", "timing.json", "--timing-root", "E:/timing", "--name", "draft",
            "--report", "report.json", "--skill-root", "skill",
        ]
    )
    assert (parsed.width, parsed.height) == (1920, 1080)
    with pytest.raises(ValueError, match="report_must_not_use_c_drive"):
        draft._output_root(Path("C:/Users/Admin/report.json"), "report")


def test_jianying_import_expands_summary_subsegments() -> None:
    draft = _load_module("scripts/phase1_jianying_tts_draft.py", "jianying_subsegments_test")
    parent = {
        "start_microseconds": 70_000_000,
        "end_microseconds": 80_000_000,
        "duration_microseconds": 10_000_000,
        "audio_relative_path": "probe/parent.ogg",
        "audio_sha256": "a" * 64,
        "subsegments": [
            {"index": 1, "start_microseconds": 70_000_000, "end_microseconds": 74_000_000, "duration_microseconds": 4_000_000, "audio_relative_path": "probe/a.ogg", "audio_sha256": "b" * 64},
            {"index": 2, "start_microseconds": 74_100_000, "end_microseconds": 80_000_000, "duration_microseconds": 5_900_000, "audio_relative_path": "probe/b.ogg", "audio_sha256": "c" * 64},
        ],
    }
    assert [entry["audio_relative_path"] for entry in draft.manifest_audio_entries(parent)] == ["probe/a.ogg", "probe/b.ogg"]


def test_audio_preview_expands_same_summary_subsegments() -> None:
    preview = _load_module("scripts/assemble_jianying_voice_preview.py", "jianying_preview_subsegments_test")
    parent = {
        "audio_relative_path": "probe/parent.ogg",
        "subsegments": [
            {"audio_relative_path": "probe/a.ogg"},
            {"audio_relative_path": "probe/b.ogg"},
        ],
    }
    assert [entry["audio_relative_path"] for entry in preview.manifest_audio_entries(parent)] == ["probe/a.ogg", "probe/b.ogg"]


def test_audio_preview_mixer_uses_expanded_audio_entry_count() -> None:
    source = (ROOT / "scripts/assemble_jianying_voice_preview.py").read_text(encoding="utf-8")
    assert "amix=inputs={len(audio_entries)}" in source
