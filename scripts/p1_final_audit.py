"""Fail-closed, read-only audit for the P1 offline review candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path, PurePosixPath
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.factory.config import database_path, jobs_root
from src.factory.db import CandidateStore
from src.factory.delivery import load_json_object, valid_delivery_manifest


REQUIRED_ARTIFACTS = (
    "job.json",
    "script.json",
    "storyboard.json",
    "render_input.json",
    "render_manifest.json",
    "voice.wav",
    "captions.json",
    "captions.srt",
    "final_master.mp4",
    "feishu_preview.mp4",
    "cover.png",
    "quality_report.json",
    "publish_info.md",
    "delivery_manifest.json",
    "dry_run_execution_proof.json",
    "run_metrics.json",
)
DELIVERY_ARTIFACTS = (
    "final_master.mp4",
    "feishu_preview.mp4",
    "cover.png",
    "captions.srt",
    "quality_report.json",
)
EXPECTED_ROLES = {
    "fix001_nvenc": {"fixture": "FIX-001", "template": "protocol-frame", "encoder": "h264_nvenc"},
    "fix001_cpu": {"fixture": "FIX-001", "template": "protocol-frame", "encoder": "libx264"},
    "engineering_case": {"fixture": "FIX-002", "template": "engineering-case"},
    "flow_diagram": {"fixture": "FIX-003", "template": "flow-diagram"},
    "code_explainer": {"fixture": "SAMPLE-CODE-001", "template": "code-explainer"},
}
FORBIDDEN_PROMOTION_ARTIFACTS = ("P1_READY.json", "P1_TEST_RESULTS.json")
SENSITIVE_KEYS = frozenset({"secret", "token", "password", "authorization", "environment", "env", "command_line"})
URL_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)
DRIVE_RE = re.compile(r"^[a-z]:[\\/]", re.IGNORECASE)
FINAL_AUDIT_OUTPUT_NAMES = (
    "P1_FINAL_AUDIT_059.json",
    "P1_FINAL_AUDIT_059.md",
    "P1_FINAL_ARTIFACT_INDEX_059.json",
)


class AuditFailure(RuntimeError):
    """A stable, report-safe audit failure."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = load_json_object(path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise AuditFailure("json_invalid") from exc
    if not isinstance(value, dict):
        raise AuditFailure("json_object_required")
    return value


def _fixed_report_outputs() -> tuple[Path, Path, Path]:
    """Return the only permitted audit-report destinations."""
    reports = ROOT / "reports"
    if reports.is_symlink() or not reports.is_dir():
        raise AuditFailure("report_output_root_unsafe")
    resolved_root = ROOT.resolve()
    resolved_reports = reports.resolve()
    if resolved_reports.parent != resolved_root:
        raise AuditFailure("report_output_root_unsafe")
    outputs = tuple(resolved_reports / name for name in FINAL_AUDIT_OUTPUT_NAMES)
    if any(
        path.parent != resolved_reports
        or path.is_symlink()
        or path.exists() and not path.is_file()
        for path in outputs
    ):
        raise AuditFailure("report_output_path_unsafe")
    return outputs  # type: ignore[return-value]


def _safe_relative(value: str) -> PurePosixPath:
    candidate = value.replace("\\", "/")
    if not candidate or URL_RE.match(candidate) or DRIVE_RE.match(value):
        raise AuditFailure("unsafe_artifact_path")
    path = PurePosixPath(candidate)
    if path.is_absolute() or ".." in path.parts:
        raise AuditFailure("unsafe_artifact_path")
    return path


def _resolve_within(root: Path, relative_path: str) -> Path:
    relative = _safe_relative(relative_path)
    resolved_root = root.resolve()
    resolved = (resolved_root / Path(*relative.parts)).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise AuditFailure("unsafe_artifact_path") from exc
    return resolved


def _selection_roles(selection: dict[str, Any]) -> dict[str, str]:
    packages = selection.get("packages")
    if not isinstance(packages, list):
        raise AuditFailure("candidate_selection")
    roles: dict[str, str] = {}
    for package in packages:
        if not isinstance(package, dict):
            raise AuditFailure("candidate_selection")
        fixture = package.get("fixture")
        template = package.get("template")
        encoder = package.get("encoder")
        job_id = package.get("job_id")
        if not isinstance(job_id, str) or not re.fullmatch(r"job-[a-f0-9]{24}", job_id):
            raise AuditFailure("candidate_selection")
        if fixture == "FIX-001" and encoder == "h264_nvenc":
            role = "fix001_nvenc"
        elif fixture == "FIX-001" and encoder == "libx264":
            role = "fix001_cpu"
        elif fixture == "FIX-002" and template == "engineering-case":
            role = "engineering_case"
        elif fixture == "FIX-003" and template == "flow-diagram":
            role = "flow_diagram"
        elif fixture == "SAMPLE-CODE-001" and template == "code-explainer":
            role = "code_explainer"
        else:
            raise AuditFailure("candidate_selection")
        if role in roles or job_id in roles.values():
            raise AuditFailure("candidate_selection")
        roles[role] = job_id
    if set(roles) != set(EXPECTED_ROLES):
        raise AuditFailure("candidate_selection")
    return roles


def _media_details(master: Path) -> dict[str, Any]:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(master)],
        text=True,
        capture_output=True,
        check=False,
    )
    if probe.returncode != 0:
        raise AuditFailure("ffprobe_failed")
    try:
        payload = json.loads(probe.stdout)
    except json.JSONDecodeError as exc:
        raise AuditFailure("ffprobe_invalid") from exc
    video = next((item for item in payload.get("streams", []) if item.get("codec_type") == "video"), None)
    audio = next((item for item in payload.get("streams", []) if item.get("codec_type") == "audio"), None)
    if not isinstance(video, dict) or not isinstance(audio, dict):
        raise AuditFailure("media_stream_missing")
    try:
        fps = float(Fraction(str(video.get("avg_frame_rate", "0/1"))))
        duration = float(payload.get("format", {}).get("duration", 0.0))
    except (ValueError, ZeroDivisionError, TypeError) as exc:
        raise AuditFailure("media_metadata_invalid") from exc
    decode = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", str(master), "-f", "null", "-"],
        text=True,
        capture_output=True,
        check=False,
    )
    if decode.returncode != 0:
        raise AuditFailure("media_decode_failed")
    return {
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": fps,
        "duration_seconds": duration,
        "audio_codec": audio.get("codec_name"),
    }


def _metrics_safe(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                return False
            if not _metrics_safe(child):
                return False
    elif isinstance(value, list):
        return all(_metrics_safe(item) for item in value)
    elif isinstance(value, str):
        return not DRIVE_RE.match(value) and not URL_RE.match(value)
    return True


def _utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo == UTC
    except ValueError:
        return False


def _validate_delivery(package: Path, job_id: str, store: CandidateStore) -> dict[str, Any]:
    manifest = _read_json(package / "delivery_manifest.json")
    if manifest.get("network_called") is not False or manifest.get("lark_cli_called") is not False:
        raise AuditFailure("delivery_not_dry_run")
    if not valid_delivery_manifest(manifest, job_id, include_delivery_key=True):
        raise AuditFailure("delivery_contract_invalid")
    expected_key = hashlib.sha256(f"{job_id}|offline-dry-run|v2".encode("utf-8")).hexdigest()
    if manifest.get("delivery_key") != expected_key:
        raise AuditFailure("delivery_key_invalid")
    try:
        database_delivery = store.delivery(expected_key)
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuditFailure("delivery_database_json_invalid") from exc
    if not isinstance(database_delivery, dict):
        raise AuditFailure("delivery_database_missing")
    if (
        database_delivery.get("job_id") != job_id
        or database_delivery.get("mode") != "dry-run"
        or database_delivery.get("status") != "recorded"
    ):
        raise AuditFailure("delivery_database_state_invalid")
    database_manifest = database_delivery.get("manifest")
    expected_database_manifest = {key: value for key, value in manifest.items() if key != "delivery_key"}
    if database_manifest != expected_database_manifest:
        raise AuditFailure("delivery_database_manifest_mismatch")
    entries = manifest["artifacts"]
    by_name: dict[str, dict[str, Any]] = {}
    for item in entries:
        name = item["name"]
        if name in by_name or name not in DELIVERY_ARTIFACTS:
            raise AuditFailure("delivery_contract_invalid")
        by_name[name] = item
    if set(by_name) != set(DELIVERY_ARTIFACTS):
        raise AuditFailure("delivery_contract_invalid")
    for name, item in by_name.items():
        path = package / name
        if item.get("sha256") != _sha256(path) or item.get("size_bytes") != path.stat().st_size:
            raise AuditFailure("delivery_artifact_hash_mismatch")
    proof = _read_json(package / "dry_run_execution_proof.json")
    allowed_proof_keys = {
        "schema_version",
        "mode",
        "status",
        "job_id",
        "delivery_key",
        "delivery_manifest_sha256",
        "runner_source_sha256",
        "guard",
        "evidence_level",
        "artifacts",
        "completed_at",
    }
    if set(proof) != allowed_proof_keys or not _metrics_safe(proof):
        raise AuditFailure("dry_run_proof_unsafe")
    runner = ROOT / "scripts" / "p1_dry_run_delivery_runner.py"
    if (
        proof.get("schema_version") != "1.0"
        or proof.get("mode") != "offline-dry-run"
        or proof.get("status") != "completed"
        or proof.get("job_id") != job_id
        or proof.get("delivery_key") != expected_key
        or proof.get("delivery_manifest_sha256") != _sha256(package / "delivery_manifest.json")
        or proof.get("runner_source_sha256") != _sha256(runner)
        or not _utc_timestamp(proof.get("completed_at"))
        or proof.get("evidence_level") != "local_self_attestation"
    ):
        raise AuditFailure("dry_run_proof_invalid")
    if proof.get("guard") != {
        "policy": "deny_transport_runtime_v1",
        "socket_events": 0,
        "process_events": 0,
    }:
        raise AuditFailure("dry_run_proof_guard_invalid")
    if proof.get("artifacts") != entries:
        raise AuditFailure("dry_run_proof_artifact_mismatch")
    return {
        "mode": "dry-run",
        "delivery_key_valid": True,
        "artifact_count": len(by_name),
        "delivery_evidence": "local_self_attestation",
    }


def _validate_job(
    store: CandidateStore,
    role: str,
    job_id: str,
    project_root: Path,
    candidate_jobs_root: Path,
    media_validator: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    expected = EXPECTED_ROLES[role]
    job = store.status(job_id)
    if job.get("state") != "PENDING_REVIEW":
        raise AuditFailure("job_state_invalid")
    if job.get("fixture_id") != expected["fixture"] or job.get("template") != expected["template"]:
        raise AuditFailure("job_contract_mismatch")
    package = _resolve_within(candidate_jobs_root, job_id)
    if not package.is_dir():
        raise AuditFailure("job_package_missing")
    expected_prefix = f"jobs/p1_candidate/{job_id}/"
    db_artifacts = {item["artifact_type"]: item for item in store.artifacts(job_id)}
    evidence: list[dict[str, Any]] = []
    for name in REQUIRED_ARTIFACTS:
        path = package / name
        if not path.is_file():
            raise AuditFailure("artifact_missing")
        record = db_artifacts.get(name)
        if not isinstance(record, dict):
            raise AuditFailure("artifact_database_missing")
        relative = record.get("relative_path")
        if not isinstance(relative, str) or relative != expected_prefix + name:
            raise AuditFailure("unsafe_artifact_path")
        resolved = _resolve_within(project_root, relative)
        if resolved != path.resolve():
            raise AuditFailure("unsafe_artifact_path")
        actual_hash = _sha256(path)
        if record.get("sha256") != actual_hash:
            raise AuditFailure("artifact_hash_mismatch")
        evidence.append({"artifact_type": name, "relative_path": relative, "size_bytes": path.stat().st_size, "sha256": actual_hash})
    quality = _read_json(package / "quality_report.json")
    checks = quality.get("checks")
    if quality.get("status") != "pass" or not isinstance(checks, dict) or not checks or not all(checks.values()):
        raise AuditFailure("quality_gate_failed")
    render = _read_json(package / "render_manifest.json")
    if render.get("renderer") != "remotion" or render.get("network_called") is not False:
        raise AuditFailure("render_contract_invalid")
    if render.get("width") != 1080 or render.get("height") != 1920 or render.get("fps") != 30:
        raise AuditFailure("render_contract_invalid")
    encoder = render.get("master", {}).get("encoder") if isinstance(render.get("master"), dict) else None
    if expected.get("encoder") and encoder != expected["encoder"]:
        raise AuditFailure("encoder_mismatch")
    metrics = _read_json(package / "run_metrics.json")
    if not _metrics_safe(metrics):
        raise AuditFailure("metrics_sensitive_field")
    delivery = _validate_delivery(package, job_id, store)
    media = media_validator(package / "final_master.mp4")
    if media.get("width") != 1080 or media.get("height") != 1920 or abs(float(media.get("fps", 0.0)) - 30.0) > 0.01:
        raise AuditFailure("media_contract_invalid")
    expected_duration = float(render.get("resolved_duration_seconds", 0.0))
    if expected_duration <= 0 or abs(float(media.get("duration_seconds", 0.0)) - expected_duration) > 0.75:
        raise AuditFailure("media_contract_invalid")
    if not media.get("audio_codec"):
        raise AuditFailure("media_stream_missing")
    return {
        "job_id": job_id,
        "role": role,
        "fixture": job["fixture_id"],
        "template": job["template"],
        "state": job["state"],
        "encoder": encoder,
        "media": media,
        "quality_status": quality["status"],
        "delivery": delivery,
        "artifacts": evidence,
    }


def audit_candidate(
    selection_path: Path,
    store: CandidateStore,
    *,
    project_root: Path = ROOT,
    candidate_jobs_root: Path | None = None,
    media_validator: Callable[[Path], dict[str, Any]] = _media_details,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    selection_path = selection_path if selection_path.is_absolute() else project_root / selection_path
    selection_path = selection_path.resolve()
    try:
        selection_path.relative_to(project_root)
    except ValueError as exc:
        raise AuditFailure("candidate_selection") from exc
    selection = _read_json(selection_path)
    roles = _selection_roles(selection)
    candidate_jobs_root = (candidate_jobs_root or project_root / "jobs" / "p1_candidate").resolve()
    results = {
        role: _validate_job(store, role, job_id, project_root, candidate_jobs_root, media_validator)
        for role, job_id in sorted(roles.items())
    }
    forbidden = {name: (project_root / "reports" / name).exists() for name in FORBIDDEN_PROMOTION_ARTIFACTS}
    if any(forbidden.values()):
        raise AuditFailure("forbidden_promotion_artifact")
    return {
        "schema_version": "1.0",
        "task": "P1-OFFLINE-CANDIDATE-FINAL-AUDIT-059",
        "status": "P1_OFFLINE_REVIEW_PACKAGE_LIMITED_SELF_ATTESTATION",
        "offline_only": True,
        "p1_promotion": False,
        "candidate_selection": selection_path.relative_to(project_root).as_posix(),
        "jobs": results,
        "forbidden_promotion_artifacts": forbidden,
        "limits": [
            "offline candidate evidence only",
            "no OpenClaw, Feishu, Gateway, Cron, OAuth, ComfyUI or Analyzer contact",
            "P0 real R3 validation remains required before formal P1 qualification",
            "delivery evidence is local self-attestation and not independent runner-execution proof",
        ],
    }


def _artifact_index(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "task": report["task"],
        "status": report["status"],
        "jobs": {
            role: {"job_id": item["job_id"], "artifacts": item["artifacts"]}
            for role, item in report["jobs"].items()
        },
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = ["# P1 离线候选最终审计（059）", "", f"状态：`{report['status']}`", "", "## 作业", ""]
    for role, item in report["jobs"].items():
        lines.append(f"- `{role}`：`{item['job_id']}`，质量 `{item['quality_status']}`，交付 `{item['delivery']['mode']}`。")
    lines.extend(["", "## 边界", "", *[f"- {item}" for item in report["limits"]], ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, default=ROOT / "reports" / "P1_POLISH_CANDIDATE_058.json")
    args = parser.parse_args(argv)
    try:
        output_json, output_markdown, artifact_index = _fixed_report_outputs()
    except AuditFailure as exc:
        print(json.dumps({"status": f"P1_OFFLINE_AUDIT_BLOCKED:{exc.code}"}, ensure_ascii=False))
        return 2
    store = CandidateStore(database_path())
    store.initialize()
    try:
        report = audit_candidate(args.selection, store)
    except AuditFailure as exc:
        report = {
            "schema_version": "1.0",
            "task": "P1-OFFLINE-CANDIDATE-FINAL-AUDIT-059",
            "status": f"P1_OFFLINE_AUDIT_BLOCKED:{exc.code}",
            "offline_only": True,
            "p1_promotion": False,
        }
        exit_code = 2
    else:
        exit_code = 0
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if exit_code == 0:
        output_markdown.write_text(_markdown(report), encoding="utf-8")
        artifact_index.write_text(json.dumps(_artifact_index(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        output_markdown.write_text(f"# P1 离线候选最终审计（059）\n\n状态：`{report['status']}`\n", encoding="utf-8")
        artifact_index.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"]}, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
