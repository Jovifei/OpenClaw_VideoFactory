"""Shared, strict timing-manifest helpers for the local Jianying/Remotion chain.

The manifest deliberately contains only runtime-relative audio references and
hashes. It is the single timing authority for Remotion scenes, Jianying audio,
and native subtitles.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = "1.0"
DEFAULT_GAP_MICROSECONDS = 100_000
FPS = 30
FRAME_TOLERANCE_MICROSECONDS = (1_000_000 + FPS - 1) // FPS
MIN_VISUAL_DURATION_SECONDS = 25
MAX_VISUAL_DURATION_SECONDS = 120
VISUAL_CUE_IDS = ("watershed", "phase_lead", "time_scale", "design_fc", "design_validate", "next_preview")
MIN_DIRECTOR_BEATS = 5
MAX_DIRECTOR_BEATS = 9


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_script(path: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    beats = value.get("beats") if isinstance(value, dict) else None
    if not isinstance(beats, list) or not MIN_DIRECTOR_BEATS <= len(beats) <= MAX_DIRECTOR_BEATS:
        raise ValueError("script_beat_count_invalid")
    result: list[dict[str, str]] = []
    for index, beat in enumerate(beats, start=1):
        if not isinstance(beat, dict):
            raise ValueError(f"beat_{index}_invalid")
        narration = str(beat.get("narration", "")).strip()
        subtitle = str(beat.get("subtitle", "")).strip()
        if not narration or not subtitle:
            raise ValueError(f"beat_{index}_text_missing")
        result.append({"narration": narration, "subtitle": subtitle})
    return value, result


def validate_visual_cues(cues: Any, *, parent_start: int, parent_end: int) -> list[dict[str, Any]]:
    if not isinstance(cues, list) or [item.get("cue_id") if isinstance(item, dict) else None for item in cues] != list(VISUAL_CUE_IDS):
        raise ValueError("visual_cue_ids_invalid")
    previous_end = parent_start
    validated: list[dict[str, Any]] = []
    for item in cues:
        start = item.get("start_microseconds")
        end = item.get("end_microseconds")
        if not isinstance(start, int) or not isinstance(end, int) or start < previous_end or end <= start or end > parent_end:
            raise ValueError("visual_cue_range_invalid")
        validated.append(item)
        previous_end = end
    return validated


def _safe_relative(value: Any, field: str) -> str:
    raw = str(value or "").replace("\\", "/")
    if not raw or raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise ValueError(f"{field}_must_be_relative")
    parts = PurePosixPath(raw).parts
    if ".." in parts or any(part in {"", "."} for part in parts):
        raise ValueError(f"{field}_path_invalid")
    return "/".join(parts)


def resolve_audio_path(manifest: dict[str, Any], drafts_root: Path, segment: dict[str, Any]) -> Path:
    relative = _safe_relative(segment.get("audio_relative_path"), "audio_relative_path")
    root = drafts_root.resolve()
    target = (root / Path(*PurePosixPath(relative).parts)).resolve()
    if os.path.commonpath([str(root), str(target)]) != str(root):
        raise ValueError("audio_path_outside_drafts_root")
    if not target.is_file():
        raise ValueError("timing_audio_missing")
    return target


def manifest_audio_entries(parent_segment: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand an optional narration subsegment list into final VoiceOver entries."""
    subsegments = parent_segment.get("subsegments")
    if subsegments is None:
        return [parent_segment]
    if not isinstance(subsegments, list) or not subsegments or not all(isinstance(item, dict) for item in subsegments):
        raise ValueError("timing_subsegments_invalid")
    return [dict(item) for item in subsegments]


def validate_manifest(value: Any, *, drafts_root: Path | None = None) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("timing_manifest_schema_invalid")
    timing = value.get("timing")
    voice = value.get("voice")
    segments = value.get("segments")
    if not isinstance(timing, dict) or not isinstance(voice, dict) or not isinstance(segments, list) or not MIN_DIRECTOR_BEATS <= len(segments) <= MAX_DIRECTOR_BEATS:
        raise ValueError("timing_manifest_shape_invalid")
    fps = timing.get("fps")
    gap_us = timing.get("inter_segment_gap_microseconds")
    if fps != FPS or not isinstance(gap_us, int) or gap_us < 0 or gap_us > 2_000_000:
        raise ValueError("timing_policy_invalid")
    previous_end = 0
    previous_scene_end = 0
    for expected_index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict) or segment.get("index") != expected_index:
            raise ValueError("timing_segment_index_invalid")
        start = segment.get("start_microseconds")
        end = segment.get("end_microseconds")
        duration = segment.get("duration_microseconds")
        if not all(isinstance(item, int) and item >= 0 for item in (start, end, duration)):
            raise ValueError("timing_segment_values_invalid")
        if end != start + duration or end <= start:
            raise ValueError("timing_segment_range_invalid")
        if expected_index > 1 and start != previous_end + gap_us:
            raise ValueError("timing_segment_gap_invalid")
        if expected_index == 1 and start != 0:
            raise ValueError("timing_first_segment_must_start_at_zero")
        scene_start = segment.get("scene_start_microseconds")
        scene_end = segment.get("scene_end_microseconds")
        if scene_start != start or not isinstance(scene_end, int) or scene_end < end:
            raise ValueError("timing_scene_range_invalid")
        if expected_index > 1 and scene_start != previous_scene_end:
            raise ValueError("timing_scene_gap_invalid")
        if not isinstance(segment.get("audio_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", segment["audio_sha256"]):
            raise ValueError("timing_audio_hash_invalid")
        _safe_relative(segment.get("audio_relative_path"), "audio_relative_path")
        subsegments = segment.get("subsegments")
        if subsegments is not None:
            if not isinstance(subsegments, list) or not subsegments:
                raise ValueError("timing_subsegments_invalid")
            previous_sub_end = start
            for sub_index, subsegment in enumerate(subsegments, start=1):
                if not isinstance(subsegment, dict) or subsegment.get("index") != sub_index:
                    raise ValueError("timing_subsegment_index_invalid")
                sub_start = subsegment.get("start_microseconds")
                sub_end = subsegment.get("end_microseconds")
                sub_duration = subsegment.get("duration_microseconds")
                if not all(isinstance(item, int) for item in (sub_start, sub_end, sub_duration)) or sub_start < previous_sub_end or sub_end != sub_start + sub_duration:
                    raise ValueError("timing_subsegment_range_invalid")
                if not isinstance(subsegment.get("audio_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", subsegment["audio_sha256"]):
                    raise ValueError("timing_subsegment_audio_hash_invalid")
                _safe_relative(subsegment.get("audio_relative_path"), "subsegment_audio_relative_path")
                previous_sub_end = sub_end
            if subsegments[0]["start_microseconds"] != start or subsegments[-1]["end_microseconds"] != end:
                raise ValueError("timing_subsegment_parent_mismatch")
        previous_end = end
        previous_scene_end = scene_end
    if voice.get("segment_count") != len(segments) or voice.get("voice_end_microseconds") != previous_end:
        raise ValueError("timing_voice_end_invalid")
    visual_duration = value.get("visual_duration_seconds")
    if not isinstance(visual_duration, (int, float)) or not (MIN_VISUAL_DURATION_SECONDS <= float(visual_duration) <= MAX_VISUAL_DURATION_SECONDS):
        raise ValueError("timing_visual_duration_invalid")
    visual_duration_us = round(float(visual_duration) * 1_000_000)
    if visual_duration_us != previous_scene_end:
        raise ValueError("timing_scene_duration_invalid")
    if visual_duration_us < previous_end:
        raise ValueError("timing_visual_shorter_than_voice")
    visual_cues = value.get("visual_cues")
    if visual_cues:
        validate_visual_cues(visual_cues, parent_start=int(segments[-1]["start_microseconds"]), parent_end=int(segments[-1]["end_microseconds"]))
    if drafts_root is not None:
        for segment in segments:
            audio_path = resolve_audio_path(value, drafts_root, segment)
            if sha256(audio_path) != segment["audio_sha256"]:
                raise ValueError("timing_audio_hash_mismatch")
            for subsegment in manifest_audio_entries(segment) if segment.get("subsegments") is not None else []:
                audio_path = resolve_audio_path(value, drafts_root, subsegment)
                if sha256(audio_path) != subsegment["audio_sha256"]:
                    raise ValueError("timing_subsegment_audio_hash_mismatch")
    return value


def load_manifest(path: Path, *, drafts_root: Path | None = None) -> dict[str, Any]:
    return validate_manifest(json.loads(path.read_text(encoding="utf-8")), drafts_root=drafts_root)


def manifest_digest(path: Path) -> str:
    return sha256(path)
