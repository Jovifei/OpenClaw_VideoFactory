"""Local, deterministic Video Job lifecycle snapshots for Director jobs.

This module deliberately stops at an atomic JSON snapshot.  It is not a
database, scheduler, retry engine, or OpenClaw state store.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .errors import FactoryContractError
from .failure_contract import normalize_execution_error, sanitize_error_payload
from .validation import validate


_STATES = (
    "created",
    "planning",
    "script_ready",
    "storyboard_ready",
    "rendering",
    "quality_check",
    "completed",
    "failed",
)
_NEXT = {
    "created": "planning",
    "planning": "script_ready",
    "script_ready": "storyboard_ready",
    "storyboard_ready": "rendering",
    "rendering": "quality_check",
    "quality_check": "completed",
}
_TERMINAL = {"completed", "failed"}


def _topic_digest(topic: str) -> str:
    return hashlib.sha256(topic.encode("utf-8")).hexdigest()


def _safe_ref(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FactoryContractError(
            "video_job_state_invalid",
            "Video job artifact references must be non-empty relative paths.",
            {"field": field, "reason": "empty"},
        )
    raw = value.replace("\\", "/")
    candidate = Path(raw)
    if candidate.is_absolute() or ":" in raw or any(part in {"", ".", ".."} for part in candidate.parts):
        raise FactoryContractError(
            "video_job_state_invalid",
            "Video job artifact references must remain relative to the job directory.",
            {"field": field, "reason": "path"},
        )
    return "/".join(candidate.parts)


class VideoJobStateMachine:
    """Validate and persist the bounded Phase 2 local lifecycle."""

    def __init__(self, *, work_dir: Path | None = None) -> None:
        self.work_dir = Path(work_dir).resolve() if work_dir is not None else None

    def initial(self, *, job_id: str, topic: str, factual_review_required: bool = True, factual_review_status: str | None = None) -> dict[str, object]:
        if not isinstance(job_id, str) or not job_id or not job_id.replace("_", "").isalnum() or job_id.lower() != job_id:
            raise FactoryContractError("video_job_state_invalid", "Video job ID is invalid.", {"field": "job_id", "reason": "format"})
        if not isinstance(topic, str) or not topic.strip():
            raise FactoryContractError("video_job_state_invalid", "Video job topic is invalid.", {"field": "topic", "reason": "empty"})
        review_status = factual_review_status or ("review_required" if factual_review_required else "not_applicable")
        if review_status not in {"verified", "review_required", "not_applicable"}:
            raise FactoryContractError("video_job_state_invalid", "Factual review status is invalid.", {"field": "factual_review_status", "reason": "enum"})
        snapshot: dict[str, object] = {
            "schema_version": "2.0",
            "job_id": job_id,
            "topic": topic,
            "topic_digest": _topic_digest(topic),
            "state": "created",
            "state_revision": 0,
            "factual_review_required": bool(factual_review_required),
            "factual_review_status": review_status,
        }
        self._validate(snapshot)
        return snapshot

    def transition(
        self,
        snapshot: dict[str, object],
        target: str,
        *,
        artifact_refs: dict[str, str] | None = None,
        error: dict[str, object] | None = None,
    ) -> dict[str, object]:
        if not isinstance(snapshot, dict):
            raise FactoryContractError("video_job_state_invalid", "Video job state snapshot must be an object.", {"reason": "type"})
        current = snapshot.get("state")
        if target not in _STATES:
            raise FactoryContractError("video_job_state_invalid", "Video job state target is unknown.", {"field": "state", "reason": "enum"})
        if current in _TERMINAL:
            raise FactoryContractError("video_job_state_invalid", "A terminal Video Job state cannot transition.", {"field": "state", "reason": "terminal"})
        if target != "failed" and _NEXT.get(str(current)) != target:
            raise FactoryContractError("video_job_state_invalid", "Video Job state transition is not allowed.", {"field": "state", "reason": "transition"})
        if target == "failed" and current not in _STATES[:-1]:
            raise FactoryContractError("video_job_state_invalid", "A failed state cannot be reopened.", {"field": "state", "reason": "terminal"})
        updated = dict(snapshot)
        updated["state"] = target
        updated["state_revision"] = int(snapshot.get("state_revision", 0)) + 1
        if artifact_refs:
            for field, value in artifact_refs.items():
                if field not in {"script_ref", "storyboard_ref", "timeline_ref", "output_ref", "render_report_ref", "quality_report_ref"}:
                    raise FactoryContractError("video_job_state_invalid", "Unknown artifact reference field.", {"field": field, "reason": "field"})
                updated[field] = _safe_ref(value, field=field)
        if target == "failed":
            if not isinstance(error, dict) or not {"code", "message", "context"}.issubset(error):
                raise FactoryContractError("video_job_state_invalid", "Failed Video Jobs require a structured error.", {"field": "error", "reason": "required"})
            updated["error"] = {"code": str(error["code"]), "message": str(error["message"]), "context": dict(error["context"] if isinstance(error.get("context"), dict) else {})}
        elif error is not None:
            raise FactoryContractError("video_job_state_invalid", "Only failed states may contain a lifecycle error.", {"field": "error", "reason": "state"})
        self._validate(updated)
        return updated

    def fail(
        self,
        snapshot: dict[str, object],
        error: object,
        *,
        stage: object | None = None,
        path: Path | None = None,
    ) -> dict[str, object]:
        """Transition *snapshot* to ``failed`` and atomically persist it.

        ``write`` already uses a same-directory temporary file and
        ``os.replace``.  Keeping the transition and write here prevents
        callers from accidentally updating an in-memory failure while
        forgetting the durable snapshot.  Non-contract exceptions are
        reduced to the path-free ``video_job_execution_failed`` contract.
        """

        if isinstance(error, FactoryContractError):
            payload = sanitize_error_payload(error, stage=stage)
        elif isinstance(error, dict):
            payload = sanitize_error_payload(error, stage=stage)
        else:
            payload = normalize_execution_error(
                error if isinstance(error, BaseException) else TypeError("invalid_error"),
                stage=stage or "unknown",
            ).to_dict()
        updated = self.transition(snapshot, "failed", error=payload)
        self.write(updated, path=path)
        return updated

    def write(self, snapshot: dict[str, object], path: Path | None = None) -> Path:
        target = Path(path) if path is not None else (self.work_dir / "video_job_state.json" if self.work_dir else None)
        if target is None:
            raise FactoryContractError("video_job_state_invalid", "A state snapshot path is required.", {"reason": "path_missing"})
        self._validate(snapshot)
        target = target.resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(snapshot, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
        finally:
            try:
                Path(temp_name).unlink()
            except FileNotFoundError:
                pass
        return target

    @staticmethod
    def _validate(snapshot: dict[str, object]) -> None:
        validate(snapshot, "video_job_state")


__all__ = ["VideoJobStateMachine"]
