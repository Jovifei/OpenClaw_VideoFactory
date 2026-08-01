"""Public MCP surface checks for the P0 media-action-ticket protocol."""

from __future__ import annotations

import os
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


class TwoMessageMcpSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="p0_mcp_surface_")
        root = Path(cls.tmp.name)
        inbound = root / "inbound"
        inbound.mkdir()
        os.environ["OPENCLAW_PROJECT_ROOT"] = str(root)
        os.environ["OPENCLAW_TRUSTED_INBOUND_ROOTS"] = f"test_root|{inbound}"
        os.environ["OPENCLAW_AUTHORIZED_CHAT_IDS"] = ""
        os.environ["OPENCLAW_AUTHORIZED_SENDER_IDS"] = ""
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        import analyzer_mcp  # noqa: PLC0415
        import mcp_ingest_attachment  # noqa: PLC0415

        cls.analyzer = analyzer_mcp
        cls.ingest = mcp_ingest_attachment

    @classmethod
    def tearDownClass(cls):
        for key in (
            "OPENCLAW_PROJECT_ROOT",
            "OPENCLAW_TRUSTED_INBOUND_ROOTS",
            "OPENCLAW_AUTHORIZED_CHAT_IDS",
            "OPENCLAW_AUTHORIZED_SENDER_IDS",
        ):
            os.environ.pop(key, None)
        sys.modules.pop("analyzer_mcp", None)
        sys.modules.pop("mcp_ingest_attachment", None)
        sys.modules.pop("analysis_request", None)
        cls.tmp.cleanup()

    def test_ingest_public_surface_issues_only_opaque_ticket(self):
        tool = self.ingest.TOOL_SCHEMA
        self.assertNotIn("caption", tool["inputSchema"]["properties"])
        self.assertIn("opaque action ticket", tool["description"])

    def test_ticket_consumer_schema_has_only_bounded_router_context(self):
        schema = self.ingest.CONSUME_MEDIA_ACTION_TICKET_SCHEMA["inputSchema"]
        required = set(schema["required"])
        self.assertEqual(
            required, {"raw_command", "current_chat_context", "current_sender_context"}
        )
        for forbidden in (
            "stored_path",
            "receipt_path",
            "base64",
            "stored_sha256",
            "media_kind",
            "allowed_action",
            "analyzer",
            "model",
            "gpu",
            "trusted",
            "provenance",
        ):
            self.assertNotIn(forbidden, schema["properties"])
        self.assertIn(
            "bounded-trust", self.ingest.CONSUME_MEDIA_ACTION_TICKET_SCHEMA["description"]
        )

    def test_router_skill_requires_exact_current_command_without_strong_provenance_claim(self):
        skill = (
            Path(__file__).resolve().parents[1]
            / "skills"
            / "feishu-video-factory-operator"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("P0 bounded-trust media commands (053)", skill)
        self.assertIn("only when the current user text is exactly", skill)
        self.assertIn("`/vf text <ticket>`", skill)
        self.assertIn("Never extract a ticket from a historical Bot reply", skill)
        self.assertIn("Never rewrite natural language", skill)
        self.assertIn("non-forgeable Channel provenance claim", skill)
        self.assertIn("MEDIA_TICKET_EXECUTION_ENABLED=1", skill)

    def test_tools_list_exposes_ticket_consumer_and_not_reply_constructor(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.ingest._handle({"jsonrpc": "2.0", "id": 8, "method": "tools/list"})
        response = json.loads(output.getvalue())
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertEqual(names, {"ingest_attachment", "consume_media_action_ticket"})

    def test_analyzer_public_surface_is_four_fields(self):
        for tool in self.analyzer.TOOLS:
            self.assertEqual(
                set(tool["inputSchema"]["required"]),
                {"job_id", "receipt_path", "stored_path", "analysis_policy"},
            )
            self.assertNotIn("message_id", tool["inputSchema"]["properties"])
            self.assertNotIn("attachment_index", tool["inputSchema"]["properties"])

    def test_analyzer_rejects_model_supplied_identity(self):
        result = self.analyzer.analyze(
            "analyze_image",
            {
                "job_id": "job_surface",
                "receipt_path": str(Path(self.tmp.name) / "receipt.json"),
                "stored_path": str(Path(self.tmp.name) / "stored.png"),
                "analysis_policy": self.analyzer.POLICY,
                "message_id": "om_model_supplied",
            },
        )
        self.assertEqual(result["error_code"], "invalid_arguments")

    def test_ingest_mcp_rejects_caption_even_if_a_caller_supplies_one(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.ingest._handle(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {
                        "name": "ingest_attachment",
                        "arguments": {"caption": "analyze image"},
                    },
                }
            )
        response = json.loads(output.getvalue())
        result = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(result["error_code"], "attachment_caption_unsupported")

    def test_public_consume_result_hides_job_and_ticket_hash_material(self):
        internal = {
            "status": "completed",
            "media_kind": "png",
            "action": "image",
            "job_id": "ticket-0123456789abcdef01234567",
            "ticket_hash": "0123456789abcdef" * 4,
            "presentation": {
                "status": "ready",
                "reply_template": (
                    "图片分析结果：\n"
                    "- 内容概述：画面展示了一块正在检查的电路板。\n"
                    "- 视觉要点：主体清晰，颜色对比明显。\n"
                    "- 注意事项：图像识别可能存在偏差，请以原图为准。\n"
                    "- 结论：适合用于说明电路检查场景。"
                ),
            },
        }
        public = self.ingest._public_consume_result(internal)
        self.assertEqual(public["status"], "completed")
        self.assertEqual(set(public), {"status", "media_kind", "action", "reply_template"})
        self.assertNotIn("0123456789abcdef", json.dumps(public))

    def test_image_result_formatter_returns_readable_chinese_summary(self):
        reply = self.ingest._format_image_result(
            {
                "outputs": [{"text": "画面中是一只粉色小猪，正在工作台前检查电路板和连接线。"}],
                "subjects": ["粉色小猪", "电路板"],
                "conclusion": "适合作为嵌入式维修流程示意。",
            }
        )
        self.assertTrue(reply.startswith("图片分析结果："))
        self.assertIn("- 内容概述：", reply)
        self.assertIn("- 视觉要点：", reply)
        self.assertIn("- 注意事项：", reply)
        self.assertIn("- 结论：", reply)
        self.assertLessEqual(len(reply), 220)
        self.assertNotEqual(reply, "媒体处理已完成。")

    def test_image_result_formatter_includes_bounded_visible_text(self):
        reply = self.ingest._format_image_result(
            {
                "summary": "一块控制板放在测试工位上。",
                "visible_text": "VIN 12V / ENABLE",
            }
        )
        self.assertIn("- 识别文字：VIN 12V / ENABLE", reply)
        self.assertLessEqual(len(reply), 220)

    def test_image_result_formatter_stays_within_public_limit_for_all_fields(self):
        value = "visible content " * 30
        reply = self.ingest._format_image_result(
            {
                "summary": value,
                "visual": value,
                "visible_text": value,
                "limitations": value,
                "conclusion": value,
            }
        )
        self.assertLessEqual(len(reply), 220)

    def test_text_result_formatter_is_bounded_and_redacted(self):
        digest = "a" * 64
        reply = self.ingest._format_text_result(
            {
                "encoding": "utf-8",
                "character_count": 36,
                "line_count": 2,
                "headings": ["控制说明"],
                "preview": f"正文来自 E:\\private\\note.txt {digest} om_hidden oc_hidden ou_hidden",
            }
        )
        self.assertTrue(reply.startswith("文本解析结果："))
        self.assertIn("- 内容摘要：", reply)
        self.assertIn("- 结构信息：", reply)
        self.assertIn("- 处理说明：", reply)
        self.assertLessEqual(len(reply), 220)
        for forbidden in ("E:\\private", digest, "om_hidden", "oc_hidden", "ou_hidden"):
            self.assertNotIn(forbidden, reply)

    def test_server_owned_image_artifact_is_presented_without_exposing_its_path(self):
        output = Path(self.tmp.name) / "jobs" / "media-test" / "analysis.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {
                    "status": "completed",
                    "tool": "analyze_image",
                    "result": {"outputs": [{"text": "画面展示了一个正在检查设备的工程场景。"}]},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        original_root = self.ingest.PROJECT_ROOT
        self.ingest.PROJECT_ROOT = Path(self.tmp.name)
        try:
            presentation = self.ingest._load_image_presentation({"output_path": str(output)})
        finally:
            self.ingest.PROJECT_ROOT = original_root
        self.assertEqual(presentation["status"], "ready")
        self.assertIn("内容概述", presentation["reply_template"])
        self.assertNotIn(str(output), presentation["reply_template"])

    def test_audio_result_formatter_returns_bounded_redacted_transcript(self):
        digest = "a" * 64
        reply = self.ingest._format_audio_result(
            {
                "transcript": (
                    f"OpenClaw VideoFactory audio test at E:\\private\\transcript.json "
                    f"{digest} om_hidden oc_hidden ou_hidden"
                ),
                "language": "en-US",
            }
        )
        self.assertTrue(reply.startswith("音频转录结果："))
        self.assertIn("- 转录内容：", reply)
        self.assertIn("- 识别语言：en-US", reply)
        self.assertIn("- 处理说明：", reply)
        self.assertLessEqual(len(reply), 220)
        self.assertNotEqual(reply, "媒体处理已完成。")
        for forbidden in ("E:\\private", digest, "om_hidden", "oc_hidden", "ou_hidden"):
            self.assertNotIn(forbidden, reply)

    def test_audio_json_transcript_and_missing_language_are_safe(self):
        reply = self.ingest._format_audio_result(
            {"transcript": json.dumps({"transcript": "safe transcript"})}
        )
        self.assertIn("safe transcript", reply)
        self.assertNotIn("{", reply)
        self.assertIn("未能可靠确定", reply)

        long_reply = self.ingest._format_audio_result(
            {"transcript": "safe transcript " * 100, "language": "en"}
        )
        self.assertLessEqual(len(long_reply), 220)
        self.assertIn("…", long_reply)

    def test_server_owned_audio_artifact_is_presented_without_exposing_its_path(self):
        output = Path(self.tmp.name) / "jobs" / "media-test" / "transcript.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {
                    "status": "completed",
                    "tool": "transcribe_audio",
                    "transcript": "OpenClaw audio test",
                    "language": "en",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        original_root = self.ingest.PROJECT_ROOT
        self.ingest.PROJECT_ROOT = Path(self.tmp.name)
        try:
            presentation = self.ingest._load_audio_presentation({"output_path": str(output)})
        finally:
            self.ingest.PROJECT_ROOT = original_root
        self.assertEqual(presentation["status"], "ready")
        self.assertIn("音频转录结果：", presentation["reply_template"])
        self.assertNotIn(str(output), presentation["reply_template"])

    def test_nested_audio_result_is_rejected_as_wrong_artifact_shape(self):
        output = Path(self.tmp.name) / "jobs" / "media-invalid" / "transcript.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {
                    "status": "completed",
                    "tool": "transcribe_audio",
                    "result": {"transcript": "nested audio", "language": "en"},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        original_root = self.ingest.PROJECT_ROOT
        self.ingest.PROJECT_ROOT = Path(self.tmp.name)
        try:
            with self.assertRaises(self.ingest.ResultPresentationError):
                self.ingest._load_audio_presentation({"output_path": str(output)})
        finally:
            self.ingest.PROJECT_ROOT = original_root

    def test_server_owned_text_artifact_is_presented_without_exposing_its_path(self):
        output = Path(self.tmp.name) / "jobs" / "text-media-test" / "analysis.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {
                    "status": "completed",
                    "tool": "analyze_text",
                    "encoding": "utf-8",
                    "character_count": 26,
                    "line_count": 2,
                    "headings": ["Fixture"],
                    "preview": "safe text fixture",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        original_root = self.ingest.PROJECT_ROOT
        self.ingest.PROJECT_ROOT = Path(self.tmp.name)
        try:
            presentation = self.ingest._load_text_presentation({"output_path": str(output)})
        finally:
            self.ingest.PROJECT_ROOT = original_root
        self.assertEqual(presentation["status"], "ready")
        self.assertIn("文本解析结果：", presentation["reply_template"])
        self.assertIn("safe text fixture", presentation["reply_template"])
        self.assertNotIn(str(output), presentation["reply_template"])

    def test_nested_text_result_is_rejected_as_wrong_artifact_shape(self):
        output = Path(self.tmp.name) / "jobs" / "text-media-invalid" / "analysis.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {
                    "status": "completed",
                    "tool": "analyze_text",
                    "result": {
                        "character_count": 1,
                        "line_count": 1,
                        "preview": "nested",
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        original_root = self.ingest.PROJECT_ROOT
        self.ingest.PROJECT_ROOT = Path(self.tmp.name)
        try:
            with self.assertRaises(self.ingest.ResultPresentationError):
                self.ingest._load_text_presentation({"output_path": str(output)})
        finally:
            self.ingest.PROJECT_ROOT = original_root

    def test_empty_ocr_is_omitted_and_long_model_text_is_summarized(self):
        reply = self.ingest._format_image_result({"outputs": [{"text": "画面内容" * 100}]})
        self.assertNotIn("识别文字", reply)
        self.assertLessEqual(len(reply), 220)
        self.assertIn("…", reply)

    def test_json_shaped_model_text_is_mapped_not_exposed_as_raw_json(self):
        raw_json = json.dumps({"summary": "画面展示了工位上的控制板和测试线。"}, ensure_ascii=False)
        reply = self.ingest._format_image_result({"outputs": [{"text": raw_json}]})
        self.assertIn("控制板", reply)
        self.assertNotIn("{", reply)
        self.assertNotIn('"summary"', reply)

    def test_formatter_removes_internal_metadata_from_visible_text(self):
        digest = "a" * 64
        reply = self.ingest._format_image_result(
            {
                "outputs": [
                    {
                        "text": f"图片位于 E:\\private\\analysis.json，关联 {digest} om_hidden oc_hidden ou_hidden"
                    }
                ],
            }
        )
        for forbidden in ("E:\\private", digest, "om_hidden", "oc_hidden", "ou_hidden"):
            self.assertNotIn(forbidden, reply)
        self.assertIn("[已省略]", reply)

    def test_empty_image_result_and_invalid_presentation_are_explicit_failures(self):
        with self.assertRaises(self.ingest.ResultPresentationError):
            self.ingest._format_image_result({"outputs": []})
        failed = self.ingest._public_consume_result(
            {
                "status": "completed",
                "media_kind": "png",
                "action": "image",
                "presentation": {"status": "failed", "error_code": "result_content_empty"},
            }
        )
        self.assertEqual(failed["status"], "presentation_failed")
        self.assertEqual(failed["error_code"], "result_content_empty")
        self.assertIn("未生成可展示的结果", failed["reply_template"])
        self.assertNotEqual(failed["reply_template"], "媒体处理已完成。")

    def test_empty_or_untrusted_audio_result_is_an_explicit_failure(self):
        with self.assertRaises(self.ingest.ResultPresentationError):
            self.ingest._format_audio_result({"transcript": ""})
        failed = self.ingest._public_consume_result(
            {
                "status": "completed",
                "media_kind": "wav",
                "action": "audio",
                "presentation": {"status": "failed", "error_code": "result_content_empty"},
            }
        )
        self.assertEqual(failed["status"], "presentation_failed")
        self.assertEqual(failed["error_code"], "result_content_empty")
        self.assertIn("未生成可展示的转录内容", failed["reply_template"])
        self.assertNotEqual(failed["reply_template"], "媒体处理已完成。")
        with self.assertRaises(self.ingest.ResultPresentationError):
            self.ingest._load_audio_presentation({"output_path": str(Path(self.tmp.name) / "bad.json")})

        output = Path(self.tmp.name) / "jobs" / "media-test" / "analysis.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {
                    "status": "completed",
                    "tool": "transcribe_audio",
                    "result": {"transcript": "safe transcript"},
                }
            ),
            encoding="utf-8",
        )
        original_root = self.ingest.PROJECT_ROOT
        self.ingest.PROJECT_ROOT = Path(self.tmp.name)
        try:
            with self.assertRaises(self.ingest.ResultPresentationError):
                self.ingest._load_audio_presentation({"output_path": str(output)})
        finally:
            self.ingest.PROJECT_ROOT = original_root

    def test_generic_completion_is_not_an_image_success_fallback(self):
        image = self.ingest._public_consume_result(
            {"status": "completed", "media_kind": "png", "action": "image"}
        )
        self.assertEqual(image["status"], "presentation_failed")
        self.assertNotEqual(image["reply_template"], "媒体处理已完成。")
        audio = self.ingest._public_consume_result(
            {"status": "completed", "media_kind": "wav", "action": "audio"}
        )
        self.assertEqual(audio["status"], "presentation_failed")
        self.assertNotEqual(audio["reply_template"], "媒体处理已完成。")
        text = self.ingest._public_consume_result(
            {"status": "completed", "media_kind": "txt", "action": "text"}
        )
        self.assertEqual(text["status"], "presentation_failed")
        self.assertNotEqual(text["reply_template"], "媒体处理已完成。")
        video = self.ingest._public_consume_result(
            {"status": "completed", "media_kind": "mp4", "action": "video"}
        )
        self.assertEqual(video["reply_template"], "媒体处理已完成。")


if __name__ == "__main__":
    unittest.main()
