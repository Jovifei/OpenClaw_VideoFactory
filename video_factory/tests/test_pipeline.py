from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import generate_video
from video_factory.pipeline.asset_loader import AssetLoadError, build_asset_manifest
from video_factory.pipeline.renderer import build_render_command
from video_factory.pipeline.subtitle import build_srt
from video_factory.pipeline.timeline import build_timeline, rendered_duration_seconds


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets" / "pink_pig"


class PinkPigPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = build_asset_manifest(ASSETS)
        self.timeline = build_timeline(
            self.manifest, duration_seconds=1.5, transitions=["fade", "zoom", "slide"]
        )

    def test_asset_manifest_discovers_natural_order_and_dimensions(self) -> None:
        self.assertEqual(["pig01.png", "pig02.png", "pig03.png", "pig04.png", "pig05.png"], [item["path"] for item in self.manifest["assets"]])
        self.assertTrue(all(item["width"] == 1080 and item["height"] == 1920 for item in self.manifest["assets"]))

    def test_timeline_has_expected_duration_and_transitions(self) -> None:
        self.assertEqual(["fade", "zoom", "slide", "fade", "none"], [item["transition"] for item in self.timeline])
        self.assertEqual(5.9, rendered_duration_seconds(self.timeline, 0.4))

    def test_subtitle_and_renderer_command_have_required_stages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            script = temp / "script.txt"
            subtitle = temp / "subtitle.srt"
            script.write_text("第一句\n第二句\n", encoding="utf-8")
            captions = build_srt(script, self.timeline, subtitle, transition_seconds=0.4)
            command, duration = build_render_command(
                asset_dir=ASSETS,
                timeline=self.timeline,
                subtitle_path=subtitle,
                output_path=temp / "demo.mp4",
                transition_seconds=0.4,
                audio_path=ASSETS / "demo_music.wav",
            )
        self.assertEqual(5, len(captions))
        self.assertEqual(5.9, captions[-1]["end"])
        self.assertEqual(5.9, duration)
        filter_graph = command[command.index("-filter_complex") + 1]
        self.assertIn("transition=fade", filter_graph)
        self.assertIn("transition=zoomin", filter_graph)
        self.assertIn("transition=slideleft", filter_graph)
        self.assertIn("subtitles=", filter_graph)

    def test_empty_directory_and_invalid_image_fail_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            empty = Path(directory) / "empty"
            empty.mkdir()
            with self.assertRaisesRegex(AssetLoadError, "asset_directory_empty"):
                build_asset_manifest(empty)
            invalid = empty / "bad.png"
            invalid.write_text("not an image", encoding="utf-8")
            with self.assertRaisesRegex(AssetLoadError, "invalid_image:bad.png"):
                build_asset_manifest(empty)

    def test_missing_config_fails_cleanly(self) -> None:
        with self.assertRaisesRegex(ValueError, "config_missing"):
            generate_video.load_config(ROOT / "examples" / "pink_pig_demo" / "missing.yaml")


if __name__ == "__main__":
    unittest.main()
