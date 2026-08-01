"""Validate an operator-supplied local rollback manifest without controlling services."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STEPS = (
    "stop_project_gateway",
    "restore_core_binding",
    "start_core_gateway",
    "verify_text_attachment_session",
    "record_event",
)


def check(manifest: dict) -> dict:
    missing = [step for step in STEPS if step not in manifest.get("steps", [])]
    backup = Path(manifest.get("backup_path", ""))
    failures = (["rollback_backup_missing"] if not backup.is_file() else []) + (
        ["rollback_steps_missing:" + ",".join(missing)] if missing else []
    )
    return {"status": "pass" if not failures else "fail", "failures": failures}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(check(json.loads(args.manifest.read_text(encoding="utf-8"))), ensure_ascii=False)
    )
