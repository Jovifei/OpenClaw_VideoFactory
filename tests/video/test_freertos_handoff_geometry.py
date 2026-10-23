"""Measure the FreeRTOS handoff label against its box and outgoing arrow."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree

from generate_video import _local_brief_subtitle_style
from video_factory.pipeline.renderer import _subtitle_force_style

from . import ROOT


SVG = ROOT / "assets/freertos_mutex_plain_illustrations/02-isr-nonblocking-handoff.svg"
CHROME = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
PADDING = 16


def _chrome_boxes(tmp_path: Path) -> dict[str, dict[str, float]]:
    assert CHROME.is_file(), "installed Chrome required for qualified SVG geometry"
    source = SVG.read_text(encoding="utf-8")
    html = tmp_path / "handoff_bbox.html"
    html.write_text(
        "<!doctype html><meta charset='utf-8'><body style='margin:0'>"
        + source
        + "<script>(async()=>{await document.fonts.ready;"
        + "const ids={box:'handoff-middle-box',label:'handoff-api-label',arrow:'handoff-outgoing-arrow'};"
        + "const out={};for(const [name,id] of Object.entries(ids)){"
        + "const b=document.getElementById(id).getBBox();"
        + "out[name]={x:b.x,y:b.y,width:b.width,height:b.height};}"
        + "document.documentElement.setAttribute('data-bbox-json',encodeURIComponent(JSON.stringify(out)));"
        + "})();</script></body>",
        encoding="utf-8",
    )
    command = [
        str(CHROME), "--headless=new", "--no-first-run", "--disable-background-networking",
        "--disable-component-update", "--disable-sync", "--virtual-time-budget=3000",
        f"--user-data-dir={tmp_path / 'chrome-profile'}", "--dump-dom", html.as_uri(),
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False, timeout=20)
    assert result.returncode == 0, result.stderr[-500:]
    match = re.search(r'data-bbox-json="([^"]+)"', result.stdout)
    assert match is not None, result.stdout[-500:]
    return json.loads(unquote(match.group(1)))


def test_freertos_handoff_api_label_is_inside_box_and_clear_of_arrow(tmp_path: Path) -> None:
    svg = ElementTree.parse(SVG).getroot()
    label_element = svg.find(".//*[@id='handoff-api-label']")
    assert label_element is not None
    assert "".join(label_element.itertext()) == "xTaskNotifyFromISR / QueueFromISR"

    boxes = _chrome_boxes(tmp_path)
    box, label, arrow = boxes["box"], boxes["label"], boxes["arrow"]
    left, right = label["x"], label["x"] + label["width"]
    top, bottom = label["y"], label["y"] + label["height"]
    assert left >= box["x"] + PADDING, boxes
    assert right <= box["x"] + box["width"] - PADDING, boxes
    assert top >= box["y"] + PADDING, boxes
    assert bottom <= box["y"] + box["height"] - PADDING, boxes
    arrow_left = arrow["x"] - PADDING
    arrow_right = arrow["x"] + arrow["width"] + PADDING
    arrow_top = arrow["y"] - PADDING
    arrow_bottom = arrow["y"] + arrow["height"] + PADDING
    assert right <= arrow_left or left >= arrow_right or bottom <= arrow_top or top >= arrow_bottom, boxes

    subtitle_style = _local_brief_subtitle_style(1920, 1080)
    ass_style = _subtitle_force_style(subtitle_style, canvas_width=1920, canvas_height=1080)
    ass_values = dict(part.split("=", 1) for part in ass_style.split(","))
    subtitle_top = 1080 - int(ass_values["MarginV"]) * 1080 / 288 - 1.5 * int(ass_values["FontSize"]) * 1080 / 288
    assert (box["y"] + box["height"]) * 1080 / 941 + 20 <= subtitle_top
