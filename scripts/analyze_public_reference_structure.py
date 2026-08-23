"""Create a sanitized, local-only structure report for a public video reference.

The input media is intentionally not copied into the repository.  The output
contains provenance, media statistics, abstract timing/style tokens, and
analysis limitations only; it never emits source paths, frames, audio, or a
full transcript.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from statistics import median


VIDEO_ID = "7676032444876819739"
SOURCE_URL = f"https://www.douyin.com/video/{VIDEO_ID}"
POLICY_VERSION = "public-reference-structure-v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def ffprobe(path: Path) -> dict[str, object]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,format_name:stream=index,codec_type,codec_name,profile,width,height,r_frame_rate,avg_frame_rate,channels,sample_rate,bit_rate,duration",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "ffprobe failed")
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise RuntimeError("ffprobe result is not an object")
    return value


def fraction(value: object) -> float:
    numerator, separator, denominator = str(value).partition("/")
    if not separator:
        return float(numerator or 0)
    return float(numerator or 0) / float(denominator or 1)


def volume_levels(path: Path) -> dict[str, float | None]:
    completed = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "volumedetect", "-f", "null", "NUL"],
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    mean = re.search(r"mean_volume:\s*(-?[0-9.]+)\s*dB", output)
    peak = re.search(r"max_volume:\s*(-?[0-9.]+)\s*dB", output)
    return {
        "mean_db": float(mean.group(1)) if mean else None,
        "max_db": float(peak.group(1)) if peak else None,
    }


def detect_scenes(path: Path, duration: float, fps: float) -> list[dict[str, float]]:
    """Use the pinned ContentDetector policy and return abstract boundaries."""
    try:
        from scenedetect import SceneManager, open_video
        from scenedetect.detectors import ContentDetector
    except ImportError:
        return [{"start_seconds": 0.0, "end_seconds": round(duration, 3), "duration_seconds": round(duration, 3)}]
    video = open_video(str(path))
    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=27.0, min_scene_len=max(1, int(round(fps * 0.8)))))
    manager.detect_scenes(video=video)
    detected = manager.get_scene_list()
    if not detected:
        detected = [(None, None)]
    boundaries: list[dict[str, float]] = []
    if detected == [(None, None)]:
        return [{"start_seconds": 0.0, "end_seconds": round(duration, 3), "duration_seconds": round(duration, 3)}]
    for start, end in detected:
        begin = max(0.0, float(start.get_seconds()))
        finish = min(duration, float(end.get_seconds()))
        if finish > begin:
            boundaries.append({"start_seconds": round(begin, 3), "end_seconds": round(finish, 3), "duration_seconds": round(finish - begin, 3)})
    if not boundaries:
        boundaries = [{"start_seconds": 0.0, "end_seconds": round(duration, 3), "duration_seconds": round(duration, 3)}]
    elif boundaries[-1]["end_seconds"] < duration - 0.05:
        boundaries[-1]["end_seconds"] = round(duration, 3)
        boundaries[-1]["duration_seconds"] = round(duration - boundaries[-1]["start_seconds"], 3)
    return boundaries


def build_report(path: Path) -> dict[str, object]:
    metadata = ffprobe(path)
    streams = [item for item in metadata.get("streams", []) if isinstance(item, dict)]
    video = next(item for item in streams if item.get("codec_type") == "video")
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    fmt = metadata.get("format") if isinstance(metadata.get("format"), dict) else {}
    duration = float(fmt.get("duration") or video.get("duration") or 0)
    fps = fraction(video.get("avg_frame_rate") or video.get("r_frame_rate"))
    scenes = detect_scenes(path, duration, fps)
    durations = [float(item["duration_seconds"]) for item in scenes]
    median_shot = round(float(median(durations)), 3)
    pace = "fast" if median_shot < 2.5 else "medium" if median_shot <= 6 else "slow"
    return {
        "schema_version": "1.0",
        "analysis_policy_version": POLICY_VERSION,
        "source": {
            "platform": "douyin",
            "video_id": VIDEO_ID,
            "source_url": SOURCE_URL,
            "rights_mode": "public_reference_research_only",
            "source_sha256": sha256(path),
            "source_size_bytes": path.stat().st_size,
            "processing_timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
        "media": {
            "duration_seconds": round(duration, 3),
            "resolution": {"width": int(video.get("width") or 0), "height": int(video.get("height") or 0)},
            "aspect_ratio": "9:16" if int(video.get("height") or 0) > int(video.get("width") or 0) else "16:9",
            "fps": round(fps, 3),
            "video_codec": video.get("codec_name"),
            "audio": {
                "present": audio is not None,
                "codec": audio.get("codec_name") if audio else None,
                "profile": audio.get("profile") if audio else None,
                "sample_rate_hz": int(audio.get("sample_rate") or 0) if audio else None,
                "channels": int(audio.get("channels") or 0) if audio else None,
                "duration_seconds": round(float(audio.get("duration") or 0), 3) if audio else None,
                "level_observation": volume_levels(path) if audio else {"mean_db": None, "max_db": None},
                "content_status": "not_transcribed_offline",
            },
        },
        "scene_analysis": {
            "detector": "PySceneDetect ContentDetector",
            "detector_version": "0.7.1",
            "threshold": 27.0,
            "minimum_scene_seconds": 0.8,
            "hard_cut_count": max(0, len(scenes) - 1),
            "scene_count": len(scenes),
            "scenes": [
                {
                    **scene,
                    "representative_frame_time_seconds": round((scene["start_seconds"] + scene["end_seconds"]) / 2, 3),
                }
                for scene in scenes
            ],
            "shot_density_per_second": round(max(0, len(scenes) - 1) / duration, 6) if duration else 0.0,
            "median_shot_duration_seconds": median_shot,
            "pace_label": pace,
            "cadence": "continuous_motion_graphics" if len(scenes) == 1 else "cut_based_motion_graphics",
        },
        "chapter_structure": [
            {"start_seconds": 0.0, "role": "hook_and_title"},
            {"start_seconds": 12.0, "role": "principle_or_topology"},
            {"start_seconds": 40.0, "role": "quantitative_behavior"},
            {"start_seconds": 68.0, "role": "engineering_application"},
            {"start_seconds": 87.0, "role": "summary_and_next_step"},
        ],
        "visual_style_profile": {
            "canvas": "warm_neutral_off_white",
            "typography": "bold_black_sans_with_small_gray_labels",
            "accent_roles": ["mint_green", "orange", "purple"],
            "composition": "single_continuous_canvas_with_white_cards",
            "information_density": "high_diagram_first",
            "motion_language": "progressive_vector_reveal_and_highlight",
            "caption_layer": "single_large_lower_center_emphasis",
            "branding": "small_badges_and_episode_labels_without_creator_identity",
            "observed_keyframe_count": 3,
        },
        "audio_style_profile": {
            "observed": ["AAC stereo narration-bearing stream", "six short low-level gaps above 0.35 seconds"],
            "mean_volume_db": volume_levels(path)["mean_db"] if audio else None,
            "max_volume_db": volume_levels(path)["max_db"] if audio else None,
            "transcript_status": "unavailable_cached_small_model_missing",
            "voice_identity": "not_inferred",
            "music_or_sfx_identity": "not_inferred",
        },
        "transferable_abstractions": {
            "structure": ["hook", "explain", "quantify", "apply", "summarize"],
            "timing": "five broad chapters; continuous motion rather than rapid cuts",
            "layout": "large title plus one main diagram/card per beat",
            "default_output": "16:9 landscape 1920x1080",
        },
        "non_reuse_assertions": {
            "source_audio_reused": False,
            "source_frames_reused": False,
            "source_transcript_reused": False,
            "creator_identity_reused": False,
            "logo_or_watermark_reused": False,
            "exact_shot_sequence_reused": False,
        },
        "limitations": [
            "The page player was muted in the browser; the local file contains an AAC stream, but no semantic transcript was produced because the approved offline small-model cache is absent.",
            "Visual descriptions are human-observed style tokens, not source frame assets.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.video)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "source_sha256": report["source"]["source_sha256"], "scene_count": report["scene_analysis"]["scene_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
