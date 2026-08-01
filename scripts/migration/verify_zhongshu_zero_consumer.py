"""Offline proof evaluator for the Core-to-Project zero-consumer window."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.migration.inspect_zhongshu_consumer import _forbidden, inspect


def _time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def check(snapshot: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
    samples = snapshot.get("samples") if isinstance(snapshot, dict) else snapshot
    failures: list[str] = []
    if not isinstance(samples, list) or len(samples) < 3:
        return {
            "status": "ZERO_CONSUMER_NOT_PROVEN",
            "sample_count": 0 if not isinstance(samples, list) else len(samples),
            "window_seconds": None,
            "failures": ["three_samples_required"],
        }
    times, observations = [], []
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            failures.append(f"sample_{index}_invalid")
            continue
        captured = _time(sample.get("sampled_at"))
        if captured is None:
            failures.append(f"sample_{index}_timestamp_invalid")
        else:
            times.append(captured)
        observation = sample.get("observation")
        if not isinstance(observation, dict):
            failures.append(f"sample_{index}_observation_invalid")
            continue
        if _forbidden(observation):
            failures.append(f"sample_{index}_observation_forbidden")
            continue
        observations.append(inspect(observation) if "observations" in observation else observation)
    if len(times) == len(samples):
        intervals = [(later - earlier).total_seconds() for earlier, later in zip(times, times[1:])]
        window = (times[-1] - times[0]).total_seconds()
        if window < 10:
            failures.append("observation_window_under_ten_seconds")
        if any(interval < 5 for interval in intervals):
            failures.append("sample_interval_under_five_seconds")
    else:
        window = None
    for index, observed in enumerate(observations):
        if not (
            observed.get("status") == "stopped"
            and observed.get("binding_owner") == "none"
            and observed.get("consumer_count") == 0
            and observed.get("feishu_connection_count") == 0
        ):
            failures.append(f"sample_{index}_explicit_zero_not_proven")
    return {
        "status": "ZERO_CONSUMER_PROVEN" if not failures else "ZERO_CONSUMER_NOT_PROVEN",
        "sample_count": len(samples),
        "window_seconds": window,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify supplied zero-consumer samples offline; never starts a gateway."
    )
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            check(json.loads(args.snapshot.read_text(encoding="utf-8"))),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
