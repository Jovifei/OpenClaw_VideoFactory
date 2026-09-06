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

MIN_SUBJECT_VOICE_COVERAGE = 0.75


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


def _write_json_atomically(path: Path, value: dict[str, Any]) -> dict[str, Any]:
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        raise ValueError("subject_media_result_temp_exists")
    encoded = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with temporary.open("xb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)
    return _load(path)


def validate_timing_coverage(timing: dict[str, Any], *, visual_duration_us: int,
                             minimum_ratio: float = MIN_SUBJECT_VOICE_COVERAGE) -> float:
    try:
        voice_end = int(timing["voice"]["voice_end_microseconds"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("subject_media_voice_coverage_invalid") from exc
    if visual_duration_us <= 0 or voice_end < 0 or voice_end > visual_duration_us:
        raise ValueError("subject_media_voice_coverage_invalid")
    ratio = voice_end / visual_duration_us
    if ratio < minimum_ratio:
        raise ValueError("subject_media_voice_coverage_below_minimum")
    reported = timing.get("voice", {}).get("coverage_ratio")
    if reported is not None and abs(float(reported) - ratio) > 0.000_001:
        raise ValueError("subject_media_voice_coverage_invalid")
    return ratio


def validate_ready_reports(reports: dict[str, dict[str, Any]], *, scene_count: int, expanded_audio_count: int, visual_duration_us: int) -> None:
    def require(condition: bool, field: str) -> None:
        if not condition:
            raise ValueError(f"ready_report_contract_invalid:{field}")
    try:
        timing, render, review, preview, draft = (reports[k] for k in ("timing","render","visual_review","preview","jianying"))
        voice = timing["voice"]
        require(timing["status"] == "timing_manifest_ready", "timing.status")
        require(len(timing["segments"]) == scene_count, "timing.segment_count")
        require(voice["rendered_audio_segment_count"] == expanded_audio_count, "timing.expanded_audio_count")
        require(voice["voice_end_microseconds"] <= visual_duration_us, "timing.voice_end")
        require(validate_timing_coverage(timing, visual_duration_us=visual_duration_us) >= MIN_SUBJECT_VOICE_COVERAGE, "timing.voice_coverage")
        visual = render["visual"]
        require(render["status"] == "passed", "render.status")
        require(visual["audio_present"] is False, "render.audio_present")
        require(visual["burned_in_subtitles"] is False, "render.burned_in_subtitles")
        require(len(visual["scene_timing"]) == scene_count, "render.scene_count")
        post = review["post_render"]
        require(review["status"] == "passed", "visual_review.status")
        require(bool(review["contact_sheet"]["sha256"]), "visual_review.contact_sheet_hash")
        require(bool(review["post_render_report"]["sha256"]), "visual_review.post_report_hash")
        require(post["full_decode"] is True, "visual_review.full_decode")
        require(post["all_frame_scan"]["status"] == "passed", "visual_review.all_frame_scan")
        out, sync = preview["output"], preview["sync_validation"]
        require(preview["status"] == "audio_preview_ready_for_manual_listening", "preview.status")
        require(out["audio_present"] is True and out["full_decode"] == "passed", "preview.decode")
        require(str(out["codec"]).lower() == "aac", "preview.codec")
        require(isinstance(out["mean_volume_db"], (int,float)) and isinstance(out["max_volume_db"], (int,float)), "preview.loudness_type")
        require(-100 < out["mean_volume_db"] <= out["max_volume_db"] <= 1, "preview.loudness_range")
        require(sync["status"] == "passed", "preview.sync")
        require(preview["audio_source"]["segment_count"] == expanded_audio_count, "preview.segment_count")
        require(draft["status"] == "draft_ready_for_manual_jianying_review", "jianying.status")
        require(draft["sync_validation"]["status"] == "passed", "jianying.sync")
        audio, subtitle = draft["audio_validation"], draft["subtitle_validation"]
        require(audio["status"] == "passed" and audio["muted"] is False and audio["segment_count"] == expanded_audio_count, "jianying.audio_validation")
        require(subtitle["status"] == "passed" and subtitle["segment_count"] == scene_count, "jianying.subtitle_validation")
        require(draft["export"]["automatic_export"] == "disabled", "jianying.automatic_export")
        tracks = {item["name"]:item for item in draft["tracks"]}
        require(set(tracks) == {"VideoTrack","VoiceOver","Subtitles"}, "jianying.track_names")
        require(tracks["VideoTrack"]["segment_count"] == scene_count, "jianying.video_track_count")
        require(tracks["VoiceOver"]["segment_count"] == expanded_audio_count, "jianying.voice_track_count")
        require(tracks["Subtitles"]["segment_count"] == scene_count, "jianying.subtitle_track_count")
        require(abs(int(tracks["VideoTrack"]["duration_microseconds"]) - visual_duration_us) <= 33_335, "jianying.video_track_duration")
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("ready_report_contract_invalid:"):
            raise
        raise ValueError("ready_report_contract_invalid:report_shape") from exc


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
    width, height = ((1920, 1080) if topic["aspect"] == "16:9" else (1080, 1920))
    timing_root = workdir / "timing"; timing_root.mkdir()
    manifest = workdir / "timing_manifest.json"
    probe_name = f"subject_{script['script_id']}_{workdir.name}_timing"
    timing_cmd = [str(python_path), str(Path(__file__).resolve().parents[2] / "scripts/phase1_jianying_timing_probe.py"), "--script", str(request.director_script.resolve()), "--scene-plan", str(request.scene_plan.resolve()), "--drafts-root", str(timing_root), "--name", probe_name, "--manifest", str(manifest), "--skill-root", str(skill), "--visual-duration-seconds", str(duration), "--width", str(width), "--height", str(height)]
    output, render_report = workdir / "visual_master.mp4", workdir / "render_report.json"
    clips, stills = workdir / "clips", workdir / "stills"
    visual_review = workdir / "visual_review.json"
    preview, preview_report = workdir / "audible_preview.mp4", workdir / "audible_preview.json"
    draft_report = workdir / "jianying_manifest.json"; draft_name = f"Subject_{script['script_id']}_{workdir.name}"
    result_receipt = workdir / "subject_media_result.json"
    stage = "timing"
    try:
        runner(timing_cmd, check=True, shell=False, timeout=900)
        timing = _require_report(manifest, {"timing_manifest_ready"})
        if timing.get("script", {}).get("sha256") != _sha(request.director_script) or timing.get("scene_plan", {}).get("sha256") != _sha(request.scene_plan): raise ValueError("timing_input_hash_mismatch")
        validate_timing_coverage(timing, visual_duration_us=round(duration * 1_000_000))
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
        runner([str(python_path), str(Path(__file__).resolve().parents[2] / "scripts/phase1_jianying_tts_draft.py"), "--visual", str(output), "--visual-report", str(render_report), "--clips-root", str(clips), "--script", str(request.director_script.resolve()), "--timing-manifest", str(manifest), "--timing-root", str(timing_root), "--name", draft_name, "--report", str(draft_report), "--skill-root", str(skill), "--width", str(width), "--height", str(height)], check=True, shell=False, timeout=900)
        draft = _require_report(draft_report, {"draft_ready_for_manual_jianying_review"})
        inputs = draft.get("inputs", {})
        if inputs.get("script_sha256") != _sha(request.director_script) or inputs.get("timing_manifest_sha256") != _sha(manifest) or inputs.get("render_report_sha256") != _sha(render_report) or draft.get("export", {}).get("automatic_export") != "disabled": raise ValueError("jianying_output_hash_mismatch")
        expanded_count = int(timing.get("voice", {}).get("rendered_audio_segment_count", 0))
        validate_ready_reports({"timing":timing,"render":render,"visual_review":review,"preview":preview_value,"jianying":draft},
                               scene_count=len(plan["scenes"]), expanded_audio_count=expanded_count, visual_duration_us=round(duration * 1_000_000))
        paths = {"timing_manifest":manifest,"render_report":render_report,"visual_review":visual_review,"preview":preview,"preview_report":preview_report,"jianying_report":draft_report}
        result = {"schema_version":"1.0", "status":"PHASE1_TOPIC_DRAFT_READY_FOR_JOVI_REVIEW",
                  "candidate_status":"PHASE1_TOPIC_DRAFT_READY_FOR_JOVI_REVIEW", "ready_status":"READY",
                  "automatic_export":False, "paths":{k:str(v) for k,v in paths.items()},
                  "hashes":{k:_sha(v) for k,v in paths.items()}, "draft_name":draft_name}
        validation.validate(result, "phase1_subject_media_result")
        persisted = _write_json_atomically(result_receipt, result)
        validation.validate(persisted, "phase1_subject_media_result")
        return persisted
    except Exception as exc:
        if result_receipt.exists():
            result_receipt.unlink()
        temporary_receipt = result_receipt.with_name(f".{result_receipt.name}.tmp")
        if temporary_receipt.exists():
            temporary_receipt.unlink()
        _write_failure(workdir, stage, exc)
        raise
