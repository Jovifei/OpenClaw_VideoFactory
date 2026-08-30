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
from pathlib import Path
from typing import Any


EXPECTED_WIDTH = 1080
EXPECTED_HEIGHT = 1920
EXPECTED_FPS = 30.0
ALLOWED_CANVASES = {"16:9": (1920, 1080), "9:16": (1080, 1920)}


def validate_report_canvas(report: dict[str, Any], width: int, height: int) -> dict[str, Any]:
    aspect = report.get("layout_contract", {}).get("aspect", "9:16")
    if aspect not in ALLOWED_CANVASES:
        raise ValueError("post_render_aspect_invalid")
    expected = ALLOWED_CANVASES[aspect]
    declared = report.get("visual", {})
    declared_canvas = (int(declared.get("width", width)), int(declared.get("height", height)))
    if (width, height) != expected or declared_canvas != expected:
        raise ValueError("post_render_canvas_report_mismatch")
    return {"aspect": aspect, "width": width, "height": height}


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


def _rectangles_intersect(first: dict[str, float], second: dict[str, float]) -> bool:
    return not (
        first["right"] <= second["left"]
        or first["left"] >= second["right"]
        or first["bottom"] <= second["top"]
        or first["top"] >= second["bottom"]
    )


def _box_bounds(box: Any, *, field: str) -> dict[str, float]:
    if not isinstance(box, dict):
        raise ValueError(f"{field}_invalid")
    try:
        x = float(box["x"])
        y = float(box["y"])
        width = float(box["width"])
        height = float(box["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{field}_invalid") from exc
    if width <= 0 or height <= 0:
        raise ValueError(f"{field}_invalid")
    return {"left": x, "top": y, "right": x + width, "bottom": y + height}


def _mapped_y(value: float, *, top: float, bottom: float, minimum: float, maximum: float) -> float:
    if minimum >= maximum or top >= bottom:
        raise ValueError("bode_lane_invalid")
    clamped = min(max(value, minimum), maximum)
    return top + (maximum - clamped) / (maximum - minimum) * (bottom - top)


def validate_rc_highpass_geometry(value: Any) -> dict[str, Any]:
    """Verify the topology has no decorative component crossings and fc markers use curve math."""
    if not isinstance(value, dict) or value.get("version") != "2.0":
        raise ValueError("rc_geometry_contract_invalid")
    topology = value.get("topology")
    bode = value.get("bode")
    if not isinstance(topology, dict) or not isinstance(bode, dict):
        raise ValueError("rc_geometry_contract_invalid")
    resistor = _box_bounds(topology.get("resistor"), field="resistor")
    ground = _box_bounds(topology.get("ground"), field="ground")
    paths = topology.get("wave_paths")
    if not isinstance(paths, list):
        raise ValueError("wave_paths_invalid")
    for path in paths:
        if not isinstance(path, dict):
            raise ValueError("wave_path_invalid")
        try:
            bounds = {name: float(path[name]) for name in ("left", "top", "right", "bottom")}
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("wave_path_invalid") from exc
        if bounds["left"] >= bounds["right"] or bounds["top"] >= bounds["bottom"]:
            raise ValueError("wave_path_invalid")
        if _rectangles_intersect(bounds, resistor):
            raise ValueError("wave_intersects_resistor")
        if _rectangles_intersect(bounds, ground):
            raise ValueError("wave_intersects_ground")
    x_axis = bode.get("x")
    magnitude = bode.get("magnitude_lane")
    phase = bode.get("phase_lane")
    markers = bode.get("markers")
    if not all(isinstance(item, dict) for item in (x_axis, magnitude, phase, markers)):
        raise ValueError("bode_geometry_invalid")
    try:
        left = float(x_axis["left"])
        right = float(x_axis["right"])
        fc_ratio = float(x_axis["fc_ratio"])
        magnitude_fc_db = float(markers["magnitude_fc"]["db"])
        phase_fc_degrees = float(markers["phase_fc"]["degrees"])
        magnitude_y = _mapped_y(
            magnitude_fc_db,
            top=float(magnitude["top"]),
            bottom=float(magnitude["bottom"]),
            minimum=float(magnitude["min_db"]),
            maximum=float(magnitude["max_db"]),
        )
        phase_y = _mapped_y(
            phase_fc_degrees,
            top=float(phase["top"]),
            bottom=float(phase["bottom"]),
            minimum=float(phase["min_degrees"]),
            maximum=float(phase["max_degrees"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("bode_geometry_invalid") from exc
    if not (left < right and 0.1 <= fc_ratio <= 10):
        raise ValueError("bode_geometry_invalid")
    expected_db = 20.0 * math.log10(fc_ratio / math.sqrt(1.0 + fc_ratio * fc_ratio))
    expected_phase = math.degrees(math.atan(1.0 / fc_ratio))
    if abs(magnitude_fc_db - expected_db) > 0.02:
        raise ValueError("magnitude_fc_marker_not_on_curve")
    if abs(phase_fc_degrees - expected_phase) > 0.02:
        raise ValueError("phase_fc_marker_not_on_curve")
    fc_x = left + (math.log10(fc_ratio) + 1.0) / 2.0 * (right - left)
    return {
        "status": "passed",
        "magnitude_fc": {"x": round(fc_x, 6), "y": round(magnitude_y, 6), "db": round(magnitude_fc_db, 6)},
        "phase_fc": {"x": round(fc_x, 6), "y": round(phase_y, 6), "degrees": round(phase_fc_degrees, 6)},
        "wave_path_count": len(paths),
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


def _sample_frames(path: Path, duration: float, sample_count: int) -> list[dict[str, float]]:
    sample_count = max(3, sample_count)
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise ValueError("opencv_required_for_frame_gate") from exc
    target_indices = sorted(
        {
            max(0, int(round(min(max(0.0, duration * (index + 0.5) / sample_count), max(0.0, duration - 0.05)) * EXPECTED_FPS)))
            for index in range(sample_count)
        }
    )
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError("sample_frame_open_failed")
    target_set = set(target_indices)
    samples_by_index: dict[int, dict[str, float]] = {}
    frame_index = 0
    try:
        while frame_index <= target_indices[-1]:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index in target_set:
                grayscale = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (270, 480), interpolation=cv2.INTER_AREA)
                samples_by_index[frame_index] = {
                    "mean_luma": round(float(grayscale.mean()), 3),
                    "black_ratio": round(float((grayscale <= 4).mean()), 6),
                    "frame_delta": 0.0,
                }
            frame_index += 1
    finally:
        capture.release()
    if len(samples_by_index) != len(target_indices):
        raise ValueError("sample_frame_extract_failed")
    metrics = [samples_by_index[index] for index in target_indices]
    previous_mean = None
    for metric in metrics:
        if previous_mean is not None:
            metric["frame_delta"] = round(abs(metric["mean_luma"] - previous_mean), 3)
        previous_mean = metric["mean_luma"]
    if all(item["mean_luma"] < 4.0 for item in metrics):
        raise ValueError("sample_frames_black")
    return metrics


def validate_full_frame_metrics(metrics: list[dict[str, float]]) -> dict[str, Any]:
    if not metrics:
        raise ValueError("all_frame_metrics_empty")
    black_indices = [
        index
        for index, item in enumerate(metrics)
        if float(item.get("mean_luma", 0.0)) <= 4.0 or float(item.get("black_ratio", 1.0)) >= 0.98
    ]
    if black_indices:
        raise ValueError("all_frame_black_detected")
    unsafe_edge_indices = [index for index, item in enumerate(metrics) if float(item.get("unsafe_edge_dark_ratio", 1.0)) > 0.03]
    if unsafe_edge_indices:
        raise ValueError("all_frame_canvas_edge_overflow")
    longest_static_run = 0
    current_static_run = 0
    for item in metrics[1:]:
        if float(item.get("frame_delta", 0.0)) < 0.02:
            current_static_run += 1
            longest_static_run = max(longest_static_run, current_static_run)
        else:
            current_static_run = 0
    if longest_static_run > 450:
        raise ValueError("all_frame_static_run_excessive")
    return {
        "status": "passed",
        "frames_scanned": len(metrics),
        "black_frame_count": len(black_indices),
        "unsafe_edge_frame_count": len(unsafe_edge_indices),
        "longest_near_static_run_frames": longest_static_run,
    }


def scan_all_frames(path: Path) -> dict[str, Any]:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise ValueError("opencv_required_for_all_frame_gate") from exc
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError("all_frame_open_failed")
    metrics: list[dict[str, float]] = []
    previous = None
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            grayscale = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (270, 480), interpolation=cv2.INTER_AREA)
            edge = np.concatenate((grayscale[:12, :].ravel(), grayscale[-12:, :].ravel(), grayscale[:, :12].ravel(), grayscale[:, -12:].ravel()))
            delta = 0.0 if previous is None else float(cv2.absdiff(previous, grayscale).mean())
            metrics.append(
                {
                    "mean_luma": float(grayscale.mean()),
                    "black_ratio": float((grayscale <= 4).mean()),
                    "unsafe_edge_dark_ratio": float((edge <= 55).mean()),
                    "frame_delta": delta,
                }
            )
            previous = grayscale
    finally:
        capture.release()
    summary = validate_full_frame_metrics(metrics)
    summary["first_frame_luma"] = round(metrics[0]["mean_luma"], 3)
    summary["last_frame_luma"] = round(metrics[-1]["mean_luma"], 3)
    return summary


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
    canvas = validate_report_canvas(report, width, height)
    if abs(measured_fps - EXPECTED_FPS) > 0.01:
        raise ValueError("post_render_fps_invalid")
    if audio:
        raise ValueError("visual_must_not_contain_audio")
    if report.get("visual", {}).get("burned_in_subtitles") is not False:
        raise ValueError("burned_in_subtitles_forbidden")
    layout = validate_layout_contract(report.get("layout_contract"), width=width, height=height)
    geometry = validate_rc_highpass_geometry(report["geometry_contract"]) if "geometry_contract" in report else None
    duration = float(visual_probe.get("format", {}).get("duration") or 0.0)
    if duration <= 0:
        raise ValueError("post_render_duration_invalid")
    if not _decode_check(visual):
        raise ValueError("post_render_decode_failed")
    samples = _sample_frames(visual, duration, len(report.get("visual", {}).get("scene_timing", [])) or 5)
    all_frames = scan_all_frames(visual)
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
            "canvas": canvas,
            "fps_30": True,
            "visual_audio_absent": True,
            "burned_in_subtitles_absent": True,
            "layout_safe_area": layout,
            "rc_geometry": geometry,
            "full_decode": True,
            "representative_frames": samples,
            "all_frame_scan": all_frames,
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
