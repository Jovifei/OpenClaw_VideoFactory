"""Publish SQLite-owned job snapshots for read-only OpenMontage consumers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .db import CandidateStore


_STATE_MAP: dict[str, tuple[str, str]] = {
    "NEW": ("research", "in_progress"),
    "RESEARCHING": ("research", "in_progress"),
    "SCRIPTING": ("script", "in_progress"),
    "VOICE": ("edit", "in_progress"),
    "CAPTIONS": ("edit", "in_progress"),
    "ASSETS": ("assets", "in_progress"),
    "RENDERING": ("compose", "in_progress"),
    "QUALITY_CHECK": ("review", "in_progress"),
    "PENDING_REVIEW": ("review", "awaiting_human"),
    "FAILED": ("review", "failed"),
    "CANCELLED": ("review", "failed"),
}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _atomic_pointer(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    _write_json(temporary, value)
    temporary.replace(path)


def build_checkpoint(snapshot: dict[str, Any]) -> dict[str, Any]:
    job = snapshot["job"]
    state = str(job["state"])
    try:
        stage, status = _STATE_MAP[state]
    except KeyError as exc:
        raise ValueError(f"unknown_sqlite_state:{state}") from exc
    artifacts = snapshot.get("artifacts", [])
    return {
        "version": "1.0",
        "project_id": job["job_id"],
        "pipeline_type": "phase1-local-topic",
        "stage": stage,
        "status": status,
        "timestamp": job["updated_at"],
        "human_approval_required": status == "awaiting_human",
        "human_approved": False,
        "artifacts": {
            item["artifact_type"]: {"path": item["relative_path"], "sha256": item["sha256"]}
            for item in artifacts
        },
        "metadata": {
            "state_authority": "sqlite",
            "projection_only": True,
            "sqlite_state": state,
        },
    }


def project_job_read_only(store: CandidateStore, job_id: str, projects_root: Path | str) -> Path:
    """Publish one complete immutable generation, then switch its pointer."""
    snapshot = store.projection_snapshot(job_id)
    checkpoint = build_checkpoint(snapshot)
    job = snapshot["job"]
    project_dir = Path(projects_root).resolve() / job_id
    generation_id = uuid4().hex
    generation_rel = Path("generations") / generation_id
    generation = project_dir / generation_rel
    generation.mkdir(parents=True, exist_ok=False)
    _write_json(
        generation / "project.json",
        {
            **job,
            "state_authority": "sqlite",
            "projection_only": True,
            "generation": generation_id,
            "artifacts": snapshot["artifacts"],
        },
    )
    _write_json(generation / f"checkpoint_{checkpoint['stage']}.json", checkpoint)
    events_text = "".join(
        json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n"
        for value in snapshot["events"]
    )
    history = generation / "history" / "events.jsonl"
    history.parent.mkdir(parents=True, exist_ok=True)
    history.write_text(events_text, encoding="utf-8")
    _atomic_pointer(
        project_dir / "current.json",
        {"generation": generation_rel.as_posix(), "generation_id": generation_id},
    )
    return project_dir
