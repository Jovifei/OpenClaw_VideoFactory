from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _timing_module():
    spec = importlib.util.spec_from_file_location("phase1_jianying_timing", ROOT / "scripts/phase1_jianying_timing.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_summary_cues_require_ordered_speech_events_for_terms_and_design_steps() -> None:
    timing = _timing_module()
    cues = [
        {"cue_id": "watershed", "start_microseconds": 70_000_000, "end_microseconds": 72_000_000},
        {"cue_id": "phase_lead", "start_microseconds": 72_100_000, "end_microseconds": 74_000_000},
        {"cue_id": "time_scale", "start_microseconds": 74_100_000, "end_microseconds": 76_000_000},
        {"cue_id": "design_fc", "start_microseconds": 76_100_000, "end_microseconds": 78_000_000},
        {"cue_id": "design_validate", "start_microseconds": 78_100_000, "end_microseconds": 80_000_000},
        {"cue_id": "next_preview", "start_microseconds": 80_100_000, "end_microseconds": 82_000_000},
    ]
    assert timing.validate_visual_cues(cues, parent_start=70_000_000, parent_end=90_000_000) == cues


def test_script_declares_measurable_summary_narration_parts() -> None:
    script = json.loads((ROOT / "reports/phase1/douyin_7676032444876819739_rc_highpass_reconstruction_script.json").read_text(encoding="utf-8"))
    parts = script["beats"][4]["narration_parts"]
    assert [part.get("cue_id") for part in parts if part.get("cue_id")] == ["watershed", "phase_lead", "time_scale", "design_fc", "design_validate", "next_preview"]


def test_summary_component_uses_cues_not_a_modulo_card_cycle() -> None:
    source = (ROOT / "remotion/src/ReferenceRcHighPassVisual.tsx").read_text(encoding="utf-8")
    assert "visual_cues" in source
    assert "Math.floor((frame / fps) % 3)" not in source
    assert "cuePulse" in source
    assert "design_validate" in source


def test_visuals_show_key_formulas_while_they_are_explained() -> None:
    source = (ROOT / "remotion/src/ReferenceRcHighPassVisual.tsx").read_text(encoding="utf-8")
    assert "H(jω) = jωRC/(1+jωRC)" in source
    assert "XC ≫ R" in source
    assert "Δt = φ/(2πf)" in source
