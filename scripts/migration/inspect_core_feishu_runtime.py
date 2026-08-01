"""Read-only projection of the live Core Feishu account runtime.

The probe calls only ``channels.status``.  It never invokes lifecycle methods,
reads configuration, or prints raw CLI output.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from typing import Any

ACCOUNT = "zhongshu"
CHANNEL = "feishu"
UNAVAILABLE = "CORE_CONSUMER_RUNTIME_OBSERVABILITY_UNAVAILABLE"
EVIDENCE_SOURCE = "openclaw_gateway_rpc_channels.status"
Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def unavailable() -> dict[str, Any]:
    return {
        "owner": "unknown",
        "consumer_count": None,
        "runtime_state": "unknown",
        "evidence_source": UNAVAILABLE,
        "confidence": "low",
    }


def build_command(executable: str = "openclaw") -> list[str]:
    return [
        executable,
        "gateway",
        "call",
        "channels.status",
        "--params",
        json.dumps({"channel": CHANNEL, "accountId": ACCOUNT}, separators=(",", ":")),
        "--json",
        "--timeout",
        "8000",
    ]


def _default_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=12,
        check=False,
    )


def _decode(stdout: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(stdout.strip())
    except (json.JSONDecodeError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def inspect_payload(payload: dict[str, Any]) -> dict[str, Any]:
    accounts = payload.get("channelAccounts", {}).get(CHANNEL, [])
    if not isinstance(accounts, list):
        return unavailable()
    matches = [
        item for item in accounts if isinstance(item, dict) and item.get("accountId") == ACCOUNT
    ]
    if len(matches) != 1 or not isinstance(matches[0].get("running"), bool):
        return unavailable()
    account = matches[0]
    running = account["running"]
    if not running:
        return {
            "owner": "none",
            "consumer_count": 0,
            "runtime_state": "stopped",
            "evidence_source": EVIDENCE_SOURCE,
            "confidence": "high",
        }
    consumer_count = account.get("consumerCount")
    if not isinstance(consumer_count, int) or isinstance(consumer_count, bool):
        return unavailable()
    if consumer_count != 1:
        return {
            "owner": "openclaw_core_feishu",
            "consumer_count": consumer_count,
            "runtime_state": "unknown",
            "evidence_source": EVIDENCE_SOURCE,
            "confidence": "high",
        }
    return {
        "owner": "openclaw_core_feishu",
        "consumer_count": 1,
        "runtime_state": "healthy",
        "evidence_source": EVIDENCE_SOURCE,
        "confidence": "high",
    }


def inspect_core_feishu_runtime(
    runner: Runner = _default_runner,
    *,
    executable: str | None = None,
) -> dict[str, Any]:
    resolved = executable or shutil.which("openclaw")
    if not resolved:
        return unavailable()
    try:
        completed = runner(build_command(resolved))
    except (OSError, subprocess.SubprocessError, TimeoutError):
        return unavailable()
    if completed.returncode != 0:
        return unavailable()
    payload = _decode(completed.stdout)
    return inspect_payload(payload) if payload is not None else unavailable()


def main() -> int:
    result = inspect_core_feishu_runtime()
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 2 if result["runtime_state"] == "unknown" else 0


if __name__ == "__main__":
    raise SystemExit(main())
