"""Read-only evaluator for account-scoped Core Feishu lifecycle evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def evaluate(result: dict[str, Any]) -> dict[str, Any]:
    calls = result.get("calls", {})
    failures: list[str] = []
    if result.get("shadow_only") is not True or result.get("gateway_ready") is not True:
        failures.append("shadow_gateway_not_ready")
    if result.get("config_validate_exit") != 0 or result.get("config_validate_json") is not True:
        failures.append("shadow_config_validation_failed")
    if result.get("plugin_list_exit") != 0 or result.get("plugin_list_feishu_seen") is not True:
        failures.append("shadow_plugin_not_loaded")
    if result.get("process_shutdown") is not True:
        failures.append("shadow_process_not_shutdown")
    for name in ("start", "start_repeat", "start_after_stop"):
        if (
            calls.get(name, {}).get("exit") != 0
            or calls.get(name, {}).get("json") is not True
            or calls.get(name, {}).get("started") is not True
        ):
            failures.append(f"{name}_not_started")
    for name in ("stop", "stop_repeat", "stop_final"):
        if (
            calls.get(name, {}).get("exit") != 0
            or calls.get(name, {}).get("json") is not True
            or calls.get(name, {}).get("stopped") is not True
        ):
            failures.append(f"{name}_not_stopped")
    if (
        calls.get("status_after_start", {})
        .get("account_states", {})
        .get("zhongshu", {})
        .get("running")
        is not True
    ):
        failures.append("target_not_running_after_start")
    if (
        calls.get("status_after_stop", {})
        .get("account_states", {})
        .get("zhongshu", {})
        .get("running")
        is not False
    ):
        failures.append("target_not_stopped")
    for state in (
        calls.get("status_after_start", {}).get("account_states", {}),
        calls.get("status_after_stop", {}).get("account_states", {}),
    ):
        if state.get("shadow-secondary", {}).get("running") is not False:
            failures.append("secondary_account_scope_violation")
    guard = result.get("transport_guard", {})
    fake = result.get("fake_transport", {})
    if (
        guard.get("unexpected_network_access") != 0
        or guard.get("gateway_process_count", 0) < 1
        or guard.get("gateway_unexpected_network_access") != 0
        or fake.get("duplicate_connect_detected") is True
    ):
        failures.append("transport_or_duplicate_violation")
    if fake.get("active_connections") != 0 or fake.get("connect_count") != fake.get("close_count"):
        failures.append("transport_not_closed")
    shutdown = calls.get("shutdown_preflight", {})
    if (
        shutdown.get("exit") != 0
        or shutdown.get("json") is not True
        or shutdown.get("safe") is not True
    ):
        failures.append("shutdown_preflight_failed")
    if shutdown.get("counts", {}).get("totalActive", 0) != 0:
        failures.append("active_tasks_at_shutdown")
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
