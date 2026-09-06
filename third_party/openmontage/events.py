# Source: https://github.com/calesthio/OpenMontage/blob/cd9f3c1f03368be87b140af494914b8ee4e3c7a4/lib/events.py
# Modified: read-only event parsing only; attribution and append writers removed because SQLite projection is authoritative.
"""Read projected Backlot events without exposing any write surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

EVENTS_FILENAME = "events.jsonl"


def read_events(project_dir: Path | str, limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Read projected events oldest-first, tolerating malformed lines."""
    path = Path(project_dir) / EVENTS_FILENAME
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    result: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result[-limit:] if limit is not None else result
