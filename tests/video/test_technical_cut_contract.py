"""The local technical path must preserve every narration and visual second."""

import json
from pathlib import Path

from src.factory.phase1_local import build_local_plan
from video_factory.pipeline.composition import load_composition
from video_factory.pipeline.registry import load_pink_pig_registry
from video_factory.pipeline.renderer import build_render_command
from video_factory.pipeline.storyboard import compile_storyboard
from video_factory.pipeline.subtitle import build_srt_from_timeline
from video_factory.pipeline.timeline import rendered_duration_seconds


def _scenes() -> list[dict[str, object]]:
    return [
        {"order": index, "image": f"{index}.png", "duration": 8.0,
         "transition": "fade" if index < 5 else "none", "caption": f"场景 {index}"}
        for index in range(1, 6)
    ]


def test_technical_cut_preserves_all_five_windows_and_legacy_duration() -> None:
    scenes = _scenes()
    assert rendered_duration_seconds(scenes, 0.4, mode="technical_cut") == 40.0
    assert rendered_duration_seconds(scenes, 0.4) == 38.4


def test_technical_cut_subtitles_use_full_scene_boundaries(tmp_path: Path) -> None:
    doc = {"scenes": _scenes(), "transition_seconds": 0.4,
           "transition_mode": "technical_cut"}
    cues = build_srt_from_timeline(doc, tmp_path / "subtitle.srt")
    assert [(cue["start"], cue["end"]) for cue in cues] == [
        (0.0, 8.0), (8.0, 16.0), (16.0, 24.0),
        (24.0, 32.0), (32.0, 40.0),
    ]


def test_technical_cut_renderer_has_no_blended_frames(tmp_path: Path) -> None:
    subtitle = tmp_path / "subtitle.srt"
    subtitle.write_text("1\n00:00:00,000 --> 00:00:40,000\n测试\n", encoding="utf-8")
    command, duration = build_render_command(
        asset_dir=tmp_path, timeline=_scenes(), subtitle_path=subtitle,
        output_path=tmp_path / "out.mp4", transition_seconds=0.4,
        transition_mode="technical_cut", audio_path=None,
    )
    graph = command[command.index("-filter_complex") + 1]
    assert duration == 40.0
    assert "xfade=" not in graph
    assert "concat=n=5:v=1:a=0" in graph
    assert "-frames:v" in command and command[command.index("-frames:v") + 1] == "1200"


def test_phase1_local_freertos_binds_mode_from_brief_to_compiled_cues(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    brief = json.loads((root / "examples/phase1_local_freertos/brief.json").read_text(encoding="utf-8"))
    plan = build_local_plan(brief, repo_root=root)
    assert plan["storyboard"]["globals"]["transition_mode"] == "technical_cut"
    timeline = compile_storyboard(
        plan["storyboard"], load_pink_pig_registry(repo_root=root), repo_root=root,
    )
    assert timeline["transition_mode"] == "technical_cut"
    assert timeline["total_duration_seconds"] == 40.0
    cues = build_srt_from_timeline(
        timeline, tmp_path / "subtitle.srt",
        composition=load_composition("knowledge_illustration", repo_root=root),
    )
    assert [(cue["start"], cue["end"]) for cue in cues] == [
        (0.0, 8.0), (8.0, 16.0), (16.0, 24.0),
        (24.0, 32.0), (32.0, 40.0),
    ]
