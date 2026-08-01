"""Read-only inventory and retention candidates for offline P1 artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .db import CandidateStore


def _artifacts(store: CandidateStore, job_id: str) -> list[dict[str, Any]]:
    return [
        {"type": item["artifact_type"], "relative_path": item["relative_path"], "sha256": item["sha256"]}
        for item in store.artifacts(job_id)
    ]


def build_inventory(store: CandidateStore) -> dict[str, Any]:
    jobs = []
    for job in store.list_jobs():
        jobs.append(
            {
                "job_id": job["job_id"],
                "fixture_id": job["fixture_id"],
                "template": job["template"],
                "state": job["state"],
                "attempt": job["attempt"],
                "created_at": job["created_at"],
                "updated_at": job["updated_at"],
                "artifacts": _artifacts(store, job["job_id"]),
            }
        )
    return {"schema_version": "1.0", "mode": "offline_candidate", "destructive_actions": False, "jobs": jobs, "job_count": len(jobs)}


def _referenced_in_reports(job_id: str, reports_root: Path) -> bool:
    if not reports_root.exists():
        return False
    for candidate in reports_root.glob("**/*"):
        if candidate.is_file() and candidate.suffix.lower() in {".md", ".json"}:
            try:
                if job_id in candidate.read_text(encoding="utf-8"):
                    return True
            except UnicodeDecodeError:
                continue
    return False


def _recent(created_at: str, now: datetime) -> bool:
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    return created >= now - timedelta(days=30)


def build_retention_plan(store: CandidateStore, reports_root: Path) -> dict[str, Any]:
    now = datetime.now(UTC)
    entries = []
    for job in store.list_jobs():
        reasons: list[str] = []
        if job["state"] == "PENDING_REVIEW":
            reasons.append("pending_review")
        if job["state"] in {"FAILED", "CANCELLED"}:
            reasons.append("failure_or_cancellation_evidence")
        if job["attempt"]:
            reasons.append("recovery_or_retry_evidence")
        if _recent(str(job["created_at"]), now):
            reasons.append("within_recent_30_days")
        if _referenced_in_reports(job["job_id"], reports_root):
            reasons.append("referenced_by_report_or_visual_review")
        manifests = store.artifacts(job["job_id"])
        types = {item["artifact_type"] for item in manifests}
        if {"final_master.mp4", "feishu_preview.mp4"}.issubset(types):
            reasons.append("delivery_candidate_evidence")
        entries.append(
            {
                "job_id": job["job_id"],
                "state": job["state"],
                "action": "retain" if reasons else "manual_review_only",
                "reasons": sorted(set(reasons)),
            }
        )
    return {
        "schema_version": "1.0",
        "mode": "offline_candidate",
        "destructive_actions": False,
        "deletion_performed": False,
        "entries": entries,
        "next_action": "manual review only; no command in this interface deletes artifacts",
    }
