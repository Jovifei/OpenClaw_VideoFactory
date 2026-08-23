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
    with pytest.raises(ValueError, match="report_must_not_use_c_drive"):
        draft._output_root(Path("C:/Users/Admin/report.json"), "report")
