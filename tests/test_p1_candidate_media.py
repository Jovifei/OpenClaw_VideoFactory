from __future__ import annotations

import tempfile
import unittest
import wave
import shutil
import math
import struct
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.factory.captions import build_captions, write_srt
from src.factory import mascot
from src.factory.mascot import POSES, create_contact_sheet
from src.factory.metrics import RunMetrics
from src.factory.quality import captions_are_safe
from src.factory.tts import CandidateTts, normalize_wav


def write_silent_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(44100)
        output.writeframes(b"\x00\x00" * 4410)


def write_tone_wav(path: Path) -> None:
    sample_rate = 44_100
    samples = (
        int(8_000 * math.sin(2 * math.pi * 440 * index / sample_rate))
        for index in range(sample_rate)
    )
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(b"".join(struct.pack("<h", sample) for sample in samples))


def copy_normalizer(source: Path, target: Path) -> dict[str, object]:
    shutil.copy2(source, target)
    return {"status": "test_normalized"}


class CandidateMediaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_edge_failure_uses_sapi_fallback_and_records_no_text_value(self) -> None:
        output = self.root / "voice.wav"
        service = CandidateTts(
            cache_root=self.root / "cache",
            edge_runner=lambda _text, _mp3: (_ for _ in ()).throw(RuntimeError("offline")),
            sapi_runner=lambda _text, wav: write_silent_wav(wav),
            normalizer=copy_normalizer,
        )

        result = service.synthesize("Modbus 的字节计数描述后续数据长度。", output, provider="auto")

        self.assertEqual(result["provider"], "sapi")
        self.assertTrue(result["provider_fallback"])
        self.assertEqual(result["fallback_reason"], "unknown_provider_failure")
        self.assertTrue(output.exists())
        self.assertEqual(len(result["text_sha256"]), 64)
        self.assertNotIn(
            "Modbus", str({key: value for key, value in result.items() if key != "provider"})
        )

    def test_caption_times_are_monotonic_and_keep_technical_tokens_whole(self) -> None:
        captions = build_captions(
            "FreeRTOS 互斥锁不能随便在中断里释放。MCU 应把工作交回任务上下文。",
            duration_seconds=10,
        )

        self.assertGreaterEqual(len(captions), 2)
        self.assertEqual(captions[0]["start"], 0.0)
        self.assertLessEqual(captions[-1]["end"], 10.0)
        self.assertTrue(
            all(left["end"] <= right["start"] for left, right in zip(captions, captions[1:]))
        )
        self.assertTrue(all(item["text"].count("\n") <= 1 for item in captions))
        self.assertIn("FreeRTOS", "".join(item["text"] for item in captions))
        self.assertTrue(all(0.6 <= item["end"] - item["start"] <= 4.0 for item in captions))

    def test_two_line_caption_limit_counts_visible_characters(self) -> None:
        caption = {"start": 0.0, "end": 4.0, "text": "123456789012345678\n123456789012345678"}
        self.assertTrue(captions_are_safe([caption]))

    def test_srt_is_well_formed_and_monotonic(self) -> None:
        captions = build_captions("MCU 擦除 Flash 前，需要考虑看门狗节拍。", duration_seconds=10)
        target = self.root / "captions.srt"
        write_srt(captions, target)

        text = target.read_text(encoding="utf-8")
        self.assertIn(" --> ", text)
        self.assertTrue(text.endswith("\n"))

    def test_edge_boundaries_are_captured_without_boundary_text(self) -> None:
        output = self.root / "voice.wav"

        def edge_runner(_text: str, target: Path) -> list[dict[str, object]]:
            write_silent_wav(target)
            return [
                {"start": 0.0, "end": 1.0, "kind": "word"},
                {"start": 1.0, "end": 2.0, "kind": "sentence"},
            ]

        service = CandidateTts(
            cache_root=self.root / "cache",
            edge_runner=edge_runner,
            sapi_runner=lambda _text, wav: write_silent_wav(wav),
            normalizer=copy_normalizer,
        )
        manifest = service.synthesize("Modbus 响应需要按字节计数切分。", output, provider="edge")

        self.assertEqual(manifest["provider"], "edge")
        self.assertFalse(manifest["provider_fallback"])
        self.assertEqual(manifest["boundaries"][0]["kind"], "word")
        self.assertNotIn("Modbus", str(manifest["boundaries"]))
        captions = build_captions("Modbus 响应需要按字节计数切分。", 25, manifest["boundaries"])
        self.assertTrue(all(item["timing_source"] == "edge_boundary" for item in captions))

    def test_tts_cache_reuses_audio_without_second_provider_call(self) -> None:
        calls = {"sapi": 0}

        def sapi_runner(_text: str, target: Path) -> None:
            calls["sapi"] += 1
            write_silent_wav(target)

        service = CandidateTts(
            cache_root=self.root / "cache",
            edge_runner=lambda _text, _target: (_ for _ in ()).throw(RuntimeError("offline")),
            sapi_runner=sapi_runner,
            normalizer=copy_normalizer,
        )
        service.synthesize("MCU 需要记录 Flash 的擦除时间。", self.root / "first.wav")
        cached = service.synthesize("MCU 需要记录 Flash 的擦除时间。", self.root / "second.wav")

        self.assertEqual(calls["sapi"], 1)
        self.assertEqual(cached["provider"], "cache")
        self.assertTrue(cached["cache_hit"])

    def test_local_two_pass_normalization_writes_pcm_wav(self) -> None:
        source = self.root / "source.wav"
        write_tone_wav(source)
        target = self.root / "normalized.wav"
        result = normalize_wav(source, target)

        self.assertTrue(target.exists())
        self.assertEqual(result["status"], "normalized")
        self.assertEqual(result["target_integrated_lufs"], -16.0)

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
            Path("C:/chrome.exe"),
            self.root / "profile",
            self.root / "sheet.png",
            page,
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
            "VOICE",
            status="completed",
            detail={"provider": "edge", "narration": "private text", "path": "C:/private/file"},
        )
        content = target.read_text(encoding="utf-8")
        self.assertIn('"provider": "edge"', content)
        self.assertNotIn("private text", content)
        self.assertNotIn("C:/private/file", content)
