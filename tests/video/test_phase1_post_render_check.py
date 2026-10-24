from __future__ import annotations

import importlib.util
import hashlib
import json
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


def test_product_layout_contract_passes_with_declared_focus_crop() -> None:
    value = {
        "version": "website_product_demo_v1",
        "aspect": "9:16",
        "safe_area": {"left": 76, "right": 160, "top": 154, "bottom": 135},
        "subtitle_reserve": {"top": 1640, "height": 120},
        "screenshot_fit": "focus_crop",
        "attribution_preserved": True,
    }
    result = MODULE.validate_layout_contract(value)
    assert result["screenshot_fit"] == "focus_crop"


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


@pytest.fixture
def gate_inputs(tmp_path, monkeypatch):
    # Mocked media probes test gate identity, not real media qualification.
    visual = tmp_path / 'visual.mp4'
    visual.write_bytes(b'UNIT MEDIA IDENTITY ONLY')
    report = {'schema_version': '1.0', 'status': 'passed', 'renderer': 'remotion',
              'composition': 'TechnicalExplainer', 'layout_contract': _contract(),
              'visual': {'sha256': hashlib.sha256(visual.read_bytes()).hexdigest(),
                         'burned_in_subtitles': False, 'width': 1080, 'height': 1920}}
    report['review_derivation'] = {'source_visual_sha256': report['visual']['sha256']}
    monkeypatch.setattr(MODULE, '_ffprobe', lambda _p: {'streams': [
        {'codec_type': 'video', 'width': 1080, 'height': 1920, 'avg_frame_rate': '30/1'}],
        'format': {'duration': '1'}})
    monkeypatch.setattr(MODULE, '_decode_check', lambda _p: True)
    monkeypatch.setattr(MODULE, '_sample_frames', lambda *a: [])
    monkeypatch.setattr(MODULE, 'scan_all_frames', lambda *a, **k: {
        'status': 'passed', 'dark_edges_allowed': k['allow_dark_edges']})
    report_path = tmp_path / 'render.json'
    def run():
        report_path.write_text(json.dumps(report), encoding='utf-8')
        return MODULE.run_gate(visual, report_path, tmp_path / 'qa.json')
    return report, run


@pytest.mark.parametrize('field', ['visual', 'review_derivation'])
def test_gate_rejects_report_hash_mismatching_real_bytes(gate_inputs, field):
    report, run = gate_inputs
    report[field]['sha256' if field == 'visual' else 'source_visual_sha256'] = 'a' * 64
    with pytest.raises(ValueError, match='post_render_visual_identity'):
        run()


@pytest.mark.parametrize('composition', ['TechnicalExplainer', 'UnknownTemplate'])
def test_product_exemption_requires_consistent_template_identity(gate_inputs, composition):
    report, run = gate_inputs
    report['composition'] = composition
    report['content_kind'] = 'website_product_promo'
    report['layout_contract'] = {
        'version': 'website_product_demo_v1', 'aspect': '9:16',
        'safe_area': {'left': 76, 'right': 76, 'top': 154, 'bottom': 135},
        'subtitle_reserve': {'top': 1640, 'height': 120},
        'screenshot_fit': 'focus_crop', 'attribution_preserved': True}
    with pytest.raises(ValueError, match='post_render_template_identity'):
        run()


def test_valid_technical_report_retains_full_edge_checks(gate_inputs):
    report, run = gate_inputs
    assert run()['checks']['all_frame_scan']['dark_edges_allowed'] is False


@pytest.mark.parametrize(('composition', 'status'), [
    ('RcHighPass1080x1920', 'remotion_visual_ready_for_post_render_gate'),
    ('FlashWatchdog16x9', 'remotion_visual_ready_for_jianying'),
])
def test_legacy_producer_states_still_require_real_visual_identity(gate_inputs, composition, status):
    report, run = gate_inputs
    report.update(composition=composition, status=status)
    report.pop('review_derivation')
    assert run()['checks']['all_frame_scan']['dark_edges_allowed'] is False


def test_consistent_product_identity_keeps_scoped_dark_edge_exception(gate_inputs):
    report, run = gate_inputs
    report.update(composition='WebsiteProductDemo', content_kind='website_product_promo')
    report['layout_contract'] = {
        'version': 'website_product_demo_v1', 'aspect': '9:16',
        'safe_area': {'left': 76, 'right': 76, 'top': 154, 'bottom': 135},
        'subtitle_reserve': {'top': 1640, 'height': 120},
        'screenshot_fit': 'focus_crop', 'attribution_preserved': True}
    assert run()['checks']['all_frame_scan']['dark_edges_allowed'] is True


def test_missing_visual_identity_is_not_treated_as_legacy_success(gate_inputs):
    report, run = gate_inputs
    report['visual'].pop('sha256')
    with pytest.raises(ValueError, match='post_render_visual_identity'):
        run()
