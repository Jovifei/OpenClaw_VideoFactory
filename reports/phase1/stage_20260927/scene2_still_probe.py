"""Render one scene-2 still with the actual local-brief subtitle style."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from generate_video import _local_brief_subtitle_style  # noqa: E402
from video_factory.pipeline.renderer import _subtitle_force_style  # noqa: E402


EVIDENCE = Path(__file__).resolve().parent
JOB = ROOT / "dist/phase1_local/phase1_8958d25a694923c9/render_job.yaml"
ORIGINAL_SRT = ROOT / "dist/phase1_local/phase1_8958d25a694923c9/subtitle.srt"
ONE_CUE = EVIDENCE / "scene2_one_cue.srt"
CANDIDATE = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_freertos_scene2_20260927/02-isr-handoff-candidate.png")
STILL = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_freertos_scene2_20260927/scene2_production_style_still.png")
REPORT = EVIDENCE / "scene2_still_probe.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    for path in (ONE_CUE, STILL, REPORT):
        if path.exists():
            raise RuntimeError(f"still_probe_target_exists:{path.name}")
    job = yaml.safe_load(JOB.read_text(encoding="utf-8"))
    width, height = int(job["render"]["width"]), int(job["render"]["height"])
    fps = int(job["render"]["fps"])
    style = job["subtitle"]["style"]
    if style != _local_brief_subtitle_style(width, height):
        raise RuntimeError("subtitle_style_drift")
    cue = next(
        block.splitlines()[2]
        for block in ORIGINAL_SRT.read_text(encoding="utf-8").strip().split("\n\n")
        if block.splitlines()[0] == "2"
    )
    ONE_CUE.write_text(f"1\n00:00:00,000 --> 00:00:01,000\n{cue}\n", encoding="utf-8")
    ass_style = _subtitle_force_style(style, canvas_width=width, canvas_height=height)
    srt_path = ONE_CUE.resolve().as_posix().replace(":", r"\:")
    filter_graph = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color={job['render']['pad_color']},"
        f"fps={fps},setsar=1,format=yuv420p,"
        f"subtitles=filename='{srt_path}':charenc=UTF-8:force_style='{ass_style}'"
    )
    command = [
        "ffmpeg", "-nostdin", "-v", "error", "-loop", "1", "-framerate", str(fps),
        "-t", "1", "-i", str(CANDIDATE), "-vf", filter_graph,
        "-frames:v", "1", "-pix_fmt", "rgb24", str(STILL),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
    report = {
        "schema_version": "phase1_scene2_still_probe_v1",
        "command": command,
        "exit_code": result.returncode,
        "stderr": result.stderr[-1500:],
        "source_candidate_sha256": sha(CANDIDATE),
        "subtitle": cue,
        "subtitle_style": style,
        "ass_force_style": ass_style,
        "still_exists": STILL.is_file(),
        "still_sha256": sha(STILL) if STILL.is_file() else None,
        "status": "rendered_for_visual_review" if result.returncode == 0 and STILL.is_file() else "failed",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "exit_code": result.returncode, "still_sha256": report["still_sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
