"""Storyboard validation and Storyboard → Timeline compiler (pure function, deterministic).

Implements compilation rules R1–R7 from §4.2 of the architecture document.
This module is the **quality gate** between director intent and render execution:
a valid storyboard + valid registry ⇒ timeline that is guaranteed renderable.

Public API (§3.7):
  - :func:`load_storyboard` — load JSON file
  - :func:`validate_storyboard` — structural checks beyond JSON Schema
  - :func:`compile_storyboard` — **pure function**, deterministic compile
  - :class:`StoryboardError` — domain exception
"""

from __future__ import annotations

import json
from pathlib import Path

from .timeline import rendered_duration_seconds
from .transition import TRANSITIONS
from video_factory.pipeline.validation import validate as _validate


class StoryboardError(ValueError):
    """Raised when storyboard validation or compilation fails."""


# ---------------------------------------------------------------------------
# Load & Validate
# ---------------------------------------------------------------------------

def load_storyboard(path: Path) -> dict:
    """Load a storyboard JSON file and return its parsed content."""
    path = Path(path)
    if not path.is_file():
        raise StoryboardError(f"storyboard_file_missing:{path}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    _validate(doc, "storyboard")
    return doc


def validate_storyboard(doc: dict) -> None:
    """Run structural checks on a loaded storyboard (R4 order uniqueness).

    This is called *before* compilation to catch ordering issues early.
    """
    scenes = doc.get("scenes", [])
    if not scenes:
        raise StoryboardError("storyboard_empty_scenes")

    # R4 — order must be 1..N contiguous and unique
    orders = [s["order"] for s in scenes]
    if sorted(orders) != list(range(1, len(scenes) + 1)):
        raise StoryboardError("scene_order_invalid")

    # scene_id uniqueness
    seen_ids: set[str] = set()
    for s in scenes:
        sid = s.get("scene_id", "")
        if sid in seen_ids:
            raise StoryboardError(f"scene_id_duplicated:{sid}")
        seen_ids.add(sid)

    # narration/caption non-empty check
    for s in scenes:
        nar = (s.get("narration") or "").strip()
        cap = s.get("caption")
        if not nar and not cap:
            raise StoryboardError(f"narration_empty:{s.get('scene_id', '?')}")


# ---------------------------------------------------------------------------
# Compiler (R1–R7)
# ---------------------------------------------------------------------------

def compile_storyboard(
    doc: dict,
    registry,
    *,
    repo_root: Path,
) -> dict:
    """Compile a validated storyboard + registry into a timeline document.

    This is a **pure function** (no I/O, no wall-clock, no random).
    The output is deterministic: same inputs → byte-identical JSON.

    Parameters
    ----------
    doc : dict
        Parsed storyboard document (already passed ``validate_storyboard``).
    registry : PinkPigRegistry
        Loaded asset registry.
    repo_root : Path
        Repository root path (used only for constructing relative paths).

    Returns
    -------
    dict
        Timeline document conforming to ``timeline.schema.json``.
    """
    globals_cfg = doc.get("globals", {})
    transition_seconds = float(globals_cfg.get("transition_seconds", 0.4))
    fps = int(globals_cfg.get("fps", 30))

    # Pre-compile checks
    ip = doc.get("ip", {})
    if ip.get("registry_version") != registry.registry_version:
        raise StoryboardError("registry_version_mismatch")
    if ip.get("character_id") != registry.character_id:
        raise StoryboardError(f"character_mismatch:{ip.get('character_id')}")

    scenes_raw = doc.get("scenes", [])
    # Sort by order ascending (R4)
    scenes_sorted = sorted(scenes_raw, key=lambda s: s["order"])

    compiled_scenes: list[dict] = []
    fallback_events: list[dict] = []

    for idx, scene in enumerate(scenes_sorted):
        is_last = idx == len(scenes_sorted) - 1

        # R1 — Asset binding (IP consistency guarantee)
        asset = _bind_asset(scene, registry)

        # Track fallback events
        requested_id = scene.get("asset_id")
        if requested_id and requested_id != asset.asset_id:
            fallback_events.append({
                "event": "asset_fallback",
                "scene_id": scene.get("scene_id"),
                "requested": requested_id,
                "resolved": asset.asset_id,
            })

        # R2 — Duration derivation
        duration = _resolve_duration(scene, globals_cfg)

        # R3 — Transition resolution
        transition = _resolve_transition(scene, globals_cfg, is_last)

        # R5 — Caption
        caption = scene.get("caption") or scene.get("narration", "")

        image_path = asset.path or ""
        image_name = Path(image_path).name if image_path else ""

        compiled_scenes.append(
            {
                "order": scene["order"],
                "scene_id": scene.get("scene_id", f"s{idx+1:02d}"),
                "asset_id": asset.asset_id,
                "image": image_name,
                "image_path": image_path,
                "duration": round(duration, 3),
                "transition": transition,
                "narration": scene.get("narration", ""),
                "caption": caption,
            }
        )

    # R7 — Total duration (reuse existing function)
    total = rendered_duration_seconds(compiled_scenes, transition_seconds)

    return {
        "schema_version": "1.0",
        "source_storyboard_id": doc.get("storyboard_id", ""),
        "registry_version": registry.registry_version,
        "width": int(globals_cfg.get("width", 1080)),
        "height": int(globals_cfg.get("height", 1920)),
        "fps": fps,
        "transition_seconds": round(transition_seconds, 3),
        "total_duration_seconds": round(total, 3),
        "scenes": compiled_scenes,
    }


# ---------------------------------------------------------------------------
# Internal helpers (R1–R5)
# ---------------------------------------------------------------------------


def _bind_asset(scene: dict, registry):
    """R1 — Resolve an asset for *scene* via the registry.

    Raises ``StoryboardError`` with code ``asset_unresolved:<scene_id>``
    if all resolution steps fail.
    """
    try:
        return registry.resolve(
            asset_id=scene.get("asset_id"),
            pose=scene.get("pose"),
            mood=scene.get("mood"),
        )
    except Exception as exc:
        sid = scene.get("scene_id", "?")
        raise StoryboardError(f"asset_unresolved:{sid}") from exc


def _resolve_duration(scene: dict, globals_cfg: dict) -> float:
    """R2 — Derive scene duration from ``duration_intent``, then clamp."""
    di = scene.get("duration_intent", {})
    mode = di.get("mode", "auto")
    narration_cps = float(globals_cfg.get("narration_cps", 5.0))
    min_sec = float(globals_cfg.get("min_scene_seconds", 1.2))
    max_sec = float(globals_cfg.get("max_scene_seconds", 8.0))

    if mode == "fixed":
        raw = float(di.get("seconds", globals_cfg.get("default_scene_seconds", 2.5)))
    elif mode == "narration":
        text = scene.get("narration", "")
        char_count = len(text)
        raw = char_count / narration_cps if narration_cps > 0 else 2.5
    else:  # auto
        raw = float(globals_cfg.get("default_scene_seconds", 2.5))

    duration = round(raw, 3)
    duration = max(min_sec, min(max_sec, duration))

    # Hard validation bounds (must satisfy renderer constraints)
    if not (0.25 <= duration <= 30):
        sid = scene.get("scene_id", "?")
        raise StoryboardError(f"scene_duration_invalid:{sid}")

    trans_sec = float(globals_cfg.get("transition_seconds", 0.4))
    if duration <= trans_sec:
        sid = scene.get("scene_id", "?")
        raise StoryboardError(f"scene_duration_invalid:{sid}")

    return duration


def _resolve_transition(scene: dict, globals_cfg: dict, is_last: bool) -> str:
    """R3 — Resolve transition; last scene forced to 'none'."""
    if is_last:
        return "none"
    t = scene.get("transition_out") or globals_cfg.get("default_transition", "fade")
    if t not in TRANSITIONS:
        raise StoryboardError(f"transition_unsupported:{t}")
    return str(t)
