"""Machine-verifiable Phase 1 gate over approved local evidence.

The gate is deliberately read-only. It never modifies ``PROJECT_STATUS.yaml``
and never runs a renderer, Provider, Feishu, OpenClaw, Cron, or publication
operation. The caller must provide fresh evidence references and hashes.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from video_factory.pipeline.errors import FactoryContractError

_PHASE = "PHASE_1_LOCAL_VIDEO_FACTORY"
_REQUIRED_TOPIC_FIXTURES = frozenset({"modbus_rtu", "flash_watchdog", "freertos"})
_LIFECYCLE_TYPES = ("cancel", "retry", "restart_recovery", "encoder_fallback")


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fail(code: str, message: str, **context: object) -> FactoryContractError:
    return FactoryContractError(code, message, context)


def _read_object(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise _fail("phase1_gate_input_invalid", "Phase 1 gate input is missing.", field=field)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _fail("phase1_gate_input_invalid", "Phase 1 gate input is invalid JSON.", field=field) from exc
    if not isinstance(value, dict):
        raise _fail("phase1_gate_input_invalid", "Phase 1 gate input must be an object.", field=field)
    return value


def _validate(root: Path, name: str, document: dict[str, Any]) -> None:
    try:
        import jsonschema

        schema = _read_object(
            root / "schemas" / "video" / f"{name}.schema.json", field=f"schema:{name}"
        )
        validator = jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        )
        errors = sorted(
            validator.iter_errors(document),
            key=lambda error: (
                tuple(str(part) for part in error.absolute_path),
                str(error.validator),
            ),
        )
    except ImportError as exc:
        raise _fail(
            "phase1_gate_validator_unavailable",
            "jsonschema is required for the Phase 1 gate.",
            schema=name,
        ) from exc
    if errors:
        error = errors[0]
        raise _fail(
            "phase1_gate_schema_invalid",
            "Phase 1 gate evidence failed schema validation.",
            schema=name,
            path=".".join(str(part) for part in error.absolute_path),
            validator=str(error.validator),
        ) from error


def _resolve(root: Path, value: object, *, field: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise _fail(
            "phase1_gate_path_invalid",
            "Phase 1 gate evidence path must be repository-relative.",
            field=field,
        )
    root = root.resolve()
    candidate = (root / value).resolve()
    if candidate == root or root not in candidate.parents or candidate.is_symlink():
        raise _fail(
            "phase1_gate_path_invalid",
            "Phase 1 gate evidence path escapes the repository.",
            field=field,
        )
    return candidate


def _append(blockers: list[str], blocker: str) -> None:
    if blocker not in blockers:
        blockers.append(blocker)


def _load_ref(
    root: Path, ref: dict[str, Any], *, field: str
) -> tuple[dict[str, Any] | None, bool]:
    try:
        path = _resolve(root, ref.get("path"), field=field)
        expected = str(ref.get("sha256", ""))
        if len(expected) != 64 or _sha256(path) != expected:
            return None, False
        return _read_object(path, field=field), True
    except (FactoryContractError, OSError):
        return None, False


def evaluate_phase1_gate(manifest_path: Path, *, project_root: Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    manifest = _read_object(Path(manifest_path), field="acceptance_manifest")
    _validate(root, "phase1_acceptance_manifest", manifest)
    checks = {
        "source_hashes_match": True,
        "topic_fixtures_ready": False,
        "reference_mode_ready": False,
        "lifecycle_ready": False,
        "boundary_ready": False,
    }
    blockers: list[str] = []

    topic_entries = manifest.get("topic_jobs", [])
    fixture_ids = {
        str(item.get("fixture_id")) for item in topic_entries if isinstance(item, dict)
    }
    topic_ready = fixture_ids == _REQUIRED_TOPIC_FIXTURES
    for index, item in enumerate(topic_entries):
        if not isinstance(item, dict):
            topic_ready = False
            continue
        report, hash_ok = _load_ref(
            root, item.get("prereview", {}), field=f"topic_jobs.{index}.prereview"
        )
        checks["source_hashes_match"] = checks["source_hashes_match"] and hash_ok
        if not hash_ok or not isinstance(report, dict):
            topic_ready = False
            continue
        try:
            _validate(root, "phase1_job_prereview", report)
        except FactoryContractError:
            topic_ready = False
            continue
        if (
            report.get("status") != "ready"
            or report.get("input_mode") != "topic"
            or report.get("control_job_id") != item.get("control_job_id")
        ):
            topic_ready = False
    checks["topic_fixtures_ready"] = topic_ready
    if not topic_ready:
        _append(blockers, "topic_fixtures_not_ready")

    reference_ready = True
    reference_entries = manifest.get("reference_jobs", [])
    if not isinstance(reference_entries, list) or not reference_entries:
        reference_ready = False
    for index, item in enumerate(reference_entries if isinstance(reference_entries, list) else []):
        if not isinstance(item, dict):
            reference_ready = False
            continue
        report, hash_ok = _load_ref(
            root, item.get("prereview", {}), field=f"reference_jobs.{index}.prereview"
        )
        checks["source_hashes_match"] = checks["source_hashes_match"] and hash_ok
        if not hash_ok or not isinstance(report, dict):
            reference_ready = False
            continue
        try:
            _validate(root, "phase1_job_prereview", report)
        except FactoryContractError:
            reference_ready = False
            continue
        if (
            report.get("status") != "ready"
            or report.get("input_mode") != "local_reference"
            or report.get("control_job_id") != item.get("control_job_id")
            or report.get("checks", {}).get("reference_difference_ready") is not True
        ):
            reference_ready = False
    checks["reference_mode_ready"] = reference_ready
    if not reference_ready:
        _append(blockers, "reference_mode_not_ready")

    lifecycle_ready = True
    lifecycle = manifest.get("lifecycle", {})
    for evidence_type in _LIFECYCLE_TYPES:
        ref = lifecycle.get(evidence_type, {}) if isinstance(lifecycle, dict) else {}
        document, hash_ok = _load_ref(root, ref, field=f"lifecycle.{evidence_type}")
        checks["source_hashes_match"] = checks["source_hashes_match"] and hash_ok
        if not hash_ok or not isinstance(document, dict):
            lifecycle_ready = False
            continue
        try:
            _validate(root, "phase1_lifecycle_evidence", document)
        except FactoryContractError:
            lifecycle_ready = False
            continue
        if document.get("evidence_type") != evidence_type or document.get("status") != "passed":
            lifecycle_ready = False
    checks["lifecycle_ready"] = lifecycle_ready
    if not lifecycle_ready:
        _append(blockers, "lifecycle_evidence_not_ready")

    boundary_ref = manifest.get("boundary_audit", {})
    boundary, hash_ok = _load_ref(
        root,
        boundary_ref if isinstance(boundary_ref, dict) else {},
        field="boundary_audit",
    )
    checks["source_hashes_match"] = checks["source_hashes_match"] and hash_ok
    boundary_ready = hash_ok and isinstance(boundary, dict)
    if boundary_ready:
        try:
            _validate(root, "phase1_boundary_audit", boundary)
        except FactoryContractError:
            boundary_ready = False
    checks["boundary_ready"] = bool(boundary_ready)
    if not boundary_ready:
        _append(blockers, "boundary_audit_not_ready")

    if not checks["source_hashes_match"]:
        _append(blockers, "source_hash_mismatch")
    report = {
        "schema_version": "1.0",
        "phase": _PHASE,
        "status": "ready" if all(checks.values()) and not blockers else "blocked",
        "checks": checks,
        "blockers": blockers,
        "verified_at": _now(),
    }
    _validate(root, "phase1_gate_report", report)
    return report


__all__ = ["evaluate_phase1_gate"]
