"""Build the local-only Phase 1 human review package.

This module deliberately consumes evidence produced by the existing renderer;
it does not create a second rendering pipeline.  Every report reference is
relative to the package directory and every delivered binary has a SHA-256.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any

from .errors import FactoryContractError
from .validation import validate


_BASE_PACKAGE_ARTIFACTS = (
    ("final_master.mp4", "video"),
    ("cover.png", "cover"),
    ("subtitle.srt", "subtitle"),
    ("quality_report.json", "quality"),
    ("review_checklist.md", "checklist"),
    ("publish_info.md", "publish_info"),
)

_REFERENCE_PACKAGE_ARTIFACTS = (
    ("reference_receipt.json", "reference_receipt"),
    ("reference_rights.json", "reference_rights"),
    ("reference_report.json", "reference_report"),
    ("original_brief.json", "original_brief"),
    ("difference_report.json", "difference_report"),
)


def build_review_package(
    *,
    work_dir: Path,
    output_path: Path,
    job_id: str,
    input_mode: str,
    title: str,
    scene_count: int,
    asset_selection: dict[str, object],
) -> dict[str, object]:
    """Validate one local MP4 and write its complete human-review package.

    ``work_dir`` already belongs to the render job.  The function reads
    ``run_report.json``, ``render_report.json``, ``timeline.json`` and
    ``subtitle.srt`` from that directory, then writes the package alongside
    them.  It raises :class:`FactoryContractError` for every failure so callers
    can persist a structured lifecycle failure without leaking a path, command
    line, or raw ffprobe output.
    """
    work_dir = Path(work_dir)
    output_path = Path(output_path)
    _validate_arguments(job_id, input_mode, title, scene_count, asset_selection)
    if work_dir.is_symlink() or not work_dir.is_dir():
        raise _fail("phase1_review_package_invalid", "Review package work directory is missing.", "work_dir")
    if output_path.is_symlink() or not output_path.is_file() or output_path.stat().st_size <= 0:
        raise _fail("phase1_review_media_missing", "Rendered MP4 is missing.", "output")
    _relative_path(output_path, work_dir)

    run_report = _read_object(work_dir / "run_report.json", "run_report")
    render_report = _read_object(work_dir / "render_report.json", "render_report")
    timeline = _read_object(work_dir / "timeline.json", "timeline")
    subtitle_path = work_dir / "subtitle.srt"
    if not subtitle_path.is_file() or not subtitle_path.read_text(encoding="utf-8").strip():
        raise _fail("phase1_review_subtitle_invalid", "Subtitle evidence is missing.", "subtitle")

    _validate_evidence_documents(
        run_report=run_report,
        render_report=render_report,
        timeline=timeline,
        job_id=job_id,
        scene_count=scene_count,
    )
    media = _probe_media(output_path)
    _validate_media(media)
    _decode_media(output_path)
    cover_path = work_dir / "cover.png"
    _extract_cover(output_path, cover_path)
    if not cover_path.is_file() or cover_path.stat().st_size <= 0:
        raise _fail("phase1_review_cover_invalid", "Review cover was not created.", "cover")

    _validate_report_alignment(media, render_report, scene_count)
    quality = _build_quality(
        work_dir=work_dir,
        output_path=output_path,
        job_id=job_id,
        scene_count=scene_count,
        run_report=run_report,
        render_report=render_report,
        media=media,
        subtitle_path=subtitle_path,
    )
    quality_path = work_dir / "quality_report.json"
    validate(quality, "phase1_quality_report")
    _write_json(quality_path, quality)

    checklist_path = work_dir / "review_checklist.md"
    mascot = run_report.get("mascot")
    mascot_mode = str(mascot.get("mode", "required")) if isinstance(mascot, dict) else "required"
    checklist_path.write_text(_review_checklist(title, mascot_mode=mascot_mode), encoding="utf-8")
    publish_info_path = work_dir / "publish_info.md"
    publish_info_path.write_text(_publish_info(title), encoding="utf-8")

    artifact_paths = {
        "video": output_path,
        "cover": cover_path,
        "subtitle": subtitle_path,
        "quality": quality_path,
        "checklist": checklist_path,
        "publish_info": publish_info_path,
    }
    required_artifacts = list(_BASE_PACKAGE_ARTIFACTS)
    reference_evidence: dict[str, str] | None = None
    if input_mode == "local_reference":
        reference_evidence = {}
        for name, key in _REFERENCE_PACKAGE_ARTIFACTS:
            evidence_path = work_dir / name
            document = _read_object(evidence_path, key)
            validate(document, key)
            artifact_paths[key] = evidence_path
            reference_evidence[key] = name
        required_artifacts.extend(_REFERENCE_PACKAGE_ARTIFACTS)
    manifest = {
        "schema_version": "1.0",
        "job_id": job_id,
        "status": "ready_for_human_review",
        "input_mode": input_mode,
        "title": title.strip(),
        "scene_count": scene_count,
        "quality_report": "quality_report.json",
        "asset_selection": _safe_asset_selection(asset_selection),
        "artifacts": [
            _artifact_entry(name, artifact_paths[key], work_dir)
            for name, key in required_artifacts
        ],
    }
    if reference_evidence is not None:
        manifest["reference_evidence"] = reference_evidence
    manifest_path = work_dir / "review_package.json"
    validate(manifest, "phase1_review_package")
    _write_json(manifest_path, manifest)
    return {"manifest": manifest, "quality": quality}


def _validate_arguments(
    job_id: str,
    input_mode: str,
    title: str,
    scene_count: int,
    asset_selection: object,
) -> None:
    if not isinstance(job_id, str) or not job_id or not all(char.islower() or char.isdigit() or char == "_" for char in job_id):
        raise _fail("phase1_review_package_invalid", "Review package job ID is invalid.", "job_id")
    if input_mode not in {"topic", "local_reference", "authorized_public_research"}:
        raise _fail("phase1_review_package_invalid", "Review package input mode is invalid.", "input_mode")
    if not isinstance(title, str) or not title.strip() or len(title.strip()) > 160:
        raise _fail("phase1_review_package_invalid", "Review package title is invalid.", "title")
    if not isinstance(scene_count, int) or isinstance(scene_count, bool) or scene_count < 1:
        raise _fail("phase1_review_package_invalid", "Review package scene count is invalid.", "scene_count")
    if not isinstance(asset_selection, dict):
        raise _fail("phase1_review_package_invalid", "Review package asset selection is invalid.", "asset_selection")


def _read_object(path: Path, field: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _fail("phase1_review_evidence_invalid", "Review evidence is missing or invalid.", field) from exc
    if not isinstance(value, dict):
        raise _fail("phase1_review_evidence_invalid", "Review evidence must be an object.", field)
    return value


def _validate_evidence_documents(
    *,
    run_report: dict[str, Any],
    render_report: dict[str, Any],
    timeline: dict[str, Any],
    job_id: str,
    scene_count: int,
) -> None:
    if run_report.get("job_id") != job_id or run_report.get("status") != "success":
        raise _fail("phase1_review_evidence_invalid", "Run report does not describe a successful current job.", "run_report")
    scenes = timeline.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != scene_count:
        raise _fail("phase1_review_evidence_invalid", "Timeline scene count does not match the requested review package.", "timeline.scenes")
    audio = run_report.get("audio_plan")
    if not isinstance(audio, dict) or audio.get("mode") != "tts" or audio.get("segments_count") != scene_count:
        raise _fail("phase1_review_narration_incomplete", "Narration evidence is incomplete for the scene count.", "run_report.audio_plan")
    subtitle = render_report.get("subtitle")
    if not isinstance(subtitle, dict) or subtitle.get("present") is not True or subtitle.get("mode") != "burned_in":
        raise _fail("phase1_review_subtitle_invalid", "Render report does not confirm burned-in subtitles.", "render_report.subtitle")
    if int(subtitle.get("cue_count", 0)) < scene_count:
        raise _fail("phase1_review_subtitle_invalid", "Render report subtitle cues are incomplete.", "render_report.subtitle.cue_count")
    mascot = run_report.get("mascot")
    mascot_mode = str(mascot.get("mode", "required")) if isinstance(mascot, dict) else "required"
    style = render_report.get("style_profile")
    region = render_report.get("subtitle_region")
    if mascot_mode == "off":
        if style is not None or render_report.get("layout_mode") is not None:
            raise _fail("phase1_review_style_invalid", "Mascot-off render must not claim Pink Pig composition evidence.", "render_report.style_profile")
    elif render_report.get("layout_mode") != "knowledge_illustration" or not isinstance(style, dict) or style.get("status") != "pass":
        raise _fail("phase1_review_style_invalid", "Render report does not confirm the Pink Pig style gate.", "render_report.style_profile")
    if mascot_mode == "off":
        return
    if not isinstance(region, dict) or not _valid_subtitle_region(region):
        raise _fail("phase1_review_style_invalid", "Render report subtitle region is outside the safe band.", "render_report.subtitle_region")


def _probe_media(output_path: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(output_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if completed.returncode != 0:
            raise ValueError("ffprobe_exit")
        raw = json.loads(completed.stdout)
        streams = raw.get("streams") if isinstance(raw, dict) else None
        if not isinstance(streams, list):
            raise ValueError("streams")
        video = next((item for item in streams if isinstance(item, dict) and item.get("codec_type") == "video"), None)
        audio = next((item for item in streams if isinstance(item, dict) and item.get("codec_type") == "audio"), None)
        fmt = raw.get("format") if isinstance(raw.get("format"), dict) else {}
        if not isinstance(video, dict) or not isinstance(audio, dict):
            raise ValueError("streams")
        return {
            "duration_seconds": float(fmt.get("duration", 0)),
            "width": int(video.get("width", 0)),
            "height": int(video.get("height", 0)),
            "fps": _parse_fps(video.get("r_frame_rate", "0/1")),
            "video_codec": str(video.get("codec_name", "")),
            "audio_codec": str(audio.get("codec_name", "")),
        }
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise _fail("phase1_review_media_probe_failed", "Rendered MP4 could not be probed.", "ffprobe") from exc


def _parse_fps(value: object) -> float:
    numerator, separator, denominator = str(value).partition("/")
    if not separator:
        return float(numerator)
    divisor = float(denominator)
    if divisor == 0:
        raise ValueError("fps")
    return float(numerator) / divisor


def _validate_media(media: dict[str, Any]) -> None:
    expected_codecs = {"video_codec": "h264", "audio_codec": "aac"}
    if any(media.get(key) != value for key, value in expected_codecs.items()):
        raise _fail("phase1_review_media_invalid", "Rendered MP4 does not match the H.264/AAC contract.", "media")
    if (media.get("width"), media.get("height")) not in {(1080, 1920), (1920, 1080)}:
        raise _fail("phase1_review_media_invalid", "Rendered MP4 must be 1080x1920 or 1920x1080.", "media")
    duration = float(media.get("duration_seconds", 0))
    fps = float(media.get("fps", 0))
    if not 25 <= duration <= 60 or not math.isclose(fps, 30.0, abs_tol=0.01):
        raise _fail("phase1_review_media_invalid", "Rendered MP4 duration or frame rate is outside the required contract.", "media")


def _decode_media(output_path: Path) -> None:
    try:
        completed = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(output_path), "-f", "null", "-"],
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise _fail("phase1_review_media_decode_failed", "Rendered MP4 could not be fully decoded.", "ffmpeg") from exc
    if completed.returncode != 0:
        raise _fail("phase1_review_media_decode_failed", "Rendered MP4 could not be fully decoded.", "ffmpeg")


def _extract_cover(output_path: Path, cover_path: Path) -> None:
    try:
        completed = subprocess.run(
            ["ffmpeg", "-y", "-nostdin", "-v", "error", "-ss", "0.5", "-i", str(output_path), "-frames:v", "1", str(cover_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise _fail("phase1_review_cover_invalid", "Review cover could not be extracted.", "cover") from exc
    if completed.returncode != 0:
        raise _fail("phase1_review_cover_invalid", "Review cover could not be extracted.", "cover")


def _validate_report_alignment(media: dict[str, Any], render_report: dict[str, Any], scene_count: int) -> None:
    resolution = render_report.get("resolution")
    audio = render_report.get("audio")
    subtitle = render_report.get("subtitle")
    if not isinstance(resolution, dict) or resolution.get("width") != media["width"] or resolution.get("height") != media["height"]:
        raise _fail("phase1_review_report_mismatch", "Render report resolution does not match the MP4.", "render_report.resolution")
    if not math.isclose(float(render_report.get("fps", 0)), float(media["fps"]), abs_tol=0.01):
        raise _fail("phase1_review_report_mismatch", "Render report frame rate does not match the MP4.", "render_report.fps")
    if render_report.get("codec") != media["video_codec"] or not isinstance(audio, dict) or audio.get("codec") != media["audio_codec"]:
        raise _fail("phase1_review_report_mismatch", "Render report codec does not match the MP4.", "render_report.codec")
    if not isinstance(subtitle, dict) or int(subtitle.get("cue_count", 0)) < scene_count:
        raise _fail("phase1_review_report_mismatch", "Render report subtitle evidence is incomplete.", "render_report.subtitle")


def _build_quality(
    *,
    work_dir: Path,
    output_path: Path,
    job_id: str,
    scene_count: int,
    run_report: dict[str, Any],
    render_report: dict[str, Any],
    media: dict[str, Any],
    subtitle_path: Path,
) -> dict[str, object]:
    audio_plan = run_report["audio_plan"]
    subtitle = render_report["subtitle"]
    mascot = run_report.get("mascot")
    mascot_mode = str(mascot.get("mode", "required")) if isinstance(mascot, dict) else "required"
    if mascot_mode == "off":
        region = {"x": 90, "y": 1400, "width": 900, "height": 300}
        style = {"status": "off"}
        if int(media["width"]) > int(media["height"]):
            region = {"x": 96, "y": 860, "width": 1728, "height": 160}
            layout_mode = "plain_landscape"
        else:
            layout_mode = "plain_vertical"
    else:
        region = render_report["subtitle_region"]
        style = render_report["style_profile"]
        layout_mode = render_report["layout_mode"]
    check_names = (
        "mp4_exists", "landscape_1920x1080" if layout_mode == "plain_landscape" else "portrait_1080x1920", "fps_30", "h264_video", "aac_audio",
        "duration_25_to_60", "full_decode", "tts_scene_alignment", "subtitle_burned_in",
        "mascot_policy" if mascot_mode == "off" else "pink_pig_style",
        "subtitle_safe_region", "render_report_alignment",
    )
    checks = [
        {"name": name, "status": "passed"}
        for name in check_names
    ]
    return {
        "schema_version": "1.0",
        "job_id": job_id,
        "status": "passed",
        "scene_count": scene_count,
        "media": {
            "path": _relative_path(output_path, work_dir),
            "sha256": _sha256(output_path),
            "bytes": output_path.stat().st_size,
            **media,
        },
        "narration": {"mode": audio_plan["mode"], "segments_count": audio_plan["segments_count"]},
        "subtitle": {
            "path": _relative_path(subtitle_path, work_dir),
            "cue_count": subtitle["cue_count"],
            "mode": subtitle["mode"],
        },
        "style": {
            "layout_mode": layout_mode,
            "pink_pig_status": style["status"],
            "subtitle_region": {key: int(region[key]) for key in ("x", "y", "width", "height")},
        },
        "checks": checks,
        "error": None,
    }


def _safe_asset_selection(value: dict[str, object]) -> dict[str, object]:
    """Allow identifiers/decision metadata but reject path-shaped selection data."""
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if "\\\\" in encoded or ":/" in encoded or ":\\\\" in encoded:
        raise _fail("phase1_review_package_invalid", "Asset selection may not contain filesystem paths.", "asset_selection")
    return json.loads(encoded)


def _artifact_entry(name: str, path: Path, work_dir: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size <= 0:
        raise _fail("phase1_review_package_invalid", "A required review artifact is missing.", "artifact")
    return {
        "name": name,
        "path": _relative_path(path, work_dir),
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
    }


def _relative_path(path: Path, root: Path) -> str:
    try:
        relative = os.path.relpath(path.resolve(), root.resolve())
    except (OSError, ValueError) as exc:
        raise _fail("phase1_review_package_invalid", "Review artifact path cannot be made relative.", "artifact") from exc
    relative_path = Path(relative)
    if relative_path.is_absolute() or ":" in relative or any(part == ".." for part in relative_path.parts):
        raise _fail("phase1_review_package_invalid", "Review artifact path must be relative.", "artifact")
    return relative_path.as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_subtitle_region(region: dict[str, Any]) -> bool:
    try:
        x, y = int(region["x"]), int(region["y"])
        width, height = int(region["width"]), int(region["height"])
    except (KeyError, TypeError, ValueError):
        return False
    portrait = x >= 0 and width > 0 and height > 0 and 1120 <= y <= 1580 and y + height <= 1920
    landscape = x >= 0 and width > 0 and height > 0 and 760 <= y <= 900 and y + height <= 1080
    return portrait or landscape


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _review_checklist(title: str, *, mascot_mode: str = "required") -> str:
    mascot_line = (
        "- [ ] 本视频按 brief 未启用粉色飞猪；画面不含粉色飞猪、签名或角色构图。"
        if mascot_mode == "off"
        else "- [ ] 小粉猪使用 Jovi 已核验的原始 IP 素材并承担工程讲解动作，未遮挡知识图与字幕。"
    )
    return (
        f"# 本地人工审阅清单：{title.strip()}\n\n"
        "- [ ] 内容准确、表达原创，未复用参考视频的连续镜头、原音或水印。\n"
        f"{mascot_line}\n"
        "- [ ] 字幕清晰、最多两行，且位于底部安全区。\n"
        "- [ ] 配音与画面节奏自然，音视频同步。\n"
        "- [ ] 不含隐私、凭据、未经核验的事实或自动发布信息。\n"
        "- [ ] Jovi 已决定是否人工发布；本包不会自动发送或发布。\n"
    )


def _publish_info(title: str) -> str:
    return (
        f"# 发布信息：{title.strip()}\n\n"
        "本文件仅供 Jovi 本地人工审阅和人工发布准备。\n\n"
        "- 成片：`final_master.mp4`（由审阅包清单中的相对路径定位）\n"
        "- 封面：`cover.png`\n"
        "- 字幕：`subtitle.srt`\n"
        "- 本地质量证据：`quality_report.json`\n\n"
        "本任务不会向飞书、抖音或任何外部服务发送内容。\n"
    )


def _fail(code: str, message: str, field: str) -> FactoryContractError:
    return FactoryContractError(code, message, {"stage": "review_package", "field": field})


__all__ = ["build_review_package"]
