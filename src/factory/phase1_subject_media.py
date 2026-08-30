"""Local subject media orchestration through measured timing and one Jianying draft."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .phase1_topic_visual import render_and_review
from video_factory.pipeline import validation


@dataclass(frozen=True)
class SubjectMediaRequest:
    director_script: Path
    scene_plan: Path
    topic_request: Path
    workdir: Path


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise ValueError("subject_media_input_invalid")
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_report(path: Path, statuses: set[str]) -> dict[str, Any]:
    if not path.is_file(): raise ValueError(f"subject_media_output_missing:{path.name}")
    value = _load(path)
    if value.get("status") not in statuses: raise ValueError(f"subject_media_report_status_invalid:{path.name}")
    return value


def _write_failure(workdir: Path, stage: str, exc: Exception) -> None:
    evidence = {"schema_version":"1.0", "status":"subject_media_failed", "failed_stage":stage,
                "reason":type(exc).__name__, "ready_status_emitted":False, "workdir_preserved":True}
    (workdir / "media_failure.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_subject_media(request: SubjectMediaRequest, *, skill_root: Path | None = None,
                      media_python: Path | None = None, runner: Callable[..., Any] = subprocess.run,
                      render_runner: Callable[..., dict[str, Any]] = render_and_review) -> dict[str, Any]:
    skill = (skill_root or (Path(os.environ["JIAN_YING_SKILL_ROOT"]) if os.environ.get("JIAN_YING_SKILL_ROOT") else None))
    if skill is None: raise ValueError("jianying_skill_root_required")
    skill = skill.resolve()
    if not (skill / "scripts" / "jy_wrapper.py").is_file(): raise ValueError("jianying_skill_root_invalid")
    selected_python = media_python or (Path(os.environ["PHASE1_MEDIA_PYTHON"]) if os.environ.get("PHASE1_MEDIA_PYTHON") else None)
    if selected_python is None: raise ValueError("media_python_required")
    python_path = selected_python.resolve()
    if not python_path.is_file() or python_path.drive.upper() != "E:": raise ValueError("media_python_invalid")
    script, plan, topic = _load(request.director_script), _load(request.scene_plan), _load(request.topic_request)
    if not validation.is_available(): raise ValueError("subject_media_schema_validation_unavailable")
    validation.validate(script, "director_script"); validation.validate(plan, "phase1_scene_plan"); validation.validate(topic, "phase1_topic_request")
    if script.get("script_id") != plan.get("script_id") or len(script.get("beats", [])) != len(plan.get("scenes", [])):
        raise ValueError("subject_media_plan_mismatch")
    duration = float(topic["duration"])
    if not 25 <= duration <= 60: raise ValueError("subject_media_duration_invalid")
    workdir = request.workdir.resolve()
    if workdir.drive.upper() != "E:": raise ValueError("subject_media_workdir_must_use_e_drive")
    workdir.mkdir(parents=True, exist_ok=False)
    timing_root = workdir / "timing"; timing_root.mkdir()
    manifest = workdir / "timing_manifest.json"
    probe_name = f"subject_{script['script_id']}_{workdir.name}_timing"
    timing_cmd = [str(python_path), str(Path(__file__).resolve().parents[2] / "scripts/phase1_jianying_timing_probe.py"), "--script", str(request.director_script.resolve()), "--scene-plan", str(request.scene_plan.resolve()), "--drafts-root", str(timing_root), "--name", probe_name, "--manifest", str(manifest), "--skill-root", str(skill), "--visual-duration-seconds", str(duration)]
    output, render_report = workdir / "visual_master.mp4", workdir / "render_report.json"
    clips, stills = workdir / "clips", workdir / "stills"
    visual_review = workdir / "visual_review.json"
    preview, preview_report = workdir / "audible_preview.mp4", workdir / "audible_preview.json"
    draft_report = workdir / "jianying_manifest.json"; draft_name = f"Subject_{script['script_id']}_{workdir.name}"
    stage = "timing"
    try:
        runner(timing_cmd, check=True, shell=False, timeout=900)
        timing = _require_report(manifest, {"timing_manifest_ready"})
        if timing.get("script", {}).get("sha256") != _sha(request.director_script) or timing.get("scene_plan", {}).get("sha256") != _sha(request.scene_plan): raise ValueError("timing_input_hash_mismatch")
        stage = "render"
        render_runner(script=request.director_script, scene_plan=request.scene_plan, timing_manifest=manifest, output=output, report=render_report,
                      stills_dir=stills, clips_dir=clips, review_report=visual_review, contact_sheet=workdir / "contact_sheet.png", aspect=str(topic["aspect"]))
        render = _require_report(render_report, {"passed"}); review = _require_report(visual_review, {"passed"})
        if not output.is_file() or render.get("visual", {}).get("sha256") != _sha(output) or review.get("visual", {}).get("sha256") != _sha(output): raise ValueError("render_output_hash_mismatch")
        stage = "preview"
        runner([str(python_path), str(Path(__file__).resolve().parents[2] / "scripts/assemble_jianying_voice_preview.py"), "--visual", str(output), "--visual-report", str(render_report), "--manifest", str(manifest), "--timing-root", str(timing_root), "--output", str(preview), "--report", str(preview_report)], check=True, shell=False, timeout=900)
        preview_value = _require_report(preview_report, {"audio_preview_ready_for_manual_listening"})
        if not preview.is_file() or preview_value.get("visual", {}).get("sha256") != _sha(output) or preview_value.get("render_report", {}).get("sha256") != _sha(render_report) or preview_value.get("output", {}).get("sha256") != _sha(preview): raise ValueError("preview_output_hash_mismatch")
        stage = "jianying"
        runner([str(python_path), str(Path(__file__).resolve().parents[2] / "scripts/phase1_jianying_tts_draft.py"), "--visual", str(output), "--visual-report", str(render_report), "--clips-root", str(clips), "--script", str(request.director_script.resolve()), "--timing-manifest", str(manifest), "--timing-root", str(timing_root), "--name", draft_name, "--report", str(draft_report), "--skill-root", str(skill)], check=True, shell=False, timeout=900)
        draft = _require_report(draft_report, {"draft_ready_for_manual_jianying_review"})
        inputs = draft.get("inputs", {})
        if inputs.get("script_sha256") != _sha(request.director_script) or inputs.get("timing_manifest_sha256") != _sha(manifest) or inputs.get("render_report_sha256") != _sha(render_report) or draft.get("export", {}).get("automatic_export") != "disabled": raise ValueError("jianying_output_hash_mismatch")
        paths = {"timing_manifest":manifest,"render_report":render_report,"visual_review":visual_review,"preview":preview,"preview_report":preview_report,"jianying_report":draft_report}
        result = {"schema_version":"1.0","status":"PHASE1_TOPIC_DRAFT_READY_FOR_JOVI_REVIEW","paths":{k:str(v) for k,v in paths.items()},"hashes":{k:_sha(v) for k,v in paths.items()},"draft_name":draft_name}
        validation.validate(result, "phase1_subject_media_result")
        return result
    except Exception as exc:
        _write_failure(workdir, stage, exc)
        raise
