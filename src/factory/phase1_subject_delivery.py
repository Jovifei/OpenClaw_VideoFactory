"""Fail-closed local review packaging for a completed subject-media receipt.

This module deliberately creates a review package, never a Jianying export or
published deliverable.  Tests may inject synthetic probe/decode evidence; the
default functions run the real local tools when this service is actually used.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from video_factory.pipeline import validation
from .phase1_subject_media import validate_ready_reports
from .phase1_topic_visual import verify_report_artifacts


_RECEIPT_KEYS = ("timing_manifest", "render_report", "visual_review", "preview", "preview_report", "jianying_report")
_INPUTS = ("topic_request", "research_brief", "script_candidates", "selected_script", "director_script", "scene_plan")


@dataclass(frozen=True)
class SubjectDeliveryRequest:
    job_id: str
    attempt: int
    subject_root: Path
    media_root: Path
    package_root: Path
    requested_duration_seconds: int
    aspect: str


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("subject_delivery_media_receipt_invalid")
    return value


def _contained(root: Path, candidate: Path, *, error: str) -> Path:
    try:
        resolved_root, resolved = root.resolve(strict=True), candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise ValueError(error) from exc
    if not resolved.is_file() or resolved.is_symlink():
        raise ValueError(error)
    return resolved


def _package_dir(request: SubjectDeliveryRequest) -> Path:
    if request.attempt < 1:
        raise ValueError("subject_delivery_package_path_invalid")
    root = request.package_root.resolve()
    attempt = root / f"attempt_{request.attempt}"
    if attempt.exists() and (attempt.is_symlink() or not attempt.is_dir()):
        raise ValueError("subject_delivery_package_path_invalid")
    result = attempt / "review_package"
    if result.exists() or result.is_symlink():
        raise ValueError("subject_delivery_package_path_invalid")
    result.mkdir(parents=True, exist_ok=False)
    return result


def _validate_receipt(media_root: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    if not validation.is_available():
        raise ValueError("subject_delivery_schema_validation_unavailable")
    root = media_root.resolve(strict=True)
    receipt_path = root / "subject_media_result.json"
    receipt = _load(_contained(root, receipt_path, error="subject_delivery_media_receipt_invalid"))
    try:
        validation.validate(receipt, "phase1_subject_media_result")
        if receipt["ready_status"] != "READY" or receipt["automatic_export"] is not False:
            raise ValueError
        paths = {}
        for key in _RECEIPT_KEYS:
            raw = Path(str(receipt["paths"][key]))
            if not raw.is_absolute():
                raise ValueError
            paths[key] = _contained(root, raw, error="subject_delivery_media_receipt_invalid")
        if any(_sha(paths[key]) != receipt["hashes"][key] for key in _RECEIPT_KEYS):
            raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("subject_delivery_media_receipt_invalid") from exc
    paths["media_receipt"] = receipt_path
    return receipt, paths


def validate_subject_media_receipt(media_root: Path) -> dict[str, Any]:
    """Public reuse guard for a persisted media attempt; it never trusts a path alone."""
    return _validate_receipt(media_root)[0]


def _probe_preview(path: Path) -> dict[str, object]:
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate", "-of", "json", str(path)]
    completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
    if completed.returncode != 0:
        raise ValueError("subject_delivery_preview_probe_failed")
    try:
        value = json.loads(completed.stdout)
        streams = value["streams"]
        video = next(item for item in streams if item["codec_type"] == "video")
        audio = next(item for item in streams if item["codec_type"] == "audio")
        numerator, denominator = str(video["r_frame_rate"]).split("/", 1)
        return {"width": int(video["width"]), "height": int(video["height"]), "fps": float(numerator) / float(denominator), "duration_seconds": float(value["format"]["duration"]), "video_codec": str(video["codec_name"]).lower(), "audio_codec": str(audio["codec_name"]).lower()}
    except (KeyError, StopIteration, TypeError, ValueError, ZeroDivisionError, json.JSONDecodeError) as exc:
        raise ValueError("subject_delivery_preview_probe_invalid") from exc


def _decode_preview(path: Path) -> bool:
    completed = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], capture_output=True, text=True, check=False, timeout=900)
    return completed.returncode == 0


def _srt(timing: dict[str, Any], director_script: dict[str, Any]) -> str:
    segments = timing.get("segments")
    beats = director_script.get("beats")
    if not isinstance(segments, list) or not segments or not isinstance(beats, list) or len(beats) != len(segments):
        raise ValueError("subject_delivery_timing_invalid")
    def stamp(value: int) -> str:
        milliseconds = value // 1000
        hours, milliseconds = divmod(milliseconds, 3_600_000)
        minutes, milliseconds = divmod(milliseconds, 60_000)
        seconds, milliseconds = divmod(milliseconds, 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
    blocks: list[str] = []
    for index, (segment, beat) in enumerate(zip(segments, beats), start=1):
        try:
            start, end = int(segment["start_microseconds"]), int(segment["end_microseconds"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("subject_delivery_timing_invalid") from exc
        if end <= start:
            raise ValueError("subject_delivery_timing_invalid")
        text = str(beat.get("subtitle", "")).strip()
        if not text or segment.get("subtitle_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
            raise ValueError("subject_delivery_timing_invalid")
        blocks.append(f"{index}\n{stamp(start)} --> {stamp(end)}\n{text}")
    return "\n\n".join(blocks) + "\n"


def _native_subtitles(draft: dict[str, Any], *, scene_count: int, expanded_audio_count: int) -> None:
    try:
        subtitle = draft["subtitle_validation"]
        tracks = {str(item["name"]): item for item in draft["tracks"]}
        if subtitle["status"] != "passed" or subtitle["authoritative_layer"] != "jianying_native_subtitles_track" or subtitle["burned_in_visual_must_be_false"] is not True or int(subtitle["segment_count"]) != scene_count:
            raise ValueError
        if int(tracks["Subtitles"]["segment_count"]) != scene_count or int(tracks["VoiceOver"]["segment_count"]) != expanded_audio_count:
            raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("subject_delivery_native_subtitles_invalid") from exc


def _copy(package: Path, source: Path, relative: str, role: str, artifacts: list[dict[str, Any]]) -> Path:
    target = package / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    artifacts.append({"name": target.name, "path": relative.replace("\\", "/"), "sha256": _sha(target), "bytes": target.stat().st_size, "role": role})
    return target


def _write_json_atomically(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        raise ValueError("subject_delivery_temp_exists")
    with temporary.open("xb") as handle:
        handle.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def _check_cancelled(package: Path, cancel_requested: Callable[[], bool], stage: str) -> None:
    if not cancel_requested():
        return
    cancelled = package / "cancelled.json"
    if not cancelled.exists():
        _write_json_atomically(cancelled, {"schema_version": "1.0", "status": "cancelled_before_ready_manifest", "stage": stage, "ready_manifest_written": False})
    raise ValueError("subject_delivery_cancelled")


def build_subject_review_package(request: SubjectDeliveryRequest, *, probe_media: Callable[[Path], dict[str, object]] = _probe_preview, decode_media: Callable[[Path], bool] = _decode_preview, cancel_requested: Callable[[], bool] = lambda: False) -> dict[str, Any]:
    """Copy verified evidence into one immutable local review package."""
    if not validation.is_available():
        raise ValueError("subject_delivery_schema_validation_unavailable")
    if request.aspect not in {"16:9", "9:16"} or not 25 <= request.requested_duration_seconds <= 60:
        raise ValueError("subject_delivery_request_invalid")
    receipt, receipt_paths = _validate_receipt(request.media_root)
    package = _package_dir(request)
    artifacts: list[dict[str, Any]] = []
    try:
        _check_cancelled(package, cancel_requested, "before_package_copy")
        for name in _INPUTS:
            source = _contained(request.subject_root.resolve(strict=True), request.subject_root / f"{name}.json", error="subject_delivery_input_invalid")
            _copy(package, source, f"inputs/{name}.json", "input", artifacts)
        for key, role in (("media_receipt", "media_receipt"), ("timing_manifest", "timing"), ("render_report", "render"), ("visual_review", "visual_review"), ("preview", "preview"), ("preview_report", "preview_report"), ("jianying_report", "jianying")):
            destination = "evidence/subject_media_result.json" if key == "media_receipt" else ("evidence/audible_preview.mp4" if key == "preview" else f"evidence/{receipt_paths[key].name}")
            _copy(package, receipt_paths[key], destination, role, artifacts)
        media_root = request.media_root.resolve(strict=True)
        timing = _load(receipt_paths["timing_manifest"])
        render = _load(receipt_paths["render_report"])
        visual_review = _load(receipt_paths["visual_review"])
        preview_report = _load(receipt_paths["preview_report"])
        draft = _load(receipt_paths["jianying_report"])
        director = _load(_contained(request.subject_root.resolve(strict=True), request.subject_root / "director_script.json", error="subject_delivery_input_invalid"))
        visual = _contained(media_root, media_root / "visual_master.mp4", error="subject_delivery_evidence_invalid")
        contact = _contained(media_root, media_root / "contact_sheet.png", error="subject_delivery_evidence_invalid")
        post = _contained(media_root, media_root / "post_render_check.json", error="subject_delivery_evidence_invalid")
        verified = verify_report_artifacts(receipt_paths["render_report"], visual, media_root / "stills", media_root / "clips", scene_count=len(timing.get("segments", [])))
        if visual_review.get("visual", {}).get("sha256") != _sha(visual) or visual_review.get("contact_sheet", {}).get("sha256") != _sha(contact) or visual_review.get("post_render_report", {}).get("sha256") != _sha(post):
            raise ValueError("subject_delivery_evidence_invalid")
        expanded_audio_count = int(timing.get("voice", {}).get("rendered_audio_segment_count", 0))
        validate_ready_reports({"timing": timing, "render": render, "visual_review": visual_review, "preview": preview_report, "jianying": draft}, scene_count=len(verified["clips"]), expanded_audio_count=expanded_audio_count, visual_duration_us=round(request.requested_duration_seconds * 1_000_000))
        _native_subtitles(draft, scene_count=len(verified["clips"]), expanded_audio_count=expanded_audio_count)
        _copy(package, visual, "evidence/visual_master.mp4", "visual", artifacts)
        _copy(package, contact, "evidence/contact_sheet.png", "contact_sheet", artifacts)
        _copy(package, post, "evidence/post_render_check.json", "post_render", artifacts)
        for source in verified["clips"]:
            _copy(package, source, f"evidence/clips/{source.name}", "clip", artifacts)
        for source in verified["stills"]:
            _copy(package, source, f"evidence/stills/{source.name}", "still", artifacts)
        srt_path = package / "evidence/native_subtitles.srt"
        srt_path.write_text(_srt(timing, director), encoding="utf-8")
        artifacts.append({"name": srt_path.name, "path": "evidence/native_subtitles.srt", "sha256": _sha(srt_path), "bytes": srt_path.stat().st_size, "role": "native_subtitles"})
        preview = receipt_paths["preview"]
        package_preview = package / "evidence" / "audible_preview.mp4"
        probe = probe_media(preview)
        expected_width, expected_height = ((1920, 1080) if request.aspect == "16:9" else (1080, 1920))
        checks = {"h264": probe.get("video_codec") == "h264", "aac": probe.get("audio_codec") == "aac", "fps_30": abs(float(probe.get("fps", 0)) - 30.0) < 0.001, "canvas": (probe.get("width"), probe.get("height")) == (expected_width, expected_height), "duration": abs(float(probe.get("duration_seconds", 0)) - request.requested_duration_seconds) <= 1.0, "full_decode": decode_media(preview), "native_subtitles": True, "automatic_export_disabled": receipt["automatic_export"] is False}
        if not all(checks.values()):
            raise ValueError("subject_delivery_quality_failed")
        _check_cancelled(package, cancel_requested, "after_preview_decode")
        quality = {"schema_version": "1.0", "job_id": request.job_id, "attempt": request.attempt, "status": "passed", "preview": {"path": "evidence/audible_preview.mp4", "sha256": _sha(package_preview), "bytes": package_preview.stat().st_size, "width": expected_width, "height": expected_height, "fps": 30, "duration_seconds": float(probe["duration_seconds"]), "video_codec": "h264", "audio_codec": "aac", "full_decode": True}, "subtitle": {"mode": "native_jianying_track_not_burned_in", "review_srt": "evidence/native_subtitles.srt", "cue_count": len(timing["segments"]), "burned_in": False}, "checks": [{"name": name, "status": "passed"} for name in checks], "human_review_required": True, "automatic_export": False}
        validation.validate(quality, "phase1_subject_quality_report")
        quality_path = package / "subject_quality_report.json"
        quality_path.write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        artifacts.append({"name": "subject_quality_report.json", "path": "subject_quality_report.json", "sha256": _sha(quality_path), "bytes": quality_path.stat().st_size, "role": "quality"})
        checklist = package / "REVIEW_CHECKLIST.md"
        checklist.write_text("# Local review required\n\n- Listen to the audible preview.\n- Inspect native Jianying subtitles and draft.\n- Export and publish are manual-only.\n", encoding="utf-8")
        artifacts.append({"name": "REVIEW_CHECKLIST.md", "path": "REVIEW_CHECKLIST.md", "sha256": _sha(checklist), "bytes": checklist.stat().st_size, "role": "review_instructions"})
        review = {"schema_version": "1.0", "package_kind": "phase1_subject", "job_id": request.job_id, "attempt": request.attempt, "status": "ready_for_human_review", "preview_status": "preview_not_jianying_export", "title": "Local subject preview — human review required", "input_mode": "topic", "human_review_required": True, "automatic_export": False, "media_receipt": "evidence/subject_media_result.json", "quality_report": "subject_quality_report.json", "review_checklist": "REVIEW_CHECKLIST.md", "artifacts": artifacts}
        validation.validate(review, "phase1_subject_review_package")
        review_path = package / "review_package.json"
        _check_cancelled(package, cancel_requested, "before_ready_manifest")
        _write_json_atomically(review_path, review)
        return {"package_path": str(package), "review_package": str(review_path), "quality_report": str(quality_path), "media_receipt": str(receipt_paths["media_receipt"]), "preview": str(package_preview)}
    except Exception:
        # Keep partial evidence for inspection; callers record REVIEW_BLOCKED/FAILED.
        raise
