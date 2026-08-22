from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from src.factory.phase1_gate import evaluate_phase1_gate


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = (
    "phase1_acceptance_manifest.schema.json",
    "phase1_boundary_audit.schema.json",
    "phase1_gate_report.schema.json",
    "phase1_job_prereview.schema.json",
    "phase1_lifecycle_evidence.schema.json",
)


def _write(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_schemas(root: Path) -> None:
    target = root / "schemas" / "video"
    target.mkdir(parents=True)
    for name in SCHEMAS:
        shutil.copyfile(REPO_ROOT / "schemas" / "video" / name, target / name)


def _evidence_ref(path: Path, root: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": _sha(path)}


def _prereview(root: Path, name: str, job_id: str, input_mode: str) -> Path:
    path = root / "reports" / f"{name}.json"
    checks = {
        "job_pending_review": True,
        "required_artifacts_registered": True,
        "registered_artifact_hashes_match": True,
        "review_package_valid": True,
        "review_package_artifacts_match": True,
        "quality_report_passed": True,
        "human_review_approved": True,
        "reference_difference_ready": True,
        "forbidden_integrations_absent": True,
    }
    _write(
        path,
        {
            "schema_version": "1.0",
            "phase": "PHASE_1_LOCAL_VIDEO_FACTORY",
            "control_job_id": job_id,
            "render_job_id": f"phase1_{name}",
            "input_mode": input_mode,
            "status": "ready",
            "checks": checks,
            "blockers": [],
            "final_master_sha256": "a" * 64,
            "verified_at": "2026-08-22T00:00:00Z",
        },
    )
    return path


def _ready_manifest(root: Path) -> Path:
    _copy_schemas(root)
    fixtures = (
        ("modbus_rtu", "job-" + "1" * 24),
        ("flash_watchdog", "job-" + "2" * 24),
        ("freertos", "job-" + "3" * 24),
    )
    topic_jobs = []
    for fixture_id, job_id in fixtures:
        path = _prereview(root, fixture_id, job_id, "topic")
        topic_jobs.append(
            {
                "fixture_id": fixture_id,
                "control_job_id": job_id,
                "prereview": _evidence_ref(path, root),
            }
        )
    reference_job_id = "job-" + "4" * 24
    reference_path = _prereview(
        root, "reference", reference_job_id, "local_reference"
    )
    lifecycle: dict[str, dict[str, str]] = {}
    for index, evidence_type in enumerate(
        ("cancel", "retry", "restart_recovery", "encoder_fallback"), start=5
    ):
        path = root / "reports" / f"{evidence_type}.json"
        _write(
            path,
            {
                "schema_version": "1.0",
                "phase": "PHASE_1_LOCAL_VIDEO_FACTORY",
                "evidence_type": evidence_type,
                "status": "passed",
                "job_id": "job-" + str(index) * 24,
                "assertions": {"effect_recorded": True, "duplicate_effects": 0},
                "observed_at": "2026-08-22T00:00:00Z",
            },
        )
        lifecycle[evidence_type] = _evidence_ref(path, root)
    boundary_path = root / "reports" / "boundary.json"
    _write(
        boundary_path,
        {
            "schema_version": "1.0",
            "phase": "PHASE_1_LOCAL_VIDEO_FACTORY",
            "status": "passed",
            "checks": {
                "no_feishu": True,
                "no_openclaw_runtime": True,
                "no_cron": True,
                "no_automatic_publish": True,
                "runtime_paths_private": True,
            },
            "observed_at": "2026-08-22T00:00:00Z",
        },
    )
    manifest = {
        "schema_version": "1.0",
        "phase": "PHASE_1_LOCAL_VIDEO_FACTORY",
        "topic_jobs": topic_jobs,
        "reference_jobs": [
            {
                "label": "authorized_reference",
                "control_job_id": reference_job_id,
                "prereview": _evidence_ref(reference_path, root),
            }
        ],
        "lifecycle": lifecycle,
        "boundary_audit": _evidence_ref(boundary_path, root),
    }
    path = root / "reports" / "phase1_acceptance_manifest.json"
    _write(path, manifest)
    return path


def test_gate_is_ready_for_complete_fresh_evidence(tmp_path: Path) -> None:
    manifest = _ready_manifest(tmp_path)
    report = evaluate_phase1_gate(manifest, project_root=tmp_path)
    assert report["status"] == "ready"
    assert report["blockers"] == []
    assert all(report["checks"].values())


def test_gate_rejects_tampered_evidence(tmp_path: Path) -> None:
    manifest = _ready_manifest(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    evidence = tmp_path / value["lifecycle"]["retry"]["path"]
    evidence.write_text("{}\n", encoding="utf-8")
    report = evaluate_phase1_gate(manifest, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "source_hash_mismatch" in report["blockers"]
    assert "lifecycle_evidence_not_ready" in report["blockers"]


def test_gate_requires_each_fixed_topic_fixture(tmp_path: Path) -> None:
    manifest = _ready_manifest(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["topic_jobs"][2]["fixture_id"] = "modbus_rtu"
    _write(manifest, value)
    report = evaluate_phase1_gate(manifest, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "topic_fixtures_not_ready" in report["blockers"]


def test_gate_requires_reference_prereview(tmp_path: Path) -> None:
    manifest = _ready_manifest(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    reference = tmp_path / value["reference_jobs"][0]["prereview"]["path"]
    document = json.loads(reference.read_text(encoding="utf-8"))
    document["status"] = "blocked"
    document["blockers"] = ["human_review_not_approved"]
    _write(reference, document)
    value["reference_jobs"][0]["prereview"]["sha256"] = _sha(reference)
    _write(manifest, value)
    report = evaluate_phase1_gate(manifest, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "reference_mode_not_ready" in report["blockers"]
