"""Redacted runtime metrics for offline candidate jobs only."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any


SAFE_FALLBACK_REASONS = {
    "none",
    "nvenc_unavailable",
    "nvenc_failed",
    "encoder_not_requested",
}


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _safe_number(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return None


def directory_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


class RunMetrics:
    """Persist only whitelisted timing and resource measurements.

    The class intentionally accepts stage labels and scalar detail only. It never
    serializes fixture narration, filesystem paths, environment values, subprocess
    output, or provider error text.
    """

    def __init__(self, job_id: str, output: Path, attempt: int) -> None:
        self.output = output
        self.payload: dict[str, Any] = {
            "schema_version": "1.0",
            "mode": "offline_candidate",
            "job_id": job_id,
            "attempt": attempt,
            "started_at": _timestamp(),
            "stages": [],
            "render": {},
            "resource_observation": {
                "peak_cpu_percent": None,
                "peak_working_set_bytes": None,
                "peak_gpu_memory_mib": None,
                "staging_peak_bytes": 0,
            },
            "cancellation_count": 0,
            "recovery_count": 0,
        }
        self._stage_starts: dict[str, tuple[float, str]] = {}
        self.save()

    def stage_started(self, stage: str, stage_attempt: int) -> None:
        self._stage_starts[stage] = (monotonic(), _timestamp())
        self.payload["stages"].append(
            {"stage": stage, "attempt": stage_attempt, "started_at": self._stage_starts[stage][1]}
        )
        self.save()

    def stage_completed(self, stage: str, *, status: str, detail: dict[str, Any]) -> None:
        started = self._stage_starts.pop(stage, None)
        record = next(item for item in reversed(self.payload["stages"]) if item["stage"] == stage)
        record["completed_at"] = _timestamp()
        record["duration_seconds"] = round(monotonic() - started[0], 3) if started else None
        record["status"] = status
        record["detail"] = {
            key: value
            for key, value in detail.items()
            if isinstance(value, bool) or _safe_number(value) is not None or key in {"provider", "quality", "delivery", "master_encoder", "preview_encoder"}
        }
        self.save()

    def render_observed(self, detail: dict[str, Any]) -> None:
        allowed = {
            "resolved_concurrency",
            "rendered_frames",
            "encoded_frames",
            "rendered_done_in_seconds",
            "encoded_done_in_seconds",
            "peak_cpu_percent",
            "peak_working_set_bytes",
            "peak_gpu_memory_mib",
            "staging_peak_bytes",
        }
        sanitized = {
            key: value
            for key, value in detail.items()
            if key in allowed and _safe_number(value) is not None
        }
        self.payload["render"] = sanitized
        for key in ("peak_cpu_percent", "peak_working_set_bytes", "peak_gpu_memory_mib", "staging_peak_bytes"):
            value = sanitized.get(key)
            if value is not None:
                prior = self.payload["resource_observation"].get(key)
                self.payload["resource_observation"][key] = max(prior or 0, value)
        self.save()

    def record_recovery(self) -> None:
        self.payload["recovery_count"] += 1
        self.save()

    def record_cancellation(self) -> None:
        self.payload["cancellation_count"] += 1
        self.save()

    def save(self) -> None:
        self.payload["updated_at"] = _timestamp()
        self.output.write_text(json.dumps(self.payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def host_memory_bytes() -> int | None:
    """Read a scalar host-memory total through the local Windows API shell."""
    if shutil.which("powershell") is None:
        return None
    import subprocess

    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"],
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    try:
        return int(result.stdout.strip()) if result.returncode == 0 else None
    except ValueError:
        return None
