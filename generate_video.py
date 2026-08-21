"""Run the local pink-pig image-to-MP4 MVP without any OpenClaw dependency.

Supports two modes:
  --config  Legacy mode (directory-scan driven, unchanged behavior)
  --job     New mode (storyboard-driven, Phase 1 productization)
  --local-brief  Deterministic local topic brief → Phase 1 review package
  --topic   Director mode (topic → Storyboard → existing Video Factory)
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml

from video_factory.pipeline.asset_loader import build_asset_manifest
from video_factory.pipeline.export import write_json
from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.failure_contract import sanitize_error_payload, sanitize_reason, sanitize_stage
from video_factory.pipeline.renderer import render_video
from video_factory.pipeline.render_report import build_render_report
from video_factory.pipeline.subtitle import build_srt, build_srt_from_timeline
from video_factory.pipeline.timeline import build_timeline, to_render_timeline
from video_factory.pipeline.mascot import load_mascot_contract


ROOT = Path(__file__).resolve().parent


def load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError("config_missing")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("config_invalid")
    required = {"asset_dir", "script", "output", "image_duration_seconds", "transition_seconds", "transitions"}
    if not required.issubset(value):
        raise ValueError("config_required_field_missing")
    return value


def resolve(config_path: Path, value: str) -> Path:
    return (config_path.parent / value).resolve()


# ---------------------------------------------------------------------------
# Legacy --config mode (unchanged)
# ---------------------------------------------------------------------------

def run(config_path: Path) -> dict[str, object]:
    config_path = config_path.resolve()
    config = load_config(config_path)
    asset_dir = resolve(config_path, str(config["asset_dir"]))
    output_path = (ROOT / str(config["output"])).resolve()
    manifest_path = (ROOT / str(config.get("asset_manifest", "dist/asset_manifest.json"))).resolve()
    timeline_path = (ROOT / str(config.get("timeline", "dist/video_timeline.json"))).resolve()
    subtitle_path = (ROOT / str(config.get("subtitle", "dist/subtitle.srt"))).resolve()
    audio_value = config.get("audio")
    audio_path = resolve(config_path, str(audio_value)) if audio_value else None
    mascot_contract = load_mascot_contract(ROOT, config.get("mascot"))
    manifest = build_asset_manifest(asset_dir)
    timeline = build_timeline(
        manifest,
        duration_seconds=float(config["image_duration_seconds"]),
        transitions=list(config["transitions"]),
    )
    wrap_value = config.get("subtitle_max_chars_per_line")
    wrap_chars = int(wrap_value) if wrap_value is not None else None
    captions = build_srt(
        resolve(config_path, str(config["script"])),
        timeline,
        subtitle_path,
        transition_seconds=float(config["transition_seconds"]),
        max_chars_per_line=wrap_chars,
        max_lines=2,
    )
    write_json(manifest_path, manifest)
    write_json(timeline_path, timeline)
    audio_mode = "file" if audio_path is not None else "silent"
    audio_loop = True
    audio_fallback_reason = None
    if config.get("audio_mode") == "tts_with_offline_fallback":
        from video_factory.pipeline.audio_planner import plan_audio

        audio_cfg = dict(config.get("audio_config", {}))
        audio_cfg.setdefault("strategy", "tts_with_offline_fallback")
        audio_cfg.setdefault("allow_network", True)
        audio_cfg.setdefault("fallback_bgm", "assets/pink_pig/demo_music.wav")
        narration_doc = {
            "total_duration_seconds": sum(float(item["duration"]) for item in timeline)
            - float(config["transition_seconds"]) * (len(timeline) - 1),
            "scenes": [
                {
                    "scene_id": f"s{index:02d}",
                    "duration": float(item["duration"]),
                    "narration": str(captions[index - 1]["text"]).replace("\n", " "),
                }
                for index, item in enumerate(timeline, start=1)
            ],
        }
        audio_work_dir = ROOT / str(config.get("audio_work_dir", "dist/audio_work"))
        audio_plan = plan_audio(
            narration_doc,
            work_dir=audio_work_dir,
            audio_config=audio_cfg,
            repo_root=ROOT,
        )
        audio_path = audio_plan.path
        audio_loop = audio_plan.loop
        audio_mode = audio_plan.mode
        audio_fallback_reason = audio_plan.fallback_reason
    subtitle_style = config.get("subtitle_style")
    if subtitle_style is not None and not isinstance(subtitle_style, dict):
        raise ValueError("subtitle_style_invalid")
    render = render_video(
        asset_dir=asset_dir,
        timeline=timeline,
        subtitle_path=subtitle_path,
        output_path=output_path,
        transition_seconds=float(config["transition_seconds"]),
        audio_path=audio_path,
        audio_loop=audio_loop,
        subtitle_style=subtitle_style,
        audio_gain=float(config.get("audio_gain", 1.0)),
        audio_normalize=bool(config.get("audio_normalize", False)),
        audio_sample_rate=24000 if audio_mode == "tts" else (48000 if audio_path is not None else None),
    )
    result = {
        "manifest": str(manifest_path),
        "timeline": str(timeline_path),
        "subtitle": str(subtitle_path),
        "captions": len(captions),
        "audio_mode": audio_mode,
        "audio_fallback_reason": audio_fallback_reason,
        "mascot": mascot_contract,
        **render,
    }
    print(json.dumps(result, ensure_ascii=False))
    return result


def _relative_to_root(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def _load_director_job_defaults() -> dict[str, Any]:
    path = ROOT / "video_factory" / "configs" / "director_job.defaults.yaml"
    if not path.is_file():
        raise FactoryContractError(
            "director_context_invalid",
            "Director job defaults are unavailable.",
            {"field": "director_job_defaults", "reason": "missing"},
        )
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FactoryContractError(
            "director_context_invalid",
            "Director job defaults are invalid.",
            {"field": "director_job_defaults", "reason": "type"},
        )
    return value


def _safe_topic_file(path: Path) -> Path:
    """Resolve a topic file without allowing path escape from the repo."""

    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise FactoryContractError(
            "director_topic_invalid",
            "Topic file must remain inside the repository.",
            {"field": "topic_file", "reason": "path"},
        ) from exc
    return resolved


def _safe_output_name(value: str | None) -> str:
    name = str(value or "output.mp4")
    path = Path(name.replace("\\", "/"))
    if path.name != name or path.is_absolute() or ".." in path.parts or path.suffix.lower() != ".mp4":
        raise FactoryContractError(
            "video_job_invalid",
            "Output name must be a safe MP4 basename.",
            {"field": "output_name", "reason": "path"},
        )
    return name


def _reset_director_work_dir(work_dir: Path) -> None:
    """Start a stable-topic job from a single, non-mixed artifact snapshot.

    Topic jobs intentionally use a stable directory name.  A retry for the
    same topic must therefore remove only artifacts produced by this renderer
    before writing a new state snapshot; otherwise a failed provider attempt
    could be mistaken for a completed media run.  The directory is pipeline
    owned (under ``dist/director``), and unknown files are left untouched.
    """

    generated_names = {
        "topic.txt",
        "research.md",
        "sources.json",
        "style_tokens.json",
        "script.json",
        "director_score.json",
        "storyboard.json",
        "asset_selection.json",
        "director_report.json",
        "video_job.yaml",
        "video_job_state.json",
        "storyboard.resolved.json",
        "timeline.json",
        "subtitle.srt",
        "render_report.json",
        "director_quality_report.json",
        "director_quality_report.md",
        "run_report.json",
        "concat_list.txt",
    }
    if not work_dir.is_dir():
        return
    for child in work_dir.iterdir():
        if child.name == ".director_sandbox" and child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
            continue
        if not child.is_file() or child.name in generated_names or child.suffix.lower() in {".mp4", ".wav", ".mp3"}:
            if child.is_file() and (child.name in generated_names or child.suffix.lower() in {".mp4", ".wav", ".mp3"}):
                child.unlink()


def _write_director_support_artifacts(work_dir: Path, *, topic: str, context: Any, brief: Any | None) -> None:
    """Write bounded, source-linked context artifacts without raw prompts."""

    (work_dir / "topic.txt").write_text(topic + "\n", encoding="utf-8")
    if brief is None:
        (work_dir / "research.md").write_text(
            "# Factual review\n\nNo factual brief was supplied. This candidate remains review_required.\n",
            encoding="utf-8",
        )
        write_json(work_dir / "sources.json", {"review_status": "review_required", "sources": []})
    else:
        facts = brief.document.get("facts", [])
        lines = ["# Factual brief", "", f"Review status: {brief.document.get('review_status', 'review_required')}", ""]
        for fact in facts:
            if isinstance(fact, dict):
                lines.append(f"- {fact.get('fact_id', 'fact')}: {fact.get('claim', '')}")
        (work_dir / "research.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        write_json(work_dir / "sources.json", {"review_status": brief.document.get("review_status"), "sources": brief.document.get("sources", [])})
    profile = context.style_profile
    write_json(
        work_dir / "style_tokens.json",
        {
            "schema_version": "1.0",
            "character_id": context.registry.character_id,
            "registry_version": context.registry.registry_version,
            "persona": profile.brand_identity.get("persona", []),
            "allowed_poses": list(context.allowed_poses),
            "composition_id": context.composition.get("composition_id"),
            "mascot_mode": "required",
        },
    )


def _build_director_quality_report(*, job_id: str, score: dict[str, object] | None, factual_brief: Any | None, render_report_ref: str, render_report: dict[str, object] | None = None) -> dict[str, object]:
    score_value = int(score.get("score", 0)) if isinstance(score, dict) else 0
    verified = bool(factual_brief is not None and factual_brief.verified)
    report = render_report if isinstance(render_report, dict) else {}
    resolution = report.get("resolution") if isinstance(report.get("resolution"), dict) else {}
    audio = report.get("audio") if isinstance(report.get("audio"), dict) else {}
    subtitle = report.get("subtitle") if isinstance(report.get("subtitle"), dict) else {}
    technical_checks = [
        ("resolution", resolution.get("width") == 1080 and resolution.get("height") == 1920, "1080x1920 required"),
        ("fps", float(report.get("fps", 0.0)) == 30.0, "30 fps required"),
        ("codec", str(report.get("codec", "")).lower() == "h264", "H.264 required"),
        ("audio", bool(audio.get("present")), "audio track required"),
        ("subtitle_region", isinstance(report.get("subtitle_region"), dict) and bool(subtitle.get("present")), "subtitle safe region required"),
        ("duration", 25.0 <= float(report.get("duration", 0.0)) <= 60.0, "duration must be 25-60 seconds"),
    ]
    checks = [
        {"check_id": "director_score", "status": "pass" if score_value >= 85 else "fail", "detail": f"score={score_value}"},
        {"check_id": "factual_review", "status": "pass" if verified else "review_required", "detail": "verified brief" if verified else "human review required"},
    ]
    checks.extend({"check_id": check_id, "status": "pass" if passed else "fail", "detail": detail} for check_id, passed, detail in technical_checks)
    technical_ok = all(passed for _, passed, _ in technical_checks)
    status = "failed" if not technical_ok or score_value < 85 else ("completed" if verified else "review_required")
    error = None if status != "failed" else {"code": "director_quality_failed", "message": "Director post-render quality checks failed.", "context": {}}
    return {
        "schema_version": "1.0",
        "job_id": job_id,
        "status": status,
        "score": score_value,
        "checks": checks,
        "factual_review_required": not verified,
        "factual_review_status": "verified" if verified else "review_required",
        "render_report_ref": render_report_ref,
        "error": error,
    }


def _build_director_failure_report(*, topic: str, director: Any, error: FactoryContractError, factual_review_required: bool = True) -> dict[str, object]:
    """Create a schema-valid sanitized report when planning fails early."""

    normalized = str(topic)
    provider = str(getattr(director, "_provider_name", lambda: type(director).__name__)())
    version = str(getattr(director, "_provider_version", lambda: "unknown")())
    safe_error = sanitize_error_payload(error)
    context = dict(safe_error.get("context", {}))
    return {
        "schema_version": "1.0",
        "provider": provider,
        "provider_version": version[:128] or "unknown",
        "prompt_version": "pink_pig_director_v1",
        "topic_digest": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "attempts": int(context.get("attempt", 1)),
        "draft_validation": {"status": "fail", "error_count": 1, "validator": "provider"},
        "storyboard_validation": {"status": "fail", "error_count": 1, "validator": "director"},
        "semantic_validation": {"status": "fail", "error_count": 1, "validator": "director"},
        "storyboard_id": "sb_" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16],
        "storyboard_sha256": hashlib.sha256(b"{}").hexdigest(),
        "compiled_duration_seconds": 0.0,
        "factual_review_required": bool(factual_review_required),
        "error": {"code": str(safe_error["code"]), "message": str(safe_error["message"]), "context": context},
    }


def _report_is_current_failure(report: object, *, topic: str, error: FactoryContractError) -> bool:
    """Accept only a failure report produced for this topic and failure."""

    if not isinstance(report, dict):
        return False
    expected_digest = hashlib.sha256(topic.encode("utf-8")).hexdigest()
    report_error = report.get("error")
    return (
        report.get("topic_digest") == expected_digest
        and isinstance(report_error, dict)
        and report_error.get("code") == error.code
    )


def run_topic(
    topic: str,
    *,
    director: Any | None = None,
    provider_name: str = "codex-cli",
    factual_brief_path: str | Path | None = None,
    output_name: str = "output.mp4",
    emit: bool = True,
) -> dict[str, object]:
    """Generate a Script/Storyboard from *topic* and invoke existing ``run_job`` once."""

    from src.factory.director import AIDirector, CodexCliDirectorProvider, load_factual_brief, load_director_context, normalize_topic
    from video_factory.pipeline.validation import validate as _validate_director_report
    from video_factory.pipeline.job_state import VideoJobStateMachine
    from video_factory.pipeline.failure_contract import normalize_execution_error

    normalized = normalize_topic(topic)
    if provider_name != "codex-cli" and director is None:
        raise FactoryContractError(
            "director_provider_unavailable",
            "The requested Director provider is not configured.",
            {"provider": provider_name, "reason": "provider_not_configured"},
        )

    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    job_id = f"director_{digest}"
    phase2 = director is None or getattr(director, "workflow", "legacy") == "phase2"
    work_dir = ROOT / "dist" / "director" / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    if phase2:
        _reset_director_work_dir(work_dir)
    storyboard_path = work_dir / "storyboard.json"
    director_report_path = work_dir / "director_report.json"
    job_path = work_dir / "video_job.yaml"
    output_basename = _safe_output_name(output_name)
    output_path = work_dir / output_basename
    sandbox = work_dir / ".director_sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)

    machine = VideoJobStateMachine(work_dir=work_dir)
    state = machine.initial(
        job_id=job_id,
        topic=normalized,
        factual_review_required=True,
        factual_review_status="review_required",
    )
    if phase2:
        machine.write(state)
    brief = None

    def _cleanup_sandbox() -> None:
        """Remove only this job's validated, non-symlink provider sandbox."""

        try:
            owner = (ROOT.resolve() / "dist" / "director").resolve()
            current = work_dir.resolve()
            current.relative_to(owner)
            candidate = sandbox.resolve()
            candidate.relative_to(current)
        except FileNotFoundError:
            return
        except (OSError, RuntimeError, ValueError) as exc:
            raise FactoryContractError(
                "video_job_execution_failed",
                "Video job sandbox path is invalid.",
                {"stage": "context", "reason": "sandbox_path_invalid"},
            ) from exc
        if sandbox.is_symlink() or not sandbox.is_dir():
            return
        try:
            shutil.rmtree(candidate)
        except FileNotFoundError:
            return
        except OSError:
            # An ordinary cleanup race or lock must not leak its raw path.
            return

    def _execution_error(exc: BaseException, stage: str) -> FactoryContractError:
        return exc if isinstance(exc, FactoryContractError) else normalize_execution_error(exc, stage=stage)

    def _persist_failure(exc: BaseException, stage: str, *, cleanup: bool = True) -> FactoryContractError:
        normalized_error = _execution_error(exc, stage)
        try:
            if phase2:
                # ``fail`` performs the transition and atomic write as one
                # lifecycle operation.  Persistence failures get a stable
                # contract instead of leaking filesystem exception text.
                nonlocal state
                state = machine.fail(state, normalized_error, stage=stage)
        except Exception as persist_exc:
            raise FactoryContractError(
                "video_job_state_persist_failed",
                "Video job failure state could not be persisted.",
                {"stage": sanitize_stage(stage), "reason": sanitize_reason(persist_exc)},
            ) from persist_exc
        finally:
            if cleanup:
                _cleanup_sandbox()
        return normalized_error

    try:
        if factual_brief_path is not None:
            brief = load_factual_brief(factual_brief_path, repo_root=ROOT, topic=normalized)
        context = load_director_context(ROOT)
        if brief is not None and brief.verified:
            state["factual_review_required"] = False
            state["factual_review_status"] = "verified"
            machine._validate(state)
            if phase2:
                machine.write(state)
        _write_director_support_artifacts(work_dir, topic=normalized, context=context, brief=brief)
    except Exception as exc:
        normalized_error = _persist_failure(exc, "context")
        raise normalized_error from exc

    if director is None:
        director = AIDirector(
            provider=CodexCliDirectorProvider(working_dir=sandbox),
            repo_root=ROOT,
            workflow="phase2",
        )
    if phase2 and hasattr(director, "factual_brief"):
        director.factual_brief = brief
    try:
        if phase2:
            state = machine.transition(state, "planning")
            machine.write(state)
        storyboard = director.create_storyboard(normalized)
    except Exception as raw_exc:
        exc = _execution_error(raw_exc, "storyboard")
        try:
            report = getattr(director, "last_report", None)
            if not _report_is_current_failure(report, topic=normalized, error=exc):
                report = _build_director_failure_report(
                    topic=normalized,
                    director=director,
                    error=exc,
                    factual_review_required=bool(state.get("factual_review_required", True)),
                )
            else:
                # Even a topic-matching provider report may contain an unsafe
                # exception payload.  Rebuild only its structured error before
                # schema validation and persistence.
                report = dict(report)
                report["error"] = sanitize_error_payload(report.get("error"), stage="storyboard")
            try:
                _validate_director_report(report, "director_run_report")
            except Exception:
                # A stale or malformed provider report must never mask the
                # real provider failure; replace it with deterministic data.
                report = _build_director_failure_report(
                    topic=normalized,
                    director=director,
                    error=exc,
                    factual_review_required=bool(state.get("factual_review_required", True)),
                )
                _validate_director_report(report, "director_run_report")
            write_json(director_report_path, report)
        except Exception as report_exc:
            persist_error = _persist_failure(report_exc, "storyboard")
            raise persist_error from report_exc
        _persist_failure(exc, "storyboard")
        raise exc from raw_exc
    try:
        _cleanup_sandbox()
    except Exception as cleanup_exc:
        persist_error = _persist_failure(cleanup_exc, "storyboard", cleanup=False)
        raise persist_error from cleanup_exc

    try:
        script = getattr(director, "last_script", None)
        if phase2 and isinstance(script, dict):
            write_json(work_dir / "script.json", script)
            write_json(work_dir / "director_score.json", getattr(director, "last_score", {}) or {})
            state = machine.transition(state, "script_ready", artifact_refs={"script_ref": "script.json"})
            machine.write(state)
        write_json(storyboard_path, storyboard)
        if phase2:
            selection_report = getattr(director, "last_asset_selection", None)
            if isinstance(selection_report, dict):
                selection_report = dict(selection_report)
                selection_report["job_id"] = job_id
                write_json(work_dir / "asset_selection.json", selection_report)
            state = machine.transition(state, "storyboard_ready", artifact_refs={"storyboard_ref": "storyboard.json"})
            machine.write(state)
        report = getattr(director, "last_report", None)
        if not isinstance(report, dict):
            raise FactoryContractError(
                "director_storyboard_invalid",
                "Director did not produce a sanitized run report.",
                {"reason": "report_missing"},
            )
        _validate_director_report(report, "director_run_report")
        expected_factual = bool(state.get("factual_review_required", True))
        if report.get("factual_review_required") != expected_factual:
            raise FactoryContractError(
                "director_run_report_invalid",
                "Director report factual review status does not match job state.",
                {"reason": "factual_review_mismatch"},
            )
        write_json(director_report_path, report)

        job = copy.deepcopy(_load_director_job_defaults())
        job.update(
            {
                "schema_version": "1.0",
                "job_id": job_id,
                "job_kind": "video_render",
                "storyboard_ref": "storyboard.json",
                "outputs": {
                    "video": _relative_to_root(output_path),
                    "work_dir": _relative_to_root(work_dir),
                },
            }
        )
        from video_factory.pipeline.validation import validate as _validate_job

        _validate_job(job, "video_job")
        job_path.write_text(
            yaml.safe_dump(job, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        if phase2:
            state = machine.transition(state, "rendering", artifact_refs={"timeline_ref": "timeline.json"})
            machine.write(state)
    except Exception as raw_exc:
        exc = _persist_failure(raw_exc, "job_validation")
        raise exc from raw_exc
    try:
        result = run_job(job_path, emit=False)
    except Exception as raw_exc:
        exc = _persist_failure(raw_exc, "rendering")
        raise exc from raw_exc
    quality_report = None
    if phase2:
        try:
            render_report_value = None
            render_report_file = work_dir / "render_report.json"
            if render_report_file.is_file():
                parsed_render_report = json.loads(render_report_file.read_text(encoding="utf-8"))
                if isinstance(parsed_render_report, dict):
                    render_report_value = parsed_render_report
            quality_report = _build_director_quality_report(
                job_id=job_id,
                score=getattr(director, "last_score", None),
                factual_brief=brief,
                render_report_ref="render_report.json",
                render_report=render_report_value,
            )
            _validate_director_report(quality_report, "director_quality_report")
            write_json(work_dir / "director_quality_report.json", quality_report)
            (work_dir / "director_quality_report.md").write_text(
                f"# Director Quality Report\n\n- status: {quality_report['status']}\n- score: {quality_report['score']}\n- factual_review_status: {quality_report['factual_review_status']}\n",
                encoding="utf-8",
            )
            state = machine.transition(
                state,
                "quality_check",
                artifact_refs={"timeline_ref": "timeline.json", "render_report_ref": "render_report.json", "quality_report_ref": "director_quality_report.json"},
            )
            machine.write(state)
            if quality_report["status"] == "failed":
                quality_error = FactoryContractError(
                    str((quality_report.get("error") or {}).get("code", "director_quality_failed")),
                    str((quality_report.get("error") or {}).get("message", "Director quality checks failed.")),
                    dict((quality_report.get("error") or {}).get("context", {})),
                )
                state = machine.fail(state, quality_error, stage="quality_check")
            elif quality_report["status"] == "completed":
                state = machine.transition(state, "completed", artifact_refs={"output_ref": output_basename})
                machine.write(state)
        except Exception as raw_exc:
            exc = _persist_failure(raw_exc, "quality_check")
            raise exc from raw_exc
    result.update(
        {
            "mode": "topic",
            "job_id": job_id,
            "output": _relative_to_root(output_path),
            "render_report": _relative_to_root(work_dir / "render_report.json"),
            "storyboard": _relative_to_root(storyboard_path),
            "director_report": _relative_to_root(director_report_path),
            "job": _relative_to_root(job_path),
        }
    )
    if phase2:
        result["status"] = str(quality_report["status"])
        result["video_job_state"] = _relative_to_root(work_dir / "video_job_state.json")
        result["director_quality_report"] = _relative_to_root(work_dir / "director_quality_report.json")
    if emit:
        print(json.dumps(result, ensure_ascii=False))
    return result


# ---------------------------------------------------------------------------
# New --job mode (Phase 1 productization)
# ---------------------------------------------------------------------------

def run_job(job_path: Path, *, emit: bool = True) -> dict[str, object]:
    """Execute a VideoRenderJob from a YAML job definition."""
    job_path = job_path.resolve()

    # --- Load job ---
    if not job_path.is_file():
        raise ValueError("job_missing")
    job = yaml.safe_load(job_path.read_text(encoding="utf-8"))
    if not isinstance(job, dict):
        raise ValueError("job_invalid")

    # --- Validate job against schema ---
    from video_factory.pipeline.validation import validate as _validate_job
    _validate_job(job, "video_job")
    mascot_contract = load_mascot_contract(ROOT, job.get("mascot"))

    # --- Resolve paths ---
    job_dir = job_path.parent
    storyboard_path = (job_dir / str(job["storyboard_ref"])).resolve()
    registry_ref = job.get("registry_ref", "src/factory/assets/pink_pig/registry.json")
    registry_path = (ROOT / registry_ref).resolve()
    render_cfg = job.get("render", {})
    audio_cfg = job.get("audio", {})
    outputs_cfg = job.get("outputs", {})
    output_path = (ROOT / str(outputs_cfg.get("video", "dist/output.mp4"))).resolve()
    work_dir = (ROOT / str(outputs_cfg.get("work_dir", "dist/story_demo"))).resolve()

    # --- Stage B: Registry ---
    from video_factory.pipeline.registry import load_pink_pig_registry
    t0 = time.perf_counter()
    registry = load_pink_pig_registry(repo_root=ROOT)
    t_reg = round(time.perf_counter() - t0, 3)

    # --- Stage C: Storyboard ---
    from video_factory.pipeline.storyboard import (
        load_storyboard as _load_sb,
        validate_storyboard as _validate_sb,
        compile_storyboard as _compile_sb,
    )
    t1 = time.perf_counter()
    sb_doc = _load_sb(storyboard_path)
    _validate_sb(sb_doc)
    write_json(work_dir / "storyboard.resolved.json", sb_doc)
    t_sb = round(time.perf_counter() - t1, 3)

    # --- Stage D: Compile → Timeline ---
    t2 = time.perf_counter()
    tl_doc = _compile_sb(sb_doc, registry, repo_root=ROOT)
    # Post-compile validation
    from video_factory.pipeline.validation import validate as _validate_tl
    _validate_tl(tl_doc, "timeline")
    write_json(work_dir / "timeline.json", tl_doc)
    t_compile = round(time.perf_counter() - t2, 3)

    # Knowledge composition is activated by explicit scene layout metadata or
    # the required Pink Pig mode. Legacy jobs without either signal retain
    # their historical full-frame renderer behavior.
    raw_scenes = sb_doc.get("scenes", [])
    explicit_layouts = {
        str(scene.get("layout_mode"))
        for scene in raw_scenes
        if isinstance(scene, dict) and scene.get("layout_mode")
    }
    composition = None
    style_evidence: dict[str, object] | None = None
    signature_asset_id: str | None = None
    signature_path: Path | None = None
    if explicit_layouts or mascot_contract.get("mode") == "required":
        if len(explicit_layouts) > 1:
            raise FactoryContractError(
                "composition_region_invalid",
                "A render job cannot mix composition layout modes.",
                {"field": "scenes.layout_mode"},
            )
        from video_factory.pipeline.composition import load_composition
        from video_factory.pipeline.pink_pig_quality import validate_pink_pig_quality

        layout_mode = next(iter(explicit_layouts), "knowledge_illustration")
        composition = load_composition(layout_mode, repo_root=ROOT)
        style_evidence = validate_pink_pig_quality(
            storyboard=sb_doc,
            timeline=tl_doc,
            registry=registry,
            composition=composition,
            mascot_contract=mascot_contract,
            repo_root=ROOT,
        )
        signature_asset_id = str(style_evidence.get("signature_asset_id", "pink_pig.signature.v1"))
        signature_asset = registry.get(signature_asset_id)
        if signature_asset is None or not signature_asset.path:
            raise FactoryContractError(
                "pink_pig_style_missing",
                "Pink Pig signature asset is not renderable.",
                {"field": "signature_asset_id"},
            )
        signature_path = (ROOT / signature_asset.path).resolve()

    # --- Stage E: Audio planning ---
    from video_factory.pipeline.audio_planner import plan_audio
    t3 = time.perf_counter()
    audio_plan = plan_audio(
        tl_doc,
        work_dir=work_dir,
        audio_config=audio_cfg,
        repo_root=ROOT,
    )
    if bool(audio_cfg.get("require_narration", False)):
        segments = tuple(audio_plan.segments)
        if audio_plan.mode != "tts" or len(segments) != len(tl_doc.get("scenes", [])) or any(
            float(segment.get("actual_duration", 0.0)) <= 0 for segment in segments
        ):
            raise FactoryContractError(
                "audio_narration_incomplete",
                "The job requires a non-empty narration segment for every scene.",
                {"mode": audio_plan.mode, "segments": len(segments)},
            )
    t_audio = round(time.perf_counter() - t3, 3)

    # --- Stage F: Subtitles ---
    t4 = time.perf_counter()
    srt_path = work_dir / "subtitle.srt"
    captions = build_srt_from_timeline(tl_doc, srt_path, composition=composition)
    t_sub = round(time.perf_counter() - t4, 3)

    # --- Stage G: Render ---
    t5 = time.perf_counter()
    render_timeline = to_render_timeline(tl_doc)
    transition_sec = float(render_cfg.get("transition_seconds", 0.4))
    effective_subtitle_style = job.get("subtitle", {}).get("style") if isinstance(job.get("subtitle"), dict) else None
    # VideoRenderJob 1.0 keeps its historical bottom_safe_band enum.  When
    # the storyboard activates the Phase 1.5 composition, the composition is
    # the authoritative render style and supplies the 52–60px safe-band
    # values without changing the immutable job contract.
    if composition is not None and isinstance(composition.get("subtitle_style"), dict):
        effective_subtitle_style = dict(composition["subtitle_style"])
    render = render_video(
        asset_dir=ROOT,  # asset_dir is now secondary; image_path takes priority
        timeline=render_timeline,
        subtitle_path=srt_path,
        output_path=output_path,
        transition_seconds=transition_sec,
        audio_path=audio_plan.path,
        audio_loop=audio_plan.loop,
        repo_root=ROOT,
        subtitle_style=effective_subtitle_style,
        audio_gain=float(job.get("audio", {}).get("gain", 1.0)) if isinstance(job.get("audio"), dict) else 1.0,
        audio_sample_rate=24000 if audio_plan.mode == "tts" else (48000 if audio_plan.path else None),
        composition=composition,
        signature_path=signature_path,
    )
    t_render = round(time.perf_counter() - t5, 3)

    # --- Stage H: Evidence (ffprobe) ---
    t6 = time.perf_counter()
    ffprobe_meta = {}
    if output_path.is_file():
        try:
            proc = subprocess.run(
                ["ffprobe", "-v", "error", "-show_format", "-show_streams",
                 "-of", "json", str(output_path)],
                capture_output=True, text=True, timeout=15,
            )
            fp_data = json.loads(proc.stdout)
            # Extract key metadata
            fmt = fp_data.get("format", {})
            vstreams = [s for s in fp_data.get("streams", []) if s.get("codec_type") == "video"]
            astreams = [s for s in fp_data.get("streams", []) if s.get("codec_type") == "audio"]
            ffprobe_meta = {
                "duration": float(fmt.get("duration", 0)),
                "size": int(fmt.get("size", 0)),
                "format_name": fmt.get("format_name", ""),
                "video": {
                    "codec": vstreams[0]["codec_name"] if vstreams else "",
                    "width": int(vstreams[0]["width"]) if vstreams else 0,
                    "height": int(vstreams[0]["height"]) if vstreams else 0,
                    "fps": vstreams[0].get("r_frame_rate", "") if vstreams else "",
                } if vstreams else {},
                "audio": {
                    "codec": astreams[0]["codec_name"] if astreams else "",
                    "sample_rate": astreams[0].get("sample_rate", "") if astreams else "",
                } if astreams else {},
                "has_audio": len(astreams) > 0,
            }
        except Exception:
            ffprobe_meta = {"error": "ffprobe_failed"}
    t_probe = round(time.perf_counter() - t6, 3)

    render_report = build_render_report(
        ffprobe_meta=ffprobe_meta,
        timeline=tl_doc,
        subtitle_path=srt_path,
        captions_count=len(captions),
        composition=composition,
        style_evidence=style_evidence,
        signature_asset_id=signature_asset_id,
    )
    render_report_path = work_dir / "render_report.json"
    write_json(render_report_path, render_report)

    # --- Write run report ---
    run_report = {
        "job_id": job.get("job_id", ""),
        "status": "success",
        "stages": {
            "registry_load": {"seconds": t_reg},
            "storyboard_validate": {"seconds": t_sb},
            "compile": {"seconds": t_compile},
            "audio_plan": {"seconds": t_audio},
            "subtitle": {"seconds": t_sub},
            "render": {"seconds": t_render},
            "evidence": {"seconds": t_probe},
        },
        "audio_plan": {
            "mode": audio_plan.mode,
            "loop": audio_plan.loop,
            "fallback_reason": audio_plan.fallback_reason,
            "path": str(audio_plan.path) if audio_plan.path else None,
            "segments_count": len(audio_plan.segments),
        },
        "mascot": mascot_contract,
        "ffprobe": ffprobe_meta,
        "render_report": "render_report.json",
        "output": str(output_path),
        "renderer": render,
        "captions_count": len(captions),
    }
    write_json(work_dir / "run_report.json", run_report)

    result = {
        "mode": "job",
        "job_id": job.get("job_id", ""),
        "output": str(output_path),
        "captions": len(captions),
        "audio_mode": audio_plan.mode,
        "audio_fallback_reason": audio_plan.fallback_reason,
        "mascot": mascot_contract,
        "render_report": str(render_report_path),
        **render,
    }
    if emit:
        print(json.dumps(result, ensure_ascii=False))
    return result


# ---------------------------------------------------------------------------
# Local Phase 1 brief mode (no Provider / no network)
# ---------------------------------------------------------------------------

_PHASE1_OWNED_FILES = {
    "input_brief.json",
    "factual_brief.json",
    "sources.json",
    "script.json",
    "storyboard.json",
    "asset_selection_report.json",
    "render_job.yaml",
    "storyboard.resolved.json",
    "timeline.json",
    "subtitle.srt",
    "audio.wav",
    "concat_list.txt",
    "render_report.json",
    "run_report.json",
    "render_manifest.json",
    "audio_manifest.json",
    "quality_report.json",
    "review_package.json",
    "review_checklist.md",
    "publish_info.md",
    "cover.png",
    "final_master.mp4",
    "video_job_state.json",
}


def _prepare_phase1_work_dir(work_dir: Path) -> None:
    """Reset only files owned by one stable local-brief job.

    Re-runs are intentionally idempotent, but an unexpected file or directory
    is preserved.  This keeps the operation recoverable in a dirty workspace.
    """

    owner = (ROOT / "dist" / "phase1_local").resolve()
    target = work_dir.resolve()
    if target == owner or owner not in target.parents:
        raise FactoryContractError(
            "phase1_output_path_invalid",
            "Phase 1 output must remain inside its owned job directory.",
            {"reason": "containment"},
        )
    if work_dir.exists() and work_dir.is_symlink():
        raise FactoryContractError(
            "phase1_output_path_invalid",
            "Phase 1 output directory cannot be a link.",
            {"reason": "reparse"},
        )
    work_dir.mkdir(parents=True, exist_ok=True)
    for name in sorted(_PHASE1_OWNED_FILES):
        candidate = work_dir / name
        if candidate.is_symlink():
            raise FactoryContractError(
                "phase1_output_path_invalid",
                "Phase 1 output artifacts cannot be links.",
                {"reason": "reparse", "artifact": name},
            )
        if candidate.is_file():
            candidate.unlink()
    for pattern in ("seg_*.wav", "seg_*.mp3", "padded_*.wav"):
        for candidate in work_dir.glob(pattern):
            if candidate.is_symlink() or not candidate.is_file():
                raise FactoryContractError(
                    "phase1_output_path_invalid",
                    "Phase 1 temporary audio artifacts are invalid.",
                    {"reason": "reparse"},
                )
            candidate.unlink()


def run_local_brief(brief_path: Path, *, emit: bool = True) -> dict[str, object]:
    """Build one fully local review package through the existing pipeline."""

    from src.factory.phase1_local import build_local_plan, load_local_brief
    from video_factory.pipeline.job_state import VideoJobStateMachine
    from video_factory.pipeline.review_package import build_review_package

    brief = load_local_brief(brief_path)
    plan = build_local_plan(brief, repo_root=ROOT)
    job_id = str(plan["job_id"])
    work_dir = ROOT / "dist" / "phase1_local" / job_id
    _prepare_phase1_work_dir(work_dir)

    machine = VideoJobStateMachine(work_dir=work_dir)
    state = machine.initial(
        job_id=job_id,
        topic=str(plan["topic"]),
        factual_review_required=False,
        factual_review_status="verified",
    )
    machine.write(state)
    try:
        state = machine.transition(state, "planning")
        machine.write(state)

        write_json(work_dir / "input_brief.json", brief)
        write_json(work_dir / "factual_brief.json", plan["factual_brief"])
        write_json(
            work_dir / "sources.json",
            {
                "review_status": "verified",
                "sources": list(plan["factual_brief"]["sources"]),
            },
        )
        write_json(work_dir / "script.json", plan["script"])
        state = machine.transition(state, "script_ready", artifact_refs={"script_ref": "script.json"})
        machine.write(state)

        write_json(work_dir / "storyboard.json", plan["storyboard"])
        selection_report = dict(plan["asset_selection"])
        selection_report["job_id"] = job_id
        write_json(work_dir / "asset_selection_report.json", selection_report)
        state = machine.transition(state, "storyboard_ready", artifact_refs={"storyboard_ref": "storyboard.json"})
        machine.write(state)

        render_job = {
            "schema_version": "1.0",
            "job_id": job_id,
            "job_kind": "video_render",
            "storyboard_ref": "storyboard.json",
            "registry_ref": "src/factory/assets/pink_pig/registry.json",
            "render": {
                "width": 1080,
                "height": 1920,
                "fps": 30,
                "transition_seconds": 0.4,
                "pad_color": "0xF7E4EA",
            },
            "audio": {
                "strategy": "tts_with_offline_fallback",
                "allow_network": False,
                "require_narration": True,
                "tts": {"provider": "windows-sapi", "voice": "Microsoft Huihui Desktop"},
                "fallback_bgm": "assets/pink_pig/demo_music.wav",
            },
            "subtitle": {
                "enabled": True,
                "source": "scene_caption",
                "style": {
                    "layout": "bottom_safe_band",
                    "font_name": "Microsoft YaHei",
                    "font_size": 56,
                    "margin_left": 90,
                    "margin_right": 90,
                    "margin_vertical": 250,
                },
            },
            "mascot": {
                "mode": "required",
                "skill_ref": "skills/pink-pig-mascot-director/SKILL.md",
                "style_profile_ref": "src/factory/assets/pink_pig/style_profile.json",
            },
            "outputs": {
                "video": f"dist/phase1_local/{job_id}/final_master.mp4",
                "work_dir": f"dist/phase1_local/{job_id}",
            },
        }
        (work_dir / "render_job.yaml").write_text(
            yaml.safe_dump(render_job, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        state = machine.transition(
            state,
            "rendering",
            artifact_refs={"timeline_ref": "timeline.json"},
        )
        machine.write(state)

        render_result = run_job(work_dir / "render_job.yaml", emit=False)
        package = build_review_package(
            work_dir=work_dir,
            output_path=work_dir / "final_master.mp4",
            job_id=job_id,
            input_mode=str(brief["input_mode"]),
            title=str(brief.get("title", plan["topic"])),
            scene_count=len(plan["storyboard"]["scenes"]),
            asset_selection=selection_report,
        )
        state = machine.transition(
            state,
            "quality_check",
            artifact_refs={
                "timeline_ref": "timeline.json",
                "render_report_ref": "render_report.json",
                "quality_report_ref": "quality_report.json",
            },
        )
        machine.write(state)
        state = machine.transition(
            state,
            "completed",
            artifact_refs={"output_ref": "final_master.mp4"},
        )
        machine.write(state)
        result = {
            "mode": "local_brief",
            "status": "pending_review",
            "job_id": job_id,
            "review_package": str(work_dir / "review_package.json"),
            "output": str(work_dir / "final_master.mp4"),
            "quality_status": package["quality"]["status"],
            "audio_mode": render_result.get("audio_mode"),
        }
        if emit:
            print(json.dumps(result, ensure_ascii=False))
        return result
    except Exception as exc:
        if state.get("state") not in {"completed", "failed"}:
            machine.fail(state, exc, stage=state.get("state"))
        raise


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Pink Pig Video Factory")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--config", type=Path, default=None, help="Legacy config YAML path")
    group.add_argument("--job", type=Path, default=None, help="Phase 1 job YAML path")
    group.add_argument("--local-brief", type=Path, default=None, help="Deterministic local Phase 1 brief JSON")
    group.add_argument("--topic", type=str, default=None, help="Generate a storyboard from a topic")
    group.add_argument("--topic-file", type=Path, default=None, help="Read a topic from a repository-relative text file")
    parser.add_argument("--factual-brief", type=Path, default=None, help="Repository-relative factual brief JSON for topic mode")
    parser.add_argument("--output-name", type=str, default="output.mp4", help="Safe MP4 basename for topic mode")
    parser.add_argument(
        "--director-provider",
        choices=["codex-cli"],
        default="codex-cli",
        help="Provider used with --topic",
    )
    args = parser.parse_args()

    if args.factual_brief is not None and args.topic is None and args.topic_file is None:
        parser.error("--factual-brief requires --topic or --topic-file")
    if args.output_name != "output.mp4" and args.topic is None and args.topic_file is None:
        parser.error("--output-name requires --topic or --topic-file")

    # Default to legacy --config if neither specified
    if args.config is None and args.job is None and args.local_brief is None and args.topic is None and args.topic_file is None:
        args.config = ROOT / "examples" / "pink_pig_demo" / "config.yaml"

    try:
        if args.topic is not None or args.topic_file is not None:
            if args.topic_file is not None:
                if args.factual_brief is not None and args.topic is not None:
                    raise FactoryContractError("director_topic_invalid", "Topic and topic-file are mutually exclusive.", {"field": "topic"})
                topic_path = _safe_topic_file(args.topic_file)
                topic_value = topic_path.read_text(encoding="utf-8").strip()
            else:
                topic_value = args.topic
            return 0 if run_topic(topic_value, provider_name=args.director_provider, factual_brief_path=args.factual_brief, output_name=args.output_name) else 0
        if args.local_brief is not None:
            return 0 if run_local_brief(args.local_brief) else 0
        if args.job is not None:
            return 0 if run_job(args.job) else 0
        else:
            run(args.config)
            return 0
    except FactoryContractError as exc:
        print(json.dumps({"status": "error", "error": exc.to_dict()}, ensure_ascii=False))
        return 2
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
