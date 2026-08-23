"""Render a Jianying-safe visual through the canonical local renderer.

The review MP4 intentionally contains burned-in captions. Jianying drafts
must instead import a visual-only render and carry captions on exactly one
native text track. This helper changes only the temporary job contract and
still calls ``generate_video.run_job``; it does not introduce a second
renderer or control the desktop.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("output_must_remain_in_project") from exc


def _reject_c_drive(path: Path, field: str) -> Path:
    resolved = path.resolve()
    if resolved.drive.upper() == "C:":
        raise ValueError(f"{field}_must_not_use_c_drive")
    return resolved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", required=True, type=Path, help="Existing VideoRenderJob YAML")
    parser.add_argument("--output", required=True, type=Path, help="E-drive visual-only MP4 output")
    parser.add_argument("--report", required=True, type=Path, help="E-drive JSON report")
    parser.add_argument("--tail-seconds", type=float, default=5.0, help="Clone the last frame for this many seconds")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    job_path = args.job.resolve()
    output_path = _reject_c_drive(args.output, "output")
    report_path = _reject_c_drive(args.report, "report")
    if args.tail_seconds < 0 or args.tail_seconds > 30:
        raise ValueError("tail_seconds_invalid")
    if not job_path.is_file():
        raise ValueError("job_missing")
    job = yaml.safe_load(job_path.read_text(encoding="utf-8"))
    if not isinstance(job, dict):
        raise ValueError("job_invalid")
    original_work_dir = job_path.parent.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    auxiliary_dir = output_path.parent / "jianying_visual_render"
    if auxiliary_dir.exists() and auxiliary_dir.is_symlink():
        raise ValueError("auxiliary_work_dir_reparse")
    auxiliary_dir.mkdir(parents=True, exist_ok=True)
    temporary_job = auxiliary_dir / "render_job.yaml"
    visual_job = json.loads(json.dumps(job, ensure_ascii=False))
    base_job_id = str(visual_job.get("job_id", "phase1"))
    visual_job["job_id"] = f"{base_job_id}_jyvisual"
    visual_job["storyboard_ref"] = os.path.relpath(
        original_work_dir / str(job["storyboard_ref"]), auxiliary_dir
    ).replace("\\", "/")
    visual_job["subtitle"] = dict(visual_job.get("subtitle") or {})
    visual_job["subtitle"]["enabled"] = False
    visual_job["audio"] = dict(visual_job.get("audio") or {})
    visual_job["audio"]["strategy"] = "silent"
    visual_job["audio"]["require_narration"] = False
    visual_job["outputs"] = {
        "video": _repo_relative(auxiliary_dir / "visual_raw.mp4"),
        "work_dir": _repo_relative(auxiliary_dir),
    }
    temporary_job.write_text(
        yaml.safe_dump(visual_job, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from generate_video import run_job

    result = run_job(temporary_job, emit=False)
    raw_visual = auxiliary_dir / "visual_raw.mp4"
    if not raw_visual.is_file() or raw_visual.stat().st_size <= 0:
        raise ValueError("visual_output_missing")
    render_report = json.loads((auxiliary_dir / "render_report.json").read_text(encoding="utf-8"))
    if render_report.get("subtitle", {}).get("present") is not False:
        raise ValueError("visual_subtitle_burn_in_not_disabled")
    if render_report.get("audio", {}).get("present") is not False:
        raise ValueError("visual_audio_not_disabled")
    if args.tail_seconds:
        padded = output_path.with_suffix(".padding.mp4")
        completed = subprocess.run(
            [
                "ffmpeg", "-y", "-nostdin", "-v", "error", "-i", str(raw_visual),
                "-vf", f"tpad=stop_mode=clone:stop_duration={args.tail_seconds:.3f}",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", str(padded),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        if completed.returncode != 0 or not padded.is_file() or padded.stat().st_size <= 0:
            raise ValueError("visual_tail_padding_failed")
        os.replace(padded, output_path)
    else:
        shutil.copyfile(raw_visual, output_path)
    manifest = {
        "schema_version": "1.0",
        "status": "ready_for_jianying",
        "visual_filename": output_path.name,
        "visual_path": _repo_relative(output_path),
        "visual_sha256": _sha256(output_path),
        "subtitle_burn_in": False,
        "audio_present": False,
        "tail_pad_seconds": float(args.tail_seconds),
        "subtitle_authority": "jianying_native_subtitles_track",
        "renderer": "generate_video.run_job",
        "source_job_id": str(job.get("job_id", "")),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps({"result": result, "visual": manifest}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "code": "jianying_visual_ready", "visual": manifest}, ensure_ascii=False))
    return 0


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "code": "jianying_visual_failed", "reason": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
