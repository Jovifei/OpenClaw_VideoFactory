"""Re-measure e77761c Flash SVGs with selector-only temporary IDs."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from tests.video.test_freertos_scene45_subtitle_geometry import _chrome_boxes, _subtitle_top


ROOT = Path(__file__).resolve().parents[3]
REV = "e77761c"
OUTPUT = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_flash_geometry_20260927/flash_red_replay.json")
SCALE = min(1920 / 1672, 1080 / 941)


REPLACEMENTS = {
    "01-flash-window": [
        ('<rect x="120" y="337"', '<rect id="flash-cpu-box" x="120" y="337"'),
        ('<text x="145" y="374"', '<text id="flash-cpu-label" x="145" y="374"'),
        ('<path d="M275 364h105"', '<path id="flash-cpu-arrow-line" d="M275 364h105"'),
        ('<rect x="650" y="337"', '<rect id="flash-error-box" x="650" y="337"'),
        ('<text x="669" y="373"', '<text id="flash-error-label" x="669" y="373"'),
        ('<circle cx="1285" cy="365"', '<circle id="flash-clock-rim" cx="1285" cy="365"'),
        ('<text x="1248" y="443"', '<text id="flash-clock-caption" x="1248" y="443"'),
        ('<rect x="78" y="700"', '<rect id="flash-scene1-callout" x="78" y="700"'),
        ('<text x="112" y="770"', '<text id="flash-scene1-callout-text" x="112" y="770"'),
    ],
    "02-erase-sequence": [
        ('<rect x="470" y="615"', '<rect id="flash-scene2-callout" x="470" y="615"'),
        ('<text x="520" y="730"', '<text id="flash-scene2-callout-lower" x="520" y="730"'),
    ],
    "03-watchdog-budget": [
        ('<text x="665" y="525"', '<text id="flash-budget-erase-label" x="665" y="525"'),
        ('<text x="1115" y="525"', '<text id="flash-budget-timeout-label" x="1115" y="525"'),
        ('<path d="M720 375v180"', '<path id="flash-budget-erase-marker" d="M720 375v180"'),
        ('<path d="M1190 375v180"', '<path id="flash-budget-timeout-marker" d="M1190 375v180"'),
    ],
    "05-checklist": [
        ('<g transform="translate(105,255)"', '<g id="flash-checklist-group" transform="translate(105,255)"'),
        ('<rect y="375"', '<rect id="flash-checklist-fourth-box" y="375"'),
        ('<text x="1090" y="700"', '<text id="flash-checklist-slogan" x="1090" y="700"'),
    ],
}


def old_source(name: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{REV}:assets/flash_watchdog_plain_illustrations/{name}.svg"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    source = result.stdout
    for before, after in REPLACEMENTS[name]:
        assert source.count(before) == 1, (name, before)
        source = source.replace(before, after, 1)
    return source


def bottom(box: dict[str, float]) -> float:
    return box["y"] + box["height"]


def right(box: dict[str, float]) -> float:
    return box["x"] + box["width"]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="flash_red_") as directory:
        temp = Path(directory)
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
        boxes = {}
        for name, mapping in ids.items():
            svg = temp / f"{name}.svg"
            work = temp / name
            work.mkdir()
            svg.write_text(old_source(name), encoding="utf-8")
            boxes[name] = _chrome_boxes(svg, mapping, work)
        a, b, c, d = (boxes[name] for name in ids)
        top = _subtitle_top()
        results = {
            "source_commit": REV,
            "selector_only_temporary_changes": True,
            "subtitle_top_px": top,
            "scene1": {
                "cpu_label_right": right(a["cpu_label"]), "cpu_box_right": right(a["cpu_box"]),
                "arrow_start": a["arrow"]["x"], "error_label_right": right(a["error_label"]),
                "error_box_right": right(a["error_box"]),
                "clock_rim_bottom": bottom(a["rim"]), "clock_caption_top": a["caption"]["y"],
                "callout_bottom_px": bottom(a["callout"]) * SCALE,
                "callout_text_bottom_px": bottom(a["callout_text"]) * SCALE,
            },
            "scene2": {"callout_bottom_px": bottom(b["callout"]) * SCALE,
                       "lower_text_bottom_px": bottom(b["lower"]) * SCALE},
            "scene3": {"erase_marker_bottom": bottom(c["erase_marker"]),
                       "erase_label_top": c["erase_label"]["y"],
                       "timeout_marker_bottom": bottom(c["timeout_marker"]),
                       "timeout_label_top": c["timeout_label"]["y"]},
            "scene5": {"fourth_box_bottom_px": (bottom(d["fourth"]) + 255) * SCALE,
                       "slogan_bottom_px": bottom(d["slogan"]) * SCALE},
        }
        assert results["scene1"]["cpu_label_right"] + 10 > results["scene1"]["cpu_box_right"]
        assert results["scene1"]["error_label_right"] + 8 > results["scene1"]["error_box_right"]
        assert results["scene1"]["clock_rim_bottom"] + 8.5 > results["scene1"]["clock_caption_top"]
        assert results["scene1"]["callout_bottom_px"] + 20 > top
        assert results["scene2"]["callout_bottom_px"] + 20 > top
        assert results["scene3"]["erase_marker_bottom"] + 8 > results["scene3"]["erase_label_top"]
        assert results["scene3"]["timeout_marker_bottom"] + 8 > results["scene3"]["timeout_label_top"]
        assert results["scene5"]["fourth_box_bottom_px"] + 20 > top
        assert results["scene5"]["slogan_bottom_px"] + 20 > top
        OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
