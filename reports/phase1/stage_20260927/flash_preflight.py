"""Bounded Flash asset, subtitle, audio and transition checks; no full video job."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image

from generate_video import _local_brief_subtitle_style
from src.factory.phase1_local import build_local_plan, load_local_brief
from video_factory.pipeline.audio_planner import plan_audio
from video_factory.pipeline.registry import load_pink_pig_registry
from video_factory.pipeline.renderer import build_render_command
from video_factory.pipeline.storyboard import compile_storyboard
from video_factory.pipeline.subtitle import build_srt_from_timeline


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_flash_preflight_20260927")
BRIEF = ROOT / "examples/phase1_local_flash_watchdog/brief.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, timeout: int = 90) -> str:
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"command failed: {command[0]}: {result.stderr[-1000:]}")
    return result.stdout


def short_render(
    label: str, scenes: list[dict[str, object]], cue_texts: list[str],
    style: dict[str, object], profile: dict[str, object], frame_numbers: tuple[int, ...],
) -> dict[str, object]:
    subtitle = OUTPUT / f"{label}.srt"
    interval = 1.0 / len(scenes)
    def stamp(value: float) -> str:
        milliseconds = round(value * 1000)
        seconds, milliseconds = divmod(milliseconds, 1000)
        return f"00:00:{seconds:02d},{milliseconds:03d}"
    subtitle.write_text(
        "\n".join(
            f"{index + 1}\n{stamp(index * interval)} --> "
            f"{stamp((index + 1) * interval)}\n{text}\n"
            for index, text in enumerate(cue_texts)
        ), encoding="utf-8",
    )
    short_scenes = [{**scene, "duration": interval} for scene in scenes]
    mp4 = OUTPUT / f"{label}.mp4"
    command, duration = build_render_command(
        asset_dir=ROOT, timeline=short_scenes, subtitle_path=subtitle,
        output_path=mp4, transition_seconds=0.4, transition_mode="technical_cut",
        audio_path=None, repo_root=ROOT, subtitle_style=style, encoder="cpu",
        canvas_width=int(profile["width"]), canvas_height=int(profile["height"]),
        fps=int(profile["fps"]), pad_color=str(profile["pad_color"]),
    )
    run(command)
    frames = []
    for number in frame_numbers:
        png = OUTPUT / f"{label}_frame_{number:02d}.png"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4),
             "-vf", f"select=eq(n\\,{number})", "-vsync", "0", "-frames:v", "1", str(png)])
        frames.append({"number": number, "path": str(png), "sha256": sha(png)})
    metadata = json.loads(run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=duration,nb_frames", "-of", "json", str(mp4),
    ]))["streams"][0]
    return {"label": label, "duration_seconds": duration, "mp4_sha256": sha(mp4),
            "video_stream": metadata, "frames": frames}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    brief = load_local_brief(BRIEF)
    plan = build_local_plan(brief, repo_root=ROOT)
    registry = load_pink_pig_registry(repo_root=ROOT)
    timeline = compile_storyboard(plan["storyboard"], registry, repo_root=ROOT)
    profile = plan["render_profile"]
    assert timeline["transition_mode"] == "technical_cut"
    assert timeline["total_duration_seconds"] == 37.8
    assert (profile["width"], profile["height"], profile["fps"]) == (1920, 1080, 30)
    style = _local_brief_subtitle_style(1920, 1080)
    srt = OUTPUT / "subtitle_37_8.srt"
    cues = build_srt_from_timeline(timeline, srt)
    assert cues[-1]["end"] == 37.8

    assets = []
    for index, selection in enumerate(plan["asset_selection"]["selections"], start=1):
        asset = registry.get(selection["asset_id"])
        assert asset is not None and asset.path is not None
        path = ROOT / asset.path
        with Image.open(path) as image:
            image.load()
            dimensions = list(image.size)
        assert dimensions == [asset.width, asset.height]
        digest = sha(path)
        assert digest == asset.sha256 == selection["sha256"]
        run(["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1", "-f", "null", "NUL"], timeout=20)
        svg = ROOT / asset.source_svg if asset.source_svg else None
        assets.append({"asset_id": asset.asset_id, "path": asset.path, "sha256": digest,
                       "dimensions": dimensions, "source_svg": asset.source_svg,
                       "source_svg_sha256": sha(svg) if svg and svg.is_file() else None})
        print(f"[{index}/5] asset decoded {asset.asset_id}", flush=True)

    audio_config = {"strategy": "tts_with_offline_fallback", "allow_network": False,
                    "require_narration": True,
                    "tts": {"provider": "windows-sapi", "voice": "Microsoft Huihui Desktop"},
                    "fallback_bgm": "assets/pink_pig/demo_music.wav"}
    audio = plan_audio(timeline, work_dir=OUTPUT / "audio", audio_config=audio_config, repo_root=ROOT)
    assert audio.mode == "tts" and audio.path is not None and len(audio.segments) == 5
    audio_metadata = json.loads(run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(audio.path),
    ]))
    audio_duration = float(audio_metadata["format"]["duration"])
    assert abs(audio_duration - 37.8) < 0.01, audio_duration

    command, full_duration = build_render_command(
        asset_dir=ROOT, timeline=timeline["scenes"], subtitle_path=srt,
        output_path=OUTPUT / "NOT_RENDERED_full.mp4", transition_seconds=0.4,
        transition_mode="technical_cut", audio_path=audio.path, audio_loop=False,
        repo_root=ROOT, subtitle_style=style, encoder="cpu", canvas_width=1920,
        canvas_height=1080, fps=30, pad_color=str(profile["pad_color"]),
    )
    graph = command[command.index("-filter_complex") + 1]
    assert "xfade=" not in graph and "concat=n=5:v=1:a=0" in graph
    assert "-shortest" not in command
    assert command[command.index("-frames:v") + 1] == "1134"
    assert full_duration == 37.8

    stills = []
    for index, scene in enumerate(timeline["scenes"], start=1):
        stills.append(short_render(f"scene_{index}", [scene], [str(cues[index - 1]["text"])],
                                   style, profile, (15,)))
        print(f"[{index}/5] production-style still rendered", flush=True)
    cuts = []
    boundaries = []
    total = 0.0
    for index in range(4):
        total += float(timeline["scenes"][index]["duration"])
        boundaries.append({"seconds": round(total, 3), "frame": round(total * 30)})
        cuts.append(short_render(
            f"cut_{index + 1}", timeline["scenes"][index:index + 2],
            [str(cues[index]["text"]), str(cues[index + 1]["text"])],
            style, profile, (14, 15),
        ))
        print(f"[{index + 1}/4] cut probe rendered", flush=True)

    report = {
        "status": "probes_rendered_visual_review_pending",
        "source_commit": "84e5665acbbbef74071cf0444b9f69c6b838d2b8",
        "brief_sha256": sha(BRIEF), "registry_version": timeline["registry_version"],
        "profile": profile, "transition_mode": timeline["transition_mode"],
        "planned_duration_seconds": full_duration, "planned_frames": 1134,
        "boundaries": boundaries, "assets": assets,
        "srt_sha256": sha(srt), "srt_cues": cues,
        "audio_mode": audio.mode, "audio_sha256": sha(audio.path),
        "audio_duration_seconds": audio_duration,
        "full_command_topology": "technical_cut concat, no xfade, no -shortest; full command not executed",
        "stills": stills, "cuts": cuts,
    }
    (OUTPUT / "flash_preflight_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
