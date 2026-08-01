"""Evaluate a local, redacted maintenance snapshot; never queries OpenClaw."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = (
    "config_backup_exists",
    "config_sha256",
    "gateway_running",
    "binding_count",
    "cron_count",
    "running_tasks",
    "pending_media",
)


def check(snapshot: dict) -> dict:
    missing = [key for key in REQUIRED if key not in snapshot]
    failures = []
    if missing:
        failures.append("missing:" + ",".join(missing))
    if not snapshot.get("config_backup_exists"):
        failures.append("config_backup_missing")
    if not snapshot.get("config_sha256"):
        failures.append("config_sha_missing")
    if not snapshot.get("gateway_running"):
        failures.append("gateway_not_running")
    if int(snapshot.get("binding_count", 0)) != 1:
        failures.append("binding_count_not_one")
    if int(snapshot.get("running_tasks", 0)) != 0:
        failures.append("active_tasks_present")
    if int(snapshot.get("pending_media", 0)) != 0:
        failures.append("pending_media_present")
    return {
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "cron_count": int(snapshot.get("cron_count", 0)),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(check(json.loads(args.snapshot.read_text(encoding="utf-8"))), ensure_ascii=False)
    )
