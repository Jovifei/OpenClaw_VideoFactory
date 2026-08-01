"""JSON-only command-line surface for the offline candidate."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT, database_path, jobs_root, state_root
from .db import CandidateStore
from .fixtures import load_fixture


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
    chrome = next(
        (
            path
            for path in (
                Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
                Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
            )
            if path.exists()
        ),
        None,
    )
    return {
        "mode": "offline_candidate",
        "state_root": str(state_root()),
        "jobs_root": str(jobs_root()),
        "project_root": str(PROJECT_ROOT),
        "ffmpeg_available": shutil.which("ffmpeg") is not None,
        "ffprobe_available": shutil.which("ffprobe") is not None,
        "node_available": shutil.which("node") is not None,
        "chrome_available": chrome is not None,
        "openclaw_contacted": False,
        "feishu_contacted": False,
    }


def main(arguments: list[str] | None = None) -> int:
    args = parser().parse_args(arguments)
    store = CandidateStore(database_path())
    try:
        if args.command == "doctor":
            return emit(doctor_payload())
        store.initialize()
        if args.command == "init-db":
            return emit({"status": "initialized", "database": str(database_path())})
        if args.command == "create":
            fixture = load_fixture(args.fixture)
            return emit(
                store.create_job(
                    fixture["id"],
                    args.idempotency_key,
                    fixture["template"],
                    fixture["topic"],
                    requested_duration_seconds=args.duration_seconds,
                )
            )
        if args.command == "status":
            return emit(store.status(args.job_id))
        if args.command == "cancel":
            from .pipeline import cancel_job

            return emit(cancel_job(store, args.job_id))
        if args.command == "retry":
            return emit(store.retry(args.job_id, "operator_requested"))
        if args.command == "run":
            from .pipeline import run_job

            return emit(run_job(store, args.job_id, args.encoder, args.tts))
        if args.command == "verify":
            from .quality import verify_job

            return emit(verify_job(store, args.job_id))
        if args.command == "benchmark":
            from .benchmark import run_benchmark

            return emit(run_benchmark(store, args.fixture))
        if args.command == "inventory":
            from .inventory import build_inventory

            return emit(build_inventory(store))
        if args.command == "retention-plan":
            from .inventory import build_retention_plan

            return emit(build_retention_plan(store, PROJECT_ROOT / "reports"))
    except (KeyError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return emit({"status": "error", "error": str(exc)}, 2)
    raise AssertionError(f"unsupported_command:{args.command}")
