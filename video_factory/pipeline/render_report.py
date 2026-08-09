"""Stable, audit-friendly report for one rendered video artifact."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import FactoryContractError


def _fps(value: str | int | float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    numerator, separator, denominator = str(value).partition("/")
    if not separator:
        return float(numerator)
    denominator_value = float(denominator)
    if denominator_value == 0:
        raise ValueError("zero denominator")
    return float(numerator) / denominator_value


def _probe_failure(message: str, field: str) -> FactoryContractError:
    return FactoryContractError(
        "render_report_probe_failed",
        message,
        {"field": field},
    )


def build_render_report(
    *,
    ffprobe_meta: dict[str, Any],
    timeline: dict[str, Any],
    subtitle_path: Path,
    captions_count: int,
) -> dict[str, Any]:
    """Build a deterministic report from real probe data and pipeline evidence."""
    if ffprobe_meta.get("error") or not ffprobe_meta.get("has_audio") and "video" not in ffprobe_meta:
        raise _probe_failure("ffprobe did not return usable media metadata.", "ffprobe")

    video = ffprobe_meta.get("video") or {}
    if not video.get("codec") or not video.get("width") or not video.get("height"):
        raise _probe_failure("ffprobe returned no complete video stream.", "video")

    try:
        fps = round(_fps(video.get("fps", "0/1")), 3)
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise _probe_failure("ffprobe returned an invalid frame rate.", "video.fps") from exc
    if fps <= 0:
        raise _probe_failure("ffprobe returned a non-positive frame rate.", "video.fps")

    audio = ffprobe_meta.get("audio") or {}
    sample_rate: int | None
    try:
        sample_rate = int(audio["sample_rate"]) if audio.get("sample_rate") else None
    except (TypeError, ValueError) as exc:
        raise _probe_failure("ffprobe returned an invalid audio sample rate.", "audio.sample_rate") from exc

    scenes = timeline.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise FactoryContractError(
            "render_report_invalid",
            "Timeline has no scenes for asset traceability.",
            {"field": "timeline.scenes"},
        )
    asset_ids = [str(scene["asset_id"]) for scene in scenes]

    subtitle_present = subtitle_path.is_file() and captions_count > 0
    return {
        "schema_version": "1.0",
        "duration": round(float(ffprobe_meta.get("duration", 0.0)), 3),
        "resolution": {
            "width": int(video["width"]),
            "height": int(video["height"]),
        },
        "fps": fps,
        "codec": str(video["codec"]),
        "audio": {
            "present": bool(ffprobe_meta.get("has_audio")),
            "codec": str(audio.get("codec", "")),
            "sample_rate": sample_rate,
        },
        "subtitle": {
            "present": subtitle_present,
            "mode": "burned_in" if subtitle_present else "disabled",
            "cue_count": int(captions_count),
        },
        "asset_ids": asset_ids,
    }
