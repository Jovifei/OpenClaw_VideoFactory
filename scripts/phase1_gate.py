"""Formal read-only gate for the local Phase 1 video factory."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if os.fspath(ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(ROOT))

from src.factory.phase1_gate import evaluate_phase1_gate  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="phase1_gate.py")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "reports" / "gates"
    )
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
    output_dir = args.output_dir.resolve()
    root = ROOT.resolve()
    if output_dir == root or root not in output_dir.parents:
        raise SystemExit("output_dir_outside_repository")
    report = evaluate_phase1_gate(args.manifest, project_root=ROOT)
    filename = "PHASE1_READY.json" if report["status"] == "ready" else "PHASE1_FAILED.json"
    _atomic_write(output_dir / filename, report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
