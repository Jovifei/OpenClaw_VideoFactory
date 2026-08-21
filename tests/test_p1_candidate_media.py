from __future__ import annotations

import importlib
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.factory import mascot
from src.factory.mascot import POSES, create_contact_sheet
from src.factory.metrics import RunMetrics


class CandidateMediaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_historical_media_modules_are_not_importable(self) -> None:
        for module in ("src.factory.tts", "src.factory.captions", "src.factory.quality"):
            with self.subTest(module=module):
                with self.assertRaises(ModuleNotFoundError):
                    importlib.import_module(module)

    def test_media_module_retirement_is_consistent_for_all_three_modules(self) -> None:
        modules = ["src.factory.tts", "src.factory.captions", "src.factory.quality"]
        failures = []
        for module in modules:
            try:
                importlib.import_module(module)
            except ModuleNotFoundError:
                continue
            failures.append(module)
        self.assertEqual(failures, [])

    def test_all_mascot_poses_are_deterministic_and_contact_sheet_is_png(self) -> None:
        self.assertEqual(
            POSES,
            ("normal", "question", "warning", "thinking", "repair", "measure", "success", "ending"),
        )
        target = self.root / "mascot-contact-sheet.png"
        create_contact_sheet(target)
        self.assertTrue(target.exists())
        self.assertGreater(target.stat().st_size, 1000)
        png = target.read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", png[16:24]), (1360, 780))

    def test_contact_sheet_browser_command_uses_isolated_swiftshader_only(self) -> None:
        page = (self.root / "page.html").resolve()
        command = mascot._contact_sheet_chrome_command(
            Path("C:/chrome.exe"), self.root / "profile", self.root / "sheet.png", page
        )
        self.assertIn("--use-gl=angle", command)
        self.assertIn("--use-angle=swiftshader", command)
        self.assertNotIn("--disable-gpu", command)
        self.assertNotIn("--no-sandbox", command)
        self.assertEqual(sum(item.startswith("file:") for item in command), 1)
        self.assertTrue(any(item.startswith("--user-data-dir=") for item in command))

    def test_contact_sheet_failure_is_bounded_and_does_not_expose_local_page(self) -> None:
        target = self.root / "mascot-contact-sheet.png"
        failure = SimpleNamespace(returncode=1, stderr="file:///private/contact-sheet.html", stdout="")
        with patch("src.factory.mascot.subprocess.run", return_value=failure) as runner:
            with self.assertRaisesRegex(RuntimeError, "mascot_contact_sheet_failed:1:local_path_redacted"):
                create_contact_sheet(target)
        self.assertEqual(runner.call_args.kwargs["timeout"], mascot.CONTACT_SHEET_TIMEOUT_SECONDS)

    def test_metrics_drop_text_and_private_path_values(self) -> None:
        target = self.root / "run_metrics.json"
        metrics = RunMetrics("job-0123456789abcdef01234567", target, 1)
        metrics.stage_started("VOICE", 1)
        metrics.stage_completed(
            "VOICE", status="completed", detail={"provider": "edge", "narration": "private text", "path": "C:/private/file"}
        )
        content = target.read_text(encoding="utf-8")
        self.assertIn('"provider": "edge"', content)
        self.assertNotIn("private text", content)
        self.assertNotIn("C:/private/file", content)
