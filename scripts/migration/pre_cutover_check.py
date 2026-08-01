"""Check a local mock pre-cutover snapshot; this script cannot inspect or modify production."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def check(snapshot: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if snapshot.get("mode") != "mock_qualification":
        failures.append("mock_mode_required")
    expected = {
        "old_consumer_count": 1,
        "new_consumer_count": 0,
        "old_websocket_count": 1,
        "new_websocket_count": 0,
        "active_tasks": 0,
        "pending_media": 0,
    }
    for field, value in expected.items():
        if snapshot.get(field) != value:
            failures.append(f"{field}_unexpected")
    if not snapshot.get("binding_backup_exists"):
        failures.append("binding_backup_missing")
    if snapshot.get("duplicate_events") or snapshot.get("duplicate_replies"):
        failures.append("duplicate_observed")
    return {
        "status": "pass" if not failures else "fail",
        "scope": "local_mock_only",
        "failures": failures,
        "planned_owner": "project_gateway",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    if not args.mock:
        parser.error("--mock is required; live cutover is unsupported")
    print(
        json.dumps(check(json.loads(args.snapshot.read_text(encoding="utf-8"))), ensure_ascii=False)
    )
