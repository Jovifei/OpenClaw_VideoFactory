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


def _topic_only_manifest(root: Path) -> Path:
    manifest = _ready_manifest(root)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["acceptance_scope"] = "topic_only_v1"
    value["reference_jobs"] = []
    value["topic_jobs"][0]["fixture_id"] = "i2c"
    live_job_id = "job-" + "9" * 24
    live = _prereview(root, "live_i2c_topic", live_job_id, "topic")
    value["live_topic_job"] = {
        "control_job_id": live_job_id,
        "prereview": _evidence_ref(live, root),
    }
    _write(manifest, value)
    return manifest


def test_topic_only_scope_accepts_empty_references_with_live_topic_review(tmp_path: Path) -> None:
    manifest = _topic_only_manifest(tmp_path)
    report = evaluate_phase1_gate(manifest, project_root=tmp_path)
    assert report["status"] == "ready"
    assert report["checks"]["reference_mode_ready"] is True
    assert report["checks"]["live_topic_ready"] is True


def test_legacy_scope_still_rejects_empty_references(tmp_path: Path) -> None:
    manifest = _ready_manifest(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["reference_jobs"] = []
    _write(manifest, value)
    import pytest
    from video_factory.pipeline.errors import FactoryContractError

    with pytest.raises(FactoryContractError, match="phase1_gate_schema_invalid"):
        evaluate_phase1_gate(manifest, project_root=tmp_path)


def test_topic_only_scope_validates_any_supplied_reference(tmp_path: Path) -> None:
    manifest = _topic_only_manifest(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    reference = tmp_path / "reports" / "reference.json"
    reference.write_text("{}\n", encoding="utf-8")
    value["reference_jobs"] = [{
        "label": "optional-but-supplied",
        "control_job_id": "job-" + "8" * 24,
        "prereview": _evidence_ref(reference, tmp_path),
    }]
    _write(manifest, value)
    report = evaluate_phase1_gate(manifest, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "reference_mode_not_ready" in report["blockers"]


def test_topic_only_scope_requires_approved_review_for_any_supplied_reference(tmp_path: Path) -> None:
    manifest = _topic_only_manifest(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    reference_job_id = "job-" + "8" * 24
    reference = _prereview(tmp_path, "optional_reference", reference_job_id, "local_reference")
    reference_value = json.loads(reference.read_text(encoding="utf-8"))
    reference_value["checks"]["human_review_approved"] = False
    _write(reference, reference_value)
    value["reference_jobs"] = [{
        "label": "optional-but-supplied",
        "control_job_id": reference_job_id,
        "prereview": _evidence_ref(reference, tmp_path),
    }]
    _write(manifest, value)
    report = evaluate_phase1_gate(manifest, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "reference_mode_not_ready" in report["blockers"]


def test_topic_only_scope_schema_requires_live_topic(tmp_path: Path) -> None:
    manifest = _topic_only_manifest(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value.pop("live_topic_job")
    _write(manifest, value)
    import pytest
    from video_factory.pipeline.errors import FactoryContractError

    with pytest.raises(FactoryContractError, match="phase1_gate_schema_invalid"):
        evaluate_phase1_gate(manifest, project_root=tmp_path)


def test_topic_only_scope_rejects_duplicate_live_topic(tmp_path: Path) -> None:
    manifest = _topic_only_manifest(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["live_topic_job"]["control_job_id"] = value["topic_jobs"][0]["control_job_id"]
    _write(manifest, value)
    report = evaluate_phase1_gate(manifest, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "live_topic_not_ready" in report["blockers"]


def test_topic_only_scope_requires_distinct_fixture_control_jobs(tmp_path: Path) -> None:
    manifest = _topic_only_manifest(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    duplicate_id = value["topic_jobs"][0]["control_job_id"]
    duplicate = value["topic_jobs"][1]
    duplicate["control_job_id"] = duplicate_id
    prereview = tmp_path / duplicate["prereview"]["path"]
    prereview_value = json.loads(prereview.read_text(encoding="utf-8"))
    prereview_value["control_job_id"] = duplicate_id
    _write(prereview, prereview_value)
    duplicate["prereview"]["sha256"] = _sha(prereview)
    _write(manifest, value)
    report = evaluate_phase1_gate(manifest, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "topic_fixtures_not_ready" in report["blockers"]
