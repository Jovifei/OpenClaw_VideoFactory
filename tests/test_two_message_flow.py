"""Deferred historical Reply flow checks; Reply cannot reach the active Analyzer."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path


class TwoMessageFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="p0_two_message_flow_")
        cls.root = Path(cls.tmp.name)
        os.environ["OPENCLAW_PROJECT_ROOT"] = str(cls.root)
        os.environ["OPENCLAW_ANALYZER_TEST_MODE"] = "1"
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        import analysis_request  # noqa: PLC0415
        import analyzer_mcp  # noqa: PLC0415

        cls.requests = analysis_request
        cls.analyzer = analyzer_mcp
        cls.requests.STORAGE_ROOT = (cls.root / "input" / "feishu").resolve()
        cls.analyzer.STORAGE_ROOT = cls.requests.STORAGE_ROOT
        cls.analyzer.JOBS_ROOT = (cls.root / "jobs").resolve()

    @classmethod
    def tearDownClass(cls):
        os.environ.pop("OPENCLAW_PROJECT_ROOT", None)
        os.environ.pop("OPENCLAW_ANALYZER_TEST_MODE", None)
        sys.modules.pop("analyzer_mcp", None)
        sys.modules.pop("analysis_request", None)
        cls.tmp.cleanup()

    def make_attachment(self):
        self.__class__._counter = getattr(self.__class__, "_counter", 0) + 1
        target = f"om_flow_attachment_013_{self._counter}"
        chat = "oc_flow_group_013"
        sender = "ou_flow_owner_013"
        folder = self.requests.STORAGE_ROOT / target / "attachment-000"
        original = folder / "original"
        original.mkdir(parents=True)
        stored = original / "p0-image-test.png"
        stored.write_bytes(b"\x89PNG\r\n\x1a\nflow-013")
        digest = hashlib.sha256(stored.read_bytes()).hexdigest()
        receipt = folder / "receipt.json"
        receipt.write_text(
            json.dumps(
                {
                    "message_id": target,
                    "attachment_index": 0,
                    "stored_path": str(stored.resolve()),
                    "detected_kind": "png",
                    "source_sha256": digest,
                    "stored_sha256": digest,
                    "stored_size_bytes": stored.stat().st_size,
                    "quarantined": True,
                    "content_parsed": False,
                    "analysis_allowed": True,
                    "analysis_requested": False,
                    "attachment_action": "ingress_only",
                    "received_at": "2026-07-20T14:00:00Z",
                    "analysis_completed": False,
                    "analysis_result_path": None,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (folder / "route_binding.json").write_text(
            json.dumps(self.requests.route_binding_payload(target, 0, chat, sender)),
            encoding="utf-8",
        )
        (self.requests.STORAGE_ROOT / target / "message_manifest.json").write_text(
            json.dumps(
                {
                    "message_id": target,
                    "attachments": [
                        {"attachment_index": 0, "receipt_path": str(receipt.resolve())}
                    ],
                }
            ),
            encoding="utf-8",
        )
        return target, chat, sender, receipt, stored, digest

    def test_reply_created_request_is_rejected_by_ticket_only_analyzer(self):
        target, chat, sender, receipt, stored, digest = self.make_attachment()
        request_message = "om_flow_request_013"
        request = self.requests.create_analysis_request(
            {
                "request_message_id": request_message,
                "target_attachment_message_id": target,
                "reply_to_message_id": target,
                "attachment_index": 0,
                "chat_id": chat,
                "requester_id": sender,
                "request_text": "请在安全入库后分析这张图片。",
            }
        )
        self.assertEqual(request["status"], "pending")
        calls = []
        original_runner = self.analyzer._analyze_image_file
        self.analyzer._analyze_image_file = lambda path: (
            calls.append(str(path)) or {"summary": "offline"}
        )
        try:
            result = self.analyzer.analyze(
                "analyze_image",
                {
                    "job_id": "job_flow_013",
                    "receipt_path": str(receipt.resolve()),
                    "stored_path": str(stored.resolve()),
                    "analysis_policy": self.analyzer.POLICY,
                },
            )
        finally:
            self.analyzer._analyze_image_file = original_runner
        self.assertEqual(result["error_code"], "analysis_request_source_invalid")
        self.assertEqual(calls, [])

    def test_standalone_text_and_missing_request_never_reach_analyzer(self):
        target, _, _, receipt, stored, _ = self.make_attachment()
        self.assertFalse((receipt.parent / "analysis_request.json").exists())
        result = self.analyzer.analyze(
            "analyze_image",
            {
                "job_id": "job_flow_no_request",
                "receipt_path": str(receipt.resolve()),
                "stored_path": str(stored.resolve()),
                "analysis_policy": self.analyzer.POLICY,
            },
        )
        self.assertEqual(result["error_code"], "analysis_request_required")


if __name__ == "__main__":
    unittest.main()
