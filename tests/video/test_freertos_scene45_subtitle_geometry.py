"""Keep complete FreeRTOS scene 4/5 diagrams above the real 16:9 subtitle band."""

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


ASSETS = ROOT / "assets/freertos_mutex_plain_illustrations"
CHROME = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
WIDTH, HEIGHT = 1920, 1080
SVG_WIDTH, SVG_HEIGHT = 1672, 941
CLEARANCE_PX = 20


def _subtitle_top() -> float:
    style = _local_brief_subtitle_style(WIDTH, HEIGHT)
    ass = _subtitle_force_style(style, canvas_width=WIDTH, canvas_height=HEIGHT)
    values = dict(part.split("=", 1) for part in ass.split(","))
    font_px = int(values["FontSize"]) * HEIGHT / 288
    bottom_margin_px = int(values["MarginV"]) * HEIGHT / 288
    return HEIGHT - bottom_margin_px - 1.5 * font_px


def _chrome_boxes(svg_path: Path, ids: dict[str, str], tmp_path: Path) -> dict[str, dict[str, float]]:
    assert CHROME.is_file(), "installed Chrome required for qualified SVG geometry"
    source = svg_path.read_text(encoding="utf-8")
    html = tmp_path / "bbox.html"
    html.write_text(
        "<!doctype html><meta charset='utf-8'><body style='margin:0'>" + source
        + "<script>(async()=>{await document.fonts.ready;"
        + "const ids=" + json.dumps(ids) + ";const out={};"
        + "for(const [name,id] of Object.entries(ids)){"
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
    result = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False, timeout=20,
    )
    assert result.returncode == 0, result.stderr[-500:]
    match = re.search(r'data-bbox-json="([^"]+)"', result.stdout)
    assert match is not None, result.stdout[-500:]
    return json.loads(unquote(match.group(1)))


def _screen_bottom(box: dict[str, float]) -> float:
    scale = min(WIDTH / SVG_WIDTH, HEIGHT / SVG_HEIGHT)
    pad_y = (HEIGHT - SVG_HEIGHT * scale) / 2
    return pad_y + (box["y"] + box["height"]) * scale


def test_scene4_principle_clears_production_subtitle(tmp_path: Path) -> None:
    svg_path = ASSETS / "04-short-isr-defer.svg"
    svg = ElementTree.parse(svg_path).getroot()
    principle = svg.find(".//*[@id='scene4-principle']")
    assert principle is not None
    assert "".join(principle.itertext()) == "原则：ISR 只负责“发生了什么”，任务负责“接下来怎么办”。"
    assert principle.attrib["font-size"] == "31"
    box = _chrome_boxes(svg_path, {"principle": "scene4-principle"}, tmp_path)["principle"]
    bottom, top = _screen_bottom(box), _subtitle_top()
    assert bottom + CLEARANCE_PX <= top, f"scene4_principle_bottom={bottom:.1f}, subtitle_top={top:.1f}, bbox={box}"


def test_scene5_complete_checklist_clears_production_subtitle(tmp_path: Path) -> None:
    svg_path = ASSETS / "05-checklist.svg"
    svg = ElementTree.parse(svg_path).getroot()
    content = svg.find(".//*[@id='scene5-checklist-content']")
    assert content is not None
    assert len([element for element in content if element.tag.endswith("circle")]) == 5
    boxes = _chrome_boxes(
        svg_path,
        {"box": "scene5-checklist-box", "content": "scene5-checklist-content"},
        tmp_path,
    )
    assert boxes["content"]["y"] >= boxes["box"]["y"] + 16, boxes
    assert boxes["content"]["y"] + boxes["content"]["height"] <= boxes["box"]["y"] + boxes["box"]["height"] - 16, boxes
    bottom, top = _screen_bottom(boxes["box"]), _subtitle_top()
    assert bottom + CLEARANCE_PX <= top, f"scene5_box_bottom={bottom:.1f}, subtitle_top={top:.1f}, bboxes={boxes}"
