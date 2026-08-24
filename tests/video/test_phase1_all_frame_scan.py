from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("phase1_post_render_check", ROOT / "scripts/phase1_post_render_check.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_full_frame_metrics_reject_black_frame() -> None:
    with pytest.raises(ValueError, match="all_frame_black_detected"):
        MODULE.validate_full_frame_metrics([
            {"mean_luma": 240.0, "black_ratio": 0.0, "unsafe_edge_dark_ratio": 0.0, "frame_delta": 0.0},
            {"mean_luma": 1.0, "black_ratio": 0.99, "unsafe_edge_dark_ratio": 0.0, "frame_delta": 4.0},
        ])


def test_full_frame_metrics_reports_every_decoded_frame() -> None:
    result = MODULE.validate_full_frame_metrics([
        {"mean_luma": 240.0, "black_ratio": 0.0, "unsafe_edge_dark_ratio": 0.0, "frame_delta": 0.0},
        {"mean_luma": 241.0, "black_ratio": 0.0, "unsafe_edge_dark_ratio": 0.0, "frame_delta": 1.0},
        {"mean_luma": 239.0, "black_ratio": 0.0, "unsafe_edge_dark_ratio": 0.0, "frame_delta": 1.2},
    ])
    assert result["frames_scanned"] == 3
    assert result["black_frame_count"] == 0


def test_representative_frames_are_selected_by_decoded_frame_index() -> None:
    source = (ROOT / "scripts/phase1_post_render_check.py").read_text(encoding="utf-8")
    assert "cv2.VideoCapture" in source
    assert "target_indices" in source
    assert "select=eq(n" not in source
