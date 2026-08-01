"""Offline proof evaluator for the Project-owned single-consumer state."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FORBIDDEN = (
    "token",
    "secret",
    "password",
    "credential",
    "authorization",
    "app_id",
    "app_secret",
    "url",
    "path",
)


def _forbidden(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            any(term in str(key).lower() for term in FORBIDDEN) or _forbidden(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_forbidden(item) for item in value)
    return False


def _time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def check(snapshot: dict[str, Any], *, heartbeat_max_age_seconds: int = 30) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(snapshot, dict) or _forbidden(snapshot):
        return {
            "status": "SINGLE_CONSUMER_NOT_PROVEN",
            "failures": ["forbidden_or_invalid_snapshot"],
        }
    required = {
        "binding_owner": "project_gateway",
        "consumer_count": 1,
        "feishu_connection_count": 1,
        "core_binding_state": "stopped",
        "core_feishu_connection_count": 0,
        "other_owner_event_count": 0,
        "duplicate_reply_count": 0,
    }
    for field, expected in required.items():
        if snapshot.get(field) != expected:
            failures.append(f"{field}_unexpected")
    pid, lease_pid = snapshot.get("owner_pid"), snapshot.get("lease_owner_pid")
    if not isinstance(pid, int) or pid <= 0 or lease_pid != pid:
        failures.append("pid_lease_mismatch")
    observed_at, heartbeat_at = (
        _time(snapshot.get("observed_at")),
        _time(snapshot.get("last_heartbeat_at")),
    )
    if (
        observed_at is None
        or heartbeat_at is None
        or (observed_at - heartbeat_at).total_seconds() < 0
        or (observed_at - heartbeat_at).total_seconds() > heartbeat_max_age_seconds
    ):
        failures.append("heartbeat_not_fresh")
    return {
        "status": "SINGLE_CONSUMER_PROVEN" if not failures else "SINGLE_CONSUMER_NOT_PROVEN",
        "failures": failures,
        "owner_pid": pid if isinstance(pid, int) and pid > 0 else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify supplied project single-consumer evidence offline."
    )
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            check(json.loads(args.snapshot.read_text(encoding="utf-8"))),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
