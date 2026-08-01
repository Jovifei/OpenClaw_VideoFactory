"""Serial, offline Remotion concurrency benchmark for public fixtures."""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from time import monotonic
from typing import Any

from .config import state_root
from .db import CandidateStore
from .fixtures import load_fixture
from .metrics import host_memory_bytes
from .pipeline import run_job


CONCURRENCIES = (1, 2, 4)
RUNS_PER_CONCURRENCY = 3


def _gpu_total_mib() -> int | None:
    import shutil
    import subprocess

    if shutil.which("nvidia-smi") is None:
        return None
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    try:
        return max(int(item.strip()) for item in result.stdout.splitlines() if item.strip())
    except ValueError:
        return None


def _read_metrics(package: Path) -> dict[str, Any]:
    return json.loads((package / "run_metrics.json").read_text(encoding="utf-8"))


def run_benchmark(store: CandidateStore, fixture_id: str) -> dict[str, Any]:
    fixture = load_fixture(fixture_id)
    host_memory = host_memory_bytes()
    gpu_total = _gpu_total_mib()
    rows: list[dict[str, Any]] = []
    for concurrency in CONCURRENCIES:
        for run_number in range(1, RUNS_PER_CONCURRENCY + 1):
            job = store.create_job(
                fixture_id,
                f"p1-polish-058-benchmark:{fixture_id}:{concurrency}:{run_number}",
                fixture["template"],
                fixture["topic"],
                requested_duration_seconds=40,
            )
            started = monotonic()
            outcome = run_job(
                store,
                job["job_id"],
                encoder="auto",
                tts_provider="auto",
                render_concurrency=concurrency,
            )
            elapsed = round(monotonic() - started, 3)
            package = Path(outcome["package"])
            metrics = _read_metrics(package)
            resource = metrics.get("resource_observation", {})
            peak_memory = resource.get("peak_working_set_bytes")
            peak_gpu = resource.get("peak_gpu_memory_mib")
            safe_memory = host_memory is not None and isinstance(peak_memory, (int, float)) and peak_memory < host_memory * 0.70
            safe_gpu = gpu_total is not None and isinstance(peak_gpu, (int, float)) and peak_gpu < gpu_total * 0.85
            rows.append({"concurrency": concurrency, "run": run_number, "job_id": job["job_id"], "status": outcome["status"], "elapsed_seconds": elapsed, "peak_working_set_bytes": peak_memory, "peak_gpu_memory_mib": peak_gpu, "safe_memory": safe_memory, "safe_gpu": safe_gpu})
    candidates: list[tuple[float, int]] = []
    for concurrency in CONCURRENCIES:
        group = [item for item in rows if item["concurrency"] == concurrency]
        if len(group) == RUNS_PER_CONCURRENCY and all(item["status"] in {"completed", "already_completed"} and item["safe_memory"] and item["safe_gpu"] for item in group):
            candidates.append((statistics.median(item["elapsed_seconds"] for item in group), concurrency))
    selected = min(candidates)[1] if candidates else 1
    status = "benchmark_complete" if candidates else "benchmark_evidence_insufficient_default_concurrency_1"
    report = {"schema_version": "1.0", "mode": "offline_candidate", "fixture": fixture_id, "runs_per_concurrency": RUNS_PER_CONCURRENCY, "host_memory_bytes": host_memory, "gpu_memory_total_mib": gpu_total, "rows": rows, "selected_concurrency": selected, "status": status}
    target = state_root() / "benchmarks" / f"{fixture_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return report
