"""Fail-closed inspection of a sanitized, externally captured consumer snapshot.

This module never reads OpenClaw configuration, processes, sockets, or the
network.  Its input is deliberately limited to evidence already collected by
an approved read-only operator procedure.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ACCOUNT = "zhongshu"
OWNERS = frozenset({"core_feishu", "project_gateway", "none", "unknown"})
SOURCES = frozenset(
    {"core_feishu_runtime", "project_gateway_runtime", "operator_verified_no_consumer"}
)
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


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _base() -> dict[str, Any]:
    return {
        "status": "unknown",
        "account": ACCOUNT,
        "binding_owner": "unknown",
        "consumer_count": None,
        "feishu_connection_count": None,
        "owner_pid": None,
        "owner_start_time": None,
        "last_heartbeat_at": None,
        "last_event_at": None,
        "evidence_sources": [],
        "confidence": "low",
        "blocking_reasons": [],
    }


def inspect(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return only facts explicitly present in a sanitized snapshot."""
    result = _base()
    if not isinstance(snapshot, dict) or _forbidden(snapshot):
        result["blocking_reasons"].append("forbidden_or_invalid_snapshot")
        return result
    if snapshot.get("account") != ACCOUNT:
        result["blocking_reasons"].append("account_not_zhongshu")
        return result
    observations = snapshot.get("observations")
    if not isinstance(observations, list) or not observations:
        result["blocking_reasons"].append("no_reliable_consumer_evidence")
        return result
    usable = [
        item
        for item in observations
        if isinstance(item, dict) and item.get("explicit") is True and item.get("source") in SOURCES
    ]
    if not usable:
        result["blocking_reasons"].append("no_reliable_consumer_evidence")
        return result
    result["evidence_sources"] = sorted({item["source"] for item in usable})
    owners = {item.get("binding_owner") for item in usable}
    if len(owners) != 1 or not owners.issubset(OWNERS - {"unknown"}):
        result["blocking_reasons"].append("conflicting_or_invalid_owner_evidence")
        return result
    owner = owners.pop()
    counts = {(item.get("consumer_count"), item.get("feishu_connection_count")) for item in usable}
    if len(counts) != 1 or not all(_integer(value) for pair in counts for value in pair):
        result["blocking_reasons"].append("conflicting_or_invalid_count_evidence")
        return result
    consumer_count, connection_count = counts.pop()
    result.update(
        binding_owner=owner, consumer_count=consumer_count, feishu_connection_count=connection_count
    )
    if owner == "none":
        if consumer_count == 0 and connection_count == 0:
            result.update(status="stopped", confidence="high")
        else:
            result["blocking_reasons"].append("none_owner_with_nonzero_count")
        return result
    if consumer_count != 1 or connection_count != 1:
        result.update(status="unhealthy", confidence="medium")
        result["blocking_reasons"].append("consumer_or_connection_count_not_one")
        return result
    pids = {item.get("owner_pid") for item in usable}
    heartbeats = {item.get("last_heartbeat_at") for item in usable}
    if (
        len(pids) != 1
        or not isinstance(next(iter(pids)), int)
        or next(iter(pids)) <= 0
        or len(heartbeats) != 1
        or not next(iter(heartbeats))
    ):
        result.update(status="unhealthy", confidence="medium")
        result["blocking_reasons"].append("owner_pid_or_heartbeat_missing")
        return result
    first = usable[0]
    result.update(
        status="healthy",
        confidence="high" if len(usable) > 1 else "medium",
        owner_pid=first.get("owner_pid"),
        owner_start_time=first.get("owner_start_time"),
        last_heartbeat_at=first.get("last_heartbeat_at"),
        last_event_at=first.get("last_event_at"),
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a sanitized zhongshu consumer snapshot offline."
    )
    parser.add_argument(
        "snapshot", type=Path, help="sanitized JSON snapshot; never a live system target"
    )
    args = parser.parse_args()
    print(
        json.dumps(
            inspect(json.loads(args.snapshot.read_text(encoding="utf-8"))),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
