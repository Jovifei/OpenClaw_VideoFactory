"""Evaluate a local simulated handoff observation; no process/socket inspection."""

from __future__ import annotations

import json
from pathlib import Path
import argparse


def check(snapshot: dict) -> dict:
    owners = snapshot.get("connection_owners", [])
    events = snapshot.get("event_ids", [])
    count = len(owners)
    duplicate = len(events) != len(set(events))
    return {
        "consumer_count": count,
        "connection_owner": owners[0] if count == 1 else None,
        "duplicate_risk": duplicate or count != 1,
        "status": "pass" if count == 1 and not duplicate else "fail",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    print(json.dumps(check(json.loads(parser.parse_args().snapshot.read_text(encoding="utf-8")))))
