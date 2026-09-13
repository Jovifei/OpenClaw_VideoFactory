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


def test_product_layout_contract_passes_with_contained_capture() -> None:
    value = {
        "version": "website_product_demo_v1",
        "aspect": "9:16",
        "safe_area": {"left": 76, "right": 160, "top": 154, "bottom": 135},
        "subtitle_reserve": {"top": 1640, "height": 120},
        "screenshot_fit": "contain",
        "attribution_preserved": True,
    }
    result = MODULE.validate_layout_contract(value)
    assert result["status"] == "passed"


def test_product_profile_allows_declared_dark_background_edges() -> None:
    metrics = [{"mean_luma": 24.0, "black_ratio": 0.1, "unsafe_edge_dark_ratio": 0.8, "frame_delta": 1.0}]
    assert MODULE.validate_full_frame_metrics(metrics, allow_dark_edges=True)["status"] == "passed"


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


@pytest.mark.parametrize(("aspect", "canvas"), [("16:9", (1920, 1080)), ("9:16", (1080, 1920))])
def test_declared_canvas_modes_are_allowlisted(aspect: str, canvas: tuple[int, int]) -> None:
    assert MODULE.validate_report_canvas({"layout_contract": {"aspect": aspect}, "visual": {"width": canvas[0], "height": canvas[1]}}, *canvas) == {"aspect": aspect, "width": canvas[0], "height": canvas[1]}


def test_declared_canvas_rejects_media_or_report_mismatch() -> None:
    with pytest.raises(ValueError, match="post_render_canvas_report_mismatch"):
        MODULE.validate_report_canvas({"layout_contract": {"aspect": "16:9"}, "visual": {"width": 1920, "height": 1080}}, 1080, 1920)


def test_landscape_layout_rejects_subtitle_reserve_beyond_measured_canvas() -> None:
    value = _contract()
    value["subtitle_reserve"] = {"top": 1000, "height": 120}
    with pytest.raises(ValueError, match="layout_subtitle_reserve_outside_canvas"):
        MODULE.validate_layout_contract(value, width=1920, height=1080)
