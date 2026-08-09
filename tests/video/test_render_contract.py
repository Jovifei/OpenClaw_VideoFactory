"""T05 / stage-four ④ — FFmpeg render-command contract.

Asserts the command string ``build_render_command`` emits, without executing
ffmpeg. Covers the contract spelt out in the T05 brief:

* N scenes ⇒ exactly ``N - 1`` ``xfade`` transitions
* every scene carries ``scale=1080:1920``
* the ``subtitles=`` filter is present
* ``audio_loop=False`` ⇒ no ``-stream_loop -1`` (TTS-aligned audio)
* ``audio_loop=True``  ⇒ ``-stream_loop -1`` is present
* ``image_path`` present + ``repo_root`` ⇒ image resolved via ``repo_root``
* ``image_path`` absent ⇒ legacy ``asset_dir / image`` behaviour is preserved

Run from the repository root (deviation D5):
    <envs/default python> -m pytest tests/video/test_render_contract.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from video_factory.pipeline.renderer import build_render_command

from . import ROOT

ASSET_PNG = "assets/pink_pig/pig01.png"
REAL_AUDIO = ROOT / "assets" / "pink_pig" / "demo_music.wav"

SCENE_COUNT = 5
TRANSITION_SECONDS = 0.4


def _timeline(with_image_path: bool) -> list[dict]:
    """Build a 5-scene timeline in the renderer's consumed shape."""
    out = []
    for i in range(1, SCENE_COUNT + 1):
        item = {
            "order": i,
            "image": f"pig{i:02d}.png",
            "duration": 2.5,
            "transition": "none" if i == SCENE_COUNT else "fade",
        }
        if with_image_path:
            item["image_path"] = f"assets/pink_pig/pig{i:02d}.png"
        out.append(item)
    return out


@pytest.fixture
def subtitle(tmp_path: Path) -> Path:
    path = tmp_path / "subtitle.srt"
    path.write_text("1\n00:00:00,000 --> 00:00:02,000\n你好\n", encoding="utf-8")
    return path


@pytest.fixture
def output(tmp_path: Path) -> Path:
    return tmp_path / "out.mp4"


# ---------------------------------------------------------------------------
# Structure of the command
# ---------------------------------------------------------------------------


class TestRenderCommandStructure:
    def test_n_minus_1_xfade_transitions(self, subtitle, output) -> None:
        command, _ = build_render_command(
            asset_dir=ROOT,
            timeline=_timeline(with_image_path=True),
            subtitle_path=subtitle,
            output_path=output,
            transition_seconds=TRANSITION_SECONDS,
            audio_path=None,
        )
        filter_graph = command[command.index("-filter_complex") + 1]
        assert filter_graph.count("xfade=") == SCENE_COUNT - 1

    def test_every_scene_is_scaled_to_1080x1920(self, subtitle, output) -> None:
        command, _ = build_render_command(
            asset_dir=ROOT,
            timeline=_timeline(with_image_path=True),
            subtitle_path=subtitle,
            output_path=output,
            transition_seconds=TRANSITION_SECONDS,
            audio_path=None,
        )
        filter_graph = command[command.index("-filter_complex") + 1]
        assert filter_graph.count("scale=1080:1920") == SCENE_COUNT

    def test_subtitles_filter_is_present(self, subtitle, output) -> None:
        command, _ = build_render_command(
            asset_dir=ROOT,
            timeline=_timeline(with_image_path=True),
            subtitle_path=subtitle,
            output_path=output,
            transition_seconds=TRANSITION_SECONDS,
            audio_path=None,
        )
        assert any("subtitles=" in token for token in command)

    def test_reported_duration_matches_the_timeline_formula(self, subtitle, output) -> None:
        from video_factory.pipeline.timeline import rendered_duration_seconds

        timeline = _timeline(with_image_path=True)
        _, duration = build_render_command(
            asset_dir=ROOT,
            timeline=timeline,
            subtitle_path=subtitle,
            output_path=output,
            transition_seconds=TRANSITION_SECONDS,
            audio_path=None,
        )
        assert duration == rendered_duration_seconds(timeline, TRANSITION_SECONDS)

    def test_missing_subtitle_raises(self, output) -> None:
        with pytest.raises(ValueError, match="subtitle_missing"):
            build_render_command(
                asset_dir=ROOT,
                timeline=_timeline(with_image_path=True),
                subtitle_path=output,  # not an existing file
                output_path=output,
                transition_seconds=TRANSITION_SECONDS,
                audio_path=None,
            )


# ---------------------------------------------------------------------------
# Audio loop contract (TTS-aligned vs. looping BGM)
# ---------------------------------------------------------------------------


class TestAudioLoopContract:
    def test_audio_loop_true_adds_stream_loop(self, subtitle, output) -> None:
        command, _ = build_render_command(
            asset_dir=ROOT,
            timeline=_timeline(with_image_path=True),
            subtitle_path=subtitle,
            output_path=output,
            transition_seconds=TRANSITION_SECONDS,
            audio_path=REAL_AUDIO,
            audio_loop=True,
        )
        assert "-stream_loop" in command
        assert "-1" in command

    def test_audio_loop_false_omits_stream_loop(self, subtitle, output) -> None:
        command, _ = build_render_command(
            asset_dir=ROOT,
            timeline=_timeline(with_image_path=True),
            subtitle_path=subtitle,
            output_path=output,
            transition_seconds=TRANSITION_SECONDS,
            audio_path=REAL_AUDIO,
            audio_loop=False,
        )
        assert "-stream_loop" not in command
        # The audio is still mapped (not silent) when a real file is supplied.
        assert "-an" not in command

    def test_audio_path_none_emits_an(self, subtitle, output) -> None:
        command, _ = build_render_command(
            asset_dir=ROOT,
            timeline=_timeline(with_image_path=True),
            subtitle_path=subtitle,
            output_path=output,
            transition_seconds=TRANSITION_SECONDS,
            audio_path=None,
        )
        assert "-an" in command

    def test_audio_loop_false_maps_the_audio_stream(self, subtitle, output) -> None:
        command, _ = build_render_command(
            asset_dir=ROOT,
            timeline=_timeline(with_image_path=True),
            subtitle_path=subtitle,
            output_path=output,
            transition_seconds=TRANSITION_SECONDS,
            audio_path=REAL_AUDIO,
            audio_loop=False,
        )
        # The audio input (index == SCENE_COUNT) is mapped, not silenced.
        assert f"{SCENE_COUNT}:a:0" in command


# ---------------------------------------------------------------------------
# Image input resolution: image_path vs. legacy asset_dir
# ---------------------------------------------------------------------------


class TestImageInputResolution:
    def test_image_path_branch_resolves_via_repo_root(self, subtitle, output) -> None:
        command, _ = build_render_command(
            asset_dir=ROOT / "ignored_assets",
            timeline=_timeline(with_image_path=True),
            subtitle_path=subtitle,
            output_path=output,
            transition_seconds=TRANSITION_SECONDS,
            audio_path=None,
            repo_root=ROOT,
        )
        # First video input must be the repo-root-resolved image_path, not asset_dir.
        i = command.index("-i")
        first_input = command[i + 1]
        # Resolve uses the real fs separator; compare via posix-normalised path.
        assert Path(first_input).as_posix().endswith(ASSET_PNG)
        assert "ignored_assets" not in first_input

    def test_legacy_branch_uses_asset_dir_when_no_image_path(
        self, subtitle, output, tmp_path
    ) -> None:
        fake_assets = tmp_path / "fake_assets"
        fake_assets.mkdir()
        command, _ = build_render_command(
            asset_dir=fake_assets,
            timeline=_timeline(with_image_path=False),
            subtitle_path=subtitle,
            output_path=output,
            transition_seconds=TRANSITION_SECONDS,
            audio_path=None,
        )
        i = command.index("-i")
        first_input = command[i + 1]
        assert str(fake_assets / "pig01.png") == first_input

    def test_image_path_branch_falls_back_to_asset_dir_when_repo_root_absent(
        self, subtitle, output, tmp_path
    ) -> None:
        """When ``repo_root`` is None the branch is disabled → legacy behaviour."""
        fake_assets = tmp_path / "fake_assets"
        fake_assets.mkdir()
        command, _ = build_render_command(
            asset_dir=fake_assets,
            timeline=_timeline(with_image_path=True),
            subtitle_path=subtitle,
            output_path=output,
            transition_seconds=TRANSITION_SECONDS,
            audio_path=None,
            repo_root=None,
        )
        i = command.index("-i")
        assert command[i + 1] == str(fake_assets / "pig01.png")
