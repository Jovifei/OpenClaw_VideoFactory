from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("phase1_post_render_check", ROOT / "scripts/phase1_post_render_check.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _geometry() -> dict[str, object]:
    return {
        "version": "2.0",
        "topology": {
            "resistor": {"x": 485, "y": 430, "width": 100, "height": 120},
            "ground": {"x": 485, "y": 550, "width": 100, "height": 76},
            "wave_paths": [],
        },
        "bode": {
            "x": {"left": 118, "right": 754, "fc_ratio": 1.0},
            "magnitude_lane": {"top": 110, "bottom": 350, "min_db": -20.0, "max_db": 0.0},
            "phase_lane": {"top": 420, "bottom": 620, "min_degrees": 0.0, "max_degrees": 90.0},
            "markers": {
                "magnitude_fc": {"db": -3.0103},
                "phase_fc": {"degrees": 45.0},
            },
        },
    }


def test_geometry_rejects_wave_intersecting_resistor() -> None:
    geometry = _geometry()
    geometry["topology"]["wave_paths"] = [{"left": 120, "top": 470, "right": 760, "bottom": 510}]
    with pytest.raises(ValueError, match="wave_intersects_resistor"):
        MODULE.validate_rc_highpass_geometry(geometry)


def test_geometry_calculates_fc_markers_on_their_own_curves() -> None:
    result = MODULE.validate_rc_highpass_geometry(_geometry())
    assert result["magnitude_fc"]["db"] == pytest.approx(-3.0103, abs=0.001)
    assert result["phase_fc"]["degrees"] == pytest.approx(45.0, abs=0.001)
    assert result["magnitude_fc"]["y"] < result["phase_fc"]["y"]


def test_component_consumes_one_geometry_contract_for_curve_and_markers() -> None:
    source = (ROOT / "remotion/src/ReferenceRcHighPassVisual.tsx").read_text(encoding="utf-8")
    assert "geometry: RcHighPassGeometry" in source
    assert "input.geometry" in source
    assert "magnitudeYForDb" in source
    assert "phaseYForDegrees" in source
    assert "cy={magnitudeFc.y}" in source
    assert "cy={phaseFc.y}" in source
