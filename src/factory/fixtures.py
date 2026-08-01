"""Load only the three repository-controlled synthetic fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from .config import PROJECT_ROOT


def load_fixture(fixture_id: str) -> dict[str, str]:
    fixtures = json.loads(
        (PROJECT_ROOT / "fixtures" / "test_topics.json").read_text(encoding="utf-8")
    )
    fixtures += json.loads(
        (PROJECT_ROOT / "fixtures" / "p1_candidate_topics.json").read_text(encoding="utf-8")
    )
    for fixture in fixtures:
        if fixture["id"] == fixture_id:
            return fixture
    raise ValueError(f"unknown_fixture:{fixture_id}")


def fixture_content(fixture_id: str) -> dict[str, object]:
    content = json.loads(
        (PROJECT_ROOT / "fixtures" / "p1_candidate_content.json").read_text(encoding="utf-8")
    )
    try:
        return content[fixture_id]
    except KeyError as exc:
        raise ValueError(f"fixture_content_missing:{fixture_id}") from exc
