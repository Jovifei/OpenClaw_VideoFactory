from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
GATES = REPORTS / "gates"

REQUIRED_SKILLS = {
    "douyin-video-factory",
    "topic-intelligence",
    "script-storyboard-director",
    "reference-video-analyzer",
    "reference-video-recreator",
    "media-asset-curator",
    "pink-pig-mascot-director",
    "feishu-video-factory-operator",
    "comfyui-gpu-renderer",
    "audio-subtitle-engine",
    "remotion-layout-engine",
    "video-quality-gate",
    "jianying-draft-exporter",
    "codex-template-maintainer",
}

SECRET_PATTERNS = {
    "openai_key": re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    "telegram_token": re.compile(r"\b\d{9,}:[A-Za-z0-9_-]{20,}\b"),
    "generic_secret_assignment": re.compile(
        r"(?i)(app[_-]?secret|access[_-]?token|refresh[_-]?token|api[_-]?key|password)"
        r"\s*[:=]\s*['\"]?[A-Za-z0-9_./+\-=]{12,}"
    ),
}

BINARY_SUFFIXES = {
    ".docx",
    ".zip",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".mp4",
    ".wav",
    ".ogg",
    ".opus",
    ".pdf",
    ".sqlite",
    ".db",
}


def run(command: list[str], timeout: int = 60) -> dict[str, Any]:
    executable = command[0]
    if os.name == "nt" and executable in {"openclaw", "codex", "lark-cli"}:
        cmd_shim = shutil.which(f"{executable}.cmd")
        if cmd_shim:
            command = [cmd_shim, *command[1:]]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-12000:],
            "stderr": completed.stderr[-12000:],
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {
            "command": command,
            "returncode": -1,
            "stdout": "",
            "stderr": str(exc),
        }


def add(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() not in BINARY_SUFFIXES


def is_archived(path: Path) -> bool:
    return "archive_v23" in path.parts or "legacy" in path.parts


def is_generated(path: Path) -> bool:
    """Exclude interpreter and VCS by-products, not project reports or source."""
    return any(part in {".git", ".venv", "__pycache__"} for part in path.parts)


def load_structured(path: Path) -> Any:
    if path.suffix in {".json", ".json5"}:
        # V2.4 .json5 files intentionally use strict JSON syntax so this check
        # does not require an extra json5 package on the user's machine.
        return json.loads(path.read_text(encoding="utf-8-sig"))
    if path.suffix in {".yaml", ".yml"}:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    raise ValueError(path)


def checksum_checks() -> list[str]:
    checksum_file = ROOT / "SHA256SUMS.txt"
    if not checksum_file.exists():
        return ["SHA256SUMS.txt missing"]

    errors: list[str] = []
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            expected, relative = line.split("  ", 1)
        except ValueError:
            errors.append(f"invalid checksum line: {line}")
            continue
        target = ROOT / relative
        if not target.exists():
            errors.append(f"missing: {relative}")
            continue
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"mismatch: {relative}")
    return errors


def package_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

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
    missing = [item for item in required if not (ROOT / item).exists()]
    add(checks, "required paths", not missing, missing or "all present")

    nested = ROOT / "工作区" / "skills"
    add(checks, "workspace is flattened", not nested.exists(), str(nested))

    skills = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
    add(
        checks,
        "local skill count and names",
        REQUIRED_SKILLS <= skills,
        {
            "required": sorted(REQUIRED_SKILLS),
            "found": sorted(skills),
            "missing": sorted(REQUIRED_SKILLS - skills),
        },
    )

    structured_errors: list[str] = []
    structured_paths = (
        list(ROOT.rglob("*.json"))
        + list(ROOT.rglob("*.json5"))
        + list(ROOT.rglob("*.yaml"))
        + list(ROOT.rglob("*.yml"))
    )
    for path in structured_paths:
        if "external" in path.parts or is_archived(path) or is_generated(path):
            continue
        try:
            load_structured(path)
        except Exception as exc:
            structured_errors.append(f"{path.relative_to(ROOT)}: {exc}")
    add(checks, "JSON/YAML/JSON5 parse", not structured_errors, structured_errors or "ok")

    frontmatter_errors: list[str] = []
    try:
        import yaml

        for path in (ROOT / "skills").glob("*/SKILL.md"):
            text = path.read_text(encoding="utf-8")
            parts = text.split("---", 2)
            if len(parts) < 3:
                frontmatter_errors.append(f"{path.relative_to(ROOT)}: broken frontmatter")
                continue
            meta = yaml.safe_load(parts[1]) or {}
            if not meta.get("name") or not meta.get("description"):
                frontmatter_errors.append(f"{path.relative_to(ROOT)}: missing name/description")
    except Exception as exc:
        frontmatter_errors.append(str(exc))
    add(checks, "skill frontmatter", not frontmatter_errors, frontmatter_errors or "ok")

    secret_hits: list[str] = []
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or not is_text_file(path)
            or path.name == "SHA256SUMS.txt"
            or is_archived(path)
            or is_generated(path)
        ):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                secret_hits.append(f"{path.relative_to(ROOT)}: {label}")
    add(checks, "no apparent secrets", not secret_hits, secret_hits or "ok")

    factory = ROOT / "scripts" / "factory.py"
    factory_text = factory.read_text(encoding="utf-8") if factory.exists() else ""
    add(
        checks,
        "factory is fail-closed before implementation",
        "production pipeline is not implemented" in factory_text.lower(),
        str(factory.relative_to(ROOT)) if factory.exists() else "missing",
    )

    stale: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or not is_text_file(path) or is_archived(path) or is_generated(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if ("工作区/" + "scripts") in text or ("工作区/" + "config") in text:
            stale.append(str(path.relative_to(ROOT)))
    add(checks, "no stale nested workspace references", not stale, stale or "ok")

    checksum_errors = checksum_checks()
    add(checks, "release checksums", not checksum_errors, checksum_errors or "ok")

    return checks


def evidence_json(name: str) -> dict[str, Any] | None:
    path = REPORTS / name
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def evidence_is_v25_passed(evidence: dict[str, Any] | None) -> bool:
    """Accept only explicit V2.5 evidence for newly corrected P0 contracts."""
    if not evidence or evidence.get("passed") is not True:
        return False
    version = evidence.get("schema_version") or evidence.get("version")
    return str(version or "") == "2.5"


def named_evidence_passed(
    evidence: dict[str, Any] | None,
    *names: str,
) -> bool:
    """Return true when any explicitly named evidence check passed."""
    if not evidence:
        return False
    expected = {name.casefold() for name in names}
    for check in evidence.get("checks", []):
        if not isinstance(check, dict):
            continue
        label = str(check.get("id") or check.get("name") or "").casefold()
        if label in expected and check.get("passed") is True:
            return True
    return False


def parse_json_stdout(result: dict[str, Any]) -> Any | None:
    if result.get("returncode") != 0:
        return None
    try:
        return json.loads(result.get("stdout", ""))
    except (TypeError, json.JSONDecodeError):
        return None


def normalized_path(value: str) -> str:
    return os.path.normcase(os.path.normpath(value))


def is_video_factory_cron(job: dict[str, Any]) -> bool:
    if str(job.get("agentId", "")).casefold() == "video-factory":
        return True
    if str(job.get("sessionKey", "")).casefold().startswith("agent:video-factory:"):
        return True
    identifying_text = json.dumps(
        {
            "name": job.get("name"),
            "description": job.get("description"),
            "payload": job.get("payload"),
        },
        ensure_ascii=False,
    ).casefold()
    return "openclaw_videofactory" in identifying_text or "video-factory" in identifying_text


def p0_checks() -> list[dict[str, Any]]:
    checks = package_checks()

    commands = {
        "openclaw": ["openclaw", "--version"],
        "gateway": ["openclaw", "gateway", "status"],
        "config_validate": ["openclaw", "config", "validate"],
        "doctor": ["openclaw", "doctor"],
        "agents": ["openclaw", "agents", "list", "--json"],
        "skills": ["openclaw", "skills", "check", "--agent", "video-factory"],
        "cron": ["openclaw", "cron", "list", "--json"],
        "codex": ["codex", "--version"],
        "lark_cli": ["lark-cli", "--version"],
        "ffmpeg": ["ffmpeg", "-version"],
        "nvenc": ["ffmpeg", "-hide_banner", "-encoders"],
        "nvidia": [
            "nvidia-smi",
            "--query-gpu=name,memory.total",
            "--format=csv,noheader",
        ],
    }

    results = {
        name: run(command, timeout=90 if name == "doctor" else 60)
        for name, command in commands.items()
    }
    for name, result in results.items():
        passed = result["returncode"] == 0
        if name == "nvenc":
            passed = passed and "h264_nvenc" in result["stdout"]
        if name == "nvidia":
            passed = passed and "4070" in result["stdout"]
        add(checks, f"runtime command: {name}", passed, result)

    skill_output = results["skills"]["stdout"] + results["skills"]["stderr"]
    visible = {skill for skill in REQUIRED_SKILLS if skill in skill_output}
    add(
        checks,
        "OpenClaw sees local skills",
        visible == REQUIRED_SKILLS,
        {"visible": sorted(visible), "missing": sorted(REQUIRED_SKILLS - visible)},
    )

    agents = parse_json_stdout(results["agents"])
    video_factory = next(
        (
            agent
            for agent in agents or []
            if isinstance(agent, dict) and agent.get("id") == "video-factory"
        ),
        None,
    )
    add(
        checks,
        "video-factory agent exists",
        video_factory is not None,
        video_factory or "missing",
    )
    workspace = video_factory.get("workspace") if video_factory else None
    add(
        checks,
        "video-factory workspace is project root",
        bool(workspace and normalized_path(workspace) == normalized_path(str(ROOT))),
        workspace or "missing",
    )

    cron_payload = parse_json_stdout(results["cron"])
    cron_jobs = cron_payload.get("jobs", []) if isinstance(cron_payload, dict) else []
    video_factory_crons = [
        job for job in cron_jobs if isinstance(job, dict) and is_video_factory_cron(job)
    ]
    add(
        checks,
        "no VideoFactory production Cron",
        cron_payload is not None and not video_factory_crons,
        {
            "cron_query_ok": cron_payload is not None,
            "matching_jobs": [
                {"id": job.get("id"), "name": job.get("name")} for job in video_factory_crons
            ],
        },
    )

    add(
        checks,
        "machine inventory evidence",
        (REPORTS / "machine_inventory.json").exists(),
        str(REPORTS / "machine_inventory.json"),
    )
    add(
        checks,
        "OpenClaw state evidence",
        (REPORTS / "openclaw_state").exists(),
        str(REPORTS / "openclaw_state"),
    )

    text_evidence = evidence_json("FEISHU_SMOKE_TEST.json")
    add(
        checks,
        "Feishu text ingress",
        named_evidence_passed(
            text_evidence,
            "inbound text and visible bot reply",
            "text_ingress",
        ),
        text_evidence or "missing",
    )

    single_consumer = evidence_json("FEISHU_SINGLE_CONSUMER_TEST.json")
    add(
        checks,
        "Feishu single consumer",
        evidence_is_v25_passed(single_consumer)
        and all(
            named_evidence_passed(single_consumer, check_id)
            for check_id in ("feishu_single_consumer", "feishu_deduplication")
        ),
        single_consumer or "missing",
    )

    ingress = evidence_json("FEISHU_INGRESS_TEST.json")
    for label, check_id in [
        ("Feishu TXT ingress", "txt_ingress"),
        ("Feishu PNG ingress", "png_ingress"),
        ("Feishu MP4 ingress", "mp4_ingress"),
        ("safe media receipt/hash/quarantine", "safe_media_ingest"),
    ]:
        add(
            checks,
            label,
            evidence_is_v25_passed(ingress) and named_evidence_passed(ingress, check_id),
            ingress or "missing",
        )

    egress = evidence_json("FEISHU_EGRESS_TEST.json")
    for label, check_id in [
        ("lark-cli Markdown egress", "lark_cli_markdown_egress"),
        ("lark-cli PNG egress", "lark_cli_png_egress"),
        ("lark-cli TXT egress", "lark_cli_txt_egress"),
        ("lark-cli MP4 egress", "lark_cli_mp4_egress"),
        ("lark-cli egress idempotency", "egress_idempotency"),
    ]:
        add(
            checks,
            label,
            evidence_is_v25_passed(egress) and named_evidence_passed(egress, check_id),
            egress or "missing",
        )

    codex_cli = evidence_json("CODEX_CLI_SMOKE.json")
    add(
        checks,
        "direct Codex CLI smoke",
        evidence_is_v25_passed(codex_cli)
        and all(
            named_evidence_passed(codex_cli, check_id)
            for check_id in (
                "direct_codex_cli_read",
                "direct_codex_cli_workspace_write",
                "workspace_isolation",
            )
        ),
        codex_cli or "missing",
    )

    regression = evidence_json("OPENCLAW_EXISTING_AGENTS_REGRESSION.json")
    add(
        checks,
        "existing agents/bindings regression",
        evidence_is_v25_passed(regression)
        and all(
            named_evidence_passed(regression, check_id)
            for check_id in ("existing_agents_regression", "bindings_regression")
        ),
        regression or "missing",
    )

    skill_evidence = evidence_json("SKILL_VISIBILITY.json")
    add(
        checks,
        "Skill visibility evidence",
        bool(skill_evidence and skill_evidence.get("passed") is True),
        skill_evidence or "missing",
    )

    return checks


def phase_checks(
    previous_gate: str,
    evidence_name: str,
    phase_label: str,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    add(
        checks, "previous gate exists", (GATES / previous_gate).exists(), str(GATES / previous_gate)
    )
    evidence = evidence_json(evidence_name)
    add(
        checks,
        f"{phase_label} evidence",
        bool(evidence and evidence.get("passed") is True),
        evidence or "missing",
    )
    return checks


def checks_for_gate(gate: str) -> list[dict[str, Any]]:
    if gate == "package":
        return package_checks()
    if gate == "p0":
        return p0_checks()
    if gate == "p1":
        checks = phase_checks("P0_READY.json", "P1_TEST_RESULTS.json", "P1")
        required = [
            "src/factory/cli.py",
            "src/factory/db.py",
            "src/factory/state.py",
            "remotion/src/templates",
        ]
        missing = [item for item in required if not (ROOT / item).exists()]
        add(checks, "P1 required artifacts", not missing, missing or "all present")
        factory_text = (ROOT / "scripts" / "factory.py").read_text(
            encoding="utf-8", errors="ignore"
        )
        add(
            checks,
            "production entrypoint replaced",
            "production pipeline is not implemented" not in factory_text.lower(),
            "scripts/factory.py",
        )
        return checks
    if gate == "p2":
        return phase_checks("P1_READY.json", "P2_TEST_RESULTS.json", "P2")
    if gate == "p3":
        return phase_checks("P2_READY.json", "P3_GPU_TEST_RESULTS.json", "P3")
    if gate == "p4":
        return phase_checks("P3_READY.json", "P4_REFERENCE_TEST_RESULTS.json", "P4")
    if gate == "p5":
        return phase_checks("P4_READY.json", "P5_JIANYING_TEST_RESULTS.json", "P5")
    if gate == "runtime":
        checks: list[dict[str, Any]] = []
        for name, command in {
            "gateway": ["openclaw", "gateway", "status"],
            "cron": ["openclaw", "cron", "list"],
            "gpu": [
                "nvidia-smi",
                "--query-gpu=name,memory.free",
                "--format=csv,noheader",
            ],
        }.items():
            result = run(command)
            add(checks, name, result["returncode"] == 0, result)
        return checks
    if gate == "production":
        checks: list[dict[str, Any]] = []
        for marker in [
            "P0_READY.json",
            "P1_READY.json",
            "P2_READY.json",
            "P3_READY.json",
            "P4_READY.json",
        ]:
            add(checks, marker, (GATES / marker).exists(), str(GATES / marker))
        trial = evidence_json("SEVEN_DAY_TRIAL.json")
        add(
            checks,
            "seven-day trial",
            bool(trial and trial.get("passed") is True),
            trial or "missing",
        )
        return checks
    raise ValueError(gate)


def write_report(gate: str, checks: list[dict[str, Any]]) -> tuple[Path, bool]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    GATES.mkdir(parents=True, exist_ok=True)

    passed = all(check["passed"] for check in checks)
    payload = {
        "gate": gate,
        "passed": passed,
        "project_root": str(ROOT),
        "checks": checks,
    }

    json_path = REPORTS / f"gate_{gate}.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [f"# Gate {gate.upper()}", "", f"Passed: **{passed}**", ""]
    for check in checks:
        symbol = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- [{symbol}] {check['name']}")
    (REPORTS / f"gate_{gate}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if passed:
        marker_name = (
            "PRODUCTION_READY.json"
            if gate == "production"
            else "PACKAGE_READY.json"
            if gate == "package"
            else f"{gate.upper()}_READY.json"
        )
        (GATES / marker_name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return json_path, passed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gate",
        required=True,
        choices=["package", "p0", "p1", "p2", "p3", "p4", "p5", "runtime", "production"],
    )
    args = parser.parse_args()

    checks = checks_for_gate(args.gate)
    report, passed = write_report(args.gate, checks)

    print(f"Gate: {args.gate}")
    print(f"Passed: {passed}")
    print(f"Report: {report}")
    for check in checks:
        print(f"{'PASS' if check['passed'] else 'FAIL'}: {check['name']}")

    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
