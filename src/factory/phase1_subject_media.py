"""Local subject media orchestration through measured timing and one Jianying draft."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
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


def run_subject_media(request: SubjectMediaRequest, *, skill_root: Path | None = None,
                      media_python: Path | None = None, runner: Callable[..., Any] = subprocess.run,
                      render_runner: Callable[..., dict[str, Any]] = render_and_review) -> dict[str, Any]:
    skill = (skill_root or (Path(os.environ["JIAN_YING_SKILL_ROOT"]) if os.environ.get("JIAN_YING_SKILL_ROOT") else None))
    if skill is None: raise ValueError("jianying_skill_root_required")
    skill = skill.resolve()
    if not (skill / "scripts" / "jy_wrapper.py").is_file(): raise ValueError("jianying_skill_root_invalid")
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
    python_path = (media_python or (Path(os.environ["PHASE1_MEDIA_PYTHON"]) if os.environ.get("PHASE1_MEDIA_PYTHON") else Path(sys.executable))).resolve()
    if not python_path.is_file() or python_path.drive.upper() != "E:": raise ValueError("media_python_invalid")
    timing_root = workdir / "timing"; timing_root.mkdir()
    manifest = workdir / "timing_manifest.json"
    probe_name = f"subject_{script['script_id']}_{workdir.name}_timing"
    timing_cmd = [str(python_path), str(Path(__file__).resolve().parents[2] / "scripts/phase1_jianying_timing_probe.py"), "--script", str(request.director_script.resolve()), "--scene-plan", str(request.scene_plan.resolve()), "--drafts-root", str(timing_root), "--name", probe_name, "--manifest", str(manifest), "--skill-root", str(skill), "--visual-duration-seconds", str(duration)]
    runner(timing_cmd, check=True, shell=False, timeout=900)
    output, render_report = workdir / "visual_master.mp4", workdir / "render_report.json"
    clips, stills = workdir / "clips", workdir / "stills"
    render_runner(script=request.director_script, scene_plan=request.scene_plan, timing_manifest=manifest, output=output, report=render_report,
                  stills_dir=stills, clips_dir=clips, review_report=workdir / "visual_review.json", contact_sheet=workdir / "contact_sheet.png", aspect=str(topic.get("aspect", "16:9")))
    preview, preview_report = workdir / "audible_preview.mp4", workdir / "audible_preview.json"
    runner([str(python_path), str(Path(__file__).resolve().parents[2] / "scripts/assemble_jianying_voice_preview.py"), "--visual", str(output), "--visual-report", str(render_report), "--manifest", str(manifest), "--timing-root", str(timing_root), "--output", str(preview), "--report", str(preview_report)], check=True, shell=False, timeout=900)
    draft_report = workdir / "jianying_manifest.json"; draft_name = f"Subject_{script['script_id']}_{workdir.name}"
    runner([str(python_path), str(Path(__file__).resolve().parents[2] / "scripts/phase1_jianying_tts_draft.py"), "--visual", str(output), "--visual-report", str(render_report), "--clips-root", str(clips), "--script", str(request.director_script.resolve()), "--timing-manifest", str(manifest), "--timing-root", str(timing_root), "--name", draft_name, "--report", str(draft_report), "--skill-root", str(skill)], check=True, shell=False, timeout=900)
    paths = {"timing_manifest": manifest, "visual_report": render_report, "audible_preview_report": preview_report, "jianying_manifest": draft_report}
    return {"schema_version":"1.0", "status":"PHASE1_TOPIC_DRAFT_READY_FOR_JOVI_REVIEW", "paths":{key:str(path) for key,path in paths.items()}, "hashes":{key:_sha(path) for key,path in paths.items() if path.is_file()}, "draft_name":draft_name}
