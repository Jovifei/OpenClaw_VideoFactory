"""Re-measure frozen pre-repair SVG geometry without changing the old Git blobs."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from tests.video.test_freertos_scene45_subtitle_geometry import (
    _chrome_boxes,
    _screen_bottom,
    _subtitle_top,
)


ROOT = Path(__file__).resolve().parents[3]
REV = "7585840"
OUTPUT = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_freertos_scene45_20260927/scene45_red_replay.json")


def old_svg(name: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{REV}:assets/freertos_mutex_plain_illustrations/{name}.svg"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    return result.stdout


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="scene45_red_") as directory:
        temp = Path(directory)
        scene4 = old_svg("04-short-isr-defer")
        scene5 = old_svg("05-checklist")
        # IDs are measurement selectors only; geometry, text, and styling remain
        # byte-for-byte equal to the source commit apart from these attributes.
        scene4 = scene4.replace('<text x="205" y="815"', '<text id="scene4-principle" x="205" y="815"', 1)
        scene5 = scene5.replace('<rect x="110" y="215"', '<rect id="scene5-checklist-box" x="110" y="215"', 1)
        a = temp / "scene4.svg"
        b = temp / "scene5.svg"
        a.write_text(scene4, encoding="utf-8")
        b.write_text(scene5, encoding="utf-8")
        a_work = temp / "a"
        b_work = temp / "b"
        a_work.mkdir()
        b_work.mkdir()
        old4 = _chrome_boxes(a, {"principle": "scene4-principle"}, a_work)["principle"]
        old5 = _chrome_boxes(b, {"box": "scene5-checklist-box"}, b_work)["box"]
        top = _subtitle_top()
        value = {
            "source_commit": REV,
            "selector_change_only": True,
            "subtitle_top_px": top,
            "scene4_old_bbox": old4,
            "scene4_old_bottom_px": _screen_bottom(old4),
            "scene5_old_bbox": old5,
            "scene5_old_bottom_px": _screen_bottom(old5),
            "scene4_red": _screen_bottom(old4) + 20 > top,
            "scene5_red": _screen_bottom(old5) + 20 > top,
        }
        assert value["scene4_red"] and value["scene5_red"]
        OUTPUT.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
