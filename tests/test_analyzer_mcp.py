"""Offline contract tests for the P0-009 Analyzer MCP server."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path


class AnalyzerMcpContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="p0_009_analyzer_")
        cls.root = Path(cls._tmp.name)
        os.environ["OPENCLAW_ANALYZER_TEST_MODE"] = "1"
        os.environ["OPENCLAW_PROJECT_ROOT"] = str(cls.root)
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        import importlib
        import analysis_request  # noqa: PLC0415
        import analyzer_mcp  # noqa: PLC0415

        importlib.reload(analysis_request)
        cls.m = importlib.reload(analyzer_mcp)
        cls.storage = cls.root / "input" / "feishu"
        cls.storage.mkdir(parents=True)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()
        os.environ.pop("OPENCLAW_ANALYZER_TEST_MODE", None)
        os.environ.pop("OPENCLAW_PROJECT_ROOT", None)
        sys.modules.pop("analyzer_mcp", None)
        sys.modules.pop("analysis_request", None)

    def make_case(self, kind: str, index: int = 0, uppercase_hash: bool = False):
        message_id = f"om_analyzer_{kind}_{index}"
        folder = self.storage / message_id / f"attachment-{index:03d}"
        original = folder / "original"
        original.mkdir(parents=True)
        suffix, mime, data = {
            "png": (".png", "image/png", b"\x89PNG\r\n\x1a\nfixture"),
            "audio": (".wav", "audio/wav", b"RIFF\x24\x00\x00\x00WAVEfmt "),
            "mp4": (".mp4", "video/mp4", b"\x00\x00\x00\x18ftypisomfixture"),
            "txt": (".txt", "text/plain", b"# Fixture\nSafe UTF-8 text\n"),
        }[kind]
        stored = original / f"fixture{suffix}"
        stored.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        receipt = folder / "receipt.json"
        receipt_hash = digest.upper() if uppercase_hash else digest
        receipt.write_text(
            json.dumps(
                {
                    "message_id": message_id,
                    "attachment_index": index,
                    "stored_path": str(stored.resolve()),
                    "detected_kind": kind,
                    "normalized_content_type": mime,
                    "sha256": receipt_hash,
                    "source_sha256": receipt_hash,
                    "stored_sha256": receipt_hash,
                    "stored_size_bytes": len(data),
                    "quarantined": True,
                    "content_parsed": False,
                    "analysis_allowed": True,
                    "attachment_action": "ingress_only",
                    "analysis_requested": False,
                    "analysis_requested_at": None,
                    "analysis_completed": False,
                    "analysis_result_path": None,
                    "trusted_root_id": "video_factory_workspace",
                }
            ),
            encoding="utf-8",
        )
        chat_id = "oc_analyzer_group"
        sender_id = "ou_analyzer_owner"
        (folder / "route_binding.json").write_text(
            json.dumps(self.m.route_binding_payload(message_id, index, chat_id, sender_id)),
            encoding="utf-8",
        )
        ticket_hash = hashlib.sha256(f"ticket-{kind}-{index}".encode("utf-8")).hexdigest()
        request_key = f"ticket-{ticket_hash}"
        requested_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        request = {
            "schema_version": "1.0",
            "request_key": request_key,
            "request_message_id": None,
            "target_attachment_message_id": message_id,
            "attachment_index": index,
            "chat_id": chat_id,
            "requester_id": sender_id,
            "action": {
                "png": "analyze_image",
                "audio": "transcribe_audio",
                "mp4": "analyze_video",
                "txt": "analyze_text",
            }[
                kind
            ],
            "action_source": "media_action_ticket",
            "ticket_hash": ticket_hash,
            "ticket_expires_at": "2099-01-01T00:00:00Z",
            "requested_at": requested_at,
            "status": "pending",
            "receipt_path": str(receipt.resolve()),
            "stored_sha256": digest,
            "analysis_policy": self.m.POLICY,
            "completed_at": None,
            "result_path": None,
            "error_code": None,
        }
        request_dir = folder / "analysis_requests"
        request_dir.mkdir()
        (request_dir / f"{request_key}.json").write_text(json.dumps(request), encoding="utf-8")
        (folder / "analysis_request.json").write_text(json.dumps(request), encoding="utf-8")
        args = {
            "job_id": f"job_{kind}_{index}",
            "receipt_path": str(receipt.resolve()),
            "stored_path": str(stored.resolve()),
            "analysis_policy": self.m.POLICY,
        }
        return args, receipt, stored

    def test_tool_surface_is_exactly_four(self):
        self.assertEqual(
            {tool["name"] for tool in self.m.TOOLS},
            {"analyze_image", "transcribe_audio", "analyze_video", "analyze_text"},
        )
        for tool in self.m.TOOLS:
            self.assertFalse(tool["inputSchema"]["additionalProperties"])
            self.assertEqual(set(tool["inputSchema"]["required"]), self.m.ALLOWED_ARGS)

    def test_image_analysis_reads_quarantined_copy(self):
        args, _, _ = self.make_case("png")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["source_sha256"], self.m._sha256(Path(args["stored_path"])))
        self.assertEqual(result["stored_sha256"], result["analyzer_computed_hash"])
        self.assertEqual(result["receipt_expected_hash"], result["stored_sha256"])
        payload = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["model"], "xiaomimimo/mimo-v2.5")
        self.assertNotIn("mimo-v2.5-pro", json.dumps(payload))
        receipt = json.loads(Path(args["receipt_path"]).read_text(encoding="utf-8"))
        self.assertTrue(receipt["analysis_completed"])
        self.assertEqual(receipt["analysis_result_path"], result["output_path"])

    def test_image_analysis_requests_structured_visible_text(self):
        args, _, stored = self.make_case("png", 902)
        original_test_mode = self.m.TEST_MODE
        original_bin = self.m.OPENCLAW_BIN
        original_run = self.m._run_fixed
        calls = []
        self.m.TEST_MODE = False
        self.m.OPENCLAW_BIN = str(Path(__file__).resolve())
        self.m._run_fixed = lambda command, timeout: calls.append((command, timeout)) or self.m.subprocess.CompletedProcess(
            command, 0, '{"summary":"fixture","visible_text":"VIN 12V"}', ""
        )
        try:
            payload = self.m._analyze_image_file(stored)
        finally:
            self.m.TEST_MODE = original_test_mode
            self.m.OPENCLAW_BIN = original_bin
            self.m._run_fixed = original_run
        command, timeout = calls[0]
        self.assertEqual(timeout, 90)
        self.assertEqual(command[command.index("--prompt") + 1], self.m.IMAGE_ANALYSIS_PROMPT)
        self.assertEqual(payload["result"]["visible_text"], "VIN 12V")

    def test_text_analysis_is_utf8_only_and_bounded(self):
        args, _, _ = self.make_case("txt")
        result = self.m.analyze("analyze_text", args)
        self.assertEqual(result["status"], "completed")
        payload = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["encoding"], "utf-8")
        self.assertEqual(payload["headings"], ["Fixture"])
        self.assertLessEqual(len(payload["preview"]), self.m.TEXT_PREVIEW_MAX_CHARS)

    def test_text_analysis_accepts_established_text_plain_receipt_shape(self):
        args, receipt, _ = self.make_case("txt", 904)
        receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
        receipt_data.pop("normalized_content_type")
        receipt_data["content_type"] = "text/plain; charset=utf-8"
        receipt.write_text(json.dumps(receipt_data), encoding="utf-8")
        self.assertEqual(self.m.analyze("analyze_text", args)["status"], "completed")

    def test_text_analysis_rejects_non_text_plain_or_non_utf8(self):
        args, receipt, stored = self.make_case("txt", 25)
        receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
        receipt_data["normalized_content_type"] = "application/pdf"
        receipt_data["content_type"] = "text/plain"
        receipt.write_text(json.dumps(receipt_data), encoding="utf-8")
        self.assertEqual(self.m.analyze("analyze_text", args)["error_code"], "text_plain_required")

        args, receipt, _ = self.make_case("txt", 905)
        receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
        receipt_data.pop("normalized_content_type")
        receipt_data["content_type"] = "application/octet-stream"
        receipt.write_text(json.dumps(receipt_data), encoding="utf-8")
        self.assertEqual(self.m.analyze("analyze_text", args)["error_code"], "text_plain_required")

        args, receipt, stored = self.make_case("txt", 26)
        content = b"\xff"
        digest = hashlib.sha256(content).hexdigest()
        stored.write_bytes(content)
        for path in (receipt, receipt.parent / "analysis_request.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            data["source_sha256"] = digest
            data["stored_sha256"] = digest
            if "stored_size_bytes" in data:
                data["stored_size_bytes"] = len(content)
            if "sha256" in data:
                data["sha256"] = digest
            path.write_text(json.dumps(data), encoding="utf-8")
        request_dir = receipt.parent / "analysis_requests"
        for path in request_dir.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            data["stored_sha256"] = digest
            path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.m.analyze("analyze_text", args)["error_code"], "text_decode_failed")

    def test_video_audio_stream_detection_distinguishes_silent_mp4(self):
        self.assertFalse(self.m._has_audio_stream({"streams": [{"codec_type": "video"}]}))
        self.assertTrue(
            self.m._has_audio_stream(
                {"streams": [{"codec_type": "video"}, {"codec_type": "audio"}]}
            )
        )

    def test_silent_fixture_continues_frame_analysis_without_transcription(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "feishu_delivery" / "p0-video-test.mp4"
        self.assertTrue(fixture.is_file())
        args, receipt, stored = self.make_case("mp4", 903)
        content = fixture.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        stored.write_bytes(content)
        for path in (receipt, receipt.parent / "analysis_request.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            data["source_sha256"] = digest
            data["stored_sha256"] = digest
            if "sha256" in data:
                data["sha256"] = digest
            if "stored_size_bytes" in data:
                data["stored_size_bytes"] = len(content)
            path.write_text(json.dumps(data), encoding="utf-8")
        for path in (receipt.parent / "analysis_requests").glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            data["stored_sha256"] = digest
            path.write_text(json.dumps(data), encoding="utf-8")

        original = {
            "test_mode": self.m.TEST_MODE,
            "image": self.m._analyze_image_file,
            "transcribe": self.m._transcribe_file,
        }
        self.m.JOBS_ROOT.mkdir(parents=True, exist_ok=True)
        self.m.TEST_MODE = False
        self.m._analyze_image_file = lambda _path: {"summary": "offline frame fixture"}
        self.m._transcribe_file = lambda *_args: self.fail("silent video must not transcribe")
        try:
            result = self.m.analyze("analyze_video", args)
        finally:
            self.m.TEST_MODE = original["test_mode"]
            self.m._analyze_image_file = original["image"]
            self.m._transcribe_file = original["transcribe"]
        self.assertEqual(result["status"], "completed")
        payload = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["audio_status"], "no_audio_stream")
        self.assertFalse(payload["audio_extracted"])
        self.assertEqual(payload["transcript"], "")
        self.assertEqual(payload["frames_extracted"], 3)

    def test_uppercase_receipt_hash_is_canonicalized(self):
        args, _, _ = self.make_case("png", 20, uppercase_hash=True)
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["status"], "completed")

    def test_audio_analysis_is_local_cuda_contract(self):
        args, _, _ = self.make_case("audio")
        result = self.m.analyze("transcribe_audio", args)
        self.assertEqual(result["status"], "completed")
        payload = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["engine"], "faster-whisper")
        self.assertEqual(payload["device"], "cuda")

    def test_video_analysis_is_bounded_and_uses_multimodal_model(self):
        args, _, _ = self.make_case("mp4")
        result = self.m.analyze("analyze_video", args)
        self.assertEqual(result["status"], "completed")
        payload = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["frames_extracted"], 3)
        self.assertEqual(payload["model"], "xiaomimimo/mimo-v2.5")
        self.assertEqual(payload["video_duration_cap_seconds"], self.m.MAX_VIDEO_DURATION_SECONDS)
        self.assertEqual(payload["audio_duration_cap_seconds"], self.m.MAX_VIDEO_DURATION_SECONDS)
        self.assertEqual(payload["audio_status"], "transcribed")

    def test_gpu_lease_window_exceeds_work_timeout_and_has_heartbeat(self):
        self.assertGreater(self.m.GPU_LOCK_STALE_AFTER_SECONDS, self.m.GPU_LOCK_TIMEOUT_SECONDS)
        self.assertGreater(self.m.GPU_LOCK_HEARTBEAT_SECONDS, 0)
        with tempfile.TemporaryDirectory(prefix="p0_gpu_lock_") as directory:
            lock = self.m.GpuMediaLock.acquire(
                "gpu-media",
                job_id="job_gpu_contract",
                message_id="om_gpu_contract",
                attachment_index=0,
                timeout_seconds=self.m.GPU_LOCK_TIMEOUT_SECONDS,
                stale_after_seconds=self.m.GPU_LOCK_STALE_AFTER_SECONDS,
                lock_dir=Path(directory),
            )
            try:
                self.assertEqual(
                    lock.record["stale_after_seconds"], self.m.GPU_LOCK_STALE_AFTER_SECONDS
                )
            finally:
                lock.release()

    def test_success_is_idempotent(self):
        args, _, _ = self.make_case("png", 1)
        first = self.m.analyze("analyze_image", args)
        second = self.m.analyze("analyze_image", args)
        self.assertEqual(first["status"], "completed")
        self.assertEqual(second["error_code"], "analysis_already_completed")

    def test_running_request_rejects_concurrent_analyzer(self):
        args, receipt, _ = self.make_case("png", 28)
        request_path = receipt.parent / "analysis_request.json"
        request = json.loads(request_path.read_text(encoding="utf-8"))
        request["status"] = "running"
        request_path.write_text(json.dumps(request), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "analysis_in_progress")

    def test_extra_raw_media_path_and_model_supplied_identity_are_rejected(self):
        args, _, _ = self.make_case("png", 2)
        args["raw_media_path"] = args["stored_path"]
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "invalid_arguments")

    def test_invalid_policy_is_rejected(self):
        args, _, _ = self.make_case("png", 3)
        args["analysis_policy"] = "read_original_inbound"
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "invalid_analysis_policy")

    def test_original_inbound_path_is_not_an_analyzer_input(self):
        args, _, _ = self.make_case("png", 4)
        args["stored_path"] = str(self.root / "media" / "inbound" / "raw.png")
        result = self.m.analyze("analyze_image", args)
        self.assertIn(result["error_code"], {"stored_file_missing", "stored_path_outside_storage"})

    def test_receipt_message_id_is_derived_and_must_be_valid(self):
        args, receipt, _ = self.make_case("png", 5)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["message_id"] = "om_other"
        receipt.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "analysis_request_target_mismatch")

    def test_unquarantined_receipt_is_rejected(self):
        args, receipt, _ = self.make_case("png", 6)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["quarantined"] = False
        receipt.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "receipt_not_quarantined")

    def test_parsed_receipt_is_rejected(self):
        args, receipt, _ = self.make_case("png", 7)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["content_parsed"] = True
        receipt.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "receipt_not_quarantined")

    def test_analysis_not_allowed_receipt_is_rejected(self):
        args, receipt, _ = self.make_case("png", 8)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["analysis_allowed"] = False
        receipt.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "analysis_not_allowed")

    def test_hash_mismatch_is_rejected(self):
        args, receipt, stored = self.make_case("png", 9)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["stored_sha256"] = "0" * 64
        data["source_sha256"] = "0" * 64
        data["sha256"] = "0" * 64
        receipt.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "stored_hash_mismatch")
        self.assertTrue(stored.exists())

    def test_source_stored_hash_mismatch_is_rejected(self):
        args, receipt, _ = self.make_case("png", 21)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["source_sha256"] = "0" * 64
        receipt.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "source_stored_hash_mismatch")

    def test_analysis_requires_explicit_intent(self):
        args, receipt, _ = self.make_case("png", 22)
        (receipt.parent / "analysis_request.json").unlink()
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "analysis_request_required")

    def test_analysis_action_must_match_receipt(self):
        args, receipt, _ = self.make_case("png", 23)
        request_path = receipt.parent / "analysis_request.json"
        data = json.loads(request_path.read_text(encoding="utf-8"))
        data["action"] = "transcribe_audio"
        request_path.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "analysis_request_action_mismatch")

    def test_truncated_hash_is_rejected(self):
        args, receipt, _ = self.make_case("png", 24)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["stored_sha256"] = data["stored_sha256"][:12]
        receipt.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "receipt_hash_invalid")

    def test_missing_stored_hash_is_rejected(self):
        args, receipt, _ = self.make_case("png", 25)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data.pop("stored_sha256")
        receipt.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "receipt_hash_missing")

    def test_hash_prefix_is_rejected(self):
        args, receipt, _ = self.make_case("png", 26)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["stored_sha256"] = "sha256:" + data["stored_sha256"]
        receipt.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "receipt_hash_invalid")

    def test_missing_stored_size_is_rejected(self):
        args, receipt, _ = self.make_case("png", 27)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data.pop("stored_size_bytes")
        receipt.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "receipt_size_invalid")

    def test_wrong_analyzer_kind_is_rejected(self):
        args, _, _ = self.make_case("png", 10)
        result = self.m.analyze("transcribe_audio", args)
        self.assertEqual(result["error_code"], "detected_kind_mismatch")

    def test_unknown_tool_is_rejected(self):
        args, _, _ = self.make_case("png", 11)
        result = self.m.analyze("analyze_anything", args)
        self.assertEqual(result["error_code"], "unknown_tool")

    def test_job_id_traversal_is_rejected(self):
        args, _, _ = self.make_case("png", 12)
        args["job_id"] = "../escape"
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "invalid_job_id")

    def test_message_id_format_is_rejected_from_receipt(self):
        args, _, _ = self.make_case("png", 13)
        receipt = Path(args["receipt_path"])
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["message_id"] = "not_feishu_id"
        receipt.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "invalid_message_id")

    def test_attachment_index_format_is_rejected_from_receipt(self):
        args, _, _ = self.make_case("png", 14)
        receipt = Path(args["receipt_path"])
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["attachment_index"] = -1
        receipt.write_text(json.dumps(data), encoding="utf-8")
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "invalid_attachment_index")

    def test_relative_receipt_path_is_rejected(self):
        args, _, _ = self.make_case("png", 15)
        args["receipt_path"] = "input/feishu/receipt.json"
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "path_not_absolute")

    def test_receipt_outside_storage_is_rejected(self):
        args, _, _ = self.make_case("png", 16)
        outside = self.root / "receipt.json"
        outside.write_text(Path(args["receipt_path"]).read_text(encoding="utf-8"), encoding="utf-8")
        args["receipt_path"] = str(outside)
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "receipt_path_outside_storage")

    def test_stored_path_receipt_binding_is_enforced(self):
        args, receipt, stored = self.make_case("png", 17)
        other = stored.with_name("other.png")
        other.write_bytes(stored.read_bytes())
        args["stored_path"] = str(other)
        result = self.m.analyze("analyze_image", args)
        self.assertEqual(result["error_code"], "stored_path_receipt_mismatch")

    def test_temp_video_artifacts_are_not_left_in_job_root(self):
        args, _, _ = self.make_case("mp4", 18)
        result = self.m.analyze("analyze_video", args)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(any(path.name.startswith("video_") for path in self.m.JOBS_ROOT.iterdir()))

    def test_completed_output_does_not_include_raw_inbound_path(self):
        args, _, _ = self.make_case("png", 19)
        result = self.m.analyze("analyze_image", args)
        output = Path(result["output_path"]).read_text(encoding="utf-8")
        self.assertNotIn("raw_media_path", output)
        self.assertNotIn("media/inbound", output)


if __name__ == "__main__":
    unittest.main()
