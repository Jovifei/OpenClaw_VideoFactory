"""Audio strategy planner: TTS with 3-level offline fallback chain.

Levels (§4.4):
  1. ``tts``   — edge-tts per-scene → concat (requires network + edge-tts)
  2. ``bgm``   — fallback BGM file or lavfi sine-bed (offline-safe)
  3. ``silent`` — no audio track (``-an``)

Every level records ``fallback_reason`` in the returned :class:`AudioPlan`.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .voice_generator import generate_voice


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
        overflow = seg_dur > duration

        segments.append({
            "scene_id": scene.get("scene_id", f"s{idx+1:02d}"),
            "narration": narration,
            "audio_file": str(seg_path.name),
            "actual_duration": round(seg_dur, 3),
            "scene_duration": duration,
            "overflow": overflow,
        })
        segment_paths.append(seg_path)

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


def _align_audio(input_path: Path, output_path: Path, *, target_duration: float) -> None:
    """Pad (apad) or trim (atrim) *input_path* to exactly *target_duration*."""
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
        # Trim to target (overflow case — we truncate)
        cmd = [
            "ffmpeg", "-y", "-nostdin", "-loglevel", "error",
            "-i", str(input_path),
            "-t", str(target_duration),
            "-acodec", "pcm_s16le",
            str(output_path),
        ]
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
