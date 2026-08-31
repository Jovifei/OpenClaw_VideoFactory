"""Read-only per-job prereview for the local Phase 1 video factory.

The prereview intentionally does not mutate the job, update ``PROJECT_STATUS.yaml``,
or invoke rendering, providers, Feishu, OpenClaw, or a network client. It
reconciles the SQLite control record, registered artifact hashes, the renderer's
human-review package, and one explicit human-review decision.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from video_factory.pipeline.errors import FactoryContractError

from .config import PROJECT_ROOT
from .db import CandidateStore

_PHASE = "PHASE_1_LOCAL_VIDEO_FACTORY"
_REQUIRED_REGISTERED_ARTIFACTS = frozenset({"final_master", "review_package"})
_REQUIRED_HUMAN_CHECKS = (
    "video_playable",
    "audio_clear",
    "subtitles_readable",
    "pink_pig_consistent",
    "technical_content_acceptable",
    "originality_acceptable",
)
_FORBIDDEN_TEXT_MARKERS = (
    "feishu",
    "openclaw gateway",
    "lark-cli",
    "cron",
    "douyin",
)


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
        raise _fail("phase1_prereview_input_invalid", "Phase 1 prereview input is missing.", field=field)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _fail("phase1_prereview_input_invalid", "Phase 1 prereview input is invalid JSON.", field=field) from exc
    if not isinstance(value, dict):
        raise _fail("phase1_prereview_input_invalid", "Phase 1 prereview input must be an object.", field=field)
    return value


def _schema(root: Path, name: str) -> dict[str, Any]:
    path = root / "schemas" / "video" / f"{name}.schema.json"
    return _read_object(path, field=f"schema:{name}")


def _validate(root: Path, name: str, document: dict[str, Any]) -> None:
    try:
        import jsonschema

        validator = jsonschema.Draft202012Validator(
            _schema(root, name), format_checker=jsonschema.FormatChecker()
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
            "phase1_prereview_validator_unavailable",
            "jsonschema is required for Phase 1 prereview.",
            schema=name,
        ) from exc
    if errors:
        error = errors[0]
        raise _fail(
            "phase1_prereview_schema_invalid",
            "Phase 1 prereview evidence failed schema validation.",
            schema=name,
            path=".".join(str(part) for part in error.absolute_path),
            validator=str(error.validator),
        ) from error


def _resolve_under(root: Path, relative: object, *, field: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise _fail(
            "phase1_prereview_path_invalid",
            "Phase 1 prereview path must be repository-relative.",
            field=field,
        )
    root = root.resolve()
    candidate = (root / relative).resolve()
    if candidate == root or root not in candidate.parents or candidate.is_symlink():
        raise _fail(
            "phase1_prereview_path_invalid",
            "Phase 1 prereview path escapes the repository.",
            field=field,
        )
    return candidate


def _resolve_package_artifact(package_dir: Path, relative: object, *, field: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise _fail(
            "phase1_prereview_path_invalid",
            "Review package artifact path must be relative.",
            field=field,
        )
    package_dir = package_dir.resolve()
    candidate = (package_dir / relative).resolve()
    if candidate == package_dir or package_dir not in candidate.parents or candidate.is_symlink():
        raise _fail(
            "phase1_prereview_path_invalid",
            "Review package artifact path escapes its job directory.",
            field=field,
        )
    return candidate


def _append(blockers: list[str], value: str) -> None:
    if value not in blockers:
        blockers.append(value)


def _subject_render_job_id(control_job_id: str) -> str | None:
    prefix = "job-"
    suffix = control_job_id.removeprefix(prefix)
    if not control_job_id.startswith(prefix) or len(suffix) != 24:
        return None
    if any(character not in "0123456789abcdef" for character in suffix):
        return None
    return f"phase1_subject_{suffix}"


def evaluate_job_prereview(
    store: CandidateStore,
    control_job_id: str,
    human_review_path: Path,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    """Return a machine-readable, read-only prereview for one Phase 1 job."""

    root = Path(project_root).resolve()
    checks = {
        "job_pending_review": False,
        "required_artifacts_registered": False,
        "registered_artifact_hashes_match": False,
        "review_package_valid": False,
        "review_package_artifacts_match": False,
        "quality_report_passed": False,
        "human_review_approved": False,
        "reference_difference_ready": False,
        "forbidden_integrations_absent": False,
    }
    blockers: list[str] = []
    render_job_id: str | None = None
    final_master_sha: str | None = None
    input_mode = "unknown"

    try:
        job = store.status(control_job_id)
    except KeyError:
        _append(blockers, "job_not_found")
        return _report(
            control_job_id, render_job_id, input_mode, checks, blockers, final_master_sha, root
        )

    metadata = job.get("metadata")
    metadata_input_mode = "unknown"
    fixture_id = str(job.get("fixture_id", ""))
    if isinstance(metadata, dict):
        candidate_mode = metadata.get("input_mode")
        if candidate_mode in {"topic", "local_reference", "authorized_public_research"}:
            metadata_input_mode = str(candidate_mode)
            input_mode = metadata_input_mode
        elif candidate_mode == "local_subject":
            metadata_input_mode = "local_subject"
    checks["job_pending_review"] = job.get("state") == "PENDING_REVIEW"
    if not checks["job_pending_review"]:
        _append(blockers, "job_not_pending_review")

    records = store.artifacts(control_job_id)
    record_map = {
        str(record.get("artifact_type")): record
        for record in records
        if isinstance(record, dict) and record.get("artifact_type")
    }
    checks["required_artifacts_registered"] = _REQUIRED_REGISTERED_ARTIFACTS.issubset(
        record_map
    )
    if not checks["required_artifacts_registered"]:
        _append(blockers, "required_artifacts_missing")

    registered_paths: dict[str, Path] = {}
    registered_hashes_ok = checks["required_artifacts_registered"]
    for artifact_type in _REQUIRED_REGISTERED_ARTIFACTS:
        record = record_map.get(artifact_type)
        if not isinstance(record, dict):
            continue
        try:
            artifact_path = _resolve_under(
                root, record.get("relative_path"), field=f"artifact:{artifact_type}"
            )
            expected_sha = str(record.get("sha256", ""))
            if (
                artifact_path.is_file()
                and len(expected_sha) == 64
                and _sha256(artifact_path) == expected_sha
            ):
                registered_paths[artifact_type] = artifact_path
            else:
                registered_hashes_ok = False
        except (FactoryContractError, OSError):
            registered_hashes_ok = False
    checks["registered_artifact_hashes_match"] = registered_hashes_ok
    if not registered_hashes_ok:
        _append(blockers, "registered_artifact_hash_mismatch")

    package: dict[str, Any] | None = None
    package_schema: str | None = None
    package_path = registered_paths.get("review_package")
    final_path = registered_paths.get("final_master")
    if final_path is not None:
        final_master_sha = _sha256(final_path)
    if package_path is not None:
        try:
            package = _read_object(package_path, field="review_package")
            package_kind = package.get("package_kind")
            if package_kind is None:
                if metadata_input_mode == "local_subject":
                    raise _fail(
                        "phase1_prereview_subject_package_required",
                        "Local subject metadata requires a strict subject review package.",
                    )
                package_schema = "phase1_review_package"
                _validate(root, package_schema, package)
                render_job_id = str(package.get("job_id", "")) or None
                package_mode = package.get("input_mode")
                if package_mode in {"topic", "local_reference", "authorized_public_research"}:
                    if input_mode == "unknown":
                        input_mode = str(package_mode)
                    elif input_mode != package_mode:
                        _append(blockers, "input_mode_mismatch")
            elif package_kind == "phase1_subject":
                package_schema = "phase1_subject_review_package"
                _validate(root, package_schema, package)
                if package.get("job_id") != control_job_id:
                    raise _fail("phase1_prereview_subject_identity_invalid", "Subject review package job does not match its control job.")
                render_job_id = _subject_render_job_id(control_job_id)
                if render_job_id is None:
                    raise _fail("phase1_prereview_subject_identity_invalid", "Subject review package control job is invalid.")
                if metadata_input_mode != "local_subject" or fixture_id != "local_subject":
                    raise _fail(
                        "phase1_prereview_subject_identity_invalid",
                        "Subject review packages require local_subject fixture and metadata.",
                    )
                input_mode = "topic"
            else:
                raise _fail("phase1_prereview_package_kind_invalid", "Review package kind is not supported.")
            checks["review_package_valid"] = True
        except FactoryContractError:
            _append(blockers, "review_package_invalid")
    else:
        _append(blockers, "review_package_unavailable")

    package_files: dict[str, tuple[Path, dict[str, Any]]] = {}
    package_files_by_name: dict[str, tuple[Path, dict[str, Any]]] = {}
    package_hashes_ok = package is not None and checks["review_package_valid"]
    if package is not None and package_path is not None:
        package_dir = package_path.parent
        artifacts = package.get("artifacts")
        if not isinstance(artifacts, list):
            package_hashes_ok = False
        else:
            for index, entry in enumerate(artifacts):
                if not isinstance(entry, dict):
                    package_hashes_ok = False
                    continue
                name = str(entry.get("name", ""))
                try:
                    artifact_path = _resolve_package_artifact(
                        package_dir,
                        entry.get("path"),
                        field=f"package.artifacts.{index}",
                    )
                    expected_sha = str(entry.get("sha256", ""))
                    expected_bytes = int(entry.get("bytes", -1))
                    if (
                        not artifact_path.is_file()
                        or artifact_path.stat().st_size != expected_bytes
                        or _sha256(artifact_path) != expected_sha
                    ):
                        package_hashes_ok = False
                        continue
                    relative_path = str(entry.get("path", name))
                    if relative_path in package_files or name in package_files_by_name:
                        package_hashes_ok = False
                        continue
                    package_files[relative_path] = (artifact_path, entry)
                    package_files_by_name[name] = (artifact_path, entry)
                except (FactoryContractError, OSError, TypeError, ValueError):
                    package_hashes_ok = False
    checks["review_package_artifacts_match"] = package_hashes_ok
    if not package_hashes_ok:
        _append(blockers, "review_package_artifact_mismatch")

    if package_schema == "phase1_subject_review_package":
        quality_item = package_files.get(str(package.get("quality_report", ""))) if package else None
    else:
        quality_item = package_files_by_name.get(str(package.get("quality_report", ""))) if package else None
    if quality_item is not None and final_master_sha is not None:
        try:
            quality = _read_object(quality_item[0], field="quality_report")
            if package_schema == "phase1_subject_review_package":
                _validate(root, "phase1_subject_quality_report", quality)
                preview = quality.get("preview")
                subtitle = quality.get("subtitle")
                preview_item = package_files.get(str(preview.get("path", ""))) if isinstance(preview, dict) else None
                subtitle_item = package_files.get(str(subtitle.get("review_srt", ""))) if isinstance(subtitle, dict) else None
                checks["quality_report_passed"] = (
                    quality.get("job_id") == control_job_id
                    and isinstance(preview, dict)
                    and preview.get("sha256") == final_master_sha
                    and preview_item is not None
                    and preview_item[0] == final_path
                    and preview_item[1].get("role") == "preview"
                    and subtitle_item is not None
                    and subtitle_item[1].get("role") == "native_subtitles"
                )
            else:
                _validate(root, "phase1_quality_report", quality)
                media = quality.get("media")
                checks["quality_report_passed"] = (
                    quality.get("status") == "passed"
                    and isinstance(media, dict)
                    and media.get("sha256") == final_master_sha
                )
        except FactoryContractError:
            checks["quality_report_passed"] = False
    if not checks["quality_report_passed"]:
        _append(blockers, "quality_report_not_passed")

    try:
        human_review = _read_object(Path(human_review_path), field="human_review")
        _validate(root, "phase1_human_review", human_review)
        checklist = human_review.get("checklist")
        checks["human_review_approved"] = (
            human_review.get("control_job_id") == control_job_id
            and human_review.get("render_job_id") == render_job_id
            and human_review.get("reviewed_artifact_sha256") == final_master_sha
            and human_review.get("decision") == "approved"
            and isinstance(checklist, dict)
            and all(checklist.get(name) is True for name in _REQUIRED_HUMAN_CHECKS)
        )
    except FactoryContractError:
        checks["human_review_approved"] = False
    if not checks["human_review_approved"]:
        _append(blockers, "human_review_not_approved")

    if input_mode == "local_reference":
        reference_evidence = package.get("reference_evidence", {}) if package else {}
        difference_name = (
            str(reference_evidence.get("difference_report", ""))
            if isinstance(reference_evidence, dict)
            else ""
        )
        difference_item = package_files_by_name.get(difference_name)
        if difference_item is not None:
            try:
                difference = _read_object(difference_item[0], field="difference_report")
                checks["reference_difference_ready"] = (
                    difference.get("status") == "ready_for_human_review"
                )
            except FactoryContractError:
                checks["reference_difference_ready"] = False
        if not checks["reference_difference_ready"]:
            _append(blockers, "reference_difference_not_ready")
    else:
        checks["reference_difference_ready"] = input_mode in {
            "topic",
            "authorized_public_research",
        }
        if not checks["reference_difference_ready"]:
            _append(blockers, "input_mode_unknown")

    if package is not None:
        encoded = json.dumps(package, ensure_ascii=False, sort_keys=True).lower()
        checks["forbidden_integrations_absent"] = not any(
            marker in encoded for marker in _FORBIDDEN_TEXT_MARKERS
        )
    if not checks["forbidden_integrations_absent"]:
        _append(blockers, "forbidden_integration_reference")

    return _report(
        control_job_id, render_job_id, input_mode, checks, blockers, final_master_sha, root
    )


def _report(
    control_job_id: str,
    render_job_id: str | None,
    input_mode: str,
    checks: dict[str, bool],
    blockers: list[str],
    final_master_sha: str | None,
    root: Path,
) -> dict[str, Any]:
    status = "ready" if all(checks.values()) and not blockers else "blocked"
    report = {
        "schema_version": "1.0",
        "phase": _PHASE,
        "control_job_id": control_job_id,
        "render_job_id": render_job_id,
        "input_mode": input_mode,
        "status": status,
        "checks": checks,
        "blockers": blockers,
        "final_master_sha256": final_master_sha,
        "verified_at": _now(),
    }
    _validate(root, "phase1_job_prereview", report)
    return report


__all__ = ["evaluate_job_prereview"]
