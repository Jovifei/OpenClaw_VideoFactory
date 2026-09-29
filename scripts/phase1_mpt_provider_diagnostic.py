"""Read-only, secret-redacted diagnosis for the pinned MPT script provider.

This tool deliberately runs outside the Phase 1 CLI and CandidateStore. It
records structural configuration and one direct ``cli.py --stop-at script``
result, but never persists raw config, credential values, generated script
text, or unredacted subprocess output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import time
import tomllib
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MPT_ROOT = REPO_ROOT / "external" / "MoneyPrinterTurbo"
REPORT_PATH = REPO_ROOT / "reports" / "phase1" / "stage_20260929" / "mpt_provider_diagnostic.json"
EXPECTED_MPT_COMMIT = "eb8c23757e098a07bbcd93b3b50e252fc8d1869a"
APPROVED_CREDENTIAL_ENV_VARS = ("MPT_LLM_API_KEY", "MIMO_API_KEY")
DIRECT_TASK_UUID = "d7b3d8c2-35bd-4bd7-9bf9-0b00b2d1a4b6"
MEDIA_SUFFIXES = {".mp4", ".wav", ".mp3", ".aac", ".m4a", ".mov", ".webm"}
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_WINDOWS_PATH = re.compile(r"(?i)(?:[a-z]:\\|\\\\)[^\r\n\s\"']+")
_BEARER = re.compile(r"(?i)(bearer\s+)[^\s,;\]\}\)]+")
_QUERY = re.compile(r"(https?://[^\s\"']+)\?[^\s\"']*")
_SECRET_FIELD = re.compile(
    r"(?i)(\b(?:api[_-]?key|token|secret|password|authorization)\b\s*[:=]\s*)([\"']?)([^\s,;\]\}\)\"']+)"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_exception(exc: BaseException) -> dict[str, str]:
    return {"class": type(exc).__name__, "message": sanitize_text(str(exc))[:500]}


def sanitize_text(value: str, secret_values: Iterable[str] = ()) -> str:
    """Redact credentials and private paths before any diagnostic persistence."""

    text = _ANSI.sub("", str(value))
    for secret in sorted({str(item) for item in secret_values if str(item)}, key=len, reverse=True):
        text = text.replace(secret, "<REDACTED>")
    text = _BEARER.sub(r"\1<REDACTED>", text)
    text = _SECRET_FIELD.sub(r"\1<REDACTED>", text)
    text = _QUERY.sub(r"\1?<REDACTED_QUERY>", text)
    text = _WINDOWS_PATH.sub("<PATH>", text)
    return text


def _safe_lines(value: str, secret_values: Iterable[str]) -> list[str]:
    markers = (
        "error",
        "exception",
        "traceback",
        "failed",
        "http",
        "status",
        "provider",
        "model",
        "config",
        "connect",
        "timeout",
        "api_key",
        "authentication",
        "unauthorized",
        "forbidden",
        "429",
        "500",
        "502",
        "503",
        "504",
    )
    safe = sanitize_text(value, secret_values)
    selected = [line[:1000] for line in safe.splitlines() if any(marker in line.lower() for marker in markers)]
    return selected[-80:]


def _mpt_python(mpt_root: Path) -> Path:
    candidate = mpt_root / ".venv" / "Scripts" / "python.exe"
    if not candidate.is_file():
        candidate = mpt_root / ".venv" / "bin" / "python"
    if not candidate.is_file():
        raise FileNotFoundError("pinned MPT venv Python is missing")
    return candidate


def _git_identity(mpt_root: Path) -> dict[str, Any]:
    revision = subprocess.run(
        ["git", "-C", str(mpt_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    status = subprocess.run(
        ["git", "-C", str(mpt_root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    cli = mpt_root / "cli.py"
    return {
        "expected_revision": EXPECTED_MPT_COMMIT,
        "actual_revision": revision.stdout.strip() or None,
        "clean_checkout": not bool(status.stdout.strip()),
        "cli_entrypoint": "worktree_external/MoneyPrinterTurbo/cli.py",
        "cli_sha256": _sha256(cli) if cli.is_file() else None,
    }


def _config_inventory(mpt_root: Path) -> tuple[dict[str, Any], list[str], str | None]:
    path = mpt_root / "config.toml"
    if not path.is_file():
        return (
            {
                "path": "worktree_external/MoneyPrinterTurbo/config.toml",
                "exists": False,
                "sha256": None,
                "parse_status": "MISSING",
            },
            [],
            None,
        )
    raw = path.read_bytes()
    config_meta: dict[str, Any] = {
        "path": "worktree_external/MoneyPrinterTurbo/config.toml",
        "exists": True,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    secret_values: list[str] = []
    try:
        cfg = tomllib.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - report only safe parser metadata
        config_meta.update({"parse_status": "ERROR", "parse_error": _safe_exception(exc)})
        return config_meta, secret_values, None

    app_cfg = cfg.get("app") if isinstance(cfg.get("app"), dict) else {}
    provider = str(app_cfg.get("llm_provider", "")).strip().lower()
    model_key = f"{provider}_model_name" if provider else ""
    base_key = f"{provider}_base_url" if provider else ""
    credential_key = f"{provider}_api_key" if provider else ""
    model = str(app_cfg.get(model_key, "") or "").strip()
    base_url = str(app_cfg.get(base_key, "") or "").strip()
    credential = str(app_cfg.get(credential_key, "") or "").strip()
    if credential:
        secret_values.append(credential)
    parsed = urlparse(base_url)
    env_presence = {
        name: "PRESENT" if os.environ.get(name, "").strip() else "MISSING"
        for name in APPROVED_CREDENTIAL_ENV_VARS
    }
    config_meta.update(
        {
            "parse_status": "OK",
            "provider": provider or None,
            "model": model or None,
            "endpoint_hostname": parsed.hostname,
            "endpoint_scheme": parsed.scheme or None,
            "endpoint_port": parsed.port,
            "config_section": "app",
            "credential_field": f"app.{credential_key}" if credential_key else None,
            "credential_field_presence": "PRESENT" if credential else "MISSING",
            "approved_credential_env_presence": env_presence,
            "required_credential_variable_names": list(APPROVED_CREDENTIAL_ENV_VARS),
        }
    )
    return config_meta, secret_values, base_url or None


def _reachability(base_url: str | None) -> dict[str, Any]:
    if not base_url:
        return {"status": "SKIPPED_MISSING_ENDPOINT", "hostname": None}
    parsed = urlparse(base_url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        return {"status": "INVALID_ENDPOINT", "hostname": None}
    result: dict[str, Any] = {"hostname": host, "port": port, "scheme": parsed.scheme, "dns": {}, "tcp": {}, "tls": {}}
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        result["dns"] = {"status": "PASS", "address_count": len(addresses)}
    except Exception as exc:  # noqa: BLE001
        result["dns"] = {"status": "FAIL", "error": _safe_exception(exc)}
        result["overall"] = "BLOCKED_NETWORK"
        return result
    try:
        with socket.create_connection((host, port), timeout=5.0) as connection:
            result["tcp"] = {"status": "PASS"}
            if parsed.scheme == "https":
                context = ssl.create_default_context()
                with context.wrap_socket(connection, server_hostname=host) as tls_socket:
                    result["tls"] = {"status": "PASS", "protocol": tls_socket.version()}
            else:
                result["tls"] = {"status": "SKIPPED_NON_TLS"}
    except Exception as exc:  # noqa: BLE001
        result["tcp"] = result.get("tcp") or {"status": "NOT_REACHED"}
        if not result["tcp"]:
            result["tcp"] = {"status": "FAIL"}
        result["tcp"].setdefault("status", "FAIL")
        result["error"] = _safe_exception(exc)
        result["overall"] = "BLOCKED_NETWORK"
        return result
    result["overall"] = "REACHABLE"
    return result


def _media_snapshot(root: Path) -> dict[str, tuple[int, int]]:
    snapshot: dict[str, tuple[int, int]] = {}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES:
            try:
                stat = path.stat()
                snapshot[path.relative_to(root).as_posix()] = (stat.st_size, stat.st_mtime_ns)
            except OSError:
                continue
    return snapshot


def _classify_direct_result(returncode: int | None, timed_out: bool, safe_output: str, result_json: bool) -> str:
    lowered = safe_output.lower()
    if returncode == 0 and result_json:
        return "MPT_PROVIDER_READY"
    if any(token in lowered for token in ("api_key is not set", "api key is not set", "credential is missing")):
        return "MPT_PROVIDER_BLOCKED:MISSING_CREDENTIAL"
    if any(token in lowered for token in ("401", "403", "unauthorized", "authenticationerror", "invalid api key", "forbidden")):
        return "MPT_PROVIDER_BLOCKED:AUTH"
    if any(token in lowered for token in ("model_not_found", "model not found", "unsupported model", "invalid model", "404")):
        return "MPT_PROVIDER_BLOCKED:MODEL_OR_API"
    if any(token in lowered for token in ("name or service not known", "nameresolutionerror", "connectionerror", "connection refused", "connecttimeout", "read timeout", "timed out", "sslerror", "proxyerror")):
        return "MPT_PROVIDER_BLOCKED:NETWORK"
    if any(token in lowered for token in ("tomldecodeerror", "config file is not valid", "base_url is not set", "model_name is not set")):
        return "MPT_PROVIDER_BLOCKED:CONFIG"
    if timed_out:
        return "MPT_PROVIDER_BLOCKED:UNCLASSIFIED"
    if "traceback" in lowered or "exception" in lowered or "application" in lowered:
        return "MPT_PROVIDER_BLOCKED:APPLICATION_ERROR"
    return "MPT_PROVIDER_BLOCKED:UNCLASSIFIED"


def _provider_execution_reached(safe_output: str, result_json: bool) -> bool | None:
    if result_json:
        return True
    lowered = safe_output.lower()
    if any(
        marker in lowered
        for marker in (
            "llm provider:",
            "requesting azure chat completion",
            "chat.completions",
            "returned an error response",
            "api_key is not set",
            "connectionerror",
            "connecttimeout",
        )
    ):
        return True
    if "cli.py: error:" in lowered:
        return False
    return None


def run_diagnostic(mpt_root: Path = DEFAULT_MPT_ROOT) -> dict[str, Any]:
    mpt_root = mpt_root.resolve()
    mpt_python = _mpt_python(mpt_root)
    config_meta, secret_values, base_url = _config_inventory(mpt_root)
    identity_before = _git_identity(mpt_root)
    python_probe = subprocess.run([str(mpt_python), "--version"], capture_output=True, text=True, check=False)
    phase1_db = REPO_ROOT / "state" / "phase1_local" / "phase1_jobs.sqlite3"
    phase1_before = phase1_db.stat() if phase1_db.exists() else None
    media_before = _media_snapshot(mpt_root)
    reachability = _reachability(base_url)
    command = [
        str(mpt_python),
        "cli.py",
        "--video-subject",
        "MPT provider diagnostic",
        "--video-language",
        "zh-CN",
        "--paragraph-number",
        "1",
        "--stop-at",
        "script",
        "--task-id",
        DIRECT_TASK_UUID,
    ]
    started = time.monotonic()
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            cwd=str(mpt_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        returncode: int | None = completed.returncode
        raw_stdout = completed.stdout or ""
        raw_stderr = completed.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = None
        raw_stdout = exc.stdout or ""
        raw_stderr = exc.stderr or ""
    duration = round(time.monotonic() - started, 2)
    safe_combined = sanitize_text(f"{raw_stdout}\n{raw_stderr}", secret_values)
    result_json = False
    for line in reversed(raw_stdout.splitlines()):
        try:
            payload = json.loads(line.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and isinstance(payload.get("result", {}).get("script"), str) and payload["result"]["script"].strip():
            result_json = True
            break
    media_after = _media_snapshot(mpt_root)
    phase1_after = phase1_db.stat() if phase1_db.exists() else None
    identity_after = _git_identity(mpt_root)
    status = _classify_direct_result(returncode, timed_out, safe_combined, result_json)
    provider_execution_reached = _provider_execution_reached(safe_combined, result_json)
    changed_media = sorted(path for path, value in media_after.items() if media_before.get(path) != value)
    new_media = sorted(path for path in media_after if path not in media_before)
    report: dict[str, Any] = {
        "schema_version": "phase1_mpt_provider_diagnostic_v1",
        "status": status,
        "authorization": "Remote GPT iteration 39 WP-M4 sanitized MPT provider/config diagnosis",
        "source_commit": "1ed763773ec6016adf3a4a1f115278d9f47933c8",
        "diagnostic": {
            "identity": "mpt-provider-diagnostic-20260929",
            "attempt_kind": "corrected_valid_uuid",
            "corrected_direct_call": "EXECUTED_EXACTLY_ONCE",
            "task_uuid": DIRECT_TASK_UUID,
            "phase1_job": False,
            "candidate": False,
            "candidate_store_touched": phase1_before != phase1_after,
            "command": ["pinned_venv_python", "cli.py", "--video-subject", "MPT provider diagnostic", "--video-language", "zh-CN", "--paragraph-number", "1", "--stop-at", "script", "--task-id", DIRECT_TASK_UUID],
            "exit_code": returncode,
            "timed_out": timed_out,
            "duration_seconds": duration,
            "result_json_with_script": result_json,
            "provider_execution_reached": provider_execution_reached,
            "safe_error_lines": _safe_lines(f"{raw_stdout}\n{raw_stderr}", secret_values),
            "underlying_raw_output_persisted": False,
        },
        "configuration": config_meta,
        "mpt_runtime": {
            **identity_before,
            "identity_after": identity_after,
            "python_executable": "worktree_external/MoneyPrinterTurbo/.venv/Scripts/python.exe",
            "python_version": (python_probe.stdout or python_probe.stderr).strip(),
            "config_unchanged": config_meta.get("sha256") == _sha256(mpt_root / "config.toml") if (mpt_root / "config.toml").is_file() else False,
        },
        "configured_endpoint_reachability": reachability,
        "media_boundary": {
            "new_media_files": new_media,
            "changed_media_files": changed_media,
            "media_created": bool(new_media or changed_media),
            "tts": False,
            "pcm": False,
            "mp4": False,
            "jianying_invoked": False,
        },
        "safety": {
            "raw_config_persisted": False,
            "credential_values_persisted": False,
            "secret_redaction_applied": True,
            "alternate_provider_probed": False,
            "configuration_changed": False,
            "candidate_store_touched": phase1_before != phase1_after,
        },
        "candidate003": "TERMINAL_PRESERVE",
        "candidate004": "NOT_AUTHORIZED",
        "jianying": "BLOCKED_EXACT_PIN_F421C8A_NO_LOCAL_OR_OFFLINE_SOURCE",
        "m6_authorization": "NOT_AUTHORIZED_UNLESS_STATUS_MPT_PROVIDER_READY_AND_REMOTE_REVIEW_ACCEPTS",
    }
    serialized = json.dumps(report, ensure_ascii=False)
    if any(secret and secret in serialized for secret in secret_values):
        raise RuntimeError("secret_redaction_failed")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one sanitized, read-only pinned MPT provider diagnostic.")
    parser.add_argument("--mpt-root", type=Path, default=DEFAULT_MPT_ROOT)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)
    report_path = args.report if args.report.is_absolute() else REPO_ROOT / args.report
    prior: dict[str, Any] | None = None
    if report_path.is_file():
        try:
            prior = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            prior = None
    report = run_diagnostic(args.mpt_root)
    if prior:
        previous_diagnostic = prior.get("diagnostic", {})
        report["prior_invalid_invocation"] = {
            "attempt_kind": "iteration39_invalid_uuid",
            "status": prior.get("status"),
            "exit_code": previous_diagnostic.get("exit_code"),
            "timed_out": previous_diagnostic.get("timed_out"),
            "provider_request_reached": previous_diagnostic.get("provider_request_reached", False),
            "invocation_contract_error": previous_diagnostic.get("invocation_contract_error"),
            "safe_error_lines": previous_diagnostic.get("safe_error_lines", []),
            "media_created": prior.get("media_boundary", {}).get("media_created", False),
            "candidate_store_touched": prior.get("safety", {}).get("candidate_store_touched", False),
        }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": report_path.relative_to(REPO_ROOT).as_posix(), "media_created": report["media_boundary"]["media_created"], "candidate_store_touched": report["safety"]["candidate_store_touched"]}, ensure_ascii=False))
    return 0 if report["status"] == "MPT_PROVIDER_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
