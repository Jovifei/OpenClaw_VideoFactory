"""Persist current Chrome text/shape measurements for repaired Flash assets."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.video.test_freertos_scene45_subtitle_geometry import _chrome_boxes, _subtitle_top


ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "assets/flash_watchdog_plain_illustrations"
OUTPUT = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_flash_geometry_20260927/flash_green_measure.json")
SCALE = min(1920 / 1672, 1080 / 941)


def bottom(box: dict[str, float]) -> float:
    return box["y"] + box["height"]


def right(box: dict[str, float]) -> float:
    return box["x"] + box["width"]


def main() -> None:
    ids = {
        "01-flash-window": {"cpu_box": "flash-cpu-box", "cpu_label": "flash-cpu-label",
                            "arrow": "flash-cpu-arrow-line", "error_box": "flash-error-box",
                            "error_label": "flash-error-label", "rim": "flash-clock-rim",
                            "caption": "flash-clock-caption", "callout": "flash-scene1-callout",
                            "callout_text": "flash-scene1-callout-text"},
        "02-erase-sequence": {"callout": "flash-scene2-callout", "lower": "flash-scene2-callout-lower"},
        "03-watchdog-budget": {"erase_label": "flash-budget-erase-label", "timeout_label": "flash-budget-timeout-label",
                               "erase_marker": "flash-budget-erase-marker", "timeout_marker": "flash-budget-timeout-marker"},
        "05-checklist": {"fourth": "flash-checklist-fourth-box", "slogan": "flash-checklist-slogan"},
    }
    with tempfile.TemporaryDirectory(prefix="flash_green_") as directory:
        temp = Path(directory)
        boxes = {}
        for name, mapping in ids.items():
            work = temp / name
            work.mkdir()
            boxes[name] = _chrome_boxes(ASSETS / f"{name}.svg", mapping, work)
    a, b, c, d = (boxes[name] for name in ids)
    value = {
        "subtitle_top_px": _subtitle_top(),
        "scene1": {
            "cpu_label_right": right(a["cpu_label"]), "cpu_box_right": right(a["cpu_box"]),
            "arrow_start": a["arrow"]["x"], "error_label_right": right(a["error_label"]),
            "error_box_right": right(a["error_box"]),
            "clock_rim_bottom": bottom(a["rim"]), "clock_caption_top": a["caption"]["y"],
            "clock_caption_bottom": bottom(a["caption"]),
            "callout_bottom_px": bottom(a["callout"]) * SCALE,
            "callout_text_bottom_px": bottom(a["callout_text"]) * SCALE,
        },
        "scene2": {"callout_bottom_px": bottom(b["callout"]) * SCALE,
                   "lower_text_bottom_px": bottom(b["lower"]) * SCALE},
        "scene3": {"erase_marker_bottom": bottom(c["erase_marker"]),
                   "erase_label_top": c["erase_label"]["y"],
                   "timeout_marker_bottom": bottom(c["timeout_marker"]),
                   "timeout_label_top": c["timeout_label"]["y"]},
        "scene5": {"fourth_box_bottom_px": (bottom(d["fourth"]) + 195) * SCALE,
                   "slogan_bottom_px": bottom(d["slogan"]) * SCALE},
    }
    OUTPUT.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
