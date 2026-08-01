"""Fail-closed, read-only validation for a future zhongshu cutover result.

The checker compares sanitized pre- and post-cutover snapshots.  It cannot
start a Gateway, stop a Binding, send a message, or contact Feishu/OpenClaw.
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


def _hashes_are_unique(values: Any) -> bool:
    return (
        isinstance(values, list)
        and all(isinstance(item, str) and _HASH.fullmatch(item) for item in values)
        and len(values) == len(set(values))
    )


def check(post_snapshot: dict[str, Any], pre_snapshot: dict[str, Any]) -> dict[str, Any]:
    """Validate sole ownership, unique delivery evidence, and session continuity."""
    failures: list[str] = []
    if _contains_forbidden_key(post_snapshot) or _contains_forbidden_key(pre_snapshot):
        failures.append("forbidden_snapshot_field")
    if post_snapshot.get("schema") != "p0_zhongshu_postcheck_v1":
        failures.append("schema_invalid")
    if post_snapshot.get("capture_mode") != "operator_read_only":
        failures.append("read_only_capture_required")
    if post_snapshot.get("entry") != "zhongshu":
        failures.append("zhongshu_entry_required")

    core = post_snapshot.get("core", {})
    project = post_snapshot.get("project", {})
    expected_core = {
        "binding_enabled": False,
        "binding_count": 0,
        "feishu_consumer_count": 0,
        "websocket_count": 0,
        "gateway_state": "stopped",
    }
    expected_project = {
        "feishu_consumer_count": 1,
        "websocket_count": 1,
        "gateway_state": "running",
        "ready": True,
        "lease_owner": "project_gateway",
    }
    for field, expected in expected_core.items():
        if core.get(field) != expected:
            failures.append(f"core_{field}_unexpected")
    for field, expected in expected_project.items():
        if project.get(field) != expected:
            failures.append(f"project_{field}_unexpected")
    if post_snapshot.get("combined_feishu_consumer_count") != 1:
        failures.append("combined_consumer_count_unexpected")

    phase = post_snapshot.get("test_phase")
    if phase not in {"consumer", "text", "attachment", "card"}:
        failures.append("test_phase_invalid")
    event_hashes = post_snapshot.get("event_hashes", [])
    reply_hashes = post_snapshot.get("reply_hashes", [])
    if not _hashes_are_unique(event_hashes):
        failures.append("event_hashes_not_unique")
    if not _hashes_are_unique(reply_hashes):
        failures.append("reply_hashes_not_unique")
    if phase != "consumer" and (not event_hashes or not reply_hashes):
        failures.append("delivery_evidence_missing")

    pre_session = pre_snapshot.get("session", {})
    post_session = post_snapshot.get("session", {})
    if post_session.get("continuity_verified") is not True:
        failures.append("session_continuity_not_verified")
    if pre_session.get("lineage_hash") != post_session.get("lineage_hash") or not _HASH.fullmatch(
        str(post_session.get("lineage_hash", ""))
    ):
        failures.append("session_lineage_mismatch")

    return {
        "status": "pass" if not failures else "fail",
        "scope": "sanitized_read_only_snapshot",
        "execution_authorized": False,
        "failures": failures,
    }


def _load_snapshot(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("snapshot_must_be_object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only zhongshu migration postcheck checker")
    parser.add_argument("--preflight-snapshot", required=True, type=Path)
    parser.add_argument("--postcutover-snapshot", required=True, type=Path)
    args = parser.parse_args()
    result = check(
        _load_snapshot(args.postcutover_snapshot), _load_snapshot(args.preflight_snapshot)
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
