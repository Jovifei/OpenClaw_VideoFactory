"""Evidence-driven P0 prereview and minimum-MVP readiness report.

This script is read-only with respect to runtime services. It writes only the
requested prereview JSON and never creates P0_READY.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Callable


DEFAULT_REPO = Path(__file__).resolve().parents[1]
REQUIRED_SKILLS = {
    "audio-subtitle-engine",
    "codex-template-maintainer",
    "comfyui-gpu-renderer",
    "douyin-video-factory",
    "feishu-video-factory-operator",
    "jianying-draft-exporter",
    "media-asset-curator",
    "pink-pig-mascot-director",
    "reference-video-analyzer",
    "reference-video-recreator",
    "remotion-layout-engine",
    "script-storyboard-director",
    "topic-intelligence",
    "video-quality-gate",
}


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def load_current_report(reports: Path, *names: str) -> tuple[str, dict[str, Any] | None]:
    for name in names:
        payload = load_json(reports / name)
        if payload is not None:
            return name, payload
    return names[0], None


def report_outcome(payload: dict[str, Any] | None) -> str:
    for field in ("verdict", "result", "qualification", "status"):
        value = (payload or {}).get(field)
        if isinstance(value, str) and value:
            return value
    return ""


def is_v25_passed(evidence: dict[str, Any] | None) -> bool:
    if not evidence or evidence.get("passed") is not True:
        return False
    version = evidence.get("schema_version") or evidence.get("version")
    return str(version or "") == "2.5"


def named_check_passed(evidence: dict[str, Any] | None, *names: str) -> bool:
    if not evidence:
        return False
    expected = {name.casefold() for name in names}
    return any(
        isinstance(check, dict)
        and str(check.get("id") or check.get("name") or "").casefold() in expected
        and check.get("passed") is True
        for check in evidence.get("checks", [])
    )


def status_check(
    name: str,
    passed: bool,
    detail: Any,
    *,
    blocking: bool = True,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": "passed" if passed else ("blocked" if blocking else "conditional"),
        "detail": detail,
    }


def checksum_errors(repo: Path) -> list[str]:
    checksum_file = repo / "SHA256SUMS.txt"
    if not checksum_file.exists():
        return ["SHA256SUMS.txt missing"]
    errors: list[str] = []
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            expected, relative = line.split("  ", 1)
        except ValueError:
            errors.append("invalid checksum line")
            continue
        target = repo / relative
        if not target.exists():
            errors.append(f"missing: {relative}")
        elif hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            errors.append(f"mismatch: {relative}")
    return errors


def run_command(repo: Path, command: list[str], timeout: int = 60) -> dict[str, Any]:
    executable = command[0]
    if os.name == "nt" and executable in {"openclaw", "codex", "lark-cli"}:
        shim = shutil.which(f"{executable}.cmd")
        if shim:
            command = [shim, *command[1:]]
    try:
        completed = subprocess.run(
            command,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "returncode": completed.returncode,
            "stdout_head": completed.stdout[:160],
            "stderr_head": completed.stderr[:160],
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"returncode": -1, "stdout_head": "", "stderr_head": type(exc).__name__}


def package_checks(repo: Path) -> list[dict[str, Any]]:
    required = [
        "START_HERE_CODEX.md",
        "PROJECT_STATUS.yaml",
        "AGENTS.md",
        "skills",
        "config",
        "scripts",
        "runbook",
        "handoff",
    ]
    missing = [item for item in required if not (repo / item).exists()]
    skills = {path.parent.name for path in (repo / "skills").glob("*/SKILL.md")}
    factory = repo / "scripts" / "factory.py"
    factory_text = factory.read_text(encoding="utf-8", errors="ignore") if factory.exists() else ""
    sums = checksum_errors(repo)
    return [
        status_check("required paths", not missing, missing or "all present"),
        status_check(
            "local skill set",
            REQUIRED_SKILLS <= skills,
            {"missing": sorted(REQUIRED_SKILLS - skills), "found_count": len(skills)},
        ),
        status_check(
            "factory remains fail-closed before P1",
            "production pipeline is not implemented" in factory_text.lower(),
            "fail-closed marker present"
            if "production pipeline is not implemented" in factory_text.lower()
            else "fail-closed marker missing",
        ),
        status_check(
            "release checksums",
            not sums,
            sums or "ok",
            blocking=False,
        ),
    ]


def runtime_checks(
    repo: Path,
    runner: Callable[[Path, list[str], int], dict[str, Any]] = run_command,
) -> list[dict[str, Any]]:
    commands = {
        "openclaw": ["openclaw", "--version"],
        "config_validate": ["openclaw", "config", "validate"],
        "ffmpeg": ["ffmpeg", "-version"],
        "nvidia": [
            "nvidia-smi",
            "--query-gpu=name,memory.total",
            "--format=csv,noheader",
        ],
        "lark_cli": ["lark-cli", "--version"],
        "codex": ["codex", "--version"],
    }
    checks: list[dict[str, Any]] = []
    for name, command in commands.items():
        result = runner(repo, command, 60)
        passed = result["returncode"] == 0
        if name == "nvidia":
            passed = passed and "4070" in result.get("stdout_head", "")
        checks.append(status_check(f"runtime: {name}", passed, result))
    return checks


def acceptance_evidence_checks(reports: Path) -> list[dict[str, Any]]:
    text = load_json(reports / "FEISHU_SMOKE_TEST.json")
    consumer = load_json(reports / "FEISHU_SINGLE_CONSUMER_TEST.json")
    ingress = load_json(reports / "FEISHU_INGRESS_TEST.json")
    egress = load_json(reports / "FEISHU_EGRESS_TEST.json")
    codex = load_json(reports / "CODEX_CLI_SMOKE.json")
    regression = load_json(reports / "OPENCLAW_EXISTING_AGENTS_REGRESSION.json")
    skill = load_json(reports / "SKILL_VISIBILITY.json")

    def v25_named(evidence: dict[str, Any] | None, *names: str) -> bool:
        return is_v25_passed(evidence) and all(named_check_passed(evidence, name) for name in names)

    return [
        status_check(
            "P0 evidence: Feishu text ingress and visible reply",
            named_check_passed(text, "inbound text and visible bot reply", "text_ingress"),
            {"file": "FEISHU_SMOKE_TEST.json", "passed": bool(text and text.get("passed"))},
        ),
        status_check(
            "P0 evidence: single consumer and deduplication",
            v25_named(consumer, "feishu_single_consumer", "feishu_deduplication"),
            {
                "file": "FEISHU_SINGLE_CONSUMER_TEST.json",
                "schema_version": (consumer or {}).get("schema_version"),
            },
        ),
        status_check(
            "P0 evidence: TXT/PNG/MP4 safe ingress",
            v25_named(
                ingress,
                "txt_ingress",
                "png_ingress",
                "mp4_ingress",
                "safe_media_ingest",
            ),
            {
                "file": "FEISHU_INGRESS_TEST.json",
                "schema_version": (ingress or {}).get("schema_version"),
            },
        ),
        status_check(
            "P0 evidence: Markdown/PNG/TXT/MP4 egress and idempotency",
            v25_named(
                egress,
                "lark_cli_markdown_egress",
                "lark_cli_png_egress",
                "lark_cli_txt_egress",
                "lark_cli_mp4_egress",
                "egress_idempotency",
            ),
            {
                "file": "FEISHU_EGRESS_TEST.json",
                "schema_version": (egress or {}).get("schema_version"),
            },
        ),
        status_check(
            "P0 evidence: direct Codex CLI smoke",
            v25_named(
                codex,
                "direct_codex_cli_read",
                "direct_codex_cli_workspace_write",
                "workspace_isolation",
            ),
            {
                "file": "CODEX_CLI_SMOKE.json",
                "schema_version": (codex or {}).get("schema_version"),
            },
        ),
        status_check(
            "P0 evidence: existing Agent and Binding regression",
            v25_named(regression, "existing_agents_regression", "bindings_regression"),
            {
                "file": "OPENCLAW_EXISTING_AGENTS_REGRESSION.json",
                "schema_version": (regression or {}).get("schema_version"),
            },
        ),
        status_check(
            "P0 evidence: Skill visibility",
            bool(skill and skill.get("passed") is True),
            {"file": "SKILL_VISIBILITY.json"},
        ),
    ]


def _stage_status(payload: dict[str, Any] | None, *path: str) -> str | None:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    if isinstance(value, dict):
        value = value.get("status")
    return str(value).casefold() if value is not None else None


def media_sequence_checks(reports: Path) -> list[dict[str, Any]]:
    trace = load_json(reports / "P0_LIVE_EVENT_TRACE_R0_R5.json")
    r3_source, r3 = load_current_report(
        reports,
        "P0_REAL_R3_RETEST_061.json",
        "P0_REAL_R3_RETEST_056.json",
        "P0_REAL_R3_IMAGE_VERIFICATION_054A.json",
    )
    r4_source, r4 = load_current_report(
        reports,
        "P0_R4_AUDIO_QUALIFICATION_073.json",
        "P0_REAL_R4_AUDIO_QUALIFICATION_057.json",
    )
    r5_source, r5 = load_current_report(
        reports,
        "P0_R5_VIDEO_QUALIFICATION_072.json",
        "P0_REAL_R5_VIDEO_QUALIFICATION_058.json",
    )

    r3_verdict = report_outcome(r3)
    r4_verdict = report_outcome(r4)
    r5_verdict = report_outcome(r5)
    return [
        status_check(
            "real media R0 text",
            _stage_status(trace, "r0") == "passed",
            {"source": "P0_LIVE_EVENT_TRACE_R0_R5.json"},
        ),
        status_check(
            "real media R1 TXT ingress",
            _stage_status(trace, "r1_replacement") == "passed",
            {"source": "P0_LIVE_EVENT_TRACE_R0_R5.json"},
        ),
        status_check(
            "real media R2 PNG ingress-only",
            _stage_status(trace, "r2_replacement") == "passed",
            {"source": "P0_LIVE_EVENT_TRACE_R0_R5.json"},
        ),
        status_check(
            "real media R3 image result",
            r3_verdict == "R3_IMAGE_ANALYSIS_OK",
            {
                "source": r3_source,
                "verdict": r3_verdict or "missing",
            },
        ),
        status_check(
            "real media R4 audio result",
            r4_verdict == "R4_AUDIO_ANALYSIS_OK",
            {
                "source": r4_source,
                "verdict": r4_verdict or "missing",
            },
        ),
        status_check(
            "real media R5 video result",
            r5_verdict
            in {
                "R5_VIDEO_ANALYSIS_OK",
                "P0_REAL_MEDIA_SEQUENCE_COMPLETE",
                "PASS_REAL_VISIBLE_COMPLETION",
            },
            {
                "source": r5_source,
                "verdict": r5_verdict or "missing",
            },
        ),
    ]


def choose_next_action(
    media_checks: list[dict[str, Any]],
    acceptance_checks: list[dict[str, Any]],
    p0_ready: bool,
) -> str:
    media_actions = {
        "real media R3 image result": "RUN_FRESH_REAL_R3_RETEST",
        "real media R4 audio result": "RUN_REAL_R4_AUDIO_AFTER_R3_PASS",
        "real media R5 video result": "RUN_REAL_R5_VIDEO_AFTER_R4_PASS",
    }
    for check in media_checks:
        action = media_actions.get(check["name"])
        if action and check["status"] != "passed":
            return action
    for check in acceptance_checks:
        if check["status"] != "passed":
            return f"REMEDIATE_{check['name'].upper().replace(' ', '_').replace('/', '_')}"
    if not p0_ready:
        return "RUN_ACTUAL_P0_ACCEPTANCE_GATE"
    return "START_P1_A_SQLITE_STATE_STORE"


def build_report(repo: Path, *, include_runtime: bool = True) -> dict[str, Any]:
    reports = repo / "reports"
    package = package_checks(repo)
    runtime = runtime_checks(repo) if include_runtime else []
    acceptance = acceptance_evidence_checks(reports)
    media = media_sequence_checks(reports)
    p0_ready_payload = load_json(reports / "gates" / "P0_READY.json")
    p0_ready = bool(p0_ready_payload and p0_ready_payload.get("passed") is True)
    all_checks = [*package, *runtime, *acceptance, *media]
    counts = {
        status: sum(check["status"] == status for check in all_checks)
        for status in ("passed", "conditional", "blocked")
    }
    return {
        "schema_version": "1.0",
        "task": "P0-MINIMUM-COMPLETION-PLAN-056",
        "ran_actual_gate": False,
        "created_p0_ready": False,
        "checks": {
            "package": package,
            "runtime": runtime,
            "p0_acceptance_evidence": acceptance,
            "real_media_sequence": media,
        },
        "status_counts": counts,
        "p0_ready": p0_ready,
        "can_start_p1": p0_ready,
        "minimum_completion_target": "P2_AUTOMATED_DAILY_FACTORY",
        "next_milestone": "P1_DETERMINISTIC_VERTICAL_SLICE",
        "next_action": choose_next_action(media, acceptance, p0_ready),
        "overall": "READY_FOR_P1" if p0_ready else "BLOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--skip-runtime", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    output = args.output or repo / "reports" / "P0_GATE_PREREVIEW.json"
    report = build_report(repo, include_runtime=not args.skip_runtime)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "overall": report["overall"],
                "status_counts": report["status_counts"],
                "can_start_p1": report["can_start_p1"],
                "next_action": report["next_action"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["overall"] == "READY_FOR_P1" else 2


if __name__ == "__main__":
    raise SystemExit(main())
