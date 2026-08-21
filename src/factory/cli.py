"""JSON-only command-line surface for the offline candidate."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from video_factory.pipeline.errors import FactoryContractError

from .config import PROJECT_ROOT, database_path, jobs_root, state_root
from .db import CandidateStore
from .legacy_candidate_control import (
    cancel_job,
    retire_benchmark,
    retire_create,
    retire_retry,
    retire_run,
    retire_verify,
)


def emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return code


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="factory.py candidate")
    commands = root.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor")
    doctor.add_argument("--json", action="store_true")
    commands.add_parser("init-db")
    create = commands.add_parser("create")
    create.add_argument("--fixture", required=True)
    create.add_argument("--idempotency-key", required=True)
    create.add_argument("--duration-seconds", type=int, default=40)
    run = commands.add_parser("run")
    run.add_argument("--job-id", required=True)
    run.add_argument("--encoder", choices=("auto", "nvenc", "cpu"), default="auto")
    run.add_argument("--tts", choices=("auto", "edge", "sapi"), default="auto")
    status = commands.add_parser("status")
    status.add_argument("--job-id", required=True)
    status.add_argument("--json", action="store_true")
    cancel = commands.add_parser("cancel")
    cancel.add_argument("--job-id", required=True)
    retry = commands.add_parser("retry")
    retry.add_argument("--job-id", required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--job-id", required=True)
    benchmark = commands.add_parser("benchmark")
    benchmark.add_argument("--fixture", required=True)
    benchmark.add_argument("--json", action="store_true")
    inventory = commands.add_parser("inventory")
    inventory.add_argument("--json", action="store_true")
    retention = commands.add_parser("retention-plan")
    retention.add_argument("--json", action="store_true")
    return root


def doctor_payload() -> dict[str, Any]:
    return {
        "mode": "legacy_control_only",
        "state_root": str(state_root()),
        "jobs_root": str(jobs_root()),
        "project_root": str(PROJECT_ROOT),
        "render_pipeline": "retired",
        "canonical_video_entrypoint": "generate_video.py",
        "retired_commands": sorted(("create", "retry", "run", "verify", "benchmark")),
        "openclaw_contacted": False,
        "feishu_contacted": False,
    }


def main(arguments: list[str] | None = None) -> int:
    args = parser().parse_args(arguments)
    try:
        if args.command == "doctor":
            return emit(doctor_payload())
        if args.command == "init-db":
            store = CandidateStore(database_path())
            store.initialize()
            return emit({"status": "initialized", "database": str(database_path())})
        if args.command == "create":
            return emit(retire_create(fixture=args.fixture))
        if args.command == "status":
            store = CandidateStore(database_path())
            store.initialize()
            return emit(store.status(args.job_id))
        if args.command == "cancel":
            store = CandidateStore(database_path())
            store.initialize()
            return emit(cancel_job(store, args.job_id))
        if args.command == "retry":
            return emit(retire_retry(job_id=args.job_id))
        if args.command == "run":
            return emit(retire_run(job_id=args.job_id))
        if args.command == "verify":
            return emit(retire_verify(job_id=args.job_id))
        if args.command == "benchmark":
            return emit(retire_benchmark(fixture=args.fixture))
        if args.command == "inventory":
            store = CandidateStore(database_path())
            store.initialize()
            from .inventory import build_inventory
            return emit(build_inventory(store))
        if args.command == "retention-plan":
            store = CandidateStore(database_path())
            store.initialize()
            from .inventory import build_retention_plan
            return emit(build_retention_plan(store, PROJECT_ROOT / "reports"))
    except FactoryContractError as exc:
        return emit({"status": "error", "error": exc.to_dict()}, 2)
    except (KeyError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return emit({"status": "error", "error": str(exc)}, 2)
    raise AssertionError(f"unsupported_command:{args.command}")
