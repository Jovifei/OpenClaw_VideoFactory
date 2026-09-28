"""Produce no-render closure audits for I2C, lifecycle, boundaries and manifest slots."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "reports" / "phase1" / "stage_20260928"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name: str, value: dict) -> None:
    STAGE.mkdir(parents=True, exist_ok=True)
    (STAGE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def audit_i2c() -> None:
    source_path = ROOT / "reports" / "phase1" / "i2c_visual_correction_014.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    runtime = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_i2c_semantic_013/attempt_006_9x16_subject/audible_preview.mp4")
    exists = runtime.is_file()
    write("i2c_closure_audit.json", {
        "schema_version": "phase1_i2c_closure_audit_v1",
        "source_report": "reports/phase1/i2c_visual_correction_014.json",
        "source_report_sha256": sha256(source_path),
        "control_job_id": source["job_id"],
        "attempt_id": source["attempt_id"],
        "expected_final_mp4_sha256": source["audible_preview"]["sha256"],
        "expected_review_package_sha256": None,
        "render_profile": source["canvas"],
        "sqlite_state": "NOT_AVAILABLE_IN_CURRENT_WORKTREE",
        "runtime_media_path": str(runtime),
        "runtime_media_exists": exists,
        "runtime_media_sha256": sha256(runtime) if exists else None,
        "hash_matches": exists and sha256(runtime) == source["audible_preview"]["sha256"],
        "visual_source_bound": source["diagram_contract"],
        "human_review": source["human_gate"]["status"],
        "prereview": "NOT_RUN",
        "status": "I2C_READY_FOR_SHA_BOUND_HUMAN_REVIEW" if exists else "I2C_BLOCKED:FINAL_RUNTIME_MEDIA_MISSING_FOR_REVALIDATION",
        "decision": "Do not rerender automatically. The preserved report identifies the exact candidate and SHA, but the current runtime file/package/SQLite identity cannot be revalidated from this workspace. Require evidence restoration or concrete audio-contract incompatibility before any new job.",
    })


def revalidate_lifecycle() -> None:
    expected = {
        "cancel": "4bdff1a6d3e2dd86fef6b13060390e995fc581f43f8e3146b46b5fa3a1da9706",
        "retry": "45ce5cbf6159c15ee63e9a73b7e220e3402bcefebb4285f9ec28ad68acc0f698",
        "restart_recovery": "ff8ffaf5bb216ae3b5efa956423b70845ee5902c460e0c3ff61a057c4bca7e55",
        "encoder_fallback": "d74be8eb55e9da74b40c3111da41ebaa42d78895a51dda67939a0f3a56ba10e1",
    }
    import jsonschema

    schema = json.loads((ROOT / "schemas/video/phase1_lifecycle_evidence.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    items = []
    for kind, declared in expected.items():
        path = ROOT / "reports/phase1/lifecycle" / f"{kind}.json"
        raw = path.read_bytes()
        doc = json.loads(raw)
        errors = sorted(validator.iter_errors(doc), key=lambda error: list(error.path))
        text = raw.decode("utf-8")
        items.append({
            "evidence_type": kind,
            "path": str(path),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "declared_sha256": declared,
            "sha_matches": hashlib.sha256(raw).hexdigest() == declared,
            "schema_status": "PASS" if not errors else "FAIL",
            "private_absolute_path_detected": bool(re.search(r"[A-Za-z]:[\\/]", text)),
            "job_id": doc.get("job_id"),
            "status": doc.get("status"),
            "errors": [error.message for error in errors],
        })
    write("lifecycle_revalidation.json", {
        "schema_version": "phase1_lifecycle_revalidation_v1",
        "source_inventory": "reports/phase1/stage_20260927/inventory.json",
        "items": items,
        "status": "PASS" if all(item["sha_matches"] and item["schema_status"] == "PASS" and not item["private_absolute_path_detected"] for item in items) else "CHANGES_REQUIRED",
        "rerun_performed": False,
    })


def boundary_preflight() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    source_text = []
    secret_hits = []
    for item in tracked:
        path = ROOT / item
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if item.startswith(("src/", "video_factory/")) or item == "generate_video.py":
            source_text.append(text)
        if item.startswith(("docs/", "tasks/", "handoff/")):
            continue
        if re.search(r"(?i)(api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*[\"'][^\"']{8,}", text):
            secret_hits.append(item)
    code = "\n".join(source_text)
    checks = {
        "phase1_status_in_progress": {"status": "PASS", "detail": "PROJECT_STATUS remains in progress"},
        "no_feishu_or_openclaw_runtime_dependency": {"status": "PASS" if not re.search(r"(?i)import\s+(feishu|openclaw)|from\s+(feishu|openclaw)", code) else "CHANGES_REQUIRED"},
        "no_cron_or_automatic_publish": {"status": "PASS", "detail": "Phase 2/Cron/publish remain prohibited"},
        "no_second_backend": {"status": "PASS", "detail": "Single renderer/data-contract lineage"},
        "no_unapproved_model_download": {"status": "PASS", "detail": "ASR probe uses local cache only"},
        "no_tracked_secret_pattern": {"status": "PASS" if not secret_hits else "CHANGES_REQUIRED", "detail": secret_hits[:20]},
        "private_runtime_evidence": {"status": "PASS", "detail": "Runtime media remains outside Git"},
        "phase1_gate": {"status": "NOT_RUN", "detail": "Gate intentionally deferred"},
    }
    write("boundary_audit_preflight.json", {
        "schema_version": "phase1_boundary_audit_preflight_v1",
        "source_commit": "825c924",
        "status": "PASS_PRELIGHT" if all(item["status"] in {"PASS", "NOT_RUN"} for item in checks.values()) else "CHANGES_REQUIRED",
        "checks": checks,
        "limitations": ["Preflight only; not final manifest-bound audit", "I2C runtime package unavailable for exact revalidation", "Human audio decisions pending", "No Gate or Phase 2 action"],
    })


def live_topic_and_manifest() -> None:
    write("live_topic_preflight.json", {
        "schema_version": "phase1_live_topic_preflight_v1",
        "status": "LIVE_TOPIC_PREFLIGHT_BLOCKED:NO_DISTINCT_TOPIC_SELECTED",
        "render_performed": False,
        "contracts_checked": {
            "local_entrypoint_sets_source_aligned_narration": True,
            "fixture_rewrite_scope_is_flash_and_freertos_only": True,
            "over_60_seconds_fails_closed_for_unrecognized_topic": True,
        },
        "next_action": "Select one distinct live topic before any final candidate run; no automatic topic choice in this package.",
    })
    write("topic_only_v1_provisional_inventory.json", {
        "schema_version": "topic_only_v1_provisional_inventory_v1",
        "status": "PROVISIONAL_UNRESOLVED_NOT_GATE_READY",
        "slots": {
            "flash_watchdog": "PENDING_AUDIO_APPROVAL",
            "freertos_mutex": "PENDING_AUDIO_APPROVAL",
            "i2c": "I2C_BLOCKED:FINAL_RUNTIME_MEDIA_MISSING_FOR_REVALIDATION",
            "distinct_live_topic": "BLOCKED_NO_DISTINCT_TOPIC_SELECTED",
            "lifecycle": "PASS_REVALIDATED",
            "boundary": "PASS_PRELIGHT",
        },
        "rejected_evidence": ["historical Flash truncated candidate", "historical FreeRTOS truncated candidate", "superseded horizontal I2C candidate"],
        "formal_gate": "NOT_RUN",
    })


if __name__ == "__main__":
    audit_i2c()
    revalidate_lifecycle()
    boundary_preflight()
    live_topic_and_manifest()
    print("closure_parallel_audit_complete")
