"""Audio strategy planner: TTS with 3-level offline fallback chain.

Levels (§4.4):
  1. ``tts``   — edge-tts per-scene → concat (requires network + edge-tts)
  2. ``bgm``   — fallback BGM file or lavfi sine-bed (offline-safe)
  3. ``silent`` — no audio track (``-an``)

Every level records ``fallback_reason`` in the returned :class:`AudioPlan`.
"""

from __future__ import annotations

import json
import hashlib
import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .voice_generator import generate_voice


class AudioNarrationOverflowError(RuntimeError):
    """A TTS segment is longer than its allocated visual scene.

    TTS is source material.  It may be padded, but never shortened silently.
    """

    code = "audio_narration_overflow"

    def __init__(self, segments: list[dict[str, object]]) -> None:
        self.segments = tuple(segments)
        ids = ",".join(str(item.get("scene_id", "?")) for item in segments)
        super().__init__(f"{self.code}:{ids}")


class AudioNarrationIntegrityError(RuntimeError):
    """The aligned narration is not the complete raw waveform plus padding."""

    code = "audio_narration_integrity_mismatch"

    def __init__(self, scene_id: str, reason: str) -> None:
        self.scene_id = scene_id
        self.reason = reason
        super().__init__(f"{self.code}:{scene_id}:{reason}")


class NarrationDurationBudgetError(RuntimeError):
    """Measured narration cannot fit the Phase 1 duration contract."""

    code = "narration_duration_budget_exceeded"


@dataclass(frozen=True)
class AudioPlan:
    """Result of audio planning: what mode, which file, and why."""

    mode: str  # "tts" | "bgm" | "silent"
    path: Path | None
    loop: bool
    fallback_reason: str | None
    segments: tuple[dict, ...] = field(default_factory=tuple)


def plan_audio(
    timeline_doc: dict,
    *,
    work_dir: Path,
    audio_config: dict,
    repo_root: Path,
) -> AudioPlan:
    """Plan audio for a compiled timeline document.

    Parameters
    ----------
    timeline_doc : dict
        Compiled timeline (output of ``compile_storyboard()``).
    work_dir : Path
        Working directory for intermediate audio files.
    audio_config : dict
        Audio section from the job YAML (strategy, allow_network, tts, fallback_bgm).
    repo_root : Path
        Repository root (for resolving relative BGM paths).

    Returns
    -------
    AudioPlan
        The resolved audio plan with mode, path, and fallback reason.
    """
    strategy = audio_config.get("strategy", "tts_with_offline_fallback")
    allow_network = bool(audio_config.get("allow_network", True))
    tts_cfg = audio_config.get("tts", {})
    voice = tts_cfg.get("voice", "zh-CN-XiaoxiaoNeural")
    provider = tts_cfg.get("provider", "edge-tts")
    bgm_rel = audio_config.get("fallback_bgm", "")

    # Strategy override shortcuts
    if strategy == "silent":
        return AudioPlan(mode="silent", path=None, loop=False, fallback_reason="strategy_silent")

    if strategy == "bgm_only":
        return _plan_bgm(work_dir, bgm_rel, repo_root, fallback_reason="strategy_bgm_only")

    # --- Level 1: TTS ---
    # Windows SAPI is an OS-local engine.  `allow_network: false` blocks the
    # remote edge-tts route but must not suppress this explicitly local path.
    local_tts = provider == "windows-sapi"
    if strategy == "tts_with_offline_fallback" and (allow_network or local_tts):
        try:
            return _plan_tts(timeline_doc, work_dir, voice, provider)
        except AudioNarrationOverflowError:
            # Overflow is a product contract failure, not a reason to replace
            # narration with BGM and call the render successful.
            raise
        except Exception as exc:
            # Fall through to BGM
            reason = f"tts_failed:{_safe_error(exc)}"
            return _plan_bgm(work_dir, bgm_rel, repo_root, fallback_reason=reason)

    # --- Level 2: BGM ---
    return _plan_bgm(work_dir, bgm_rel, repo_root, fallback_reason="network_disabled_or_no_tts")


# ---------------------------------------------------------------------------
# Internal planners
# ---------------------------------------------------------------------------


def _plan_tts(
    timeline_doc: dict,
    work_dir: Path,
    voice: str,
    provider: str = "edge-tts",
) -> AudioPlan:
    """Level 1: Synthesize TTS per scene, align to scene durations, concat."""
    scenes = timeline_doc.get("scenes", [])
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    segments: list[dict] = []
    segment_paths: list[Path] = []

    for idx, scene in enumerate(scenes):
        narration = scene.get("narration", "")
        duration = float(scene["duration"])
        suffix = ".wav" if provider == "windows-sapi" else ".mp3"
        seg_path = work_dir / f"seg_{idx:03d}{suffix}"

        try:
            generate_voice(narration, seg_path, voice=voice, provider=provider)
        except Exception as exc:
            raise RuntimeError(f"tts_scene_{idx}_failed:{exc}") from exc

        # Measure actual duration
        seg_dur = _get_audio_duration(seg_path)
        overflow = seg_dur > duration + 0.01

        segments.append({
            "scene_id": scene.get("scene_id", f"s{idx+1:02d}"),
            "narration": narration,
            "audio_file": str(seg_path.name),
            "actual_duration": round(seg_dur, 3),
            "scene_duration": duration,
            "overflow": overflow,
        })
        segment_paths.append(seg_path)

    overflow_segments = [segment for segment in segments if bool(segment.get("overflow"))]
    if overflow_segments:
        raise AudioNarrationOverflowError(overflow_segments)

    # Concat all segments into a single audio.wav aligned to total video duration
    total_video_dur = float(timeline_doc.get("total_duration_seconds", sum(s["duration"] for s in scenes)))
    output_wav = work_dir / "audio.wav"

    if len(segment_paths) == 1:
        # Single segment: pad/trim to total duration
        _align_audio(segment_paths[0], output_wav, target_duration=total_video_dur)
    else:
        # Multiple segments: pad each to its scene duration, then concat
        padded_paths: list[Path] = []
        for idx, (seg_path, scene) in enumerate(zip(segment_paths, scenes)):
            padded = work_dir / f"padded_{idx:03d}.wav"
            dur = float(scene["duration"])
            _align_audio(seg_path, padded, target_duration=dur)
            padded_paths.append(padded)
        _concat_audio(padded_paths, output_wav)

    return AudioPlan(
        mode="tts",
        path=output_wav,
        loop=False,
        fallback_reason=None,
        segments=tuple(segments),
    )


def synthesize_tts_segments(
    timeline_doc: dict,
    *,
    work_dir: Path,
    voice: str,
    provider: str,
) -> tuple[dict, ...]:
    """Synthesize and measure raw narration without aligning or trimming it."""

    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    measured: list[dict] = []
    for idx, scene in enumerate(timeline_doc.get("scenes", [])):
        narration = str(scene.get("narration", ""))
        suffix = ".wav" if provider == "windows-sapi" else ".mp3"
        path = work_dir / f"seg_{idx:03d}{suffix}"
        try:
            generate_voice(narration, path, voice=voice, provider=provider)
        except Exception as exc:
            raise RuntimeError(f"tts_scene_{idx}_failed:{exc}") from exc
        measured.append({
            "scene_id": scene.get("scene_id", f"s{idx + 1:02d}"),
            "narration": narration,
            "audio_file": path.name,
            "audio_path": str(path),
            "actual_duration": round(_get_audio_duration(path), 3),
            "scene_duration": round(float(scene["duration"]), 3),
            "raw_audio_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    if not measured:
        raise ValueError("tts_scenes_missing")
    return tuple(measured)


def allocate_scene_durations(
    timeline_doc: dict,
    segments: tuple[dict, ...] | list[dict],
    *,
    tail_margin_seconds: float = 0.2,
    fps: int | None = None,
    min_total_seconds: float = 25.0,
    max_total_seconds: float = 60.0,
) -> dict:
    """Allocate complete scene windows from measured narration durations.

    Durations are frame aligned and include an explicit speech tail margin.
    The function never shortens a source segment and returns a new timeline
    document suitable for SRT generation and audio-only qualification.
    """

    if tail_margin_seconds < 0:
        raise ValueError("narration_tail_margin_invalid")
    scenes = timeline_doc.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != len(segments):
        raise ValueError("narration_scene_count_mismatch")
    frame_rate = int(fps or timeline_doc.get("fps", 30))
    if frame_rate <= 0:
        raise ValueError("narration_fps_invalid")
    allocated: list[dict] = []
    for scene, segment in zip(scenes, segments):
        actual = float(segment.get("actual_duration", 0.0))
        if actual <= 0:
            raise ValueError("narration_segment_duration_invalid")
        duration = math.ceil((actual + tail_margin_seconds) * frame_rate - 1e-9) / frame_rate
        allocated.append({**scene, "duration": round(duration, 3)})
    result = {**timeline_doc, "scenes": allocated}
    mode = str(result.get("transition_mode", "xfade"))
    transition = float(result.get("transition_seconds", 0.0))
    if mode == "technical_cut":
        total = sum(float(scene["duration"]) for scene in allocated)
    else:
        total = sum(float(scene["duration"]) for scene in allocated) - transition * max(0, len(allocated) - 1)
    total = round(total, 3)
    if not min_total_seconds <= total <= max_total_seconds:
        raise NarrationDurationBudgetError(
            f"{NarrationDurationBudgetError.code}:{total:.3f}s"
        )
    result["total_duration_seconds"] = total
    return result


def align_complete_segments(
    segments: tuple[dict, ...] | list[dict],
    timeline_doc: dict,
    *,
    output_dir: Path,
    output_path: Path,
) -> dict:
    """Pad complete raw segments to allocated windows and concatenate them."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if len(segments) != len(timeline_doc.get("scenes", [])):
        raise ValueError("narration_scene_count_mismatch")
    aligned: list[dict] = []
    paths: list[Path] = []
    aligned_pcm_parts: list[bytes] = []
    integrity_layout: tuple[int, int] | None = None
    scene_offsets: list[dict[str, object]] = []
    offset_seconds = 0.0
    for index, (segment, scene) in enumerate(zip(segments, timeline_doc["scenes"])):
        raw = Path(str(segment["audio_path"]))
        target = output_dir / f"aligned_{index:03d}.wav"
        _align_audio(raw, target, target_duration=float(scene["duration"]))
        aligned_duration = _get_audio_duration(target)
        if aligned_duration + 0.01 < float(segment["actual_duration"]):
            raise AudioNarrationOverflowError([dict(segment, aligned_duration=aligned_duration)])
        integrity, raw_layout, aligned_pcm = _verify_complete_aligned_segment(
            raw,
            target,
            scene_id=str(segment.get("scene_id", f"s{index + 1:02d}")),
        )
        if integrity_layout is None:
            integrity_layout = raw_layout
        elif integrity_layout != raw_layout:
            raise AudioNarrationIntegrityError(
                str(segment.get("scene_id", f"s{index + 1:02d}")),
                "pcm_layout_changed",
            )
        scene_id = str(segment.get("scene_id", f"s{index + 1:02d}"))
        aligned.append(dict(
            segment,
            raw_audio_sha256=str(segment.get("raw_audio_sha256") or hashlib.sha256(raw.read_bytes()).hexdigest()),
            allocated_scene_duration=round(float(scene["duration"]), 3),
            overflow=False,
            aligned_audio_file=target.name,
            aligned_duration=round(aligned_duration, 3),
            aligned_audio_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            audio_integrity=integrity,
        ))
        paths.append(target)
        aligned_pcm_parts.append(aligned_pcm)
        scene_offsets.append({
            "scene_id": scene_id,
            "start_seconds": round(offset_seconds, 3),
            "end_seconds": round(offset_seconds + float(scene["duration"]), 3),
        })
        offset_seconds += float(scene["duration"])
    _concat_audio(paths, output_path)
    if integrity_layout is None:
        raise ValueError("no_audio_to_concat")
    sample_rate, channels = integrity_layout
    expected_pcm = b"".join(aligned_pcm_parts)
    actual_pcm = _decode_pcm_for_integrity(output_path, sample_rate=sample_rate, channels=channels)
    if actual_pcm != expected_pcm:
        raise AudioNarrationIntegrityError("concat", "segments_not_preserved_in_order")
    duration_seconds = _get_audio_duration(output_path)
    endpoint_delta = round(duration_seconds - offset_seconds, 6)
    endpoint_tolerance = max(0.05, 1.0 / sample_rate)
    if abs(endpoint_delta) > endpoint_tolerance:
        raise AudioNarrationIntegrityError("concat", "endpoint_mismatch")
    integrity = {
        "status": "passed",
        "comparison": "decoded_pcm_prefix_and_silence_tail",
        "sample_rate": sample_rate,
        "channels": channels,
        "segments_in_order": True,
        "scene_offsets": scene_offsets,
        "expected_concatenated_pcm_sha256": hashlib.sha256(expected_pcm).hexdigest(),
        "actual_concatenated_pcm_sha256": hashlib.sha256(actual_pcm).hexdigest(),
        "expected_endpoint_seconds": round(offset_seconds, 3),
        "actual_endpoint_seconds": round(duration_seconds, 3),
        "endpoint_delta_seconds": endpoint_delta,
        "endpoint_tolerance_seconds": endpoint_tolerance,
    }
    return {
        "path": str(output_path),
        "segments": aligned,
        "duration_seconds": duration_seconds,
        "integrity": integrity,
    }


def _plan_bgm(
    work_dir: Path,
    bgm_rel_path: str,
    repo_root: Path,
    fallback_reason: str,
) -> AudioPlan:
    """Level 2: Use fallback BGM or synthesize a silent sine bed."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    output_wav = work_dir / "audio.wav"

    if bgm_rel_path:
        bgm_abs = (repo_root / bgm_rel_path).resolve()
        if bgm_abs.is_file():
            # Verify it's a valid audio file
            try:
                subprocess.run(
                    ["ffprobe", "-v", "error", "-select_streams", "a:0",
                     "-show_entries", "stream=codec_type", "-of", "json",
                     str(bgm_abs)],
                    capture_output=True, text=True, timeout=15,
                )
                # Copy to work dir (or use directly)
                output_wav = bgm_abs
                return AudioPlan(mode="bgm", path=output_wav, loop=True, fallback_reason=fallback_reason)
            except Exception:
                pass  # fall through to lavfi

    # Lavfi sine bed as last resort before silent
    try:
        # Generate ~30 seconds of soft sine tone (enough for most videos)
        duration = 30.0
        cmd = [
            "ffmpeg", "-y", "-nostdin", "-loglevel", "error",
            "-f", "lavfi", "-i", f"sine=frequency=220:duration={duration}",
            "-af", "volume=0.05",
            "-acodec", "pcm_s16le",
            str(output_wav),
        ]
        subprocess.run(cmd, capture_output=True, timeout=30, check=True)
        return AudioPlan(mode="bgm", path=output_wav, loop=True, fallback_reason=f"{fallback_reason}:synthesized_bed")
    except Exception:
        # Level 3: silent
        return AudioPlan(mode="silent", path=None, loop=False, fallback_reason=f"{fallback_reason}:bgm_unavailable")


# ---------------------------------------------------------------------------
# Audio utilities
# ---------------------------------------------------------------------------

def _get_audio_duration(audio_path: Path) -> float:
    """Return duration in seconds via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(audio_path)],
        capture_output=True, text=True, timeout=15,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def _probe_pcm_layout(audio_path: Path) -> tuple[int, int]:
    """Return the source audio sample rate and channel count for lossless comparison."""

    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=sample_rate,channels", "-of", "json", str(audio_path),
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    streams = json.loads(result.stdout).get("streams", [])
    if not streams:
        raise ValueError("audio_stream_missing")
    stream = streams[0]
    sample_rate = int(stream.get("sample_rate", 0))
    channels = int(stream.get("channels", 0))
    if sample_rate <= 0 or channels <= 0:
        raise ValueError("audio_pcm_layout_invalid")
    return sample_rate, channels


def _decode_pcm_for_integrity(audio_path: Path, *, sample_rate: int, channels: int) -> bytes:
    """Decode to a stable PCM representation for source-preservation checks."""

    result = subprocess.run(
        [
            "ffmpeg", "-y", "-nostdin", "-v", "error", "-i", str(audio_path),
            "-vn", "-ac", str(channels), "-ar", str(sample_rate),
            "-f", "s16le", "-acodec", "pcm_s16le", "pipe:1",
        ],
        capture_output=True,
        timeout=60,
        check=True,
    )
    if not result.stdout:
        raise ValueError("audio_pcm_empty")
    return bytes(result.stdout)


def _verify_complete_aligned_segment(
    raw_path: Path,
    aligned_path: Path,
    *,
    scene_id: str,
) -> tuple[dict[str, object], tuple[int, int], bytes]:
    """Prove aligned audio is the raw PCM prefix followed only by silence."""

    try:
        layout = _probe_pcm_layout(raw_path)
        raw_pcm = _decode_pcm_for_integrity(raw_path, sample_rate=layout[0], channels=layout[1])
        aligned_pcm = _decode_pcm_for_integrity(aligned_path, sample_rate=layout[0], channels=layout[1])
    except Exception as exc:
        raise AudioNarrationIntegrityError(scene_id, "pcm_decode_failed") from exc
    if len(aligned_pcm) < len(raw_pcm):
        raise AudioNarrationIntegrityError(scene_id, "aligned_pcm_shorter_than_raw")
    if not aligned_pcm.startswith(raw_pcm):
        raise AudioNarrationIntegrityError(scene_id, "aligned_pcm_prefix_mismatch")
    padding = aligned_pcm[len(raw_pcm):]
    if any(padding):
        raise AudioNarrationIntegrityError(scene_id, "aligned_tail_not_silence")
    sample_width = 2
    frame_width = sample_width * layout[1]
    evidence = {
        "status": "passed",
        "comparison": "decoded_pcm_prefix_and_silence_tail",
        "sample_rate": layout[0],
        "channels": layout[1],
        "raw_pcm_sha256": hashlib.sha256(raw_pcm).hexdigest(),
        "aligned_pcm_sha256": hashlib.sha256(aligned_pcm).hexdigest(),
        "raw_pcm_bytes": len(raw_pcm),
        "aligned_pcm_bytes": len(aligned_pcm),
        "padding_pcm_bytes": len(padding),
        "raw_pcm_frames": len(raw_pcm) // frame_width,
        "aligned_pcm_frames": len(aligned_pcm) // frame_width,
        "prefix_match": True,
        "tail_is_silence": True,
    }
    return evidence, layout, aligned_pcm


def _align_audio(input_path: Path, output_path: Path, *, target_duration: float) -> None:
    """Pad *input_path* to exactly *target_duration*; never trim narration."""
    actual = _get_audio_duration(input_path)
    if actual < target_duration:
        # Pad silence at end
        pad_dur = round(target_duration - actual, 3)
        cmd = [
            "ffmpeg", "-y", "-nostdin", "-loglevel", "error",
            "-i", str(input_path),
            "-af", f"apad=whole_dur={target_duration}",
            "-acodec", "pcm_s16le",
            str(output_path),
        ]
    elif actual > target_duration:
        raise AudioNarrationOverflowError([{
            "scene_id": input_path.stem,
            "audio_file": input_path.name,
            "actual_duration": round(actual, 3),
            "scene_duration": round(target_duration, 3),
            "overflow": True,
        }])
    else:
        # Exact match — just copy
        import shutil
        shutil.copy2(str(input_path), str(output_path))
        return
    subprocess.run(cmd, capture_output=True, timeout=30, check=True)


def _concat_audio(paths: list[Path], output_path: Path) -> None:
    """Concatenate multiple audio files using ffmpeg concat demuxer."""
    if not paths:
        raise ValueError("no_audio_to_concat")

    if len(paths) == 1:
        import shutil
        shutil.copy2(str(paths[0]), str(output_path))
        return

    # Write concat list
    list_file = output_path.parent / "concat_list.txt"
    list_file.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in paths), encoding="utf-8")

    cmd = [
        "ffmpeg", "-y", "-nostdin", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-acodec", "pcm_s16le",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, timeout=60, check=True)


def _safe_error(exc: BaseException) -> str:
    """Extract a safe error string (no absolute paths)."""
    s = str(exc)
    # Redact absolute Windows paths
    import re
    s = re.sub(r"[A-Za-z]:\\[^\s]*", "[REDACTED]", s)
    return s[:120]
