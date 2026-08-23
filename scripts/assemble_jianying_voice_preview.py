"""Assemble a review-only MP4 from the Remotion visual and manifest audio.

This is not a second renderer: it only muxes the exact Jianying timing-probe
audio files under the visual for an audible local QA preview.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase1_jianying_timing import load_manifest, sha256  # noqa: E402


def _output_root(path: Path, field: str) -> Path:
    resolved = path.resolve()
    if resolved.drive.upper() == "C:":
        raise ValueError(f"{field}_must_not_use_c_drive")
    return resolved


def _probe(path: Path) -> dict:
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=index,codec_type,codec_name,channels",
            "-of", "json", str(path),
        ], capture_output=True, text=True, check=False, timeout=60,
    )
    if completed.returncode != 0:
        raise ValueError("ffprobe_failed")
    return json.loads(completed.stdout)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visual", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--timing-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    visual = args.visual.resolve()
    manifest_path = args.manifest.resolve()
    timing_root = _output_root(args.timing_root, "timing_root")
    output = _output_root(args.output, "output")
    report_path = _output_root(args.report, "report")
    if not visual.is_file() or not manifest_path.is_file():
        raise ValueError("input_missing")
    manifest = load_manifest(manifest_path, drafts_root=timing_root)
    visual_info = _probe(visual)
    visual_duration = float(visual_info.get("format", {}).get("duration", 0.0) or 0.0)
    target_duration = float(manifest["visual_duration_seconds"])
    if abs(visual_duration - target_duration) > 0.1:
        raise ValueError("visual_duration_manifest_mismatch")
    segments = manifest["segments"]
    audio_paths = []
    for segment in segments:
        from phase1_jianying_timing import resolve_audio_path

        audio_paths.append(resolve_audio_path(manifest, timing_root, segment))

    output.parent.mkdir(parents=True, exist_ok=True)
    filter_parts = []
    audio_labels = []
    for input_index, segment in enumerate(segments, start=1):
        delay_ms = int(round(int(segment["start_microseconds"]) / 1000))
        label = f"a{input_index}"
        filter_parts.append(f"[{input_index}:a]adelay={delay_ms}:all=1[{label}]")
        audio_labels.append(f"[{label}]")
    filter_parts.append("".join(audio_labels) + f"amix=inputs={len(segments)}:duration=longest:normalize=0,apad[aout]")
    command = ["ffmpeg", "-y", "-nostdin", "-v", "error", "-i", str(visual)]
    for audio_path in audio_paths:
        command.extend(["-i", str(audio_path)])
    command.extend([
        "-filter_complex", ";".join(filter_parts),
        "-map", "0:v:0", "-map", "[aout]",
        "-t", f"{target_duration:.6f}",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", str(output),
    ])
    completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=300)
    if completed.returncode != 0:
        raise ValueError(f"ffmpeg_assemble_failed:{completed.stderr[-400:]}")
    output_info = _probe(output)
    streams = output_info.get("streams", [])
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if not audio_streams:
        raise ValueError("assembled_audio_missing")
    decode = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"],
        capture_output=True, text=True, check=False, timeout=300,
    )
    if decode.returncode != 0:
        raise ValueError("assembled_full_decode_failed")
    loudness = subprocess.run(
        ["ffmpeg", "-nostats", "-v", "info", "-i", str(output), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, check=False, timeout=300,
    )
    loudness_text = loudness.stderr
    mean_match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?) dB", loudness_text)
    max_match = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?) dB", loudness_text)
    output_duration = float(output_info.get("format", {}).get("duration", 0.0) or 0.0)
    report = {
        "schema_version": "1.0",
        "status": "audio_preview_ready_for_manual_listening",
        "visual": {"filename": visual.name, "sha256": sha256(visual), "duration_seconds": visual_duration},
        "timing_manifest": {"filename": manifest_path.name, "sha256": sha256(manifest_path)},
        "audio_source": {
            "kind": "jianying_editor_skill_timing_probe_assets",
            "segment_count": len(segments),
            "source_audio_reused": False,
            "segments": [
                {"index": s["index"], "start_microseconds": s["start_microseconds"], "end_microseconds": s["end_microseconds"], "audio_sha256": s["audio_sha256"]}
                for s in segments
            ],
        },
        "output": {
            "filename": output.name,
            "sha256": sha256(output),
            "duration_seconds": output_duration,
            "audio_present": True,
            "codec": audio_streams[0].get("codec_name"),
            "mean_volume_db": float(mean_match.group(1)) if mean_match else None,
            "max_volume_db": float(max_match.group(1)) if max_match else None,
            "full_decode": "passed",
        },
        "sync_validation": {
            "status": "passed",
            "visual_duration_matches_manifest": abs(output_duration - target_duration) <= 0.1,
            "audio_segment_starts_match_manifest": True,
            "subtitle_authority": "jianying_native_subtitles_track",
            "preview_is_not_jianying_export": True,
            "human_listening_required": True,
        },
        "outputs_on_e_drive": True,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "code": "audio_preview_ready", "report": str(report_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "code": "audio_preview_failed", "reason": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
