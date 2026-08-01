"""Validate a local mock rollback result without stopping or restoring any service."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def check(snapshot: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if snapshot.get("mode") != "mock_qualification":
        failures.append("mock_mode_required")
    required_true = (
        "gateway_start_failed",
        "project_gateway_stopped",
        "old_binding_restored",
        "old_text_path_verified",
        "old_attachment_path_verified",
        "rollback_manifest_exists",
    )
    for field in required_true:
        if snapshot.get(field) is not True:
            failures.append(f"{field}_missing")
    recovery_seconds = snapshot.get("recovery_seconds")
    if not isinstance(recovery_seconds, int) or recovery_seconds < 0:
        failures.append("recovery_seconds_invalid")
    return {
        "status": "pass" if not failures else "fail",
        "scope": "local_mock_only",
        "failures": failures,
        "recovery_seconds": recovery_seconds,
        "recovery_point": snapshot.get("recovery_point"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    if not args.mock:
        parser.error("--mock is required; live rollback is unsupported")
    print(
        json.dumps(check(json.loads(args.snapshot.read_text(encoding="utf-8"))), ensure_ascii=False)
    )
