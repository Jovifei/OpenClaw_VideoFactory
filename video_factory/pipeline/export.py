"""Stable JSON writes for local MVP artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: Any) -> None:
    # A dangling symlink passes the common exists() guard but would silently
    # redirect this write; refuse any link before touching the filesystem.
    if path.is_symlink():
        raise ValueError(f"refusing to write through a symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
