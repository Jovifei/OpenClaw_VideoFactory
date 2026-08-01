"""Offline-candidate media quality checks; never a production promotion gate."""

from __future__ import annotations

import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any

from .config import jobs_root
from .db import CandidateStore


REQUIRED_FILTERS = ("loudnorm", "ebur128", "silencedetect", "blackdetect", "freezedetect")


def _probe(media: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(media)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("ffprobe_failed")
    return json.loads(result.stdout)


def _require_filters() -> None:
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-filters"], text=True, capture_output=True, check=False
    )
    source = result.stdout + result.stderr
    if result.returncode != 0 or any(re.search(rf"\b{item}\b", source) is None for item in REQUIRED_FILTERS):
        raise RuntimeError("QUALITY_CAPABILITY_BLOCKED")


def _filter_output(media: Path, filter_spec: str) -> str:
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-v", "info", "-i", str(media), "-vf", filter_spec, "-an", "-f", "null", "-"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("quality_filter_failed")
    return result.stderr


def _audio_filter_output(media: Path, filter_spec: str) -> str:
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-v", "info", "-i", str(media), "-af", filter_spec, "-vn", "-f", "null", "-"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("quality_filter_failed")
    return result.stderr


def captions_are_safe(captions: list[dict[str, Any]]) -> bool:
    previous_end = 0.0
    for item in captions:
        start, end = item.get("start"), item.get("end")
        text = item.get("text")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or not isinstance(text, str):
            return False
        if text.count("\n") > 1 or len(text.replace("\n", "")) > 36 or not start < end:
            return False
        if not 0.6 <= end - start <= 4.0 or start < previous_end:
            return False
        previous_end = float(end)
    return True


def _audio_quality(package: Path) -> dict[str, Any]:
    source = package / "audio_quality.json"
    if not source.is_file():
        return {"available": False}
    value = json.loads(source.read_text(encoding="utf-8"))
    measured = value.get("measured_output") if isinstance(value, dict) else None
    if not isinstance(measured, dict):
        return {"available": False}
    try:
        return {
            "available": True,
            "target_integrated_lufs": float(value["target_integrated_lufs"]),
            "target_true_peak_dbtp": float(value["target_true_peak_dbtp"]),
            "measured_integrated_lufs": float(measured["output_i"]),
            "measured_true_peak_dbtp": float(measured["output_tp"]),
        }
    except (KeyError, TypeError, ValueError):
        return {"available": False}


def quality_report(
    package: Path, captions: list[dict[str, Any]], expected_duration_seconds: float | None = None
) -> dict[str, Any]:
    _require_filters()
    master = package / "final_master.mp4"
    preview = package / "feishu_preview.mp4"
    probe = _probe(master)
    video = next((item for item in probe["streams"] if item.get("codec_type") == "video"), None)
    audio = next((item for item in probe["streams"] if item.get("codec_type") == "audio"), None)
    if video is None or audio is None:
        raise RuntimeError("required_stream_missing")
    try:
        fps = float(Fraction(video.get("avg_frame_rate", "0/1")))
    except (ValueError, ZeroDivisionError):
        fps = 0.0
    duration = float(probe["format"].get("duration", 0.0))
    expected = float(expected_duration_seconds or 10.0)
    decode = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(master), "-f", "null", "-"],
        text=True,
        capture_output=True,
        check=False,
    )
    black = _filter_output(master, "blackdetect=d=0.3:pix_th=0.10")
    frozen = _filter_output(master, "freezedetect=n=-60dB:d=1")
    silence = _audio_filter_output(master, "silencedetect=n=-50dB:d=2")
    black_detected = "black_start:" in black
    freeze_starts = [float(value) for value in re.findall(r"freeze_start:\s*([0-9.]+)", frozen)]
    abnormal_freeze = any(start < max(0.0, duration - 4.0) for start in freeze_starts)
    silence_starts = [float(value) for value in re.findall(r"silence_start:\s*([0-9.]+)", silence)]
    # The contract deliberately leaves a short ending hold after narration.
    abnormal_silence = any(start < max(0.0, duration - 3.5) for start in silence_starts)
    audio_quality = _audio_quality(package)
    loudness_ok = (
        audio_quality.get("available") is True
        and abs(float(audio_quality["measured_integrated_lufs"]) - (-16.0)) <= 1.5
        and float(audio_quality["measured_true_peak_dbtp"]) <= -1.0
    )
    checks = {
        "master_decode": decode.returncode == 0,
        "master_resolution": video.get("width") == 1080 and video.get("height") == 1920,
        "master_fps": abs(fps - 30.0) < 0.01,
        "contract_duration": abs(duration - expected) <= 0.75,
        "audio_track": True,
        "audio_loudness": loudness_ok,
        "no_abnormal_long_silence": not abnormal_silence,
        "no_unexpected_black_frame": not black_detected,
        "no_unexpected_freeze": not abnormal_freeze,
        "cover_nonempty": (package / "cover.png").is_file() and (package / "cover.png").stat().st_size > 1000,
        "preview_nonempty": preview.is_file() and preview.stat().st_size > 1000 and preview.stat().st_size <= 25 * 1024 * 1024,
        "subtitle_safe_contract": captions_are_safe(captions),
    }
    return {
        "schema_version": "2.0",
        "mode": "offline_candidate",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "media": {"width": video.get("width"), "height": video.get("height"), "fps": fps, "duration_seconds": duration, "audio_codec": audio.get("codec_name")},
        "quality_evidence": {"expected_duration_seconds": expected, "audio": audio_quality, "black_detected": black_detected, "freeze_starts": freeze_starts, "silence_starts": silence_starts, "abnormal_silence": abnormal_silence},
    }


def verify_job(store: CandidateStore, job_id: str) -> dict[str, Any]:
    package = jobs_root() / job_id
    report_path = package / "quality_report.json"
    if not report_path.is_file():
        raise RuntimeError("quality_report_missing")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    return {"job": store.status(job_id), "quality": report, "verified": report.get("status") == "pass"}
