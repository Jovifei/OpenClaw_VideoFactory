"""Strict JSON parsing helpers for security-sensitive local evidence."""

from __future__ import annotations

import json
from typing import Any


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate_json_key")
        value[key] = item
    return value


def load_json_object_text(text: str) -> dict[str, Any]:
    """Decode one JSON object and reject duplicate keys at every depth."""
    value = json.loads(text, object_pairs_hook=_no_duplicate_keys)
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value
