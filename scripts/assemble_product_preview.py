"""Build the audible, burned-subtitle review master for WebsiteProductDemo."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from phase1_jianying_timing import load_manifest, resolve_audio_path, sha256  # noqa: E402


def _output_root(path: Path, field: str) -> Path:
    resolved = path.resolve()
    if resolved.drive.upper() != "E:":
        raise ValueError(f"{field}_must_use_e_drive")
    return resolved


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value


def _stamp(microseconds: int) -> str:
    milliseconds = microseconds // 1000
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def _ass_stamp(microseconds: int) -> str:
    centiseconds = microseconds // 10_000
    hours, centiseconds = divmod(centiseconds, 360_000)
    minutes, centiseconds = divmod(centiseconds, 6_000)
    seconds, centiseconds = divmod(centiseconds, 100)
    return f"{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}"


def wrap_subtitle(text: str, max_chars: int = 18) -> str:
    value = " ".join(str(text).split())
    if not value or len(value) > max_chars * 2:
        raise ValueError("subtitle_line_budget")
    if len(value) <= max_chars:
        return value
    midpoint = len(value) / 2
    punctuation = set("，,。！？；：、 ")
    candidates = [
        index + 1
        for index, char in enumerate(value)
        if char in punctuation and 4 <= index + 1 <= max_chars and len(value) - index - 1 <= max_chars
    ]
    split = min(candidates, key=lambda item: abs(item - midpoint)) if candidates else max_chars
    left, right = value[:split].strip(), value[split:].strip()
    if not left or not right or len(left) > max_chars or len(right) > max_chars:
        raise ValueError("subtitle_line_budget")
    return f"{left}\n{right}"


def build_srt(timing: dict[str, Any], script: dict[str, Any]) -> str:
    segments = timing.get("segments")
    beats = script.get("beats")
    if not isinstance(segments, list) or not isinstance(beats, list) or len(segments) != len(beats) or not segments:
        raise ValueError("subtitle_timing_shape")
    blocks: list[str] = []
    previous_end = -1
    for index, (segment, beat) in enumerate(zip(segments, beats), start=1):
        if not isinstance(segment, dict) or not isinstance(beat, dict) or segment.get("index") != index:
            raise ValueError("subtitle_timing_shape")
        text = str(beat.get("subtitle", "")).strip()
        if not text or segment.get("subtitle_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
            raise ValueError("subtitle_hash_mismatch")
        try:
            start = int(segment["start_microseconds"])
            end = int(segment["end_microseconds"])
            scene_end = int(segment["scene_end_microseconds"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("subtitle_timing_shape") from exc
        if start < 0 or end <= start or start < previous_end or end > scene_end:
            raise ValueError("subtitle_timing_range")
        blocks.append(f"{index}\n{_stamp(start)} --> {_stamp(end)}\n{wrap_subtitle(text)}")
        previous_end = end
    return "\n\n".join(blocks) + "\n"


def build_ass(timing: dict[str, Any], script: dict[str, Any]) -> str:
    srt = build_srt(timing, script)
    blocks = srt.strip().split("\n\n")
    events: list[str] = []
    for block in blocks:
        lines = block.splitlines()
        index = int(lines[0]) - 1
        segment = timing["segments"][index]
        text = "\\N".join(lines[2:]).replace("{", "\\{").replace("}", "\\}")
        events.append(
            f"Dialogue: 0,{_ass_stamp(int(segment['start_microseconds']))},{_ass_stamp(int(segment['end_microseconds']))},Default,,0,0,0,{text}"
        )
    return """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, TertiaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, AlphaLevel, Encoding
Style: Default,Microsoft YaHei,48,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,1,3,0,2,76,160,220,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
""" + "\n".join(events) + "\n"


def escape_subtitle_path(path: str) -> str:
    return str(path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def _subtitle_filter(captions: Path) -> str:
    filename = escape_subtitle_path(str(captions.resolve()))
    return f"ass='{filename}'"


def _audio_filter(entries: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    labels: list[str] = []
    for input_index, entry in enumerate(entries, start=1):
        label = f"a{input_index}"
        delay_ms = int(round(int(entry["start_microseconds"]) / 1000))
        parts.append(f"[{input_index}:a]adelay={delay_ms}:all=1[{label}]")
        labels.append(f"[{label}]")
    parts.append("".join(labels) + f"amix=inputs={len(entries)}:duration=longest:normalize=0,apad[aout]")
    return ";".join(parts)


def _probe(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=index,codec_type,codec_name,width,height,avg_frame_rate,channels",
            "-of", "json", str(path),
        ], capture_output=True, text=True, check=False, timeout=60,
    )
    if completed.returncode != 0:
        raise ValueError("ffprobe_failed")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("ffprobe_invalid") from exc


def _fps(value: object) -> float:
    numerator, _, denominator = str(value or "0/1").partition("/")
    return float(numerator or 0) / float(denominator or 1)


def _validate_video(info: dict[str, Any], duration: float, *, require_audio: bool = True) -> dict[str, Any]:
    streams = info.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not video or video.get("codec_name") != "h264" or video.get("width") != 1080 or video.get("height") != 1920:
        raise ValueError("final_video_contract_invalid")
    fps = _fps(video.get("avg_frame_rate"))
    actual_duration = float(info.get("format", {}).get("duration", 0.0) or 0.0)
    if abs(fps - 30.0) > 0.001 or abs(actual_duration - duration) > 0.1 or (require_audio and (not audio or audio.get("codec_name") != "aac")):
        raise ValueError("final_media_contract_invalid")
    return {"width": 1080, "height": 1920, "fps": fps, "duration_seconds": actual_duration,
            "audio_codec": audio.get("codec_name") if audio else None,
            "audio_channels": audio.get("channels") if audio else None}


def _loudness(path: Path) -> tuple[float, float]:
    completed = subprocess.run(
        ["ffmpeg", "-nostats", "-v", "info", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, check=False, timeout=300,
    )
    mean = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?) dB", completed.stderr)
    peak = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?) dB", completed.stderr)
    if completed.returncode != 0 or mean is None or peak is None:
        raise ValueError("final_loudness_invalid")
    return float(mean.group(1)), float(peak.group(1))


def _write_exclusive(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visual", required=True, type=Path)
    parser.add_argument("--visual-report", required=True, type=Path)
    parser.add_argument("--product-input", required=True, type=Path)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--timing-root", required=True, type=Path)
    parser.add_argument("--captions", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--attempt", required=True, type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    visual = args.visual.resolve()
    visual_report_path = args.visual_report.resolve()
    product_path = args.product_input.resolve()
    script_path = args.script.resolve()
    manifest_path = args.manifest.resolve()
    timing_root = _output_root(args.timing_root, "timing_root")
    captions = _output_root(args.captions, "captions")
    ass_path = captions.with_suffix(".ass")
    output = _output_root(args.output, "output")
    report_path = _output_root(args.report, "report")
    if args.attempt < 1 or not all(path.is_file() for path in (visual, visual_report_path, product_path, script_path, manifest_path)):
        raise ValueError("input_missing")
    if any(path.exists() for path in (captions, ass_path, output, report_path)):
        raise ValueError("output_exists")

    product_bytes = product_path.read_bytes()
    product = _read_json(product_path)
    script = _read_json(script_path)
    timing = load_manifest(manifest_path, drafts_root=timing_root)
    render_report = _read_json(visual_report_path)
    product_sha = hashlib.sha256(product_bytes).hexdigest()
    script_sha = sha256(script_path)
    timing_sha = sha256(manifest_path)
    if product.get("mode") != "production_candidate" or product.get("aspect") != "9:16" or product.get("fps") != 30:
        raise ValueError("product_input_not_production")
    if product.get("scriptSha256") != script_sha or product.get("timingSha256") != timing_sha:
        raise ValueError("product_input_hash_mismatch")
    if timing.get("status") != "timing_manifest_ready" or timing.get("timing", {}).get("authority") != "local_jianying_sami_audio_files":
        raise ValueError("timing_manifest_not_sami")
    if timing.get("voice", {}).get("requested_backend") != "sami" or any(str(item).lower() != "sami" for item in timing.get("voice", {}).get("used_backends", [])):
        raise ValueError("timing_manifest_not_sami")
    if render_report.get("status") != "passed" or render_report.get("content_kind") != "website_product_promo":
        raise ValueError("visual_report_not_product")
    if render_report.get("visual", {}).get("sha256") != sha256(visual) or render_report.get("visual", {}).get("burned_in_subtitles") is not False:
        raise ValueError("visual_report_hash_mismatch")
    if len(product.get("scenes", [])) != len(timing.get("segments", [])) or len(script.get("beats", [])) != len(timing.get("segments", [])):
        raise ValueError("product_timing_scene_count_mismatch")

    visual_info = _probe(visual)
    target_duration = float(timing["visual_duration_seconds"])
    visual_meta = _validate_video(visual_info, target_duration, require_audio=False)
    srt = build_srt(timing, script)
    _write_exclusive(captions, srt)
    _write_exclusive(ass_path, build_ass(timing, script))

    audio_entries: list[dict[str, Any]] = []
    audio_paths: list[Path] = []
    for segment in timing["segments"]:
        if segment.get("subsegments") is not None:
            raise ValueError("product_subsegments_not_supported")
        audio_entries.append(segment)
        audio_paths.append(resolve_audio_path(timing, timing_root, segment))
    command = ["ffmpeg", "-y", "-nostdin", "-v", "error", "-i", str(visual)]
    for audio_path in audio_paths:
        command.extend(["-i", str(audio_path)])
    command.extend([
        "-filter_complex", _audio_filter(audio_entries),
        "-vf", _subtitle_filter(ass_path),
        "-map", "0:v:0", "-map", "[aout]", "-t", f"{target_duration:.6f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(output),
    ])
    completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=900)
    if completed.returncode != 0:
        raise ValueError(f"final_assemble_failed:{completed.stderr[-500:]}")

    info = _probe(output)
    final_meta = _validate_video(info, target_duration)
    decode = subprocess.run(["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"], capture_output=True, text=True, check=False, timeout=900)
    if decode.returncode != 0:
        raise ValueError("final_full_decode_failed")
    mean_volume, max_volume = _loudness(output)
    if max_volume >= 0.0:
        raise ValueError("final_audio_clipping")
    scenes = product["scenes"]
    cta = scenes[-1]
    cta_seconds = (int(cta["endFrame"]) - int(cta["startFrame"])) / 30.0
    if cta.get("kind") != "cta" or cta_seconds < 4.0:
        raise ValueError("cta_hold_invalid")
    report = {
        "schema_version": "1.0",
        "status": "ready_for_human_review",
        "content_kind": "website_product_promo",
        "job_id": args.job_id,
        "attempt": args.attempt,
        "composition": "WebsiteProductDemo",
        "visual_source": {"filename": visual.name, "sha256": sha256(visual), "report_sha256": sha256(visual_report_path), **visual_meta},
        "inputs": {
            "product_input": {"filename": product_path.name, "sha256": product_sha},
            "script": {"filename": script_path.name, "sha256": script_sha},
            "timing_manifest": {"filename": manifest_path.name, "sha256": timing_sha},
            "capture_manifest_sha256": product.get("captureManifestSha256"),
            "capture_review_sha256": product.get("captureReviewSha256"),
        },
        "captions": {"filename": captions.name, "sha256": sha256(captions), "ass_filename": ass_path.name, "ass_sha256": sha256(ass_path), "cue_count": len(audio_entries), "mode": "burned_in_ffmpeg_libass_ass", "burned_in": True, "safe_area": {"top": 1640, "height": 120, "margin_bottom": 220}},
        "audio": {"authority": "local_jianying_sami_audio_files", "backend": "sami", "segment_count": len(audio_entries), "coverage_ratio": timing["voice"]["coverage_ratio"], "mean_volume_db": mean_volume, "max_volume_db": max_volume, "codec": final_meta["audio_codec"], "channels": final_meta["audio_channels"]},
        "output": {"filename": output.name, "sha256": sha256(output), **final_meta, "full_decode": True, "audio_present": True, "burned_in_subtitles": True},
        "cta": {"duration_seconds": cta_seconds, "website": "photo.joviluma.com"},
        "quality": {"status": "passed", "visual_master_unchanged": True, "single_visual_render": True, "subtitle_hashes_bound": True, "sami_timing_bound": True, "capture_review_bound": True, "automatic_export": False},
        "human_review_required": True,
        "automatic_export": False,
        "outputs_on_e_drive": True,
    }
    _write_exclusive(report_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": True, "code": "website_product_preview_ready", "report": str(report_path), "output": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "code": "website_product_preview_failed", "reason": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
