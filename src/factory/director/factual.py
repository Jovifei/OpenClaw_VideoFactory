"""Safe, source-linked factual brief loading for Director jobs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.validation import validate

from .context import normalize_topic


@dataclass(frozen=True, slots=True)
class FactualBrief:
    """Validated factual metadata; source page contents are never retained."""

    document: dict[str, Any]
    relative_path: str

    @property
    def topic_digest(self) -> str:
        return str(self.document["topic_digest"])

    @property
    def verified(self) -> bool:
        return self.document.get("review_status") == "verified" and len(self.document.get("sources", [])) >= 2

    def prompt_payload(self) -> dict[str, object]:
        return {
            "topic_digest": self.topic_digest,
            "review_status": self.document.get("review_status"),
            "facts": [
                {"fact_id": item.get("fact_id"), "claim": item.get("claim"), "source_ids": item.get("source_ids", [])}
                for item in self.document.get("facts", [])
            ],
            "sources": [
                {"source_id": item.get("source_id"), "title": item.get("title"), "publisher": item.get("publisher"), "kind": item.get("kind")}
                for item in self.document.get("sources", [])
            ],
        }


def _safe_relative_path(repo_root: Path, value: str) -> tuple[Path, str]:
    if not isinstance(value, str) or not value.strip():
        raise FactoryContractError(
            "director_factual_brief_invalid",
            "Factual brief reference must be a repository-relative path.",
            {"field": "factual_brief", "reason": "empty"},
        )
    raw = value.replace("\\", "/")
    candidate = Path(raw)
    if candidate.is_absolute() or ":" in raw or any(part in {"", ".", ".."} for part in candidate.parts):
        raise FactoryContractError(
            "director_factual_brief_invalid",
            "Factual brief reference is unsafe.",
            {"field": "factual_brief", "reason": "path"},
        )
    root = repo_root.resolve()
    resolved = (root / Path(*candidate.parts)).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise FactoryContractError(
            "director_factual_brief_invalid",
            "Factual brief reference escapes the repository.",
            {"field": "factual_brief", "reason": "escape"},
        ) from exc
    return resolved, "/".join(candidate.parts)


def load_factual_brief(path: str | Path, *, repo_root: Path, topic: str) -> FactualBrief:
    """Load and validate one bounded factual brief without exposing raw input in errors."""

    normalized = normalize_topic(topic)
    resolved, relative = _safe_relative_path(repo_root, str(path))
    try:
        document = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FactoryContractError(
            "director_factual_brief_invalid",
            "Factual brief could not be read.",
            {"field": "factual_brief", "reason": "read"},
        ) from exc
    if not isinstance(document, dict):
        raise FactoryContractError(
            "director_factual_brief_invalid",
            "Factual brief must be a JSON object.",
            {"field": "factual_brief", "reason": "type"},
        )
    validate(document, "director_factual_brief")
    expected = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    if document.get("topic_digest") != expected:
        raise FactoryContractError(
            "director_factual_brief_invalid",
            "Factual brief topic digest does not match the requested topic.",
            {"field": "topic_digest", "reason": "mismatch"},
        )
    source_ids = {str(item.get("source_id")) for item in document.get("sources", []) if isinstance(item, dict)}
    for index, fact in enumerate(document.get("facts", [])):
        if not isinstance(fact, dict) or any(str(source_id) not in source_ids for source_id in fact.get("source_ids", [])):
            raise FactoryContractError(
                "director_factual_brief_invalid",
                "Every factual claim must reference a declared source.",
                {"field": f"facts.{index}.source_ids", "reason": "source_unresolved"},
            )
    if document.get("review_status") == "verified" and len(source_ids) < 2:
        raise FactoryContractError(
            "director_factual_brief_invalid",
            "A verified factual brief requires at least two sources.",
            {"field": "sources", "reason": "minimum_sources"},
        )
    return FactualBrief(document=document, relative_path=relative)


__all__ = ["FactualBrief", "load_factual_brief"]
