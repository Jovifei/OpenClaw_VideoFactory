"""Create locally guarded execution evidence for one offline delivery record."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.factory.config import database_path, jobs_root
from src.factory.db import CandidateStore


JOB_ID_RE = re.compile(r"job-[a-f0-9]{24}")
PROOF_NAME = "dry_run_execution_proof.json"
GUARD_POLICY = "deny_transport_runtime_v1"
EVIDENCE_LEVEL = "local_self_attestation"
RUNNER_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class TransportGuard:
    """Deny runtime transport and process-launch audit events for this process."""

    def __init__(self) -> None:
        self.socket_events = 0
        self.process_events = 0

    def __call__(self, event: str, _arguments: tuple[object, ...]) -> None:
        if event.startswith("socket."):
            self.socket_events += 1
            raise RuntimeError("offline_transport_denied")
        if event in {"subprocess.Popen", "os.system"}:
            self.process_events += 1
            raise RuntimeError("offline_process_launch_denied")

    def proof(self) -> dict[str, Any]:
        return {
            "policy": GUARD_POLICY,
            "socket_events": self.socket_events,
            "process_events": self.process_events,
        }


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo == UTC
    except ValueError:
        return False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _delivery_key(job_id: str) -> str:
    return hashlib.sha256(f"{job_id}|offline-dry-run|v2".encode("utf-8")).hexdigest()


def _parse_args(argv: list[str]) -> tuple[str, bool]:
    if not argv:
        raise ValueError("invalid_arguments")
    json_requested = False
    values = list(argv)
    if values and values[-1] == "--json":
        json_requested = True
        values.pop()
    if len(values) != 2 or values[0] != "--job-id" or not JOB_ID_RE.fullmatch(values[1]):
        raise ValueError("invalid_arguments")
    return values[1], json_requested


def _package_for(job_id: str) -> Path:
    root = jobs_root().resolve()
    package = (root / job_id).resolve()
    if package.parent != root or not package.is_dir():
        raise RuntimeError("candidate_package_missing")
    return package


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _proof_matches(
    proof: dict[str, Any],
    *,
    job_id: str,
    delivery_manifest_sha256: str,
    artifacts: list[dict[str, Any]],
) -> bool:
    return (
        set(proof)
        == {
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
        and proof.get("schema_version") == "1.0"
        and proof.get("mode") == "offline-dry-run"
        and proof.get("status") == "completed"
        and proof.get("job_id") == job_id
        and proof.get("delivery_key") == _delivery_key(job_id)
        and proof.get("delivery_manifest_sha256") == delivery_manifest_sha256
        and proof.get("runner_source_sha256") == RUNNER_SOURCE_SHA256
        and proof.get("guard")
        == {"policy": GUARD_POLICY, "socket_events": 0, "process_events": 0}
        and proof.get("evidence_level") == EVIDENCE_LEVEL
        and proof.get("artifacts") == artifacts
        and _utc_timestamp(proof.get("completed_at"))
    )


def _database_delivery_matches(
    record: object, manifest: dict[str, Any], job_id: str
) -> bool:
    return (
        isinstance(record, dict)
        and record.get("job_id") == job_id
        and record.get("mode") == "dry-run"
        and record.get("status") == "recorded"
        and record.get("manifest")
        == {key: value for key, value in manifest.items() if key != "delivery_key"}
    )


def create_execution_proof(job_id: str) -> dict[str, Any]:
    """Run one local dry-run record under a deny-by-default audit guard."""
    if not JOB_ID_RE.fullmatch(job_id):
        raise ValueError("invalid_job_id")
    package = _package_for(job_id)
    store = CandidateStore(database_path())
    job = store.status(job_id)
    if job.get("state") != "PENDING_REVIEW":
        raise RuntimeError("job_not_pending_review")
    manifest_path = package / "delivery_manifest.json"
    proof_path = package / PROOF_NAME
    guard = TransportGuard()
    sys.addaudithook(guard)
    from src.factory.delivery import load_json_object, valid_delivery_manifest

    manifest = load_json_object(manifest_path)
    if not valid_delivery_manifest(manifest, job_id, include_delivery_key=True):
        raise RuntimeError("delivery_manifest_invalid")
    database_delivery = store.delivery(_delivery_key(job_id))
    if not _database_delivery_matches(database_delivery, manifest, job_id):
        raise RuntimeError("delivery_record_missing_or_invalid")
    if proof_path.is_file():
        existing = load_json_object(proof_path)
        manifest_sha256 = _sha256(manifest_path)
        if isinstance(existing, dict) and _proof_matches(
            existing,
            job_id=job_id,
            delivery_manifest_sha256=manifest_sha256,
            artifacts=manifest["artifacts"],
        ):
            store.record_artifact(
                job_id,
                PROOF_NAME,
                f"jobs/p1_candidate/{job_id}/{PROOF_NAME}",
                _sha256(proof_path),
            )
            return {"status": "already_proven", "job_id": job_id}

    manifest_sha256 = _sha256(manifest_path)
    proof = {
        "schema_version": "1.0",
        "mode": "offline-dry-run",
        "status": "completed",
        "job_id": job_id,
        "delivery_key": _delivery_key(job_id),
        "delivery_manifest_sha256": manifest_sha256,
        "runner_source_sha256": RUNNER_SOURCE_SHA256,
        "guard": guard.proof(),
        "evidence_level": EVIDENCE_LEVEL,
        "artifacts": manifest["artifacts"],
        "completed_at": _utc_now(),
    }
    if not _proof_matches(
        proof,
        job_id=job_id,
        delivery_manifest_sha256=manifest_sha256,
        artifacts=manifest["artifacts"],
    ):
        raise RuntimeError("proof_contract_invalid")
    _atomic_write_json(proof_path, proof)
    store.record_artifact(
        job_id,
        PROOF_NAME,
        f"jobs/p1_candidate/{job_id}/{PROOF_NAME}",
        _sha256(proof_path),
    )
    return {"status": "completed", "job_id": job_id}


def main(argv: list[str] | None = None) -> int:
    try:
        job_id, _json_requested = _parse_args(list(sys.argv[1:] if argv is None else argv))
        result = create_execution_proof(job_id)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
        result = {"status": "failed", "reason": "delivery_runner_failed"}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] in {"completed", "already_proven"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
