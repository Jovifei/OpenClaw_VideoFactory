"""Local-only Phase 1 job control around the canonical video pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.export import write_json

from .config import PROJECT_ROOT
from .db import CandidateStore
from .phase1_local import load_local_brief
from .state import next_state


STATE_ROOT = PROJECT_ROOT / "state" / "phase1_local"
DATABASE_PATH = STATE_ROOT / "phase1_jobs.sqlite3"
INPUT_ROOT = STATE_ROOT / "inputs"


def _emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return code


def _parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="factory.py phase1")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    commands.add_parser("init-db")
    create = commands.add_parser("create-topic")
    create.add_argument("--brief", type=Path, required=True)
    create.add_argument("--idempotency-key")
    run = commands.add_parser("run")
    run.add_argument("--job-id", required=True)
    status = commands.add_parser("status")
    status.add_argument("--job-id", required=True)
    cancel = commands.add_parser("cancel")
    cancel.add_argument("--job-id", required=True)
    retry = commands.add_parser("retry")
    retry.add_argument("--job-id", required=True)
    return root


def _store() -> CandidateStore:
    store = CandidateStore(DATABASE_PATH)
    store.initialize()
    return store


def _persist_brief(brief: dict[str, Any]) -> Path:
    digest = str(brief["factual_brief"]["topic_digest"])
    target = INPUT_ROOT / f"{digest}.json"
    if target.exists() and target.is_symlink():
        raise FactoryContractError(
            "phase1_input_path_invalid",
            "Phase 1 input storage cannot be a link.",
            {"reason": "reparse"},
        )
    write_json(target, brief)
    return target


def _create_topic(args: argparse.Namespace) -> dict[str, Any]:
    brief = load_local_brief(args.brief)
    persisted = _persist_brief(brief)
    digest = str(brief["factual_brief"]["topic_digest"])
    key = args.idempotency_key or f"phase1-topic:{digest}"
    store = _store()
    result = store.create_job(
        "local_topic",
        key,
        "video_factory_local_brief",
        str(brief["topic"]),
        requested_duration_seconds=int(brief.get("duration_target_seconds", 40)),
        metadata={
            "brief_path": persisted.relative_to(PROJECT_ROOT).as_posix(),
            "topic_digest": digest,
            "input_mode": str(brief["input_mode"]),
        },
    )
    return {"status": "created" if result["created"] else "existing", "job": result}


def _advance_to_rendering(store: CandidateStore, job_id: str) -> dict[str, Any]:
    job = store.status(job_id)
    while job["state"] != "RENDERING":
        target = next_state(str(job["state"]))
        if target is None:
            raise FactoryContractError(
                "phase1_job_state_invalid",
                "Phase 1 job cannot enter rendering from its current state.",
                {"state": str(job["state"])},
            )
        job = store.advance(job_id, target, reason="local_stage_completed")
    return job


def _run_job(args: argparse.Namespace) -> dict[str, Any]:
    from generate_video import run_local_brief

    store = _store()
    job = store.status(args.job_id)
    if job["state"] == "PENDING_REVIEW":
        return {
            "status": "pending_review",
            "job": job,
            "artifacts": store.artifacts(args.job_id),
            "idempotent": True,
        }
    if job["state"] in {"FAILED", "CANCELLED"}:
        raise FactoryContractError(
            "phase1_job_retry_required",
            "A failed or cancelled Phase 1 job must be retried explicitly.",
            {"state": str(job["state"])},
        )
    brief_ref = str(job["metadata"].get("brief_path", ""))
    brief_path = (PROJECT_ROOT / brief_ref).resolve()
    if PROJECT_ROOT.resolve() not in brief_path.parents or not brief_path.is_file():
        raise FactoryContractError(
            "phase1_input_path_invalid",
            "The persisted Phase 1 brief is unavailable.",
            {"reason": "missing"},
        )
    _advance_to_rendering(store, args.job_id)
    try:
        result = run_local_brief(brief_path, emit=False)
        store.advance(args.job_id, "QUALITY_CHECK", reason="local_render_completed")
        final_job = store.advance(args.job_id, "PENDING_REVIEW", reason="local_quality_passed")
        for artifact_type, value in {
            "final_master": result["output"],
            "review_package": result["review_package"],
        }.items():
            path = Path(str(value)).resolve()
            store.record_artifact(
                args.job_id,
                artifact_type,
                path.relative_to(PROJECT_ROOT).as_posix(),
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        return {
            "status": "pending_review",
            "job": final_job,
            "artifacts": store.artifacts(args.job_id),
            "result": result,
        }
    except Exception:
        current = store.status(args.job_id)
        if current["state"] not in {"FAILED", "CANCELLED", "PENDING_REVIEW"}:
            store.fail(args.job_id, "phase1_local_execution_failed")
        raise


def main(arguments: list[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    try:
        if args.command == "doctor":
            return _emit(
                {
                    "status": "ok",
                    "mode": "phase1_local_only",
                    "canonical_video_entrypoint": "generate_video.py --local-brief",
                    "database": DATABASE_PATH.relative_to(PROJECT_ROOT).as_posix(),
                    "provider_enabled": False,
                    "feishu_enabled": False,
                    "cron_enabled": False,
                }
            )
        if args.command == "init-db":
            _store()
            return _emit({"status": "initialized", "database": DATABASE_PATH.relative_to(PROJECT_ROOT).as_posix()})
        if args.command == "create-topic":
            return _emit(_create_topic(args))
        if args.command == "run":
            return _emit(_run_job(args))
        if args.command == "status":
            store = _store()
            return _emit(
                {
                    "status": "ok",
                    "job": store.status(args.job_id),
                    "events": store.events(args.job_id),
                    "artifacts": store.artifacts(args.job_id),
                }
            )
        if args.command == "cancel":
            return _emit({"status": "cancelled", "job": _store().cancel(args.job_id, "user_requested")})
        if args.command == "retry":
            return _emit({"status": "retry_ready", "job": _store().retry(args.job_id, "user_requested")})
    except FactoryContractError as exc:
        return _emit({"status": "error", "error": exc.to_dict()}, 2)
    except KeyError:
        return _emit(
            {
                "status": "error",
                "error": {
                    "code": "phase1_job_not_found",
                    "message": "The Phase 1 job was not found.",
                    "context": {},
                },
            },
            2,
        )
    except (OSError, ValueError, RuntimeError):
        return _emit(
            {
                "status": "error",
                "error": {
                    "code": "phase1_local_execution_failed",
                    "message": "The local Phase 1 operation failed.",
                    "context": {},
                },
            },
            2,
        )
    raise AssertionError(f"unsupported_command:{args.command}")


__all__ = ["main"]
