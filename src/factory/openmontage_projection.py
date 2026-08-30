"""Atomically export SQLite-owned job state for read-only OpenMontage consumers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .db import CandidateStore


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _atomic_lines(path: Path, values: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    text = "".join(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n" for value in values)
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def project_job_read_only(store: CandidateStore, job_id: str, projects_root: Path | str) -> Path:
    """Project current job data without invoking any store transition method."""
    job = store.status(job_id)
    artifacts = store.artifacts(job_id)
    events = store.events(job_id)
    project_dir = Path(projects_root).resolve() / job_id
    project_dir.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "version": "1.0",
        "project_id": job_id,
        "pipeline_type": "phase1-local-topic",
        "stage": job["state"].lower(),
        "status": "awaiting_human" if job["state"] == "PENDING_REVIEW" else "in_progress",
        "timestamp": job["updated_at"],
        "human_approval_required": job["state"] == "PENDING_REVIEW",
        "human_approved": False,
        "artifacts": {item["artifact_type"]: {"path": item["relative_path"], "sha256": item["sha256"]} for item in artifacts},
        "metadata": {"state_authority": "factory_sqlite", "projection_only": True},
    }
    _atomic_json(project_dir / "project.json", {**job, "state_authority": "factory_sqlite", "projection_only": True, "artifacts": artifacts})
    _atomic_json(project_dir / f"checkpoint_{job['state'].lower()}.json", snapshot)
    _atomic_lines(project_dir / "history" / "events.jsonl", events)
    return project_dir
