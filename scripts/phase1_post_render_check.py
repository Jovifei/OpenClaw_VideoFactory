"""Fail-closed post-render gate for the local reference-style video chain.

The gate runs after Remotion and before Jianying. It verifies the declared
layout contract, media metadata, representative frame health, full decode,
subtitle authority, and optional assembled-preview audio.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any


EXPECTED_WIDTH = 1080
EXPECTED_HEIGHT = 1920
EXPECTED_FPS = 30.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ffprobe(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate,channels,sample_rate",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0:
        raise ValueError("ffprobe_failed")
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("ffprobe_invalid") from exc
    if not isinstance(value, dict):
        raise ValueError("ffprobe_invalid")
    return value


def _fps(value: object) -> float:
    numerator, _, denominator = str(value or "0/1").partition("/")
    return float(numerator or 0) / float(denominator or 1)


def validate_layout_contract(contract: Any, *, width: int = EXPECTED_WIDTH, height: int = EXPECTED_HEIGHT) -> dict[str, Any]:
    if not isinstance(contract, dict) or contract.get("version") != "1.0":
        raise ValueError("layout_contract_invalid")
    safe = contract.get("safe_area")
    reserve = contract.get("subtitle_reserve")
    if not isinstance(safe, dict) or not isinstance(reserve, dict):
        raise ValueError("layout_contract_shape_invalid")
    left = int(safe.get("left", -1))
    right = int(safe.get("right", -1))
    top = int(safe.get("top", -1))
    bottom = int(safe.get("bottom", -1))
    reserve_top = int(reserve.get("top", -1))
    reserve_height = int(reserve.get("height", -1))
    if min(left, right, top, bottom, reserve_top, reserve_height) < 0:
        raise ValueError("layout_contract_bounds_invalid")
    if left + right >= width or top + bottom >= height:
        raise ValueError("layout_safe_area_outside_canvas")
    if reserve_top < top or reserve_top + reserve_height > height - bottom + bottom:
        raise ValueError("layout_subtitle_reserve_outside_canvas")
    if contract.get("text_policy") != "bounded_natural_wrap" or contract.get("overflow_policy") != "fail_closed":
        raise ValueError("layout_text_policy_invalid")
    if contract.get("theme_token") != "technical_neutral" or contract.get("background_is_theme_driven") is not True:
        raise ValueError("layout_theme_policy_invalid")
    if contract.get("pink_global_background") is True:
        raise ValueError("layout_global_pink_forbidden")
    return {
        "status": "passed",
        "safe_area": {"left": left, "right": right, "top": top, "bottom": bottom},
        "subtitle_reserve": {"top": reserve_top, "height": reserve_height},
        "text_policy": contract["text_policy"],
        "theme_token": contract["theme_token"],
    }


def _decode_check(path: Path) -> bool:
    completed = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-i", str(path), "-f", "null", "NUL"],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    return completed.returncode == 0 and not completed.stderr.strip()


def _sample_frames(path: Path, duration: float, sample_count: int) -> list[Path]:
    sample_count = max(3, sample_count)
    with tempfile.TemporaryDirectory(prefix="phase1-render-check-") as temp:
        root = Path(temp)
        samples: list[Path] = []
        for index in range(sample_count):
            timestamp = min(max(0.0, duration * (index + 0.5) / sample_count), max(0.0, duration - 0.05))
            target = root / f"frame_{index:02d}.png"
            completed = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-nostdin",
                    "-v",
                    "error",
                    "-ss",
                    f"{timestamp:.3f}",
                    "-i",
                    str(path),
                    "-frames:v",
                    "1",
                    "-vf",
                    "scale=270:-1",
                    str(target),
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            if completed.returncode != 0 or not target.is_file():
                raise ValueError("sample_frame_extract_failed")
            samples.append(target)
        # Read samples while the temporary root exists; callers receive only metrics.
        metrics: list[dict[str, float]] = []
        try:
            from PIL import Image, ImageChops, ImageStat
        except ImportError as exc:
            raise ValueError("pillow_required_for_frame_gate") from exc
        previous = None
        for frame_path in samples:
            with Image.open(frame_path).convert("L") as image:
                stat = ImageStat.Stat(image)
                mean = float(stat.mean[0])
                black_ratio = sum(1 for pixel in image.getdata() if pixel <= 4) / float(image.width * image.height)
                delta = 0.0
                if previous is not None:
                    delta = float(ImageStat.Stat(ImageChops.difference(previous, image)).mean[0])
                metrics.append({"mean_luma": round(mean, 3), "black_ratio": round(black_ratio, 6), "frame_delta": round(delta, 3)})
                previous = image.copy()
        if not metrics or all(item["mean_luma"] < 4.0 for item in metrics):
            raise ValueError("sample_frames_black")
        if len(metrics) >= 3 and all(item["frame_delta"] < 0.25 for item in metrics[1:]):
            raise ValueError("sample_frames_frozen")
        return metrics


def _has_audio(path: Path) -> bool:
    metadata = _ffprobe(path)
    return any(stream.get("codec_type") == "audio" for stream in metadata.get("streams", []) if isinstance(stream, dict))


def run_gate(visual: Path, render_report: Path, output_report: Path, *, preview: Path | None = None, reference_sha256: str | None = None) -> dict[str, Any]:
    for target, field in ((visual, "visual"), (render_report, "render_report"), (output_report, "output_report")):
        if target.resolve().drive.upper() == "C:":
            raise ValueError(f"{field}_must_not_use_c_drive")
    if preview is not None and preview.resolve().drive.upper() == "C:":
        raise ValueError("preview_must_not_use_c_drive")
    if not visual.is_file() or not render_report.is_file():
        raise ValueError("post_render_input_missing")
    report = json.loads(render_report.read_text(encoding="utf-8"))
    visual_probe = _ffprobe(visual)
    streams = [item for item in visual_probe.get("streams", []) if isinstance(item, dict)]
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = [item for item in streams if item.get("codec_type") == "audio"]
    if not isinstance(video, dict):
        raise ValueError("post_render_video_stream_missing")
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    measured_fps = _fps(video.get("avg_frame_rate"))
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        raise ValueError("post_render_canvas_invalid")
    if abs(measured_fps - EXPECTED_FPS) > 0.01:
        raise ValueError("post_render_fps_invalid")
    if audio:
        raise ValueError("visual_must_not_contain_audio")
    if report.get("visual", {}).get("burned_in_subtitles") is not False:
        raise ValueError("burned_in_subtitles_forbidden")
    layout = validate_layout_contract(report.get("layout_contract"))
    duration = float(visual_probe.get("format", {}).get("duration") or 0.0)
    if duration <= 0:
        raise ValueError("post_render_duration_invalid")
    if not _decode_check(visual):
        raise ValueError("post_render_decode_failed")
    samples = _sample_frames(visual, duration, len(report.get("visual", {}).get("scene_timing", [])) or 5)
    source_distinct = True
    visual_sha = _sha256(visual)
    if reference_sha256:
        source_distinct = visual_sha.lower() != reference_sha256.lower()
        if not source_distinct:
            raise ValueError("source_output_sha_equal")
    preview_result: dict[str, Any] | None = None
    if preview is not None:
        if not preview.is_file() or not _has_audio(preview):
            raise ValueError("audio_preview_missing_or_silent")
        if not _decode_check(preview):
            raise ValueError("audio_preview_decode_failed")
        preview_result = {"path": str(preview), "audio_present": True, "full_decode": "passed", "sha256": _sha256(preview)}
    result = {
        "schema_version": "1.0",
        "status": "passed",
        "checks": {
            "canvas_1080x1920": True,
            "fps_30": True,
            "visual_audio_absent": True,
            "burned_in_subtitles_absent": True,
            "layout_safe_area": layout,
            "full_decode": True,
            "representative_frames": samples,
            "source_output_distinct": source_distinct,
            "theme_background_not_global_pink": True,
        },
        "visual": {"path": str(visual), "sha256": visual_sha, "duration_seconds": round(duration, 6)},
        "preview": preview_result,
        "human_gate": {"status": "required", "action": "Jovi visually inspects and listens in the new Jianying draft, then exports manually if accepted."},
    }
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visual", required=True, type=Path)
    parser.add_argument("--render-report", required=True, type=Path)
    parser.add_argument("--output-report", required=True, type=Path)
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--reference-sha256")
    args = parser.parse_args()
    try:
        result = run_gate(args.visual.resolve(), args.render_report.resolve(), args.output_report.resolve(), preview=args.preview.resolve() if args.preview else None, reference_sha256=args.reference_sha256)
    except Exception as exc:
        print(json.dumps({"status": "failed", "reason": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
