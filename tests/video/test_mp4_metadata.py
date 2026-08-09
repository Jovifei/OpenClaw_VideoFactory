"""T05 / stage-four ⑤ — produced MP4 metadata evidence.

Runs ``ffprobe`` against the **real** artifacts produced by ``generate_video.py``
and cross-checks them against ``run_report.json``. This is the shipping-evidence
gate: the video that was actually rendered must match the contract the rest of
the pipeline claims (1080×1920, 30 fps, h264, duration ≈ timeline, audio track
consistent with the recorded audio mode).

Two independent artifacts are checked:

* main link  → ``dist/pink_pig_story_demo.mp4`` (TTS primary chain) + ``dist/story_demo/run_report.json``
* offline    → ``dist/pink_pig_story_demo_offline.mp4`` (BGM fallback) + ``dist/story_demo_offline/run_report.json``

They are deliberately separate (the brief required the main-link evidence not be
overwritten by the offline run).

Run from the repository root (deviation D5):
    <envs/default python> -m pytest tests/video/test_mp4_metadata.py -v
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from . import ROOT

EXPECTED_WIDTH = 1080
EXPECTED_HEIGHT = 1920
EXPECTED_FPS = 30
EXPECTED_CODEC = "h264"
EXPECTED_AUDIO_CODEC = "aac"
EXPECTED_TOTAL_DURATION = 12.5
DURATION_TOLERANCE = 0.2

ARTIFACTS = [
    {
        "label": "main_link_tts",
        "mp4": ROOT / "dist" / "pink_pig_story_demo.mp4",
        "report": ROOT / "dist" / "story_demo" / "run_report.json",
        "audio_mode": "tts",
    },
    {
        "label": "offline_bgm",
        "mp4": ROOT / "dist" / "pink_pig_story_demo_offline.mp4",
        "report": ROOT / "dist" / "story_demo_offline" / "run_report.json",
        "audio_mode": "bgm",
    },
]


def _ffprobe(path: Path) -> dict:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return json.loads(proc.stdout)


def _fps(r_frame_rate: str) -> float:
    num, _, den = r_frame_rate.partition("/")
    den = den or "1"
    return float(num) / float(den) if float(den) else 0.0


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_ffprobe_is_available() -> None:
    """Honest gate: without ffprobe there is no evidence, the test must not fake-pass."""
    assert subprocess.run(["ffprobe", "-version"], capture_output=True, timeout=15).returncode == 0


@pytest.mark.parametrize(
    "artifact", ARTIFACTS, ids=[a["label"] for a in ARTIFACTS]
)
class TestMp4Metadata:
    def test_artifact_files_exist(self, artifact: dict) -> None:
        assert artifact["mp4"].is_file(), f"missing {artifact['mp4']}"
        assert artifact["report"].is_file(), f"missing {artifact['report']}"
        assert artifact["mp4"].stat().st_size > 0

    def test_video_is_1080x1920_h264_30fps(self, artifact: dict) -> None:
        data = _ffprobe(artifact["mp4"])
        vstreams = [s for s in data["streams"] if s.get("codec_type") == "video"]
        assert vstreams, "no video stream"
        v = vstreams[0]
        assert v["codec_name"] == EXPECTED_CODEC
        assert v["width"] == EXPECTED_WIDTH
        assert v["height"] == EXPECTED_HEIGHT
        assert _fps(v.get("r_frame_rate", "0/1")) == pytest.approx(EXPECTED_FPS, abs=0.01)

    def test_duration_matches_timeline_within_tolerance(self, artifact: dict) -> None:
        data = _ffprobe(artifact["mp4"])
        duration = float(data["format"]["duration"])
        assert abs(duration - EXPECTED_TOTAL_DURATION) < DURATION_TOLERANCE

    def test_has_audio_track_matching_reported_mode(self, artifact: dict) -> None:
        data = _ffprobe(artifact["mp4"])
        astreams = [s for s in data["streams"] if s.get("codec_type") == "audio"]
        assert astreams, "no audio stream"
        assert astreams[0]["codec_name"] == EXPECTED_AUDIO_CODEC

        report = json.loads(artifact["report"].read_text(encoding="utf-8"))
        # The recorded audio mode must match what was requested for this artifact.
        assert report["audio_plan"]["mode"] == artifact["audio_mode"]
        # The ffprobe evidence in the report must agree with the real container.
        assert report["ffprobe"]["has_audio"] is True
        assert report["ffprobe"]["video"]["codec"] == EXPECTED_CODEC
        assert report["ffprobe"]["video"]["width"] == EXPECTED_WIDTH
        assert report["ffprobe"]["video"]["height"] == EXPECTED_HEIGHT
        assert abs(float(report["ffprobe"]["duration"]) - EXPECTED_TOTAL_DURATION) < DURATION_TOLERANCE
        # Sample rate of the container must equal the one recorded in the report.
        assert astreams[0].get("sample_rate") == report["ffprobe"]["audio"]["sample_rate"]

    def test_separate_evidence_files_are_not_cross_contaminated(self, artifact: dict) -> None:
        """The two artifacts must describe *different* products, not the same run."""
        report = json.loads(artifact["report"].read_text(encoding="utf-8"))
        assert report["audio_plan"]["mode"] == artifact["audio_mode"]
        assert Path(report["output"]).resolve() == artifact["mp4"].resolve()
        # The main link is tts (24000 Hz); the offline link is bgm (48000 Hz).
        expected_sr = "24000" if artifact["audio_mode"] == "tts" else "48000"
        assert report["ffprobe"]["audio"]["sample_rate"] == expected_sr
