"""Render two one-second production-profile still probes without a full candidate."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml

from video_factory.pipeline.renderer import build_render_command


ROOT = Path(__file__).resolve().parents[3]
FROZEN = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_freertos_candidate004_20260927/candidate004_single_render")
OUTPUT = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_freertos_scene45_20260927")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise RuntimeError(result.stderr[-1200:])


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    timeline = json.loads((FROZEN / "timeline.json").read_text(encoding="utf-8"))
    job = yaml.safe_load((FROZEN / "render_job.yaml").read_text(encoding="utf-8"))
    source_cues = [part.splitlines()[2] for part in (FROZEN / "subtitle.srt").read_text(encoding="utf-8").strip().split("\n\n")]
    results = []
    for scene_index in (4, 5):
        label = f"scene{scene_index}"
        cue = source_cues[scene_index - 1]
        subtitle = OUTPUT / f"{label}_subtitle.srt"
        subtitle.write_text(f"1\n00:00:00,000 --> 00:00:01,000\n{cue}\n", encoding="utf-8")
        mp4 = OUTPUT / f"{label}_production_still_probe.mp4"
        scene = {**timeline["scenes"][scene_index - 1], "duration": 1.0}
        command, duration = build_render_command(
            asset_dir=ROOT, timeline=[scene], subtitle_path=subtitle,
            output_path=mp4, transition_seconds=0.4, transition_mode="technical_cut",
            audio_path=None, repo_root=ROOT, subtitle_style=job["subtitle"]["style"],
            encoder="cpu", canvas_width=1920, canvas_height=1080, fps=30,
            pad_color=job["render"]["pad_color"],
        )
        run(command)
        still = OUTPUT / f"{label}_production_still.png"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4), "-vf", "select=eq(n\\,15)",
             "-vsync", "0", "-frames:v", "1", str(still)])
        results.append({"scene": scene_index, "subtitle_text": cue, "subtitle_sha256": sha(subtitle),
                        "duration_seconds": duration, "probe_mp4_sha256": sha(mp4),
                        "still_path": str(still), "still_sha256": sha(still)})
        print(f"[{scene_index - 3}/2] {label} still={still}", flush=True)
    (OUTPUT / "scene45_still_probe_report.json").write_text(
        json.dumps({"source_candidate": "Candidate004", "source_mp4_sha256": sha(FROZEN / "final_master.mp4"),
                    "profile": "1920x1080/30fps, same bottom-safe subtitle style and real cue text",
                    "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
