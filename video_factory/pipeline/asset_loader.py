"""Discover and validate local still-image assets without image libraries."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


class AssetLoadError(ValueError):
    """A recoverable input error that callers can present without a traceback."""


def _natural_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", path.name)]


def image_dimensions(path: Path) -> tuple[int, int]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", str(path)],
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    try:
        stream = json.loads(result.stdout)["streams"][0]
        width, height = int(stream["width"]), int(stream["height"])
    except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise AssetLoadError(f"invalid_image:{path.name}") from exc
    if width < 1 or height < 1:
        raise AssetLoadError(f"invalid_image:{path.name}")
    return width, height


def build_asset_manifest(asset_dir: Path) -> dict[str, object]:
    asset_dir = Path(asset_dir)
    if not asset_dir.is_dir():
        raise AssetLoadError("asset_directory_missing")
    paths = sorted(
        (path for path in asset_dir.iterdir() if path.is_file() and path.suffix.casefold() in IMAGE_SUFFIXES),
        key=_natural_key,
    )
    if not paths:
        raise AssetLoadError("asset_directory_empty")
    assets = []
    for index, path in enumerate(paths, start=1):
        width, height = image_dimensions(path)
        assets.append(
            {"order": index, "path": path.name, "width": width, "height": height}
        )
    return {"schema_version": "1.0", "asset_directory": asset_dir.name, "assets": assets}
