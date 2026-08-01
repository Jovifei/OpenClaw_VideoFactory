from __future__ import annotations

import tempfile
import unittest
import wave
from pathlib import Path

from src.factory.render import build_render_input, chrome_executable, resolve_duration_seconds


class CandidateRenderTests(unittest.TestCase):
    def test_render_input_uses_only_staged_relative_assets(self) -> None:
        payload = build_render_input(
            job_id="job-0123456789abcdef01234567",
            template="protocol-frame",
            title="Modbus 响应字节计数",
            scenes=[{"heading": "一个字节", "body": "字节计数字段描述后续数据字节数。"}],
            captions=[{"start": 0.0, "end": 10.0, "text": "字节计数不是寄存器数量"}],
            mascot_pose="measure",
            audio_asset="runtime/job-0123456789abcdef01234567/voice.wav",
            requested_duration_seconds=40,
            resolved_duration_seconds=40.0,
            audio_duration_seconds=38.5,
        )

        self.assertEqual(payload["mascot"]["asset"], "mascot/measure.svg")
        self.assertEqual(
            payload["audio"]["asset"], "runtime/job-0123456789abcdef01234567/voice.wav"
        )
        self.assertEqual(payload["schema_version"], "2.0")
        self.assertEqual(payload["resolved_duration_seconds"], 40.0)
        self.assertEqual(payload["scenes"][0]["start_seconds"], 0.0)
        self.assertEqual(payload["scenes"][0]["end_seconds"], 40.0)

    def test_render_input_rejects_external_or_traversal_assets(self) -> None:
        with self.assertRaisesRegex(ValueError, "audio_asset_invalid"):
            build_render_input(
                job_id="job-0123456789abcdef01234567",
                template="protocol-frame",
                title="Modbus 响应字节计数",
                scenes=[{"heading": "一个字节", "body": "字节计数字段描述后续数据字节数。"}],
                captions=[{"start": 0.0, "end": 10.0, "text": "安全输入"}],
                mascot_pose="measure",
                audio_asset="https://example.invalid/voice.wav",
                requested_duration_seconds=40,
                resolved_duration_seconds=40.0,
                audio_duration_seconds=38.5,
            )

    def test_local_chrome_is_required(self) -> None:
        self.assertTrue(chrome_executable().exists())

    def test_duration_is_wav_driven_with_candidate_minimum_and_upper_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "voice.wav"
            with wave.open(str(audio), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(44_100)
                wav.writeframes(b"\x00\x00" * 44_100)
            self.assertEqual(resolve_duration_seconds(audio, 40), 25.0)
        with self.assertRaisesRegex(ValueError, "requested_duration_invalid"):
            build_render_input(
                job_id="job-0123456789abcdef01234567",
                template="protocol-frame",
                title="Modbus 响应字节计数",
                scenes=[{"heading": "一个字节", "body": "字节计数字段描述后续数据字节数。"}],
                captions=[{"start": 0.0, "end": 10.0, "text": "安全输入"}],
                mascot_pose="measure",
                audio_asset="runtime/job-0123456789abcdef01234567/voice.wav",
                requested_duration_seconds=24,
                resolved_duration_seconds=25.0,
                audio_duration_seconds=1.0,
            )
