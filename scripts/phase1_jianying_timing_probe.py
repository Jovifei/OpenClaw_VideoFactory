"""Generate exact local Jianying TTS assets and persist their shared timeline."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase1_jianying_timing import (  # noqa: E402
    DEFAULT_GAP_MICROSECONDS,
    FPS,
    load_script,
    sha256,
)


DEFAULT_DRAFTS_ROOT = Path("E:/OpenClaw_VideoFactory_Runtime/jianying_timing_probes")


def _output_root(path: Path, field: str) -> Path:
    resolved = path.resolve()
    if resolved.drive.upper() == "C:":
        raise ValueError(f"{field}_must_not_use_c_drive")
    return resolved


def _safe_draft_path(root: Path, name: str) -> Path:
    target = (root.resolve() / name).resolve()
    if os.path.commonpath([str(root.resolve()), str(target)]) != str(root.resolve()):
        raise ValueError("draft_path_outside_root")
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--drafts-root", type=Path, default=DEFAULT_DRAFTS_ROOT)
    parser.add_argument("--name", required=True)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--speaker", default="zh_male_huoli")
    parser.add_argument("--backend", choices=("sami", "edge"), default="sami")
    parser.add_argument("--skill-root", required=True, type=Path)
    parser.add_argument("--gap-ms", type=int, default=DEFAULT_GAP_MICROSECONDS // 1000)
    parser.add_argument("--visual-duration-seconds", type=float, default=50.0)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    script_path = args.script.resolve()
    drafts_root = _output_root(args.drafts_root, "drafts_root")
    manifest_path = _output_root(args.manifest, "manifest")
    skill_root = args.skill_root.resolve()
    if not script_path.is_file():
        raise ValueError("script_missing")
    if args.gap_ms < 0 or args.gap_ms > 2000:
        raise ValueError("gap_invalid")
    if args.visual_duration_seconds < 25 or args.visual_duration_seconds > 60:
        raise ValueError("visual_duration_invalid")
    if not (skill_root / "scripts" / "jy_wrapper.py").is_file():
        raise ValueError("skill_root_invalid")
    drafts_root.mkdir(parents=True, exist_ok=True)
    draft_path = _safe_draft_path(drafts_root, args.name)
    if draft_path.exists():
        raise ValueError("timing_probe_already_exists")
    script_value, beats = load_script(script_path)
    sys.path.insert(0, str(skill_root / "scripts"))
    os.environ["JY_SKILL_ROOT"] = str(skill_root)
    from jy_wrapper import JyProject

    project = None
    segments: list[dict[str, object]] = []
    cursor_us = 0
    gap_us = args.gap_ms * 1000
    backend_used: list[str] = []
    try:
        project = JyProject(
            args.name,
            width=args.width,
            height=args.height,
            drafts_root=str(drafts_root),
            overwrite=False,
        )
        for index, beat in enumerate(beats, start=1):
            sink = io.StringIO()
            with contextlib.redirect_stdout(sink):
                audio_segment, used = project.add_tts_intelligent(
                    beat["narration"],
                    speaker=args.speaker,
                    start_time=cursor_us,
                    track_name="VoiceOver",
                    tts_backend=args.backend,
                    allow_fallback=False,
                    return_backend=True,
                )
            if audio_segment is None or not used:
                raise ValueError(f"tts_segment_{index}_failed")
            material = getattr(audio_segment, "material_instance", None)
            audio_path = Path(str(getattr(material, "path", ""))).resolve()
            if not audio_path.is_file():
                raise ValueError(f"tts_segment_{index}_asset_missing")
            duration_us = int(audio_segment.target_timerange.duration)
            end_us = cursor_us + duration_us
            relative = audio_path.relative_to(drafts_root.resolve()).as_posix()
            backend_used.append(str(used))
            segments.append(
                {
                    "index": index,
                    "start_microseconds": cursor_us,
                    "end_microseconds": end_us,
                    "duration_microseconds": duration_us,
                    "audio_relative_path": relative,
                    "audio_filename": audio_path.name,
                    "audio_sha256": sha256(audio_path),
                    "narration_sha256": hashlib.sha256(beat["narration"].encode("utf-8")).hexdigest(),
                    "subtitle_sha256": hashlib.sha256(beat["subtitle"].encode("utf-8")).hexdigest(),
                }
            )
            cursor_us = end_us + (gap_us if index < len(beats) else 0)
        visual_duration_us = round(args.visual_duration_seconds * 1_000_000)
        for index, segment in enumerate(segments):
            segment["scene_start_microseconds"] = int(segment["start_microseconds"])
            segment["scene_end_microseconds"] = (
                int(segments[index + 1]["start_microseconds"])
                if index + 1 < len(segments)
                else visual_duration_us
            )
        save_sink = io.StringIO()
        with contextlib.redirect_stdout(save_sink):
            save_result = project.save()
        if not isinstance(save_result, dict) or save_result.get("status") != "SUCCESS":
            raise ValueError("timing_probe_save_failed")
        manifest = {
            "schema_version": "1.0",
            "status": "timing_manifest_ready",
            "script": {
                "filename": script_path.name,
                "sha256": sha256(script_path),
                "title": str(script_value.get("title", "")),
            },
            "timing": {
                "fps": FPS,
                "inter_segment_gap_microseconds": gap_us,
                "frame_tolerance_microseconds": 1_000_000 // FPS + 1,
                "authority": "local_jianying_sami_audio_files",
            },
            "voice": {
                "speaker": args.speaker,
                "requested_backend": args.backend,
                "used_backends": backend_used,
                "segment_count": len(segments),
                "voice_end_microseconds": segments[-1]["end_microseconds"],
                "timeline_duration_seconds": round(float(segments[-1]["end_microseconds"]) / 1_000_000, 6),
            },
            "visual_duration_seconds": args.visual_duration_seconds,
            "probe": {
                "draft_relative_path": args.name,
                "drafts_root_drive": drafts_root.drive.upper(),
                "audio_paths_are_runtime_relative": True,
            },
            "segments": segments,
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "code": "timing_manifest_ready", "manifest": str(manifest_path), "segments": segments}, ensure_ascii=False))
        return 0
    except Exception:
        if draft_path.exists():
            import shutil

            shutil.rmtree(draft_path)
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "code": "timing_probe_failed", "reason": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
