"""Production-geometry contracts for the four selected Flash technical diagrams."""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree

from . import ROOT
from .test_freertos_scene45_subtitle_geometry import _chrome_boxes, _subtitle_top


ASSETS = ROOT / "assets/flash_watchdog_plain_illustrations"
SCALE = min(1920 / 1672, 1080 / 941)
CLEARANCE_PX = 20


def _right(box: dict[str, float]) -> float:
    return box["x"] + box["width"]


def _bottom(box: dict[str, float]) -> float:
    return box["y"] + box["height"]


def test_flash_window_cpu_arrow_and_clock_caption(tmp_path: Path) -> None:
    svg = ASSETS / "01-flash-window.svg"
    root = ElementTree.parse(svg).getroot()
    label = root.find(".//*[@id='flash-cpu-label']")
    clock = root.find(".//*[@id='flash-clock-caption']")
    assert label is not None and "".join(label.itertext()) == "CPU / 总线"
    assert label.attrib["font-size"] == "25"
    assert clock is not None and "".join(clock.itertext()) == "倒计时"
    assert clock.attrib["font-size"] == "25"
    boxes = _chrome_boxes(svg, {
        "cpu_box": "flash-cpu-box", "label": "flash-cpu-label",
        "arrow": "flash-cpu-arrow-line", "arrow_head": "flash-cpu-arrow-head",
        "error_box": "flash-error-box", "error_label": "flash-error-label",
        "rim": "flash-clock-rim", "caption": "flash-clock-caption",
        "callout": "flash-scene1-callout", "callout_text": "flash-scene1-callout-text",
    }, tmp_path)
    assert _right(boxes["label"]) + 10 <= _right(boxes["cpu_box"]), boxes
    assert _right(boxes["label"]) + 10 <= boxes["arrow"]["x"], boxes
    assert boxes["arrow"]["x"] >= _right(boxes["cpu_box"]) + 10, boxes
    assert _right(boxes["error_label"]) + 8 <= _right(boxes["error_box"]), boxes
    assert _bottom(boxes["rim"]) + 4.5 + 4 <= boxes["caption"]["y"], boxes
    assert _bottom(boxes["caption"]) <= 470 - 4, boxes
    assert boxes["callout_text"]["y"] >= boxes["callout"]["y"] + 8, boxes
    assert _bottom(boxes["callout_text"]) <= _bottom(boxes["callout"]) - 8, boxes
    assert _bottom(boxes["callout"]) * SCALE + CLEARANCE_PX <= _subtitle_top(), boxes


def test_flash_erase_callout_clears_subtitle(tmp_path: Path) -> None:
    svg = ASSETS / "02-erase-sequence.svg"
    boxes = _chrome_boxes(svg, {
        "callout": "flash-scene2-callout", "main": "flash-scene2-callout-main",
        "lower": "flash-scene2-callout-lower",
    }, tmp_path)
    assert boxes["callout"]["y"] >= 520, boxes
    assert boxes["lower"]["y"] >= boxes["callout"]["y"] + 16, boxes
    assert _bottom(boxes["lower"]) <= _bottom(boxes["callout"]) - 12, boxes
    assert _bottom(boxes["callout"]) * SCALE + CLEARANCE_PX <= _subtitle_top(), boxes


def test_flash_budget_markers_clear_timing_labels(tmp_path: Path) -> None:
    svg = ASSETS / "03-watchdog-budget.svg"
    root = ElementTree.parse(svg).getroot()
    erase = root.find(".//*[@id='flash-budget-erase-label']")
    timeout = root.find(".//*[@id='flash-budget-timeout-label']")
    assert erase is not None and "".join(erase.itertext()) == "最长擦除时间"
    assert timeout is not None and "".join(timeout.itertext()) == "超时 / 复位"
    boxes = _chrome_boxes(svg, {
        "erase_label": "flash-budget-erase-label", "timeout_label": "flash-budget-timeout-label",
        "erase_marker": "flash-budget-erase-marker", "timeout_marker": "flash-budget-timeout-marker",
    }, tmp_path)
    assert boxes["erase_marker"]["x"] == 720 and boxes["timeout_marker"]["x"] == 1190, boxes
    assert _bottom(boxes["erase_marker"]) + 8 <= boxes["erase_label"]["y"], boxes
    assert _bottom(boxes["timeout_marker"]) + 8 <= boxes["timeout_label"]["y"], boxes
    assert _bottom(boxes["erase_marker"]) <= 448 and _bottom(boxes["timeout_marker"]) <= 448, boxes


def test_flash_checklist_and_slogan_clear_subtitle(tmp_path: Path) -> None:
    svg = ASSETS / "05-checklist.svg"
    root = ElementTree.parse(svg).getroot()
    group = root.find(".//*[@id='flash-checklist-group']")
    assert group is not None
    match = re.fullmatch(r"translate\(105,(\d+)\)", group.attrib["transform"])
    assert match is not None
    offset_y = int(match.group(1))
    assert len([item for item in group if item.tag.endswith("rect")]) == 4
    boxes = _chrome_boxes(svg, {
        "fourth": "flash-checklist-fourth-box", "slogan": "flash-checklist-slogan",
    }, tmp_path)
    assert (_bottom(boxes["fourth"]) + offset_y) * SCALE + CLEARANCE_PX <= _subtitle_top(), boxes
    assert _bottom(boxes["slogan"]) * SCALE + CLEARANCE_PX <= _subtitle_top(), boxes
