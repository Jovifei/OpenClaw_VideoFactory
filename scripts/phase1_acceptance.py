"""CLI for read-only Phase 1 per-job prereview."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if os.fspath(ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(ROOT))

from src.factory.db import CandidateStore  # noqa: E402
from src.factory.phase1_acceptance import evaluate_job_prereview  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="phase1_acceptance.py")
    parser.add_argument(
        "--database",
        type=Path,
        default=ROOT / "state" / "phase1_local" / "phase1_jobs.sqlite3",
    )
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser


def _atomic_write(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp.replace(path)


def main(arguments: list[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    store = CandidateStore(args.database)
    store.initialize()
    report = evaluate_job_prereview(store, args.job_id, args.review, project_root=ROOT)
    if args.output is not None:
        output = args.output.resolve()
        root = ROOT.resolve()
        if output == root or root not in output.parents:
            raise SystemExit("output_path_outside_repository")
        _atomic_write(output, report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
