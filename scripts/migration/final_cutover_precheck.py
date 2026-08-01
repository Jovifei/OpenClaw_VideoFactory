"""Read-only final gate for a zhongshu maintenance-window cutover.

The input is a sanitized snapshot assembled by approved read-only collectors.
This script never connects to OpenClaw or Feishu and never controls a process.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ACCOUNT = "zhongshu"
SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def _same_sha256(expected: Any, observed: Any) -> bool:
    return (
        isinstance(expected, str)
        and isinstance(observed, str)
        and SHA256.fullmatch(expected) is not None
        and expected.lower() == observed.lower()
    )


def evaluate(
    snapshot: dict[str, Any], *, rollback_artifact_exists: bool | None = None
) -> dict[str, bool]:
    """Evaluate a sanitized snapshot; missing or malformed fields fail closed."""
    rpc = snapshot.get("rpc") if isinstance(snapshot.get("rpc"), dict) else {}
    core = snapshot.get("core_consumer") if isinstance(snapshot.get("core_consumer"), dict) else {}
    gateway = (
        snapshot.get("project_gateway") if isinstance(snapshot.get("project_gateway"), dict) else {}
    )
    token_ready = rpc.get("token_present") is True
    rpc_ready = (
        token_ready
        and all(
            rpc.get(field) is True
            for field in ("ready", "rpc_endpoint_available", "auth_valid", "session_ready")
        )
        and rpc.get("rpc_preflight_result") == "RPC_READY"
    )
    core_consumer_known = (
        core.get("owner") == "openclaw_core_feishu"
        and core.get("consumer_count") == 1
        and core.get("runtime_state") == "healthy"
        and core.get("confidence") == "high"
    )
    artifact = (
        snapshot.get("rollback_artifact_exists")
        if rollback_artifact_exists is None
        else rollback_artifact_exists
    )
    rollback_ready = artifact is True and snapshot.get("rollback_control_ready") is True
    # The Project Gateway must be stopped now; this means it is safe to start only
    # after the Core zero-consumer proof at T+1.
    gateway_ready = gateway.get("running") is False
    account_valid = snapshot.get("account") == ACCOUNT
    config_valid = _same_sha256(
        snapshot.get("expected_config_sha256"), snapshot.get("observed_config_sha256")
    )
    return {
        "token_ready": token_ready,
        "rpc_ready": rpc_ready,
        "core_consumer_known": core_consumer_known,
        "rollback_ready": rollback_ready,
        "gateway_ready": gateway_ready,
        "can_cutover": all(
            (
                rpc_ready,
                core_consumer_known,
                rollback_ready,
                gateway_ready,
                account_valid,
                config_valid,
            )
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only final zhongshu cutover precheck.")
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--rollback-plan", type=Path)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    if not isinstance(snapshot, dict):
        raise ValueError("cutover_snapshot_object_required")
    rollback_exists = args.rollback_plan.is_file() if args.rollback_plan else None
    result = evaluate(snapshot, rollback_artifact_exists=rollback_exists)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["can_cutover"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
