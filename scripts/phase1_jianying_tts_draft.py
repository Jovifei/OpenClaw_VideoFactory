"""Create one new Jianying draft with consistent AI narration and subtitles.

This is an optional Phase 1 review adapter. It deliberately does not export
through UI automation and never reopens or overwrites an existing draft.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase1_jianying_timing import (  # noqa: E402
    FRAME_TOLERANCE_MICROSECONDS,
    load_manifest,
    load_script,
    manifest_audio_entries,
    sha256,
)


DEFAULT_DRAFTS_ROOT = Path("E:/OpenClaw_VideoFactory_Runtime/jianying_drafts")


def _sha256(path: Path) -> str:
    """Compatibility wrapper retained for callers of the older helper."""
    return sha256(path)


def _safe_draft_path(root: Path, name: str) -> Path:
    root_resolved = root.resolve()
    target = (root_resolved / name).resolve()
    if os.path.commonpath([str(root_resolved), str(target)]) != str(root_resolved):
        raise ValueError("draft_path_outside_root")
    return target


def _output_root(path: Path, field: str) -> Path:
    resolved = path.resolve()
    if resolved.drive.upper() == "C:":
        raise ValueError(f"{field}_must_not_use_c_drive")
    return resolved


def _load_script(path: Path) -> list[dict[str, str]]:
    return load_script(path)[1]


def _probe_visual_canvas(path: Path) -> tuple[int, int]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        raise ValueError("visual_probe_failed")
    try:
        streams = json.loads(completed.stdout).get("streams", [])
        width = int(streams[0]["width"])
        height = int(streams[0]["height"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("visual_probe_invalid") from exc
    if width <= 0 or height <= 0:
        raise ValueError("visual_canvas_invalid")
    return width, height


def _probe_duration_microseconds(path: Path) -> int:
    completed = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                               capture_output=True, text=True, check=False, timeout=30)
    if completed.returncode != 0:
        raise ValueError("visual_clip_probe_failed")
    try:
        return round(float(completed.stdout.strip()) * 1_000_000)
    except ValueError as exc:
        raise ValueError("visual_clip_probe_invalid") from exc


def verify_scene_clips(render_report: Path, clips_root: Path, segments: list[dict[str, Any]], *, duration_probe=_probe_duration_microseconds) -> list[dict[str, Any]]:
    report = json.loads(render_report.read_text(encoding="utf-8"))
    declarations = report.get("visual", {}).get("scene_timing")
    if not isinstance(declarations, list) or len(declarations) != len(segments):
        raise ValueError("visual_clip_count_mismatch")
    root = clips_root.resolve(); verified = []
    for expected, (declaration, timing) in enumerate(zip(declarations, segments), start=1):
        if declaration.get("scene_index") != expected or timing.get("index") != expected:
            raise ValueError("visual_clip_index_mismatch")
        clip = declaration.get("clip")
        raw = str(clip.get("filename", "")) if isinstance(clip, dict) else ""
        candidate = (render_report.parent / raw).resolve()
        if os.path.commonpath([str(root), str(candidate)]) != str(root):
            raise ValueError("visual_clip_path_escape")
        if not candidate.is_file():
            raise ValueError("visual_clip_missing")
        if clip.get("sha256") != sha256(candidate):
            raise ValueError("visual_clip_hash_mismatch")
        expected_duration = int(timing["scene_end_microseconds"]) - int(timing["scene_start_microseconds"])
        declared_start = round(float(declaration.get("start_seconds", -1)) * 1_000_000)
        declared_end = round(float(declaration.get("end_seconds", -1)) * 1_000_000)
        if declared_start != int(timing["scene_start_microseconds"]) or declared_end != int(timing["scene_end_microseconds"]):
            raise ValueError("visual_clip_declaration_timing_mismatch")
        declared_duration = declared_end - declared_start
        reported_duration = clip.get("duration_microseconds")
        if not isinstance(reported_duration, int) or reported_duration <= 0:
            raise ValueError("visual_clip_declared_duration_invalid")
        actual_duration = int(duration_probe(candidate))
        if (abs(reported_duration - declared_duration) > FRAME_TOLERANCE_MICROSECONDS
                or abs(reported_duration - expected_duration) > FRAME_TOLERANCE_MICROSECONDS
                or abs(reported_duration - actual_duration) > FRAME_TOLERANCE_MICROSECONDS
                or abs(actual_duration - expected_duration) > FRAME_TOLERANCE_MICROSECONDS
                or abs(actual_duration - declared_duration) > FRAME_TOLERANCE_MICROSECONDS):
            if reported_duration != declared_duration:
                raise ValueError("visual_clip_declared_duration_invalid")
            raise ValueError("visual_clip_duration_drift")
        verified.append({"index": expected, "path": candidate, "sha256": sha256(candidate), "duration_microseconds": actual_duration})
    if set(root.glob("scene_*.mp4")) != {item["path"] for item in verified}:
        raise ValueError("visual_clip_directory_contaminated")
    return verified


def _track_report(project: Any) -> list[dict[str, object]]:
    tracks = getattr(project.script, "tracks", {})
    values = tracks.values() if isinstance(tracks, dict) else []
    report: list[dict[str, object]] = []
    for track in values:
        segments = list(getattr(track, "segments", []) or [])
        report.append(
            {
                "name": str(getattr(track, "name", "")),
                "type": str(getattr(track, "type", "")),
                "mute": bool(getattr(track, "mute", False)),
                "volume": getattr(track, "volume", None),
                "segment_count": len(segments),
                "duration_microseconds": max(
                    [int(getattr(getattr(seg, "target_timerange", None), "end", 0)) for seg in segments]
                    or [0]
                ),
            }
        )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visual", required=True, type=Path)
    parser.add_argument("--visual-report", type=Path)
    parser.add_argument("--clips-root", type=Path)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--timing-manifest", required=True, type=Path)
    parser.add_argument("--drafts-root", type=Path, default=DEFAULT_DRAFTS_ROOT)
    parser.add_argument("--timing-root", required=True, type=Path, help="E-drive root that owns the probe audio files")
    parser.add_argument("--name", required=True)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--speaker", default="zh_male_huoli")
    parser.add_argument("--backend", choices=("sami", "edge"), default="sami")
    parser.add_argument("--skill-root", required=True, type=Path)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    visual = args.visual.resolve()
    script_path = args.script.resolve()
    timing_manifest_path = args.timing_manifest.resolve()
    drafts_root = _output_root(args.drafts_root, "drafts_root")
    timing_root = _output_root(args.timing_root, "timing_root")
    report_path = _output_root(args.report, "report")
    skill_root = args.skill_root.resolve()
    if (args.visual_report is None) != (args.clips_root is None):
        raise ValueError("visual_report_and_clips_root_required_together")

    if not visual.is_file() or not script_path.is_file() or not timing_manifest_path.is_file():
        raise ValueError("input_missing")
    if args.width < 320 or args.height < 180 or args.width % 2 or args.height % 2:
        raise ValueError("canvas_invalid")
    visual_width, visual_height = _probe_visual_canvas(visual)
    if (visual_width, visual_height) != (args.width, args.height):
        raise ValueError("visual_canvas_mismatch")
    if not (skill_root / "scripts" / "jy_wrapper.py").is_file():
        raise ValueError("skill_root_invalid")
    drafts_root.mkdir(parents=True, exist_ok=True)
    draft_path = _safe_draft_path(drafts_root, args.name)
    if draft_path.exists():
        raise ValueError("draft_already_exists")

    _, beats = load_script(script_path)
    timing_manifest = load_manifest(timing_manifest_path, drafts_root=timing_root)
    expected_script_sha = str(timing_manifest.get("script", {}).get("sha256", ""))
    if expected_script_sha != sha256(script_path):
        raise ValueError("timing_manifest_script_mismatch")
    manifest_segments = timing_manifest["segments"]
    if len(manifest_segments) != len(beats):
        raise ValueError("timing_manifest_segment_count_mismatch")
    voice_meta = timing_manifest["voice"]
    if voice_meta.get("speaker") != args.speaker or voice_meta.get("requested_backend") != args.backend:
        raise ValueError("timing_manifest_voice_settings_mismatch")
    expected_visual_duration_us = round(float(timing_manifest["visual_duration_seconds"]) * 1_000_000)
    scene_clips = verify_scene_clips(args.visual_report.resolve(), args.clips_root.resolve(), manifest_segments) if args.visual_report else None
    if scene_clips is not None:
        render_value = json.loads(args.visual_report.read_text(encoding="utf-8"))
        master = render_value.get("visual", {})
        if master.get("sha256") != sha256(visual) or Path(str(master.get("filename", ""))).name != visual.name:
            raise ValueError("visual_render_report_master_mismatch")
    scripts_dir = str(skill_root / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    os.environ["JY_SKILL_ROOT"] = str(skill_root)

    from jy_wrapper import JyProject

    project = None
    backend_used: list[str] = list(timing_manifest["voice"].get("used_backends", []))
    voice_segments: list[dict[str, object]] = []
    try:
        project = JyProject(
            args.name,
            width=args.width,
            height=args.height,
            drafts_root=str(drafts_root),
            overwrite=False,
        )
        if scene_clips is None:
            visual_segment = project.add_media_safe(str(visual), start_time="0s", track_name="VideoTrack")
            if visual_segment is None: raise ValueError("visual_import_failed")
            visual_duration_us = int(visual_segment.target_timerange.duration)
        else:
            for clip, timing_entry in zip(scene_clips, manifest_segments):
                visual_segment = project.add_media_safe(str(clip["path"]), start_time=int(timing_entry["scene_start_microseconds"]), track_name="VideoTrack")
                if visual_segment is None: raise ValueError("visual_clip_import_failed")
            visual_duration_us = expected_visual_duration_us
        if abs(visual_duration_us - expected_visual_duration_us) > FRAME_TOLERANCE_MICROSECONDS: raise ValueError("visual_duration_manifest_mismatch")

        for index, beat in enumerate(beats, start=1):
            manifest_segment = manifest_segments[index - 1]
            from phase1_jianying_timing import resolve_audio_path
            for part_index, timing_entry in enumerate(manifest_audio_entries(manifest_segment), start=1):
                audio_path = resolve_audio_path(timing_manifest, timing_root, timing_entry)
                expected_start_us = int(timing_entry["start_microseconds"])
                expected_duration_us = int(timing_entry["duration_microseconds"])
                audio_segment = project.add_media_safe(
                    str(audio_path),
                    start_time=expected_start_us,
                    track_name="VoiceOver",
                )
                if audio_segment is None:
                    raise ValueError(f"timing_audio_import_{index}_{part_index}_failed")
                duration_us = int(audio_segment.target_timerange.duration)
                if abs(duration_us - expected_duration_us) > FRAME_TOLERANCE_MICROSECONDS:
                    raise ValueError(f"timing_audio_duration_drift_{index}_{part_index}")
                actual_start_us = int(audio_segment.target_timerange.start)
                if abs(actual_start_us - expected_start_us) > FRAME_TOLERANCE_MICROSECONDS:
                    raise ValueError(f"timing_audio_start_drift_{index}_{part_index}")
                voice_segments.append(
                    {
                        "index": len(voice_segments) + 1,
                        "parent_segment_index": index,
                        "part_index": part_index,
                        "cue_id": timing_entry.get("cue_id"),
                        "start_microseconds": actual_start_us,
                        "end_microseconds": actual_start_us + duration_us,
                        "duration_microseconds": duration_us,
                        "audio_filename": audio_path.name,
                        "audio_sha256": sha256(audio_path),
                        "narration_sha256": timing_entry.get("narration_sha256", manifest_segment["narration_sha256"]),
                        "subtitle_sha256": manifest_segment["subtitle_sha256"],
                    }
                )
            expected_start_us = int(manifest_segment["start_microseconds"])
            expected_duration_us = int(manifest_segment["duration_microseconds"])
            project.add_text_simple(
                beat["subtitle"],
                start_time=expected_start_us,
                duration=expected_duration_us,
                track_name="Subtitles",
            )

        voice_end_us = max(int(segment["end_microseconds"]) for segment in voice_segments)
        if abs(voice_end_us - int(voice_meta["voice_end_microseconds"])) > FRAME_TOLERANCE_MICROSECONDS:
            raise ValueError("voice_timeline_manifest_mismatch")
        if expected_visual_duration_us < voice_end_us:
            raise ValueError("visual_shorter_than_voice")

        track_report = _track_report(project)
        video_tracks = [item for item in track_report if item.get("name") == "VideoTrack"]
        voice_tracks = [item for item in track_report if item.get("name") == "VoiceOver"]
        subtitle_tracks = [item for item in track_report if item.get("name") == "Subtitles"]
        if len(voice_tracks) != 1 or bool(voice_tracks[0].get("mute")) or int(voice_tracks[0].get("segment_count", 0)) != len(voice_segments):
            raise ValueError("voice_track_not_audible")
        if len(subtitle_tracks) != 1 or int(subtitle_tracks[0].get("segment_count", 0)) != len(beats):
            raise ValueError("subtitle_track_invalid")
        expected_video_segments = len(manifest_segments) if scene_clips is not None else 1
        if len(video_tracks) != 1 or int(video_tracks[0].get("segment_count", 0)) != expected_video_segments:
            raise ValueError("video_track_invalid")

        save_result = project.save()
        if not isinstance(save_result, dict) or save_result.get("status") != "SUCCESS":
            raise ValueError("draft_save_failed")

        report_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "schema_version": "1.0",
            "status": "draft_ready_for_manual_jianying_review",
            "draft_name": args.name,
            "draft_relative_path": args.name,
            "skill": {
                "selected_backend": "jianying-editor-skill",
                "repository": "luoluoluo22/jianying-editor-skill",
                "pinned_commit": "f421c8a036f4fda888a83b38fc90bb9c00d6faa9",
                "license": "MIT",
            },
            "inputs": {
                "visual_filename": visual.name,
                "visual_sha256": _sha256(visual),
                "script_filename": script_path.name,
                "script_sha256": _sha256(script_path),
                "timing_manifest_filename": timing_manifest_path.name,
                "timing_manifest_sha256": _sha256(timing_manifest_path),
                "render_report_filename": args.visual_report.name if args.visual_report else None,
                "render_report_sha256": _sha256(args.visual_report.resolve()) if args.visual_report else None,
                "visual_clips": ([{"index": item["index"], "filename": item["path"].name, "sha256": item["sha256"], "duration_microseconds": item["duration_microseconds"]} for item in scene_clips] if scene_clips else []),
            },
            "voice": {
                "speaker": args.speaker,
                "requested_backend": args.backend,
                "used_backends": backend_used,
                "segment_count": len(voice_segments),
                "parent_segment_count": len(beats),
                "subtitle_segment_count": len(beats),
                "voice_end_microseconds": voice_end_us,
                "timeline_duration_microseconds": voice_end_us,
                "segments": voice_segments,
            },
            "canvas": {
                "width": args.width,
                "height": args.height,
                "fps": 30,
            },
            "visual_duration_microseconds": visual_duration_us,
            "sync_validation": {
                "status": "passed",
                "timing_authority": "timing_manifest",
                "frame_tolerance_microseconds": FRAME_TOLERANCE_MICROSECONDS,
                "visual_duration_matches_manifest": abs(visual_duration_us - expected_visual_duration_us) <= FRAME_TOLERANCE_MICROSECONDS,
                "scene_and_voice_boundaries_are_manifest_driven": True,
            },
            "tracks": track_report,
            "audio_validation": {
                "status": "passed",
                "voice_track": "VoiceOver",
                "muted": False,
                "segment_count": len(voice_segments),
                "human_listening_required": True,
            },
            "subtitle_validation": {
                "status": "passed",
                "authoritative_layer": "jianying_native_subtitles_track",
                "track_name": "Subtitles",
                "segment_count": len(beats),
                "burned_in_visual_must_be_false": True,
            },
            "output_root": str(drafts_root),
            "export": {
                "automatic_export": "disabled",
                "manual_action": "open the new draft in Jianying and review/listen before exporting",
            },
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "code": "draft_ready", "data": report}, ensure_ascii=False))
        return 0
    except Exception:
        if draft_path.exists():
            shutil.rmtree(draft_path)
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "code": "draft_failed", "reason": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
