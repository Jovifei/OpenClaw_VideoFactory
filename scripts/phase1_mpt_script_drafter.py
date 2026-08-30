"""Phase 1 script-drafter adapter for the vendored MoneyPrinterTurbo tool.

Turns one Jovi-provided subject keyword into N candidate narration drafts by
calling the external MoneyPrinterTurbo CLI in isolated sub-processes with
``--stop-at script``. Drafts are text-only review inputs for the existing
original-brief flow; this adapter never invokes the render chain, never edits
media, and never handles API keys (they live only in the gitignored
external/MoneyPrinterTurbo/config.toml).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
DEFAULT_MPT_ROOT = Path(__file__).resolve().parent.parent / "external" / "MoneyPrinterTurbo"
DEFAULT_OUT_ROOT = Path(__file__).resolve().parent.parent / "dist" / "phase1_local" / "script_drafts"
MPT_COMMIT = "eb8c23757e098a07bbcd93b3b50e252fc8d1869a"
MPT_VERSION = "1.3.5"
ENDPOINT_HOST = "token-plan-cn.xiaomimimo.com"


def _mpt_python(mpt_root: Path) -> Path:
    candidate = mpt_root / ".venv" / "Scripts" / "python.exe"
    if not candidate.is_file():
        candidate = mpt_root / ".venv" / "bin" / "python"
    if not candidate.is_file():
        raise FileNotFoundError(f"MoneyPrinterTurbo venv python not found under {mpt_root}")
    return candidate


def _parse_result_line(raw: str) -> str | None:
    """Return the script from the final CLI JSON line, or None."""
    for line in reversed(raw.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        script = payload.get("result", {}).get("script")
        if isinstance(script, str) and script.strip():
            return script.strip()
    return None


def _draft_one_candidate(
    mpt_root: Path,
    *,
    subject: str,
    language: str,
    paragraphs: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    command = [
        str(_mpt_python(mpt_root)),
        "cli.py",
        "--video-subject", subject,
        "--video-language", language,
        "--paragraph-number", str(paragraphs),
        "--stop-at", "script",
    ]
    started = time.time()
    try:
        completed = subprocess.run(
            command,
            cwd=str(mpt_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "error": f"MoneyPrinterTurbo exceeded {timeout_seconds:.0f}s and was terminated",
            "duration_seconds": round(time.time() - started, 2),
        }

    duration = round(time.time() - started, 2)
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout or "").strip().splitlines()[-3:]
        return {
            "status": "failed",
            "error": f"exit code {completed.returncode}: " + " | ".join(tail),
            "duration_seconds": duration,
        }

    script = _parse_result_line(completed.stdout or "")
    if script is None:
        return {
            "status": "failed",
            "error": "no parsable script JSON in MoneyPrinterTurbo output",
            "duration_seconds": duration,
        }
    return {"status": "ok", "script": script, "duration_seconds": duration}


def run_drafts(
    *,
    subject: str,
    language: str,
    paragraphs: int,
    candidates: int,
    timeout_seconds: float,
    mpt_root: Path = DEFAULT_MPT_ROOT,
    out_root: Path = DEFAULT_OUT_ROOT,
    rewrite_guidance: str | None = None,
    research_guidance: str | None = None,
) -> Path:
    if not subject.strip():
        raise ValueError("subject must not be empty")
    if candidates < 1 or candidates > 10:
        raise ValueError("candidates must be between 1 and 10")

    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_dir = out_root / f"drafter_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=False)

    prompt_subject = subject
    if research_guidance:
        prompt_subject = f"{prompt_subject}\n\n已核验研究约束：{research_guidance.strip()}"
    if rewrite_guidance:
        prompt_subject = f"{prompt_subject}\n\n确定性改写要求：{rewrite_guidance.strip()}"
    results: list[dict[str, Any]] = []
    for index in range(1, candidates + 1):
        outcome = _draft_one_candidate(
            mpt_root,
            subject=prompt_subject,
            language=language,
            paragraphs=paragraphs,
            timeout_seconds=timeout_seconds,
        )
        outcome["candidate"] = index
        results.append(outcome)
        print(f"[drafter] candidate {index}/{candidates}: {outcome['status']} ({outcome['duration_seconds']}s)", flush=True)

    ok_results = [r for r in results if r["status"] == "ok"]
    document = {
        "schema_version": SCHEMA_VERSION,
        "kind": "phase1_script_drafts",
        "review_status": "PENDING_HUMAN_REVIEW",
        "subject": subject,
        "language": language,
        "paragraphs": paragraphs,
        "requested_candidates": candidates,
        "successful_candidates": len(ok_results),
        "mpt_version": MPT_VERSION,
        "mpt_commit": MPT_COMMIT,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "candidates": [
            {"candidate": r["candidate"], "script": r["script"], "duration_seconds": r["duration_seconds"]}
            for r in ok_results
        ],
        "failures": [
            {"candidate": r["candidate"], "status": r["status"], "error": r.get("error", "")}
            for r in results if r["status"] != "ok"
        ],
    }
    out_path = out_dir / "candidates.json"
    out_path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[drafter] wrote {out_path} ({len(ok_results)}/{candidates} candidates)", flush=True)

    if not ok_results:
        raise RuntimeError("all candidates failed; no drafts produced")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate candidate narration drafts via MoneyPrinterTurbo (script stage only).")
    parser.add_argument("--subject", required=True, help="topic keyword for the narration draft")
    parser.add_argument("--language", default="zh-CN")
    parser.add_argument("--paragraphs", type=int, default=2)
    parser.add_argument("--candidates", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--mpt-root", type=Path, default=DEFAULT_MPT_ROOT)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    args = parser.parse_args(argv)

    try:
        out_path = run_drafts(
            subject=args.subject,
            language=args.language,
            paragraphs=args.paragraphs,
            candidates=args.candidates,
            timeout_seconds=args.timeout_seconds,
            mpt_root=args.mpt_root,
            out_root=args.out_root,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"[drafter] FAILED: {exc}", file=sys.stderr, flush=True)
        return 1
    print(f"[drafter] OK {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
