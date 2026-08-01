"""Fail-closed read-only gate for Core Feishu account maintenance.

This script never stops a Binding, starts a Gateway, sends Feishu traffic, or
changes OpenClaw state. ``--execute`` is intentionally rejected in 033.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def evaluate(result: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if result.get("shadow_only") is not True:
        failures.append("shadow_only_required")
    if result.get("plugin_list_feishu_seen") is not True:
        failures.append("real_feishu_plugin_not_seen")
    if result.get("gateway_ready") is not True:
        failures.append("shadow_gateway_not_ready")
    if result.get("config_validate_exit") != 0 or result.get("config_validate_json") is not True:
        failures.append("shadow_config_validation_failed")
    if result.get("plugin_list_exit") != 0:
        failures.append("shadow_plugin_list_failed")
    guard = result.get("transport_guard", {})
    if guard.get("loopback_only") is not True or guard.get("unexpected_network_access") != 0:
        failures.append("transport_isolation_failed")
    if (
        guard.get("gateway_process_count", 0) < 1
        or guard.get("gateway_unexpected_network_access") != 0
    ):
        failures.append("gateway_transport_aggregation_failed")
    fake = result.get("fake_transport", {})
    if fake.get("transport") != "fake-feishu-sdk":
        failures.append("fake_transport_missing")
    if result.get("process_shutdown") is not True:
        failures.append("shadow_process_not_shutdown")
    shutdown = result.get("calls", {}).get("shutdown_preflight", {})
    if (
        shutdown.get("exit") != 0
        or shutdown.get("json") is not True
        or shutdown.get("safe") is not True
    ):
        failures.append("shutdown_preflight_failed")
    return {
        "status": "PASS" if not failures else "FAIL",
        "execution": "NOT_APPLIED",
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shadow-result", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.execute:
        print(json.dumps({"status": "BLOCKED", "reason": "PRODUCTION_EXECUTION_DISABLED_033"}))
        return 2
    result = evaluate(json.loads(args.shadow_result.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
