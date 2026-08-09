"""Build a deterministic, reviewable still-image timeline."""

from __future__ import annotations

from typing import Any

from .transition import TRANSITIONS


def build_timeline(
    manifest: dict[str, Any], *, duration_seconds: float, transitions: list[str]
) -> list[dict[str, object]]:
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("manifest_assets_missing")
    if not isinstance(duration_seconds, (int, float)) or not 0.25 <= float(duration_seconds) <= 30:
        raise ValueError("image_duration_invalid")
    if not transitions or any(name not in TRANSITIONS for name in transitions):
        raise ValueError("timeline_transition_invalid")
    return [
        {
            "image": str(asset["path"]),
            "order": int(asset["order"]),
            "duration": float(duration_seconds),
            "transition": transitions[index % len(transitions)] if index < len(assets) - 1 else "none",
        }
        for index, asset in enumerate(assets)
    ]


def rendered_duration_seconds(timeline: list[dict[str, object]], transition_seconds: float) -> float:
    if not timeline:
        raise ValueError("timeline_empty")
    if not 0 < transition_seconds < min(float(item["duration"]) for item in timeline):
        raise ValueError("transition_duration_invalid")
    return round(sum(float(item["duration"]) for item in timeline) - transition_seconds * (len(timeline) - 1), 3)


def to_render_timeline(timeline_doc: dict) -> list[dict]:
    """Extract the render-ready scene list from a compiled timeline document.

    The returned ``list[dict]`` is a superset of what the legacy
    ``build_timeline()`` produces — each item has at least ``image``,
    ``order``, ``duration``, ``transition``.  The renderer's
    ``build_render_command()`` consumes this format directly.

    This function is intentionally trivial: it returns ``doc["scenes"]``
    as-is so that the renderer needs **zero adaptation**.
    """
    scenes = timeline_doc.get("scenes", [])
    if not scenes:
        raise ValueError("timeline_empty")
    return scenes
