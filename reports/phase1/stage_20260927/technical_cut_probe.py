"""Bounded two-scene probes for the four FreeRTOS technical cuts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from video_factory.pipeline.renderer import build_render_command
from video_factory.pipeline.composition import load_composition
from video_factory.pipeline.subtitle import build_srt_from_timeline
from video_factory.pipeline.storyboard import compile_storyboard
from video_factory.pipeline.registry import load_pink_pig_registry


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "dist/phase1_local/phase1_8958d25a694923c9"
OUTPUT = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_technical_cut_20260927")
TIMELINE = json.loads((SOURCE / "timeline.json").read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, timeout: int = 90) -> None:
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-1200:])


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    storyboard = json.loads((SOURCE / "storyboard.json").read_text(encoding="utf-8"))
    storyboard["globals"]["transition_mode"] = "technical_cut"
    compiled = compile_storyboard(
        storyboard, load_pink_pig_registry(repo_root=ROOT), repo_root=ROOT,
    )
    full_srt = OUTPUT / "technical_cut_40s.srt"
    cues = build_srt_from_timeline(
        compiled, full_srt,
        composition=load_composition("knowledge_illustration", repo_root=ROOT),
    )
    assert compiled["total_duration_seconds"] == 40.0
    assert [(c["start"], c["end"]) for c in cues] == [
        (0.0, 8.0), (8.0, 16.0), (16.0, 24.0), (24.0, 32.0), (32.0, 40.0),
    ]
    results = []
    for index in range(4):
        label = f"boundary_{index + 1}"
        scenes = []
        for item in TIMELINE["scenes"][index:index + 2]:
            scenes.append({**item, "duration": 0.5})
        subtitle = OUTPUT / f"{label}.srt"
        subtitle.write_text(
            f"1\n00:00:00,000 --> 00:00:00,500\n{scenes[0]['caption']}\n\n"
            f"2\n00:00:00,500 --> 00:00:01,000\n{scenes[1]['caption']}\n",
            encoding="utf-8",
        )
        mp4 = OUTPUT / f"{label}.mp4"
        command, duration = build_render_command(
            asset_dir=ROOT, timeline=scenes, subtitle_path=subtitle,
            output_path=mp4, transition_seconds=0.4,
            transition_mode="technical_cut", audio_path=None, repo_root=ROOT,
            composition=load_composition("knowledge_illustration", repo_root=ROOT),
            signature_path=ROOT / "assets/pink_pig/signature.png", encoder="cpu",
            canvas_width=1920, canvas_height=1080, fps=30,
            subtitle_style={"font_name": "Microsoft YaHei", "font_size": 56,
                            "margin_left": 90, "margin_right": 90, "margin_vertical": 180},
        )
        run(command)
        frames = []
        for frame_no in (14, 15):
            png = OUTPUT / f"{label}_frame_{frame_no:02d}.png"
            run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4),
                 "-vf", f"select=eq(n\\,{frame_no})", "-vsync", "0",
                 "-frames:v", "1", str(png)])
            frames.append({"frame": frame_no, "path": str(png), "sha256": sha(png)})
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=nb_frames,duration", "-of", "json", str(mp4)],
            capture_output=True, text=True, check=True,
        )
        results.append({"boundary": index + 1, "source_scene_orders": [s["order"] for s in scenes],
                        "duration": duration, "mp4": str(mp4), "mp4_sha256": sha(mp4),
                        "video_stream": json.loads(probe.stdout)["streams"][0], "frames": frames})
        print(f"[{index + 1}/4] {label} {results[-1]['video_stream']}", flush=True)
    tail_wav = OUTPUT / "audio_tail_38_4_to_40.wav"
    run(["ffmpeg", "-y", "-v", "error", "-ss", "38.4", "-i", str(SOURCE / "audio.wav"),
         "-t", "1.6", "-c:a", "pcm_s16le", str(tail_wav)])
    tail_srt = OUTPUT / "tail.srt"
    tail_srt.write_text("1\n00:00:00,000 --> 00:00:01,600\n" + str(cues[-1]["text"]) + "\n", encoding="utf-8")
    tail_mp4 = OUTPUT / "tail_mux_probe.mp4"
    tail_scene = {**TIMELINE["scenes"][-1], "duration": 1.6}
    tail_command, tail_duration = build_render_command(
        asset_dir=ROOT, timeline=[tail_scene], subtitle_path=tail_srt,
        output_path=tail_mp4, transition_seconds=0.4, transition_mode="technical_cut",
        audio_path=tail_wav, audio_loop=False, repo_root=ROOT,
        composition=load_composition("knowledge_illustration", repo_root=ROOT),
        signature_path=ROOT / "assets/pink_pig/signature.png", encoder="cpu",
        canvas_width=1920, canvas_height=1080, fps=30,
        subtitle_style={"font_name": "Microsoft YaHei", "font_size": 56,
                        "margin_left": 90, "margin_right": 90, "margin_vertical": 180},
    )
    run(tail_command)
    tail_probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(tail_mp4)],
        capture_output=True, text=True, check=True,
    )
    tail_meta = json.loads(tail_probe.stdout)
    report = {"status": "probes_rendered_visual_review_pending", "source_job": "job-0a58d7692fb3dd4008d3a6ed",
              "source_audio_sha256": sha(SOURCE / "audio.wav"), "source_audio_path": str(SOURCE / "audio.wav"),
              "compiled_duration_seconds": compiled["total_duration_seconds"],
              "planned_frames": int(compiled["total_duration_seconds"] * compiled["fps"]),
              "subtitle_srt": str(full_srt), "subtitle_sha256": sha(full_srt),
              "subtitle_cues": cues,
              "tail_mux": {"duration": tail_duration, "path": str(tail_mp4),
                           "sha256": sha(tail_mp4), "streams": tail_meta["streams"],
                           "format_duration": tail_meta["format"]["duration"],
                           "command_has_shortest": "-shortest" in tail_command},
              "probes": results}
    (OUTPUT / "technical_cut_probe_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
