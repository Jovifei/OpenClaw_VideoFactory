"""Local-only single-consumer proof and lease utility; never inspects live sockets."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable

VALID_OWNERS = frozenset({"openclaw_binding", "project_gateway"})


class ConsumerLease:
    def __init__(
        self,
        path: Path,
        owner: str,
        *,
        now: Callable[[], float] = time.time,
        stale_after_seconds: float = 30.0,
    ):
        if owner not in VALID_OWNERS or stale_after_seconds <= 0:
            raise ValueError("consumer_lease_invalid")
        self.path, self.owner, self.now, self.stale_after_seconds = (
            path,
            owner,
            now,
            stale_after_seconds,
        )

    def _read(self) -> dict[str, Any] | None:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else None
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _stale(self, record: dict[str, Any] | None) -> bool:
        return (
            record is None
            or not isinstance(record.get("heartbeat_at"), (int, float))
            or self.now() - record["heartbeat_at"] > self.stale_after_seconds
        )

    def acquire(self) -> dict[str, Any]:
        record = self._read()
        if record and not self._stale(record) and record.get("owner") != self.owner:
            return {"status": "consumer_lock_held", "owner": record.get("owner")}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"owner": self.owner, "heartbeat_at": self.now()}), encoding="utf-8"
        )
        return {"status": "consumer_lock_acquired", "owner": self.owner}

    def heartbeat(self) -> dict[str, Any]:
        record = self._read()
        if not record or record.get("owner") != self.owner:
            return {"status": "consumer_lock_not_owned"}
        self.path.write_text(
            json.dumps({"owner": self.owner, "heartbeat_at": self.now()}), encoding="utf-8"
        )
        return {"status": "consumer_heartbeat_recorded", "owner": self.owner}


def check(snapshot: dict[str, Any]) -> dict[str, Any]:
    owners = snapshot.get("connection_owners") or [
        item.get("identity") for item in snapshot.get("consumers", []) if item.get("identity")
    ]
    owners = [owner for owner in owners if owner]
    sockets = int(snapshot.get("websocket_count", -1))
    events, replies = snapshot.get("event_ids", []), snapshot.get("reply_ids", [])
    now, stale_after = (
        float(snapshot.get("now", time.time())),
        float(snapshot.get("stale_after_seconds", 30)),
    )
    lease = snapshot.get("lease") if isinstance(snapshot.get("lease"), dict) else {}
    lease_owner, heartbeat = lease.get("owner"), lease.get("heartbeat_at")
    stale = not isinstance(heartbeat, (int, float)) or now - heartbeat > stale_after
    duplicate_events, duplicate_replies = (
        len(events) - len(set(events)),
        len(replies) - len(set(replies)),
    )
    exclusive = (
        len(owners) == 1
        and owners[0] in VALID_OWNERS
        and not (snapshot.get("binding_running") and snapshot.get("project_gateway_running"))
    )
    passed = (
        exclusive
        and sockets == 1
        and lease_owner == owners[0]
        and not stale
        and not duplicate_events
        and not duplicate_replies
    )
    return {
        "status": "pass" if passed else "fail",
        "consumer_count": len(owners),
        "websocket_count": sockets,
        "connection_owner": owners[0] if len(owners) == 1 else None,
        "lease_owner": lease_owner,
        "lease_stale": stale,
        "duplicate_events": duplicate_events,
        "duplicate_replies": duplicate_replies,
        "duplicate_risk": not passed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(check(json.loads(args.snapshot.read_text(encoding="utf-8"))), ensure_ascii=False)
    )
