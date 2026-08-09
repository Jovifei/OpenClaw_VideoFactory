"""Knowledge-video composition contract and safe-region validation.

Composition is a small, renderer-facing value object.  It does not perform
rendering or inspect pixels; it only supplies deterministic canvas/region
geometry and subtitle/signature defaults that downstream stages can share.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .errors import FactoryContractError


ROOT = Path(__file__).resolve().parents[2]
COMPOSITION_SCHEMA = ROOT / "schemas" / "video" / "composition.schema.json"
DEFAULT_COMPOSITION_PATH = ROOT / "video_factory" / "configs" / "compositions" / "knowledge_illustration.json"
KNOWLEDGE_LAYOUT = "knowledge_illustration"


def default_composition() -> dict[str, object]:
    """Return the canonical 1080x1920 knowledge-illustration layout."""

    return {
        "schema_version": "1.0",
        "composition_id": KNOWLEDGE_LAYOUT,
        "layout": KNOWLEDGE_LAYOUT,
        "canvas": {
            "width": 1080,
            "height": 1920,
            "background_color": "0xF7E4EA",
        },
        "regions": {
            "brand_area": {"x": 90, "y": 80, "width": 900, "height": 100},
            "content_area": {"x": 0, "y": 240, "width": 1080, "height": 800},
            "subtitle_area": {"x": 90, "y": 1120, "width": 900, "height": 460},
            "signature_area": {"x": 90, "y": 1760, "width": 900, "height": 100},
        },
        "subtitle_style": {
            "layout": "knowledge_illustration",
            "font_name": "Microsoft YaHei",
            "font_size": 56,
            "min_chars_per_line": 14,
            "max_chars_per_line": 18,
            "max_lines": 2,
            "margin_left": 90,
            "margin_right": 90,
            "margin_vertical": 400,
            "alignment": 2,
        },
        "signature": {
            "asset_id": "pink_pig.signature.v1",
            "max_height": 80,
        },
    }


def _error(code: str, message: str, **context: Any) -> FactoryContractError:
    allowed = {
        "field", "path", "region", "layout_mode", "validator", "reason",
        "scene_order", "asset_id", "expected", "actual",
    }
    return FactoryContractError(code, message, {k: v for k, v in context.items() if k in allowed})


def _safe_relative_path(root: Path, reference: str) -> Path:
    if not isinstance(reference, str) or not reference or "\\" in reference:
        raise _error("composition_schema_invalid", "Composition reference must be a relative POSIX path.", field="composition_ref")
    pure = PurePosixPath(reference)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts) or Path(reference).drive:
        raise _error("composition_schema_invalid", "Composition reference contains an unsafe path.", field="composition_ref")
    candidate = (root / Path(*pure.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise _error("composition_schema_invalid", "Composition reference escapes the repository.", field="composition_ref") from exc
    return candidate


def _validate_json_schema(value: dict[str, object]) -> None:
    if not COMPOSITION_SCHEMA.is_file():
        return
    try:
        import jsonschema

        schema = json.loads(COMPOSITION_SCHEMA.read_text(encoding="utf-8"))
        errors = sorted(
            jsonschema.Draft202012Validator(schema).iter_errors(value),
            key=lambda error: (tuple(str(p) for p in error.absolute_path), str(error.validator), str(error.message)),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _error("composition_schema_invalid", "Composition schema could not be loaded.", field="schema") from exc
    except Exception as exc:
        raise _error("composition_schema_invalid", "Composition schema is invalid.", field="schema") from exc
    if errors:
        err = errors[0]
        raise _error(
            "composition_schema_invalid",
            "Composition failed schema validation.",
            path=".".join(str(p) for p in err.absolute_path),
            validator=str(err.validator),
        ) from err


def _rect(regions: Mapping[str, Any], name: str, width: float, height: float) -> tuple[float, float, float, float]:
    value = regions.get(name)
    if not isinstance(value, Mapping):
        raise _error("composition_region_invalid", "Composition region is missing.", region=name)
    try:
        x, y = float(value["x"]), float(value["y"])
        w, h = float(value["width"]), float(value["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise _error("composition_region_invalid", "Composition region has invalid geometry.", region=name) from exc
    if any(v != v for v in (x, y, w, h)) or w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > width or y + h > height:
        raise _error("composition_region_invalid", "Composition region lies outside the canvas.", region=name)
    return x, y, w, h


def _overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def validate_composition(composition: Mapping[str, Any]) -> dict[str, object]:
    """Validate and return a deep-copied composition contract."""

    if not isinstance(composition, Mapping):
        raise _error("composition_schema_invalid", "Composition must be an object.", field="composition")
    value = copy.deepcopy(dict(composition))
    _validate_json_schema(value)
    if value.get("composition_id") != KNOWLEDGE_LAYOUT or value.get("layout") != KNOWLEDGE_LAYOUT:
        raise _error("composition_semantic_invalid", "Unsupported composition layout mode.", field="layout", expected=KNOWLEDGE_LAYOUT)
    canvas = value.get("canvas")
    regions = value.get("regions")
    style = value.get("subtitle_style")
    if not isinstance(canvas, Mapping) or not isinstance(regions, Mapping) or not isinstance(style, Mapping):
        raise _error("composition_schema_invalid", "Composition must contain canvas, regions, and subtitle_style.", field="canvas/regions/subtitle_style")
    try:
        width, height = int(canvas["width"]), int(canvas["height"])
        fps = int(canvas.get("fps", 30))
    except (KeyError, TypeError, ValueError) as exc:
        raise _error("composition_schema_invalid", "Composition canvas is invalid.", field="canvas") from exc
    if (width, height) != (1080, 1920) or fps != 30:
        raise _error("composition_semantic_invalid", "Knowledge composition must use 1080x1920 at 30 FPS.", field="canvas")
    brand = _rect(regions, "brand_area", width, height)
    content = _rect(regions, "content_area", width, height)
    subtitle = _rect(regions, "subtitle_area", width, height)
    signature = _rect(regions, "signature_area", width, height)
    if _overlap(brand, content) or _overlap(brand, subtitle) or _overlap(brand, signature):
        raise _error("composition_region_invalid", "Brand region overlaps another composition region.", region="brand_area")
    if _overlap(content, subtitle):
        raise _error("composition_region_invalid", "Content and subtitle regions overlap.", region="content_area/subtitle_area")
    if _overlap(content, signature):
        raise _error("composition_region_invalid", "Content and signature regions overlap.", region="content_area/signature_area")
    if _overlap(subtitle, signature):
        raise _error("composition_region_invalid", "Subtitle and signature regions overlap.", region="subtitle_area/signature_area")
    try:
        font_size = int(style.get("font_size", 56))
        min_chars = int(style.get("min_chars_per_line", 14))
        max_chars = int(style.get("max_chars_per_line", 18))
        max_lines = int(style.get("max_lines", 2))
        margin_left, margin_right = int(style.get("margin_left", 90)), int(style.get("margin_right", 90))
    except (TypeError, ValueError) as exc:
        raise _error("composition_semantic_invalid", "Subtitle style values are invalid.", field="subtitle_style") from exc
    if not 52 <= font_size <= 60 or min_chars < 1 or min_chars > max_chars or max_lines != 2 or margin_left < 40 or margin_right < 40:
        raise _error("composition_semantic_invalid", "Subtitle style is outside the safe layout contract.", field="subtitle_style")
    signature_cfg = value.get("signature")
    if not isinstance(signature_cfg, Mapping) or not isinstance(signature_cfg.get("asset_id"), str) or not signature_cfg.get("asset_id"):
        raise _error("composition_schema_invalid", "Composition signature asset is missing.", field="signature.asset_id")
    try:
        if int(signature_cfg.get("max_height", 80)) <= 0:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise _error("composition_semantic_invalid", "Composition signature height is invalid.", field="signature.max_height") from exc
    return value


def load_composition(source: str | Path | Mapping[str, Any] | None = None, *, repo_root: Path | None = None) -> dict[str, object]:
    """Load a named/path composition or return the default knowledge layout."""

    if source is None or source == KNOWLEDGE_LAYOUT:
        root = Path(repo_root).resolve() if repo_root is not None else ROOT
        configured = root / "video_factory" / "configs" / "compositions" / "knowledge_illustration.json"
        if configured.is_file():
            try:
                return validate_composition(json.loads(configured.read_text(encoding="utf-8")))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise _error("composition_schema_invalid", "Default composition could not be read.", field="composition_ref") from exc
        return validate_composition(default_composition())
    if isinstance(source, Mapping):
        return validate_composition(source)
    root = Path(repo_root).resolve() if repo_root is not None else ROOT
    if isinstance(source, Path) and source.is_absolute():
        path = source.resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise _error("composition_schema_invalid", "Composition path escapes the repository.", field="composition_ref") from exc
    else:
        reference = str(source)
        path = _safe_relative_path(root, reference)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _error("composition_schema_invalid", "Composition file could not be read.", field="composition_ref") from exc
    return validate_composition(value)


def default_regions() -> dict[str, dict[str, int]]:
    """Return only the canonical safe regions for callers building a contract."""

    return copy.deepcopy(default_composition()["regions"])  # type: ignore[return-value]


__all__ = ["KNOWLEDGE_LAYOUT", "default_composition", "default_regions", "load_composition", "validate_composition"]
