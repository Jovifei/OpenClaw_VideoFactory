"""Fail-closed, read-only validation for a future zhongshu cutover window.

This module never opens a network connection, invokes OpenClaw, or changes a
Binding.  An operator must first create a sanitized read-only snapshot during
an explicitly authorized maintenance window.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


_HASH = re.compile(r"^[a-f0-9]{64}$")
_FORBIDDEN_KEY_PARTS = ("secret", "token", "password", "authorization", "raw_")


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if any(part in str(key).lower() for part in _FORBIDDEN_KEY_PARTS):
                return True
            if _contains_forbidden_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and bool(_HASH.fullmatch(value))


def check(
    snapshot: dict[str, Any],
    *,
    config_backup_manifest_exists: bool,
    rollback_plan_exists: bool,
) -> dict[str, Any]:
    """Validate the pre-cutover invariants without exposing snapshot values."""
    failures: list[str] = []
    if _contains_forbidden_key(snapshot):
        failures.append("forbidden_snapshot_field")
    if snapshot.get("schema") != "p0_zhongshu_preflight_v1":
        failures.append("schema_invalid")
    if snapshot.get("capture_mode") != "operator_read_only":
        failures.append("read_only_capture_required")
    if snapshot.get("entry") != "zhongshu":
        failures.append("zhongshu_entry_required")

    inventory = snapshot.get("inventory", {})
    for field in (
        "agents_observed",
        "bindings_observed",
        "cron_observed",
        "gateway_observed",
        "sessions_observed",
    ):
        if inventory.get(field) is not True:
            failures.append(f"inventory_{field}_missing")

    core = snapshot.get("core", {})
    project = snapshot.get("project", {})
    expected_core = {
        "binding_enabled": True,
        "binding_count": 1,
        "feishu_consumer_count": 1,
        "websocket_count": 1,
        "gateway_state": "running",
    }
    expected_project = {
        "feishu_consumer_count": 0,
        "websocket_count": 0,
        "gateway_state": "stopped",
    }
    for field, expected in expected_core.items():
        if core.get(field) != expected:
            failures.append(f"core_{field}_unexpected")
    for field, expected in expected_project.items():
        if project.get(field) != expected:
            failures.append(f"project_{field}_unexpected")
    if snapshot.get("combined_feishu_consumer_count") != 1:
        failures.append("combined_consumer_count_unexpected")
    if snapshot.get("active_tasks") != 0:
        failures.append("active_tasks_present")
    if snapshot.get("pending_media") != 0:
        failures.append("pending_media_present")

    session = snapshot.get("session", {})
    if session.get("snapshot_present") is not True or not _is_hash(session.get("lineage_hash")):
        failures.append("session_snapshot_invalid")
    backup = snapshot.get("config_backup", {})
    if backup.get("manifest_present") is not True or not _is_hash(backup.get("sha256")):
        failures.append("config_backup_invalid")
    if not config_backup_manifest_exists:
        failures.append("config_backup_manifest_missing")
    rollback = snapshot.get("rollback", {})
    if (
        rollback.get("plan_present") is not True
        or rollback.get("plan_id") != "P0-ZHONGSHU-MIGRATION-QUALIFICATION-029"
    ):
        failures.append("rollback_plan_invalid")
    if not rollback_plan_exists:
        failures.append("rollback_plan_missing")

    return {
        "status": "pass" if not failures else "fail",
        "scope": "sanitized_read_only_snapshot",
        "migration_state": "ZHONGSHU_MIGRATION_WAITING_AUTH",
        "execution_authorized": False,
        "failures": failures,
    }


def _load_snapshot(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("snapshot_must_be_object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only zhongshu migration preflight checker")
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--config-backup-manifest", required=True, type=Path)
    parser.add_argument("--rollback-plan", required=True, type=Path)
    args = parser.parse_args()
    result = check(
        _load_snapshot(args.snapshot),
        config_backup_manifest_exists=args.config_backup_manifest.is_file(),
        rollback_plan_exists=args.rollback_plan.is_file(),
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
