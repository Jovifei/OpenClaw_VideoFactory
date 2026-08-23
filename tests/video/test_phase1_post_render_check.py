from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("phase1_post_render_check", ROOT / "scripts/phase1_post_render_check.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _contract() -> dict[str, object]:
    return {
        "version": "1.0",
        "safe_area": {"left": 72, "right": 72, "top": 68, "bottom": 180},
        "subtitle_reserve": {"top": 1590, "height": 220},
        "text_policy": "bounded_natural_wrap",
        "overflow_policy": "fail_closed",
        "theme_token": "technical_neutral",
        "background_is_theme_driven": True,
        "pink_global_background": False,
    }


def test_layout_contract_passes_for_portrait_safe_area() -> None:
    result = MODULE.validate_layout_contract(_contract())
    assert result["status"] == "passed"
    assert result["safe_area"]["left"] == 72


def test_layout_contract_rejects_global_pink() -> None:
    value = _contract()
    value["pink_global_background"] = True
    with pytest.raises(ValueError, match="layout_global_pink_forbidden"):
        MODULE.validate_layout_contract(value)


def test_layout_contract_rejects_outside_subtitle_reserve() -> None:
    value = _contract()
    value["subtitle_reserve"] = {"top": 1800, "height": 200}
    with pytest.raises(ValueError, match="layout_subtitle_reserve_outside_canvas"):
        MODULE.validate_layout_contract(value)
