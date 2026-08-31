"""Local-only Phase 1 job control around the canonical video pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.export import write_json

from .config import PROJECT_ROOT
from .db import CandidateStore
from .phase1_local import load_local_brief
from .openmontage_projection import project_job_read_only
from .phase1_subject_delivery import SubjectDeliveryRequest, build_subject_review_package, validate_subject_media_receipt
from .phase1_subject_media import SubjectMediaRequest, run_subject_media
from .phase1_topic import (
    build_director_script,
    build_research_brief,
    build_scene_plan,
    build_topic_request,
    ingest_mpt_candidates,
    select_candidate,
    stable_subject_key,
)
from scripts.phase1_mpt_script_drafter import run_drafts as MPT_RUN_DRAFTS
from .state import next_state
from .reference_video import (
    POLICY_VERSION,
    REFERENCE_RUNTIME_ROOT,
    analyze_reference,
    brief_digest,
    build_original_brief,
    ingest_reference,
    load_reference_bundle,
    stable_reference_job_key,
    write_original_brief,
)


STATE_ROOT = PROJECT_ROOT / "state" / "phase1_local"
DATABASE_PATH = STATE_ROOT / "phase1_jobs.sqlite3"
INPUT_ROOT = STATE_ROOT / "inputs"
OPENMONTAGE_PROJECTS_ROOT = STATE_ROOT / "openmontage_projects"
SUBJECT_DELIVERY_ROOT = PROJECT_ROOT / "dist" / "phase1_local"


def _emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return code


def _parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="factory.py phase1")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    commands.add_parser("init-db")
    create = commands.add_parser("create-topic")
    create.add_argument("--brief", type=Path, required=True)
    create.add_argument("--idempotency-key")
    subject = commands.add_parser("create-subject")
    subject.add_argument("--subject", required=True)
    subject.add_argument("--duration", type=int, default=40)
    subject.add_argument("--aspect-ratio", choices=["16:9", "9:16"], default="16:9")
    subject.add_argument("--mascot-mode", choices=["off", "user_original_only"], default="off")
    subject.add_argument("--idempotency-key")
    attach = commands.add_parser("attach-research")
    attach.add_argument("--job-id", required=True)
    attach.add_argument("--research", type=Path, required=True)
    reference = commands.add_parser("create-reference")
    reference.add_argument("--video", type=Path, required=True)
    reference.add_argument("--brief", type=Path, required=True)
    reference.add_argument("--rights", type=Path, required=True)
    reference.add_argument("--idempotency-key")
    run = commands.add_parser("run")
    run.add_argument("--job-id", required=True)
    run.add_argument("--plan-only", action="store_true", help="Local-subject diagnostic: stop after the ASSETS plan.")
    status = commands.add_parser("status")
    status.add_argument("--job-id", required=True)
    cancel = commands.add_parser("cancel")
    cancel.add_argument("--job-id", required=True)
    retry = commands.add_parser("retry")
    retry.add_argument("--job-id", required=True)
    return root


def _store() -> CandidateStore:
    store = CandidateStore(DATABASE_PATH)
    store.initialize()
    return store


def _persist_brief(brief: dict[str, Any]) -> Path:
    digest = str(brief["factual_brief"]["topic_digest"])
    target = INPUT_ROOT / f"{digest}.json"
    if target.exists() and target.is_symlink():
        raise FactoryContractError(
            "phase1_input_path_invalid",
            "Phase 1 input storage cannot be a link.",
            {"reason": "reparse"},
        )
    write_json(target, brief)
    return target


def _create_topic(args: argparse.Namespace) -> dict[str, Any]:
    brief = load_local_brief(args.brief)
    persisted = _persist_brief(brief)
    digest = str(brief["factual_brief"]["topic_digest"])
    key = args.idempotency_key or f"phase1-topic:{digest}"
    store = _store()
    result = store.create_job(
        "local_topic",
        key,
        "video_factory_local_brief",
        str(brief["topic"]),
        requested_duration_seconds=int(brief.get("duration_target_seconds", 40)),
        metadata={
            "brief_path": persisted.relative_to(PROJECT_ROOT).as_posix(),
            "topic_digest": digest,
            "input_mode": str(brief["input_mode"]),
        },
    )
    return {"status": "created" if result["created"] else "existing", "job": result}


def _subject_root(job_id: str) -> Path:
    return INPUT_ROOT / "subjects" / job_id


def _project_if_subject(store: CandidateStore, job: dict[str, Any]) -> None:
    if job.get("fixture_id") == "local_subject":
        project_job_read_only(store, str(job["job_id"]), OPENMONTAGE_PROJECTS_ROOT)


def _create_subject(args: argparse.Namespace) -> dict[str, Any]:
    request = build_topic_request(subject=args.subject, duration=args.duration, aspect=args.aspect_ratio, mascot=args.mascot_mode)
    canonical = stable_subject_key(request)
    key = canonical
    store = _store()
    result = store.create_job("local_subject", key, "phase1_subject_plan", request["subject"], requested_duration_seconds=request["duration"], metadata={"pipeline_type": "phase1-local-topic", "input_mode": "local_subject", "topic_digest": hashlib.sha256(request["subject"].casefold().encode("utf-8")).hexdigest(), "canonical_subject_key": canonical, "requested_idempotency_key": args.idempotency_key, "topic_request_path": "pending", "subject_input_root": "pending"})
    root = _subject_root(result["job_id"])
    root.mkdir(parents=True, exist_ok=True)
    request_path = root / "topic_request.json"
    if not request_path.exists():
        write_json(request_path, request)
    # Paths are deterministic and supplied in the response; SQLite remains the state authority.
    result["metadata"]["topic_request_path"] = request_path.relative_to(PROJECT_ROOT).as_posix()
    result["metadata"]["subject_input_root"] = root.relative_to(PROJECT_ROOT).as_posix()
    if result["created"]:
        updated = store.update_metadata(result["job_id"], result["metadata"])
        result = {**updated, "created": True}
    _project_if_subject(store, result)
    return {"status": "created" if result["created"] else "existing", "job": result, "topic_request_path": request_path.relative_to(PROJECT_ROOT).as_posix()}


def _read_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FactoryContractError("phase1_topic_contract_invalid", "Phase 1 document must be an object.", {})
    return value


def _attach_research(args: argparse.Namespace) -> dict[str, Any]:
    store = _store()
    job = store.status(args.job_id)
    if job["fixture_id"] != "local_subject":
        raise FactoryContractError("phase1_topic_contract_invalid", "Research can only be attached to a local subject job.", {})
    source = args.research.resolve()
    if not source.is_file() or source.is_symlink():
        raise FactoryContractError("phase1_input_path_invalid", "Research input must be a regular JSON file.", {})
    raw = _read_json_object(source)
    research = build_research_brief(topic=str(raw.get("topic", "")), sources=raw.get("sources", []), facts=raw.get("facts", []), comparables=raw.get("comparables", []))
    request = _read_json_object(_subject_root(args.job_id) / "topic_request.json")
    expected_digest = str(job["metadata"].get("topic_digest", ""))
    if research["topic"] != request["subject"] or research["topic_digest"] != expected_digest:
        raise FactoryContractError("phase1_research_topic_mismatch", "Research topic is not bound to this subject job.", {"job_id": args.job_id})
    target = _subject_root(args.job_id) / "research_brief.json"
    write_json(target, research)
    store.record_artifact(args.job_id, "research_brief", target.relative_to(PROJECT_ROOT).as_posix(), hashlib.sha256(target.read_bytes()).hexdigest())
    project_job_read_only(store, args.job_id, OPENMONTAGE_PROJECTS_ROOT)
    return {"status": "research_attached", "job": store.status(args.job_id), "research_path": target.relative_to(PROJECT_ROOT).as_posix()}


def _record_json_artifact(store: CandidateStore, job_id: str, kind: str, path: Path, value: dict[str, Any]) -> None:
    write_json(path, value)
    store.record_artifact(job_id, kind, path.relative_to(PROJECT_ROOT).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())


def _run_subject(store: CandidateStore, job: dict[str, Any]) -> dict[str, Any]:
    job_id = str(job["job_id"])
    if job["state"] == "ASSETS":
        return {"status": "subject_plan_ready", "job": job, "artifacts": store.artifacts(job_id), "idempotent": True}
    root = _subject_root(job_id)
    request_path, research_path = root / "topic_request.json", root / "research_brief.json"
    if not request_path.is_file() or not research_path.is_file():
        raise FactoryContractError("phase1_research_required", "Validated research must be attached before running a subject job.", {})
    request = build_topic_request(**{ "subject": _read_json_object(request_path)["subject"], "duration": _read_json_object(request_path)["duration"], "aspect": _read_json_object(request_path)["aspect"], "language": _read_json_object(request_path)["language"], "mascot": _read_json_object(request_path)["mascot"]})
    raw = _read_json_object(research_path)
    research = build_research_brief(topic=raw["topic"], sources=raw["sources"], facts=raw["facts"], comparables=raw.get("comparables", []))
    if research["topic"] != request["subject"] or research["topic_digest"] != str(job["metadata"].get("topic_digest", "")):
        raise FactoryContractError("phase1_research_topic_mismatch", "Persisted research is not bound to this subject job.", {"job_id": job_id})
    while job["state"] != "SCRIPTING":
        target = next_state(job["state"])
        if target is None:
            raise FactoryContractError("phase1_job_state_invalid", "Subject job cannot advance to scripting.", {"state": job["state"]})
        job = store.advance(job_id, target, reason="subject_research_validated")
        _project_if_subject(store, job)
    candidates = None
    selected = None
    rewrite_guidance = None
    research_guidance = "；".join(f"{fact['claim']} [fact={fact['id']};sources={','.join(fact['source_ids'])}]" for fact in research["facts"])
    for rewrite_attempt in (0, 1):
        mpt_path = MPT_RUN_DRAFTS(subject=request["subject"], language="zh-CN", paragraphs=2, candidates=3, timeout_seconds=120.0, rewrite_guidance=rewrite_guidance, research_guidance=research_guidance)
        candidates = ingest_mpt_candidates(Path(mpt_path))
        try:
            selected = select_candidate(candidates, research, rewrite_attempt=rewrite_attempt,
                                        duration_target_seconds=int(request["duration"]))
            break
        except FactoryContractError as exc:
            if exc.context.get("reason") != "selection_threshold_not_met" or rewrite_attempt == 1:
                raise
            dimensions = ",".join(map(str, exc.context.get("failed_dimensions", [])))
            duration_guidance = str(exc.context.get("duration_guidance") or "")
            rewrite_guidance = f"候选{exc.context.get('best_candidate')}总分{exc.context.get('best_score')}；改进维度：{dimensions}；必须包含完整已核验 claim 锚点，禁止否定或反转 claim；{duration_guidance}并重写。"
    if candidates is None or selected is None:  # pragma: no cover - loop is exhaustive
        raise FactoryContractError("phase1_topic_contract_invalid", "Subject selection failed closed.", {})
    director = build_director_script(request, research, selected)
    scene_plan = build_scene_plan(director, research)
    for kind, value in (("script_candidates", candidates), ("selected_script", selected), ("director_script", director), ("scene_plan", scene_plan)):
        _record_json_artifact(store, job_id, kind, root / f"{kind}.json", value)
    while job["state"] != "ASSETS":
        target = next_state(job["state"])
        if target is None:
            raise FactoryContractError("phase1_job_state_invalid", "Subject job cannot advance to assets.", {"state": job["state"]})
        job = store.advance(job_id, target, reason="subject_plan_completed")
        _project_if_subject(store, job)
    project_job_read_only(store, job_id, OPENMONTAGE_PROJECTS_ROOT)
    return {"status": "subject_plan_ready", "job": job, "artifacts": store.artifacts(job_id)}


def _create_reference(args: argparse.Namespace) -> dict[str, Any]:
    user_brief = load_local_brief(args.brief)
    if user_brief.get("input_mode") != "topic":
        raise FactoryContractError(
            "reference_brief_invalid",
            "create-reference requires a topic-mode user brief; the original brief is generated by the analyzer.",
            {"field": "input_mode"},
        )
    bundle = ingest_reference(args.video, args.rights)
    report = analyze_reference(bundle)
    original = build_original_brief(user_brief, report)
    original_path = write_original_brief(bundle, original)
    source_sha = str(bundle["source_sha256"])
    canonical_key = stable_reference_job_key(source_sha, original)
    render_job_digest = hashlib.sha256(canonical_key.encode("utf-8")).hexdigest()[:24]
    render_job_id = f"phase1_ref_{render_job_digest}"
    requested_duration = int(original["reference_abstraction"]["duration_target_seconds"])
    runtime_root = Path(bundle["runtime_root"])
    metadata = {
        "brief_path": original_path.relative_to(PROJECT_ROOT).as_posix(),
        "runtime_root": runtime_root.relative_to(PROJECT_ROOT).as_posix(),
        "reference_id": str(bundle["reference_id"]),
        "source_sha256": source_sha,
        "brief_digest": brief_digest(original),
        "analyzer_policy_version": POLICY_VERSION,
        "analysis_verified": True,
        "render_job_id": render_job_id,
        "requested_idempotency_key": args.idempotency_key,
        "input_mode": "local_reference",
    }
    store = _store()
    result = store.create_job(
        "local_reference",
        canonical_key,
        "video_factory_local_reference",
        str(original["topic"]),
        requested_duration_seconds=requested_duration,
        metadata=metadata,
    )
    return {
        "status": "created" if result["created"] else "existing",
        "job": result,
        "reference": {
            "reference_id": bundle["reference_id"],
            "source_sha256": source_sha,
            "report": (runtime_root / "reference_report.json").relative_to(PROJECT_ROOT).as_posix(),
            "original_brief": original_path.relative_to(PROJECT_ROOT).as_posix(),
        },
    }


def _advance_to_rendering(store: CandidateStore, job_id: str) -> dict[str, Any]:
    job = store.status(job_id)
    while job["state"] != "RENDERING":
        target = next_state(str(job["state"]))
        if target is None:
            raise FactoryContractError(
                "phase1_job_state_invalid",
                "Phase 1 job cannot enter rendering from its current state.",
                {"state": str(job["state"])},
            )
        job = store.advance(job_id, target, reason="local_stage_completed")
    return job


def _subject_project(store: CandidateStore, job_id: str) -> dict[str, Any]:
    job = store.status(job_id)
    _project_if_subject(store, job)
    return job


def _subject_delivery_base(job_id: str) -> Path:
    return SUBJECT_DELIVERY_ROOT / f"phase1_subject_{job_id.rsplit('-', 1)[-1]}"


def _subject_metadata_path(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def _subject_media_root(job: dict[str, Any]) -> Path | None:
    raw = job.get("metadata", {}).get("subject_media_root")
    if not isinstance(raw, str) or not raw:
        return None
    candidate = (PROJECT_ROOT / raw).resolve()
    try:
        candidate.relative_to(SUBJECT_DELIVERY_ROOT.resolve())
    except ValueError:
        return None
    return candidate


def _subject_cancelled(store: CandidateStore, job_id: str) -> bool:
    return store.status(job_id)["state"] == "CANCELLED"


def _subject_blocked(store: CandidateStore, job_id: str, reason: str) -> dict[str, Any]:
    current = store.status(job_id)
    if current["state"] not in {"FAILED", "CANCELLED", "PENDING_REVIEW"}:
        current = store.fail(job_id, reason)
        _project_if_subject(store, current)
    return {"status": "review_blocked", "job": current, "artifacts": store.artifacts(job_id), "reason": reason}


def _subject_cancelled_result(store: CandidateStore, job_id: str) -> dict[str, Any]:
    return {"status": "cancelled", "job": store.status(job_id), "artifacts": store.artifacts(job_id)}


def _withdraw_subject_ready_manifest(result: dict[str, Any]) -> None:
    ready = Path(str(result.get("review_package", ""))).resolve()
    if ready.name != "review_package.json" or ready.is_symlink() or not ready.is_file():
        return
    try:
        ready.relative_to(SUBJECT_DELIVERY_ROOT.resolve())
    except ValueError:
        return
    digest = hashlib.sha256(ready.read_bytes()).hexdigest()
    ready.unlink()
    ready.with_name("review_package.cancelled.json").write_text(json.dumps({"schema_version": "1.0", "status": "cancelled_before_publication", "withdrawn_ready_manifest": "review_package.json", "withdrawn_sha256": digest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run_subject_delivery(store: CandidateStore, job: dict[str, Any]) -> dict[str, Any]:
    """Resume only ASSETS/RENDERING/QUALITY_CHECK; all outputs are attempt-scoped."""
    job_id = str(job["job_id"])
    if _subject_cancelled(store, job_id):
        return {"status": "cancelled", "job": store.status(job_id), "artifacts": store.artifacts(job_id)}
    root = _subject_root(job_id)
    request_path = root / "topic_request.json"
    try:
        topic = _read_json_object(request_path)
    except Exception:
        return _subject_blocked(store, job_id, "phase1_subject_topic_request_invalid")
    base = _subject_delivery_base(job_id)
    media_root = _subject_media_root(job)
    state = str(job["state"])
    if state in {"ASSETS", "RENDERING"}:
        reusable = False
        if media_root is not None:
            try:
                validate_subject_media_receipt(media_root)
                reusable = True
            except ValueError:
                reusable = False
        if not reusable:
            render_attempt = store.start_stage_attempt(job_id, "RENDERING")
            media_root = base / f"attempt_{render_attempt}" / "media"
            metadata = dict(store.status(job_id)["metadata"])
            metadata.update({"subject_media_root": _subject_metadata_path(media_root), "subject_media_attempt": render_attempt})
            store.update_metadata(job_id, metadata)
            _subject_project(store, job_id)
            if state == "ASSETS":
                advanced = store.advance(job_id, "RENDERING", reason="subject_media_started")
                _project_if_subject(store, advanced)
            try:
                run_subject_media(SubjectMediaRequest(root / "director_script.json", root / "scene_plan.json", request_path, media_root))
                store.complete_stage_attempt(job_id, "RENDERING", render_attempt, "passed", {"media_root": _subject_metadata_path(media_root), "evidence_kind": "real_media_required"})
            except Exception:
                try:
                    store.complete_stage_attempt(job_id, "RENDERING", render_attempt, "failed", {"media_root": _subject_metadata_path(media_root), "evidence_kind": "media_failure_preserved"})
                except ValueError:
                    pass
                return _subject_blocked(store, job_id, "phase1_subject_media_failed")
        if _subject_cancelled(store, job_id):
            return {"status": "cancelled", "job": store.status(job_id), "artifacts": store.artifacts(job_id)}
        current = store.status(job_id)
        if current["state"] == "RENDERING":
            current = store.advance(job_id, "QUALITY_CHECK", reason="subject_media_receipt_verified")
            _project_if_subject(store, current)
        job = current
    if str(job["state"]) != "QUALITY_CHECK" or media_root is None:
        return _subject_blocked(store, job_id, "phase1_subject_delivery_state_invalid")
    try:
        validate_subject_media_receipt(media_root)
        quality_attempt = store.start_stage_attempt(job_id, "QUALITY_CHECK")
        result = build_subject_review_package(SubjectDeliveryRequest(job_id, quality_attempt, root, media_root, base, int(topic["duration"]), str(topic["aspect"])), cancel_requested=lambda: _subject_cancelled(store, job_id))
        store.complete_stage_attempt(job_id, "QUALITY_CHECK", quality_attempt, "passed", {"review_package": _subject_metadata_path(Path(result["review_package"])), "evidence_kind": "review_package"})
    except Exception:
        if _subject_cancelled(store, job_id):
            try:
                store.complete_stage_attempt(job_id, "QUALITY_CHECK", quality_attempt, "cancelled", {"evidence_kind": "cancelled_before_ready_manifest"})
            except (UnboundLocalError, ValueError):
                pass
            return _subject_cancelled_result(store, job_id)
        try:
            store.complete_stage_attempt(job_id, "QUALITY_CHECK", quality_attempt, "failed", {"media_root": _subject_metadata_path(media_root), "evidence_kind": "review_blocked"})
        except (UnboundLocalError, ValueError):
            pass
        return _subject_blocked(store, job_id, "phase1_subject_delivery_failed")
    if _subject_cancelled(store, job_id):
        _withdraw_subject_ready_manifest(result)
        return _subject_cancelled_result(store, job_id)
    for artifact_type, value in {"final_master": result["preview"], "review_package": result["review_package"], "media_receipt": result["media_receipt"]}.items():
        path = Path(str(value)).resolve()
        store.record_artifact(job_id, artifact_type, _subject_metadata_path(path), hashlib.sha256(path.read_bytes()).hexdigest())
    _subject_project(store, job_id)
    final_job = store.advance(job_id, "PENDING_REVIEW", reason="subject_review_package_ready")
    _project_if_subject(store, final_job)
    return {"status": "pending_review", "job": final_job, "artifacts": store.artifacts(job_id), "result": result}


def _run_job(args: argparse.Namespace) -> dict[str, Any]:
    store = _store()
    job = store.status(args.job_id)
    if job["state"] == "PENDING_REVIEW":
        return {
            "status": "pending_review",
            "job": job,
            "artifacts": store.artifacts(args.job_id),
            "idempotent": True,
        }
    if job["state"] in {"FAILED", "CANCELLED"}:
        raise FactoryContractError(
            "phase1_job_retry_required",
            "A failed or cancelled Phase 1 job must be retried explicitly.",
            {"state": str(job["state"])},
        )
    if job["fixture_id"] == "local_subject":
        if job["state"] in {"NEW", "RESEARCHING", "SCRIPTING", "VOICE", "CAPTIONS"}:
            try:
                planned = _run_subject(store, job)
            except Exception:
                current = store.status(args.job_id)
                if current["state"] not in {"FAILED", "CANCELLED", "PENDING_REVIEW"}:
                    current = store.fail(args.job_id, "phase1_subject_planning_failed")
                    _project_if_subject(store, current)
                raise
            if args.plan_only:
                return planned
            job = store.status(args.job_id)
        if args.plan_only:
            return {"status": "subject_plan_ready", "job": job, "artifacts": store.artifacts(args.job_id), "idempotent": True}
        return _run_subject_delivery(store, job)
    from generate_video import run_local_brief
    metadata = dict(job["metadata"])
    brief_ref = str(metadata.get("brief_path", ""))
    brief_path = (PROJECT_ROOT / brief_ref).resolve()
    if PROJECT_ROOT.resolve() not in brief_path.parents or not brief_path.is_file():
        raise FactoryContractError(
            "phase1_input_path_invalid",
            "The persisted Phase 1 brief is unavailable.",
            {"reason": "missing"},
        )
    _advance_to_rendering(store, args.job_id)
    try:
        reference_bundle = None
        reference_context = None
        if str(metadata.get("input_mode", "")) == "local_reference":
            runtime_ref = str(metadata.get("runtime_root", ""))
            runtime_root = (PROJECT_ROOT / runtime_ref).resolve()
            reference_bundle = load_reference_bundle(runtime_root, expected_source_sha256=str(metadata.get("source_sha256", "")))
            reference_bundle["job_id"] = str(metadata.get("render_job_id", ""))
            reference_context = {
                "source_sha256": str(metadata.get("source_sha256", "")),
                "policy_version": str(metadata.get("analyzer_policy_version", "")),
                "analysis_verified": bool(metadata.get("analysis_verified", False)),
            }
        result = run_local_brief(
            brief_path,
            emit=False,
            reference_context=reference_context,
            reference_bundle=reference_bundle,
        )
        store.advance(args.job_id, "QUALITY_CHECK", reason="local_render_completed")
        final_job = store.advance(args.job_id, "PENDING_REVIEW", reason="local_quality_passed")
        for artifact_type, value in {
            "final_master": result["output"],
            "review_package": result["review_package"],
        }.items():
            path = Path(str(value)).resolve()
            store.record_artifact(
                args.job_id,
                artifact_type,
                path.relative_to(PROJECT_ROOT).as_posix(),
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        return {
            "status": "pending_review",
            "job": final_job,
            "artifacts": store.artifacts(args.job_id),
            "result": result,
        }
    except Exception:
        current = store.status(args.job_id)
        if current["state"] not in {"FAILED", "CANCELLED", "PENDING_REVIEW"}:
            store.fail(args.job_id, "phase1_local_execution_failed")
        raise


def main(arguments: list[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    try:
        if args.command == "doctor":
            return _emit(
                {
                    "status": "ok",
                    "mode": "phase1_local_only",
                    "canonical_video_entrypoint": "generate_video.py --local-brief",
                    "database": DATABASE_PATH.relative_to(PROJECT_ROOT).as_posix(),
                    "provider_enabled": False,
                    "feishu_enabled": False,
                    "cron_enabled": False,
                }
            )
        if args.command == "init-db":
            _store()
            return _emit({"status": "initialized", "database": DATABASE_PATH.relative_to(PROJECT_ROOT).as_posix()})
        if args.command == "create-topic":
            return _emit(_create_topic(args))
        if args.command == "create-subject":
            return _emit(_create_subject(args))
        if args.command == "attach-research":
            return _emit(_attach_research(args))
        if args.command == "create-reference":
            return _emit(_create_reference(args))
        if args.command == "run":
            return _emit(_run_job(args))
        if args.command == "status":
            store = _store()
            return _emit(
                {
                    "status": "ok",
                    "job": store.status(args.job_id),
                    "events": store.events(args.job_id),
                    "artifacts": store.artifacts(args.job_id),
                }
            )
        if args.command == "cancel":
            store = _store()
            job = store.cancel(args.job_id, "user_requested")
            _project_if_subject(store, job)
            return _emit({"status": "cancelled", "job": job})
        if args.command == "retry":
            store = _store()
            job = store.retry(args.job_id, "user_requested")
            _project_if_subject(store, job)
            return _emit({"status": "retry_ready", "job": job})
    except FactoryContractError as exc:
        return _emit({"status": "error", "error": exc.to_dict()}, 2)
    except KeyError:
        return _emit(
            {
                "status": "error",
                "error": {
                    "code": "phase1_job_not_found",
                    "message": "The Phase 1 job was not found.",
                    "context": {},
                },
            },
            2,
        )
    except (OSError, ValueError, RuntimeError):
        return _emit(
            {
                "status": "error",
                "error": {
                    "code": "phase1_local_execution_failed",
                    "message": "The local Phase 1 operation failed.",
                    "context": {},
                },
            },
            2,
        )
    raise AssertionError(f"unsupported_command:{args.command}")


__all__ = ["main"]
