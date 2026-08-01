"""Local-only Remotion rendering and ffmpeg encoder selection."""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import time
import wave
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT
from .mascot import POSES, ensure_public_assets


TEMPLATES = {"protocol-frame", "code-explainer", "flow-diagram", "engineering-case"}
JOB_ID = re.compile(r"^job-[a-f0-9]{24}$")
MIN_DURATION_SECONDS = 25
MAX_DURATION_SECONDS = 60
FPS = 30


def chrome_executable() -> Path:
    for candidate in (
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
    ):
        if candidate.exists():
            return candidate
    raise RuntimeError("local_chrome_required")


def build_render_input(
    *,
    job_id: str,
    template: str,
    title: str,
    scenes: list[dict[str, str]],
    captions: list[dict[str, Any]],
    mascot_pose: str,
    audio_asset: str,
    requested_duration_seconds: int,
    resolved_duration_seconds: float,
    audio_duration_seconds: float,
) -> dict[str, Any]:
    if not JOB_ID.fullmatch(job_id):
        raise ValueError("job_id_invalid")
    if template not in TEMPLATES:
        raise ValueError("template_invalid")
    if mascot_pose not in POSES:
        raise ValueError("mascot_pose_invalid")
    if (
        not audio_asset.startswith(f"runtime/{job_id}/")
        or not audio_asset.endswith(".wav")
        or any(part in audio_asset for part in ("..", "://", "\\"))
    ):
        raise ValueError("audio_asset_invalid")
    if not isinstance(requested_duration_seconds, int) or not (
        MIN_DURATION_SECONDS <= requested_duration_seconds <= MAX_DURATION_SECONDS
    ):
        raise ValueError("requested_duration_invalid")
    if not MIN_DURATION_SECONDS <= resolved_duration_seconds <= MAX_DURATION_SECONDS:
        raise ValueError("resolved_duration_invalid")
    if not 0 < audio_duration_seconds <= resolved_duration_seconds:
        raise ValueError("audio_duration_invalid")
    if not scenes or len(scenes) > 5:
        raise ValueError("scenes_invalid")
    timed_scenes: list[dict[str, Any]] = []
    for index, scene in enumerate(scenes):
        if not isinstance(scene.get("heading"), str) or not isinstance(scene.get("body"), str):
            raise ValueError("scene_invalid")
        start = round(resolved_duration_seconds * index / len(scenes), 3)
        end = round(resolved_duration_seconds * (index + 1) / len(scenes), 3)
        timed_scenes.append({**scene, "start_seconds": start, "end_seconds": end})
    return {
        "schema_version": "2.0",
        "job_id": job_id,
        "template": template,
        "title": title,
        "requested_duration_seconds": requested_duration_seconds,
        "resolved_duration_seconds": resolved_duration_seconds,
        "fps": FPS,
        "scenes": timed_scenes,
        "captions": captions,
        "mascot": {"asset": f"mascot/{mascot_pose}.svg", "pose": mascot_pose},
        "audio": {"asset": audio_asset, "duration_seconds": round(audio_duration_seconds, 3)},
    }


def build_legacy_render_input(
    *,
    job_id: str,
    template: str,
    title: str,
    scenes: list[dict[str, str]],
    captions: list[dict[str, Any]],
    mascot_pose: str,
    audio_asset: str,
) -> dict[str, Any]:
    """Keep existing v1 jobs recoverable without creating new v1 jobs."""
    if not JOB_ID.fullmatch(job_id):
        raise ValueError("job_id_invalid")
    if template not in TEMPLATES:
        raise ValueError("template_invalid")
    if mascot_pose not in POSES:
        raise ValueError("mascot_pose_invalid")
    if (
        not audio_asset.startswith(f"runtime/{job_id}/")
        or not audio_asset.endswith(".wav")
        or any(part in audio_asset for part in ("..", "://", "\\"))
    ):
        raise ValueError("audio_asset_invalid")
    return {
        "schema_version": "1.0",
        "job_id": job_id,
        "template": template,
        "title": title,
        "scenes": scenes,
        "captions": captions,
        "mascot": {"asset": f"mascot/{mascot_pose}.svg", "pose": mascot_pose},
        "audio": {"asset": audio_asset, "duration_seconds": 10},
    }


def wav_duration_seconds(audio: Path) -> float:
    try:
        with wave.open(str(audio), "rb") as wav:
            if wav.getframerate() <= 0 or wav.getnframes() <= 0:
                raise RuntimeError("wav_duration_invalid")
            return wav.getnframes() / wav.getframerate()
    except wave.Error as exc:
        raise RuntimeError("wav_duration_invalid") from exc


def resolve_duration_seconds(audio: Path, requested_duration_seconds: int) -> float:
    if not isinstance(requested_duration_seconds, int) or not (
        MIN_DURATION_SECONDS <= requested_duration_seconds <= MAX_DURATION_SECONDS
    ):
        raise ValueError("requested_duration_invalid")
    resolved = max(MIN_DURATION_SECONDS, math.ceil(wav_duration_seconds(audio) + 1.5))
    if resolved > MAX_DURATION_SECONDS:
        raise RuntimeError("narration_too_long")
    return float(resolved)


def stage_audio(job_id: str, audio: Path) -> str:
    if not JOB_ID.fullmatch(job_id) or not audio.exists():
        raise RuntimeError("staging_input_invalid")
    public_root = PROJECT_ROOT / "remotion" / "public"
    ensure_public_assets(public_root)
    destination = public_root / "runtime" / job_id / "voice.wav"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(audio, destination)
    return destination.relative_to(public_root).as_posix()


def _process_snapshot(pid: int) -> tuple[float, int] | None:
    """Return only CPU seconds and working-set bytes for the local render child."""
    command = (
        "$p=Get-Process -Id "
        f"{pid} -ErrorAction Stop;"
        "[pscustomobject]@{cpu=[double]$p.CPU;working_set=[int64]$p.WorkingSet64}|ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        text=True,
        capture_output=True,
        check=False,
        timeout=5,
    )
    if result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout)
        return float(value["cpu"]), int(value["working_set"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _gpu_memory_mib() -> int | None:
    if shutil.which("nvidia-smi") is None:
        return None
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        text=True,
        capture_output=True,
        check=False,
        timeout=5,
    )
    try:
        values = [int(line.strip()) for line in result.stdout.splitlines() if line.strip()]
        return max(values) if values else None
    except ValueError:
        return None


def _render_metrics(
    process: subprocess.Popen[str], raw_output: Path
) -> dict[str, int | float | None]:
    """Sample only scalar local process/GPU/staging usage while rendering."""
    peak_cpu_percent: float | None = None
    peak_working_set: int | None = None
    peak_gpu_memory: int | None = None
    staging_peak = 0
    previous_cpu: float | None = None
    previous_time: float | None = None
    last_sample = 0.0
    while process.poll() is None:
        now = time.monotonic()
        if now - last_sample >= 1.0:
            last_sample = now
            snapshot = _process_snapshot(process.pid)
            if snapshot is not None:
                cpu_seconds, working_set = snapshot
                peak_working_set = max(peak_working_set or 0, working_set)
                if previous_cpu is not None and previous_time is not None and now > previous_time:
                    cpu_percent = max(0.0, (cpu_seconds - previous_cpu) * 100 / (now - previous_time))
                    peak_cpu_percent = max(peak_cpu_percent or 0.0, cpu_percent)
                previous_cpu, previous_time = cpu_seconds, now
            gpu_memory = _gpu_memory_mib()
            if gpu_memory is not None:
                peak_gpu_memory = max(peak_gpu_memory or 0, gpu_memory)
            staging_bytes = (
                sum(item.stat().st_size for item in raw_output.parent.rglob("*") if item.is_file())
                if raw_output.parent.exists()
                else 0
            )
            staging_peak = max(staging_peak, staging_bytes)
        time.sleep(0.2)
    return {
        "peak_cpu_percent": round(peak_cpu_percent, 2) if peak_cpu_percent is not None else None,
        "peak_working_set_bytes": peak_working_set,
        "peak_gpu_memory_mib": peak_gpu_memory,
        "staging_peak_bytes": staging_peak,
    }


def render_raw(input_path: Path, raw_output: Path, *, concurrency: int = 1) -> dict[str, Any]:
    if concurrency not in {1, 2, 4}:
        raise ValueError("render_concurrency_invalid")
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    script = PROJECT_ROOT / "remotion" / "scripts" / "render-candidate.mjs"
    process = subprocess.Popen(
        [
            "node",
            str(script),
            str(input_path),
            str(raw_output),
            str(chrome_executable()),
            str(concurrency),
        ],
        cwd=PROJECT_ROOT / "remotion",
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    sampled = _render_metrics(process, raw_output)
    stdout, _stderr = process.communicate()
    if process.returncode != 0 or not raw_output.exists():
        raise RuntimeError("remotion_render_failed")
    try:
        runtime = json.loads(stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        raise RuntimeError("remotion_metrics_missing") from None
    metrics = runtime.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("remotion_metrics_missing")
    return {
        "renderer": "remotion",
        "metrics": {
            "resolved_concurrency": metrics.get("resolved_concurrency"),
            "rendered_frames": metrics.get("rendered_frames"),
            "encoded_frames": metrics.get("encoded_frames"),
            "rendered_done_in_seconds": metrics.get("rendered_done_in_seconds"),
            "encoded_done_in_seconds": metrics.get("encoded_done_in_seconds"),
            **sampled,
        },
    }


def _available_encoders() -> str:
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"], text=True, capture_output=True, check=False
    )
    return result.stdout + result.stderr


def encode_video(
    source: Path, target: Path, encoder: str, *, preview: bool = False
) -> dict[str, Any]:
    if encoder not in {"auto", "nvenc", "cpu"}:
        raise ValueError("encoder_invalid")
    candidates = (
        ["h264_nvenc", "libx264"]
        if encoder == "auto"
        else ["h264_nvenc" if encoder == "nvenc" else "libx264"]
    )
    fallback_reason = "none"
    if encoder == "auto" and "h264_nvenc" not in _available_encoders():
        candidates = ["libx264"]
        fallback_reason = "nvenc_unavailable"
    elif encoder == "cpu":
        fallback_reason = "encoder_not_requested"
    target.parent.mkdir(parents=True, exist_ok=True)
    for selected in candidates:
        if target.exists():
            target.unlink()
        bitrate = "1200k" if preview else "4500k"
        command = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-c:v",
            selected,
            "-b:v",
            bitrate,
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(target),
        ]
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        if result.returncode == 0 and target.exists() and target.stat().st_size > 0:
            return {
                "encoder": selected,
                "fallback": selected != candidates[0] or fallback_reason != "none",
                "fallback_reason": fallback_reason,
                "preview": preview,
            }
        if selected == "h264_nvenc" and encoder == "auto":
            fallback_reason = "nvenc_failed"
    raise RuntimeError("video_encode_failed")


def write_render_input(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
