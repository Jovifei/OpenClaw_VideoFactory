"""Control responses for the retired offline Candidate pipeline.

The original ``src.factory`` Candidate implementation rendered media locally
and ran provider, subtitle, quality, and benchmark work.  That path is now a
historical compatibility surface only.  This module is deliberately small:
it provides a stable, JSON-safe response for callers while making it explicit
that no Candidate pipeline work (or state mutation) was performed.
"""

from __future__ import annotations

import re
import json
import shutil
from typing import Any
from pathlib import Path

from video_factory.pipeline.errors import FactoryContractError

from .config import PROJECT_ROOT, jobs_root
from .db import CandidateStore

RETIREMENT_STATUS = "legacy_candidate_pipeline_retired"
RETIREMENT_REASON = "historical_candidate_pipeline_retired"
# Descriptive alias kept for callers that prefer the full contract name.
LEGACY_CANDIDATE_PIPELINE_RETIRED = RETIREMENT_STATUS

RETIRED_OPERATIONS = frozenset({"create", "retry", "run", "verify", "benchmark"})
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def retired_result(operation: str, **context: Any) -> dict[str, Any]:
    """Return the canonical response for a retired Candidate operation.

    Context is intentionally restricted to scalar, non-sensitive command
    metadata.  Callers may include a job or fixture identifier for operator
    clarity, but the response never echoes media paths, source text, or
    provider configuration.
    """

    if operation not in RETIRED_OPERATIONS:
        raise ValueError(f"legacy_candidate_operation_invalid:{operation}")
    result: dict[str, Any] = {
        "status": RETIREMENT_STATUS,
        "operation": operation,
        "reason": RETIREMENT_REASON,
        "mutated": False,
    }
    for key in ("job_id", "fixture"):
        value = context.get(key)
        if isinstance(value, str) and _SAFE_IDENTIFIER.fullmatch(value):
            result[key] = value
    return result


def legacy_candidate_pipeline_retired(operation: str, **context: Any) -> dict[str, Any]:
    """Named compatibility entry point for the retirement contract."""
    return retired_result(operation, **context)


def retired_command_error(command: str) -> FactoryContractError:
    """Build the stable fail-closed error for a retired CLI command."""
    if command not in RETIRED_OPERATIONS:
        raise ValueError(f"legacy_candidate_operation_invalid:{command}")
    return FactoryContractError(
        RETIREMENT_STATUS,
        "The historical Candidate pipeline is retired; use generate_video.py.",
        {"command": command, "replacement": "generate_video.py"},
    )


def retire_create(*, fixture: str | None = None) -> dict[str, Any]:
    del fixture
    raise retired_command_error("create")


def retire_retry(*, job_id: str | None = None) -> dict[str, Any]:
    del job_id
    raise retired_command_error("retry")


def retire_run(*, job_id: str | None = None) -> dict[str, Any]:
    del job_id
    raise retired_command_error("run")


def retire_verify(*, job_id: str | None = None) -> dict[str, Any]:
    del job_id
    raise retired_command_error("verify")


def retire_benchmark(*, fixture: str | None = None) -> dict[str, Any]:
    del fixture
    raise retired_command_error("benchmark")


def cancel_job(store: CandidateStore, job_id: str) -> dict[str, Any]:
    """Preserve Candidate cancellation without importing the retired pipeline."""
    current = store.status(job_id)
    package = jobs_root() / job_id
    cancelled = store.cancel(job_id, "operator_requested")
    if current["state"] == "RENDERING":
        for name in ("render_raw.mp4", "final_master.mp4", "feishu_preview.mp4", "cover.png", "render_manifest.json"):
            (package / name).unlink(missing_ok=True)
    (package / "render_raw.mp4").unlink(missing_ok=True)
    runtime = PROJECT_ROOT / "remotion" / "public" / "runtime" / job_id
    if runtime.exists():
        shutil.rmtree(runtime)
    metrics_path = package / "run_metrics.json"
    if metrics_path.is_file():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        metrics["cancellation_count"] = int(metrics.get("cancellation_count", 0)) + 1
        metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return cancelled
