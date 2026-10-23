"""Keep the FreeRTOS priority-inheritance callout clear of local-brief subtitles."""

from __future__ import annotations

from xml.etree import ElementTree

from generate_video import _local_brief_subtitle_style
from src.factory.phase1_local import build_local_plan, load_local_brief
from video_factory.pipeline.renderer import _subtitle_force_style

from . import ROOT


SVG = ROOT / "assets/freertos_mutex_plain_illustrations/03-priority-inheritance.svg"
BRIEF = ROOT / "examples/phase1_local_freertos/brief.json"


def test_priority_inheritance_callout_clears_production_subtitle_band() -> None:
    plan = build_local_plan(load_local_brief(BRIEF), ROOT)
    profile = plan["render_profile"]
    width, height = int(profile["width"]), int(profile["height"])
    assert (width, height) == (1920, 1080)
    assert plan["asset_selection"]["selections"][2]["asset_id"] == "pink_pig.freertos_mutex_plain_priority_inheritance.v1"
    subtitle = str(plan["script"]["beats"][2]["subtitle"])
    assert "\n" not in subtitle and len(subtitle) <= 20

    style = _local_brief_subtitle_style(width, height)
    ass_style = _subtitle_force_style(style, canvas_width=width, canvas_height=height)
    ass_values = dict(part.split("=", 1) for part in ass_style.split(","))
    font_px = int(ass_values["FontSize"]) * height / 288
    bottom_margin_px = int(ass_values["MarginV"]) * height / 288
    subtitle_top = height - bottom_margin_px - 1.5 * font_px

    svg = ElementTree.parse(SVG).getroot()
    group = svg.find(".//*[@id='priority-inheritance-callout']")
    assert group is not None
    rect = next(child for child in group if child.tag.endswith("rect"))
    label = next(child for child in group if child.tag.endswith("text"))
    rect_y, rect_height = float(rect.attrib["y"]), float(rect.attrib["height"])
    assert rect_y < float(label.attrib["y"]) < rect_y + rect_height

    svg_width, svg_height = float(svg.attrib["width"]), float(svg.attrib["height"])
    scale = min(width / svg_width, height / svg_height)
    pad_y = (height - svg_height * scale) / 2
    callout_bottom = pad_y + (rect_y + rect_height) * scale
    assert callout_bottom + 20 <= subtitle_top, (
        f"callout_bottom={callout_bottom:.1f}, subtitle_top={subtitle_top:.1f}"
    )
