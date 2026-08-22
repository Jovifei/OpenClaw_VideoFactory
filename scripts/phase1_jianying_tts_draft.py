"""Create one new Jianying draft with consistent AI narration and subtitles.

This is an optional Phase 1 review adapter. It deliberately does not export
through UI automation and never reopens or overwrites an existing draft.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_draft_path(root: Path, name: str) -> Path:
    root_resolved = root.resolve()
    target = (root_resolved / name).resolve()
    if os.path.commonpath([str(root_resolved), str(target)]) != str(root_resolved):
        raise ValueError("draft_path_outside_root")
    return target


def _load_script(path: Path) -> list[dict[str, str]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    beats = value.get("beats") if isinstance(value, dict) else None
    if not isinstance(beats, list) or len(beats) != 5:
        raise ValueError("script_must_have_five_beats")
    result: list[dict[str, str]] = []
    for index, beat in enumerate(beats, start=1):
        if not isinstance(beat, dict):
            raise ValueError(f"beat_{index}_invalid")
        narration = str(beat.get("narration", "")).strip()
        subtitle = str(beat.get("subtitle", "")).strip()
        if not narration or not subtitle:
            raise ValueError(f"beat_{index}_text_missing")
        result.append({"narration": narration, "subtitle": subtitle})
    return result


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
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--drafts-root", required=True, type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--speaker", default="zh_male_huoli")
    parser.add_argument("--backend", choices=("sami", "edge"), default="sami")
    parser.add_argument("--skill-root", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    visual = args.visual.resolve()
    script_path = args.script.resolve()
    drafts_root = args.drafts_root.resolve()
    report_path = args.report.resolve()
    skill_root = args.skill_root.resolve()

    if not visual.is_file() or not script_path.is_file():
        raise ValueError("input_missing")
    if not (skill_root / "scripts" / "jy_wrapper.py").is_file():
        raise ValueError("skill_root_invalid")
    drafts_root.mkdir(parents=True, exist_ok=True)
    draft_path = _safe_draft_path(drafts_root, args.name)
    if draft_path.exists():
        raise ValueError("draft_already_exists")

    beats = _load_script(script_path)
    scripts_dir = str(skill_root / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    os.environ["JY_SKILL_ROOT"] = str(skill_root)

    from jy_wrapper import JyProject

    project = None
    backend_used: list[str] = []
    try:
        project = JyProject(
            args.name,
            width=1080,
            height=1920,
            drafts_root=str(drafts_root),
            overwrite=False,
        )
        visual_segment = project.add_media_safe(str(visual), start_time="0s", track_name="VideoTrack")
        if visual_segment is None:
            raise ValueError("visual_import_failed")
        visual_duration_us = int(visual_segment.target_timerange.duration)

        cursor_us = 0
        for index, beat in enumerate(beats, start=1):
            # The Skill prints local Jianying identifiers while it probes the
            # native backend. Capture that output and never persist it.
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
            backend_used.append(str(used))
            duration_us = int(audio_segment.target_timerange.duration)
            project.add_text_simple(
                beat["subtitle"],
                start_time=cursor_us,
                duration=duration_us,
                track_name="Subtitles",
            )
            cursor_us += duration_us + 100_000

        if cursor_us > visual_duration_us:
            raise ValueError("visual_shorter_than_voice")

        save_sink = io.StringIO()
        with contextlib.redirect_stdout(save_sink):
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
            },
            "voice": {
                "speaker": args.speaker,
                "requested_backend": args.backend,
                "used_backends": backend_used,
                "segment_count": len(beats),
                "subtitle_segment_count": len(beats),
                "timeline_duration_microseconds": cursor_us,
            },
            "visual_duration_microseconds": visual_duration_us,
            "tracks": _track_report(project),
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
