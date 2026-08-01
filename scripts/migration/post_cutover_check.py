"""Check a local mock post-cutover snapshot; it has no live-socket capability."""

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
        "old_consumer_count": 0,
        "new_consumer_count": 1,
        "old_websocket_count": 0,
        "new_websocket_count": 1,
    }
    for field, value in expected.items():
        if snapshot.get(field) != value:
            failures.append(f"{field}_unexpected")
    if snapshot.get("connection_owner") != "project_gateway":
        failures.append("project_gateway_not_owner")
    if snapshot.get("duplicate_events") or snapshot.get("duplicate_replies"):
        failures.append("duplicate_observed")
    return {
        "status": "pass" if not failures else "fail",
        "scope": "local_mock_only",
        "failures": failures,
        "consumer_count": snapshot.get("new_consumer_count", 0),
        "connection_owner": snapshot.get("connection_owner"),
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
