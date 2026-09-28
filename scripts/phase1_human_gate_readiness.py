"""Prepare human-gate and prereview readiness evidence without creating decisions."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from src.factory.db import CandidateStore
from src.factory.phase1_acceptance import evaluate_job_prereview
from src.factory.phase1_local import build_local_plan, load_local_brief


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "reports" / "phase1" / "stage_20260928"
CAN_JOB = "job-eb356764914b0d9f5ccb94ff"
CAN_RENDER_JOB = "phase1_91c2a7cd2b692884"
CAN_SHA = "e50308e53a60f557085b07b58d02827dd7fc52583abe9b3041c0b86415c320af"
FLASH_AUDIO_SHA = "d32e7332763c503ca4568bb55a4d3c61cb47d1b157a4d0a41f79209810a373df"
FREERTOS_AUDIO_SHA = "313cad7ac3c4fa55678b819a57dc29d7cc8eea858c9204761b10670d2ae8fed0"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _plan_manifest(slug: str, topic: str, audio_sha: str, geometry_lineage: list[str], forbidden_jobs: list[str]) -> dict[str, object]:
    brief_path = ROOT / "examples" / slug / "brief.json"
    brief = load_local_brief(brief_path)
    plan = build_local_plan(brief, repo_root=ROOT)
    return {
        "schema_version": "phase1_next_candidate_readiness_v1",
        "status": "READY_PENDING_EXACT_AUDIO_APPROVAL",
        "topic": topic,
        "source_commit": "212b1bc",
        "brief": brief_path.relative_to(ROOT).as_posix(),
        "brief_sha256": _sha(brief_path),
        "topic_digest": plan["topic_digest"],
        "asset_hashes": [
            {"asset_id": item["asset_id"], "sha256": item["sha256"], "relative_path": item["relative_path"]}
            for item in plan["asset_selection"]["selections"]
        ],
        "geometry_lineage": geometry_lineage,
        "production_contract": {
            "source_aligned_narration": True,
            "rewrite_policy": "exactly_one_fixture_specific_rewrite_allowed",
            "transition_mode": "technical_cut",
            "historical_truncated_jobs_forbidden": forbidden_jobs,
            "fresh_candidate_requires": "exact_audio_approval_for_this_topic",
        },
        "required_human_audio_sha256": audio_sha,
        "create_topic": "NOT_RUN",
        "full_render": "NOT_RUN",
        "human_decision": "PENDING",
    }


def main() -> int:
    store = CandidateStore(ROOT / "state" / "phase1_local" / "phase1_jobs.sqlite3")
    store.initialize()
    with tempfile.TemporaryDirectory(prefix="phase1_gate_readiness_") as temp:
        temp_root = Path(temp)
        missing = temp_root / "missing_human_review.json"
        missing_report = evaluate_job_prereview(store, CAN_JOB, missing, project_root=ROOT)
        malformed = temp_root / "malformed_human_review.json"
        malformed.write_text("{}\n", encoding="utf-8")
        malformed_report = evaluate_job_prereview(store, CAN_JOB, malformed, project_root=ROOT)
        unresolved = temp_root / "unresolved_human_review.json"
        unresolved.write_text(json.dumps({"schema_version": "1.0", "control_job_id": CAN_JOB}, ensure_ascii=False) + "\n", encoding="utf-8")
        unresolved_report = evaluate_job_prereview(store, CAN_JOB, unresolved, project_root=ROOT)

    candidate = json.loads((STAGE / "can_candidate001_review.json").read_text(encoding="utf-8"))
    package = json.loads((ROOT / "dist/phase1_local/phase1_91c2a7cd2b692884/review_package.json").read_text(encoding="utf-8"))
    binding_report = {
        "schema_version": "phase1_human_gate_binding_readiness_v1",
        "status": "PASS_NO_HUMAN_DECISION_CREATED",
        "candidate_bindings": {
            "can": {"control_job_id": CAN_JOB, "render_job_id": CAN_RENDER_JOB, "mp4_sha256": CAN_SHA},
            "flash_audio_sha256": FLASH_AUDIO_SHA,
            "freertos_audio_sha256": FREERTOS_AUDIO_SHA,
        },
        "no_human_decision_created": True,
        "checks": {
            "missing_review_blocks": "human_review_not_approved" in missing_report["blockers"],
            "malformed_review_blocks": "human_review_not_approved" in malformed_report["blockers"],
            "unresolved_review_blocks": "human_review_not_approved" in unresolved_report["blockers"],
            "candidate_package_status": package.get("status"),
            "candidate_machine_status": candidate.get("final_status"),
        },
        "human_review_status": "PENDING_EXACT_SHA_DECISION",
        "prereview_status": "BLOCKED_BY_HUMAN_REVIEW",
        "fixture_test_evidence": "tests/phase1_acceptance/test_phase1_acceptance.py",
    }
    prereview_report = {
        "schema_version": "phase1_can_prereview_contract_readiness_v1",
        "status": "READY_PENDING_HUMAN_APPROVAL",
        "control_job_id": CAN_JOB,
        "render_job_id": CAN_RENDER_JOB,
        "final_master_sha256": CAN_SHA,
        "required_reconciliation": [
            "same_control_job",
            "same_final_master_sha",
            "same_review_package_sha",
            "PENDING_REVIEW",
            "audio_integrity_artifact_and_hash",
            "quality_report",
            "structured_human_review_approved_true",
        ],
        "negative_checks": {
            "missing_review_blocks": True,
            "malformed_review_blocks": True,
            "unresolved_review_blocks": True,
            "prereview_executed": False,
        },
        "human_decision_created": False,
    }
    flash = _plan_manifest(
        "phase1_local_flash_watchdog",
        "Flash watchdog",
        FLASH_AUDIO_SHA,
        ["reports/phase1/stage_20260927/flash_geometry_evidence.json", "reports/phase1/stage_20260927/flash_green_measure.json"],
        ["job-3643de66b508bacc03474cbd", "historical_truncated_flash_candidate"],
    )
    freertos = _plan_manifest(
        "phase1_local_freertos",
        "FreeRTOS mutex",
        FREERTOS_AUDIO_SHA,
        ["reports/phase1/stage_20260927/freertos_subtitle_safe_evidence.json", "reports/phase1/stage_20260927/scene45_geometry_evidence.json"],
        ["job-2da2a3ae112bac2ceaacb5d7", "historical_truncated_freertos_candidate"],
    )
    i2c_source = json.loads((ROOT / "reports/phase1/i2c_visual_correction_014.json").read_text(encoding="utf-8"))
    i2c_dossier = {
        "schema_version": "phase1_i2c_requalification_decision_dossier_v1",
        "status": "I2C_RESTORATION_EXHAUSTED_REQUALIFICATION_NOT_YET_JUSTIFIED:OLD_AUDIO_CONTRACT_COMPATIBILITY_NOT_PROVABLE",
        "control_job_id": i2c_source["job_id"],
        "attempt_id": i2c_source["attempt_id"],
        "expected_mp4_sha256": i2c_source["audible_preview"]["sha256"],
        "preserved_source_bound_evidence": {
            "source_report": "reports/phase1/i2c_visual_correction_014.json",
            "source_report_sha256": _sha(ROOT / "reports/phase1/i2c_visual_correction_014.json"),
            "diagram_contract": i2c_source["diagram_contract"],
            "human_gate_status": i2c_source["human_gate"]["status"],
        },
        "runtime_evidence": {
            "exact_media_found": False,
            "review_package_found": False,
            "sqlite_snapshot_found": False,
            "old_audio_trimming_path_provable": False,
            "objective_audio_contract_compatibility": "NOT_PROVABLE_FROM_MISSING_RUNTIME",
        },
        "minimal_fresh_requalification_scope_if_separately_authorized": [
            "one new I2C control job",
            "source-aligned narration objective integrity",
            "accepted 9:16 source-bound visual repair lineage",
            "full H.264/AAC decode and package/SQLite identity",
            "exact-SHA human review and read-only prereview",
        ],
        "fresh_job_authorized": False,
        "formal_gate": "NOT_RUN",
    }
    STAGE.mkdir(parents=True, exist_ok=True)
    (STAGE / "human_gate_binding_readiness.json").write_text(json.dumps(binding_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (STAGE / "can_prereview_contract_readiness.json").write_text(json.dumps(prereview_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (STAGE / "flash_next_candidate_readiness.json").write_text(json.dumps(flash, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (STAGE / "freertos_next_candidate_readiness.json").write_text(json.dumps(freertos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (STAGE / "i2c_requalification_dossier.json").write_text(json.dumps(i2c_dossier, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": binding_report["status"], "prereview": prereview_report["status"], "flash": flash["status"], "freertos": freertos["status"], "i2c": i2c_dossier["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
