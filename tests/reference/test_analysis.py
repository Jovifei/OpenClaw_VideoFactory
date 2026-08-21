from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src.factory.reference_video import analyze_reference


def _make_video(path: Path, *, cuts: bool = False, audio: bool = False) -> None:
    if cuts:
        command = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=30:d=1.0",
            "-f", "lavfi", "-i", "color=c=red:s=320x180:r=30:d=1.0",
            "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
            "-map", "[v]",
        ]
    else:
        command = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=30:d=1.2"]
    if audio:
        if cuts:
            command.extend(["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000", "-map", "2:a:0"])
        else:
            command.extend(["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000"])
        command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest"])
    else:
        command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-an"])
    command.append(str(path))
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr


def _bundle(video: Path, runtime: Path) -> dict[str, object]:
    runtime.mkdir(exist_ok=True)
    return {
        "runtime_root": runtime,
        "stored_path": video,
        "receipt": {
            "reference_id": "ref_" + "a" * 24,
            "source_sha256": "b" * 64,
        },
    }


def test_analysis_uses_one_full_scene_without_cut_and_is_deterministic(tmp_path: Path) -> None:
    video = tmp_path / "single.mp4"
    _make_video(video)
    first = analyze_reference(_bundle(video, tmp_path / "runtime"))
    second = analyze_reference(_bundle(video, tmp_path / "runtime"))
    assert len(first["scenes"]) == 1
    scene = first["scenes"][0]
    assert scene["start_seconds"] == 0.0
    assert scene["end_seconds"] == first["duration_seconds"]
    assert first["scenes"] == second["scenes"]
    assert first["style_fingerprint"] == second["style_fingerprint"]
    assert "frame_path" not in json.dumps(first)
    assert "audio_path" not in json.dumps(first)


def test_analysis_detects_multiple_scenes_and_preserves_abstract_only_report(tmp_path: Path) -> None:
    video = tmp_path / "cuts.mp4"
    _make_video(video, cuts=True)
    report = analyze_reference(_bundle(video, tmp_path / "runtime"))
    assert len(report["scenes"]) >= 2
    assert report["style_fingerprint"]["scene_count"] == len(report["scenes"])
    assert all("representative_frame_time_seconds" in scene for scene in report["scenes"])
    encoded = json.dumps(report, ensure_ascii=False)
    assert "input/reference_videos" not in encoded
    assert "audio_path" not in encoded


def test_audio_analysis_degrades_without_cached_model(tmp_path: Path, monkeypatch) -> None:
    video = tmp_path / "audio.mp4"
    _make_video(video, audio=True)
    monkeypatch.setattr("src.factory.reference_video._cached_whisper_model", lambda: None)
    report = analyze_reference(_bundle(video, tmp_path / "runtime"))
    assert report["asr"] == {"status": "unavailable", "model": None, "reason": "cached_small_model_missing"}
    assert report["transcript"] == []
