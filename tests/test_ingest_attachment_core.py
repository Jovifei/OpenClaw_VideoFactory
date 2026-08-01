"""
Offline tests for the ingest_attachment tool core (no MCP stdio, no Gateway).

Covers: TXT/PNG/MP4 success, multi-attachment manifest, idempotency,
path traversal rejection, unauthorized route, MIME mismatch, signature
mismatch, oversize, unsafe filename, missing source, message_manifest.

Run:
    python tests/test_ingest_attachment_core.py
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
FIXTURES = REPO / "tests" / "fixtures" / "feishu_delivery"


class IngestAttachmentCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="ingest_core_"))
        cls.inbound = cls.tmp / "inbound"
        cls.workspace_inbound = cls.tmp / "workspace" / "media" / "inbound"
        cls.project = cls.tmp / "project"
        cls.inbound.mkdir(parents=True)
        cls.workspace_inbound.mkdir(parents=True)
        cls.project.mkdir(parents=True)
        # Stage fixtures as inbound files.
        shutil.copy(FIXTURES / "p0-file-test.txt", cls.inbound / "a.txt")
        shutil.copy(FIXTURES / "p0-image-test.png", cls.inbound / "b.png")
        shutil.copy(FIXTURES / "p0-video-test.mp4", cls.inbound / "c.mp4")
        shutil.copy(FIXTURES / "p0-audio-test.wav", cls.inbound / "d.wav")
        shutil.copy(FIXTURES / "p0-file-test.txt", cls.workspace_inbound / "workspace.txt")
        # Configure the module via env BEFORE import.
        os.environ["OPENCLAW_INBOUND_ROOT"] = str(cls.inbound)
        os.environ["OPENCLAW_TRUSTED_INBOUND_ROOTS"] = (
            f"openclaw_global|{cls.inbound};video_factory_workspace|{cls.workspace_inbound}"
        )
        os.environ["OPENCLAW_PROJECT_ROOT"] = str(cls.project)
        os.environ["OPENCLAW_INGEST_SCRIPT"] = str(SCRIPTS / "run_ingest_safe.ps1")
        os.environ["OPENCLAW_AUTHORIZED_CHAT_IDS"] = "oc_test1234"
        os.environ["OPENCLAW_AUTHORIZED_SENDER_IDS"] = "ou_test1234"
        os.environ["OPENCLAW_ACCOUNT_ID"] = "zhongshu"
        os.environ["OPENCLAW_MAX_BYTES"] = "5242880"
        sys.path.insert(0, str(SCRIPTS))
        import importlib
        import mcp_ingest_attachment as m

        importlib.reload(m)
        cls.m = m

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _args(self, **overrides):
        base = dict(
            message_id="om_t1",
            attachment_index=0,
            attachment_count=1,
            source_media_path=str(self.inbound / "a.txt"),
            original_file_name="a.txt",
            content_type="text/plain",
            chat_id="oc_test1234",
            sender_id="ou_test1234",
        )
        base.update(overrides)
        return base

    def test_txt_success(self):
        r = self.m.ingest_attachment(self._args(message_id="om_txt_ok"))
        self.assertEqual(r["status"], "quarantined")
        self.assertEqual(r["detected_kind"], "txt")
        self.assertFalse(r["content_parsed"])
        self.assertTrue(r["quarantined"])
        self.assertTrue(r["analysis_allowed"])
        self.assertTrue(r["ticket_issued"])
        self.assertEqual(r["ticket_action"], "text")
        self.assertFalse(r["already_ingested"])
        self.assertTrue(r["stored_path"])
        self.assertTrue(r["receipt_path"])

    def test_router_can_omit_size_field(self):
        r = self.m.ingest_attachment(self._args(message_id="om_no_size"))
        self.assertEqual(r["status"], "quarantined")
        self.assertEqual(r["actual_size_bytes"], (self.inbound / "a.txt").stat().st_size)

    def test_wrong_legacy_size_is_audit_only(self):
        r = self.m.ingest_attachment(self._args(message_id="om_wrong_old", size_bytes=1))
        receipt = json.loads(Path(r["receipt_path"]).read_text(encoding="utf-8"))
        self.assertEqual(r["status"], "quarantined")
        self.assertEqual(r["declared_size_bytes"], None)
        self.assertFalse(r["declared_size_trusted"])
        self.assertEqual(r["untrusted_size_claim_bytes"], 1)
        self.assertEqual(r["actual_size_bytes"], (self.inbound / "a.txt").stat().st_size)
        self.assertEqual(receipt["untrusted_size_claim_bytes"], 1)
        self.assertEqual(receipt["untrusted_size_claim_source"], "untrusted_legacy_size_bytes")

    def test_r1_style_67_claim_with_actual_55_is_quarantined(self):
        source = self.inbound / "r1-55.txt"
        source.write_bytes(b"OpenClaw VideoFactory P0 file ingress test\nNo secrets.\n")
        self.assertEqual(source.stat().st_size, 55)
        r = self.m.ingest_attachment(
            self._args(
                message_id="om_r1_67",
                source_media_path=str(source),
                original_file_name="r1-55.txt",
                size_bytes=67,
            )
        )
        self.assertEqual(r["status"], "quarantined")
        self.assertEqual(r["actual_size_bytes"], 55)
        self.assertEqual(r["untrusted_size_claim_bytes"], 67)

    def test_trusted_declared_size_correct_is_recorded(self):
        size = (self.inbound / "a.txt").stat().st_size
        r = self.m.ingest_attachment(
            self._args(message_id="om_trusted_ok"),
            trusted_declared_size_bytes=size,
            trusted_declared_size_source="channel_attachment_metadata",
        )
        self.assertEqual(r["status"], "quarantined")
        self.assertEqual(r["declared_size_bytes"], size)
        self.assertTrue(r["declared_size_trusted"])

    def test_trusted_declared_size_mismatch_is_rejected(self):
        r = self.m.ingest_attachment(
            self._args(message_id="om_trusted_bad"),
            trusted_declared_size_bytes=1,
            trusted_declared_size_source="download_content_length",
        )
        self.assertEqual(r["error_code"], "trusted_declared_size_mismatch")

    def test_unrecognized_trusted_provenance_is_rejected(self):
        size = (self.inbound / "a.txt").stat().st_size
        r = self.m.ingest_attachment(
            self._args(message_id="om_trusted_source_bad"),
            trusted_declared_size_bytes=size,
            trusted_declared_size_source="router_claim",
        )
        self.assertEqual(r["error_code"], "invalid_declared_size")

    def test_invalid_trusted_declared_sizes_are_rejected(self):
        for index, value in enumerate(("55", -1, 55.5, None)):
            with self.subTest(value=value):
                r = self.m.ingest_attachment(
                    self._args(message_id=f"om_decl_bad_{index}"),
                    trusted_declared_size_bytes=value,
                    trusted_declared_size_source="channel_attachment_metadata",
                )
                self.assertEqual(r["error_code"], "invalid_declared_size")

    def test_untrusted_string_negative_decimal_and_null_claims_do_not_reject(self):
        for index, value in enumerate(("55", -1, 55.5, None)):
            with self.subTest(value=value):
                r = self.m.ingest_attachment(
                    self._args(message_id=f"om_claim_{index}", declared_size_bytes=value)
                )
                self.assertEqual(r["status"], "quarantined")
                self.assertEqual(r["declared_size_bytes"], None)
                self.assertFalse(r["declared_size_trusted"])

    def test_zero_byte_txt_uses_actual_filesystem_size(self):
        source = self.inbound / "empty.txt"
        source.write_bytes(b"")
        r = self.m.ingest_attachment(
            self._args(
                message_id="om_zero", source_media_path=str(source), original_file_name="empty.txt"
            )
        )
        self.assertEqual(r["status"], "quarantined")
        self.assertEqual(r["actual_size_bytes"], 0)
        self.assertEqual(r["stored_size_bytes"], 0)

    def test_server_owned_size_limit_rejects_real_oversize(self):
        with mock.patch.object(self.m, "MAX_BYTES_DEFAULT", 1):
            r = self.m.ingest_attachment(self._args(message_id="om_big"))
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["error_code"], "file_too_large")

    def test_router_cannot_override_server_owned_size_limit(self):
        with mock.patch.object(self.m, "MAX_BYTES_DEFAULT", 1):
            r = self.m.ingest_attachment(self._args(message_id="om_big_router", max_bytes=99999999))
        self.assertEqual(r["error_code"], "file_too_large")

    def test_png_success(self):
        r = self.m.ingest_attachment(
            self._args(
                message_id="om_png_ok",
                source_media_path=str(self.inbound / "b.png"),
                original_file_name="b.png",
                content_type="image/png",
            )
        )
        self.assertEqual(r["status"], "quarantined")
        self.assertEqual(r["detected_kind"], "png")
        self.assertTrue(r["ticket_issued"])
        self.assertRegex(r["ticket"], r"^[A-Za-z0-9_-]{43,}$")

    def test_audio_success_issues_ticket(self):
        r = self.m.ingest_attachment(
            self._args(
                message_id="om_audio_ok",
                source_media_path=str(self.inbound / "d.wav"),
                original_file_name="d.wav",
                content_type="audio/wav",
            )
        )
        self.assertEqual(r["status"], "quarantined")
        self.assertEqual(r["detected_kind"], "audio")
        self.assertTrue(r["ticket_issued"])

    def test_caption_cannot_request_analysis_or_change_receipt(self):
        r = self.m.ingest_attachment(
            self._args(
                message_id="om_png_intent",
                source_media_path=str(self.inbound / "b.png"),
                original_file_name="b.png",
                content_type="image/png",
                caption="分析图片",
            )
        )
        self.assertTrue(r["ticket_issued"])
        receipt = json.loads(Path(r["receipt_path"]).read_text(encoding="utf-8"))
        self.assertNotIn("attachment_action", receipt)
        self.assertNotIn("analysis_requested", receipt)

    def test_txt_caption_never_requests_or_consumes_ticket(self):
        for index, caption in enumerate((None, "", "please inspect this attachment")):
            with self.subTest(caption=caption):
                r = self.m.ingest_attachment(
                    self._args(message_id=f"om_caption_default_{index}", caption=caption)
                )
                self.assertTrue(r["ticket_issued"])
                receipt = json.loads(Path(r["receipt_path"]).read_text(encoding="utf-8"))
                self.assertNotIn("attachment_action", receipt)
                self.assertNotIn("analysis_requested", receipt)

    def test_workspace_root_success(self):
        source = self.workspace_inbound / "workspace.txt"
        r = self.m.ingest_attachment(
            self._args(
                message_id="om_workspace",
                source_media_path=str(source),
                original_file_name="workspace.txt",
                content_type="text/plain",
            )
        )
        self.assertEqual(r["status"], "quarantined")
        self.assertEqual(r["trusted_root_id"], "video_factory_workspace")
        receipt = json.loads(Path(r["receipt_path"]).read_text(encoding="utf-8"))
        self.assertEqual(receipt["trusted_root_id"], "video_factory_workspace")
        self.assertTrue(receipt["source_root_match"])
        self.assertEqual(
            receipt["canonical_source_path"].split(":/", 1)[0], "video_factory_workspace"
        )

    def test_mp4_success(self):
        r = self.m.ingest_attachment(
            self._args(
                message_id="om_mp4_ok",
                source_media_path=str(self.inbound / "c.mp4"),
                original_file_name="c.mp4",
                content_type="video/mp4",
            )
        )
        self.assertEqual(r["status"], "quarantined")
        self.assertEqual(r["detected_kind"], "mp4")
        self.assertTrue(r["ticket_issued"])

    def test_multi_attachment_manifest(self):
        r0 = self.m.ingest_attachment(
            self._args(
                message_id="om_multi1",
                attachment_index=0,
                attachment_count=2,
                original_file_name="a.txt",
                content_type="text/plain",
            )
        )
        r1 = self.m.ingest_attachment(
            self._args(
                message_id="om_multi1",
                attachment_index=1,
                attachment_count=2,
                source_media_path=str(self.inbound / "b.png"),
                original_file_name="b.png",
                content_type="image/png",
            )
        )
        self.assertEqual(r0["status"], "quarantined")
        self.assertEqual(r1["status"], "quarantined")
        manifest_path = self.project / "input" / "feishu" / "om_multi1" / "message_manifest.json"
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["attachment_count"], 2)
        self.assertEqual(len(manifest["attachments"]), 2)
        idxs = [a["attachment_index"] for a in manifest["attachments"]]
        self.assertEqual(idxs, [0, 1])
        self.assertTrue(all("attachment_action" not in a for a in manifest["attachments"]))
        self.assertTrue(all("analysis_requested" not in a for a in manifest["attachments"]))

    def test_multi_attachment_sizes_are_independent(self):
        r0 = self.m.ingest_attachment(
            self._args(message_id="om_multi_size", attachment_index=0, attachment_count=2)
        )
        r1 = self.m.ingest_attachment(
            self._args(
                message_id="om_multi_size",
                attachment_index=1,
                attachment_count=2,
                source_media_path=str(self.inbound / "b.png"),
                original_file_name="b.png",
                content_type="image/png",
                size_bytes=3,
            )
        )
        self.assertEqual(r0["status"], "quarantined")
        self.assertEqual(r1["status"], "quarantined")
        self.assertNotEqual(r0["actual_size_bytes"], r1["actual_size_bytes"])

    def test_idempotent_same_message_index_hash(self):
        first = self.m.ingest_attachment(
            self._args(
                message_id="om_idem",
                source_media_path=str(self.inbound / "b.png"),
                original_file_name="b.png",
                content_type="image/png",
            )
        )
        second = self.m.ingest_attachment(
            self._args(
                message_id="om_idem",
                source_media_path=str(self.inbound / "b.png"),
                original_file_name="b.png",
                content_type="image/png",
            )
        )
        self.assertFalse(first["already_ingested"])
        self.assertTrue(second["already_ingested"])
        self.assertTrue(first["ticket_issued"])
        self.assertTrue(second["ticket_already_issued"])
        self.assertIsNone(second["ticket"])
        self.assertEqual(first["sha256"], second["sha256"])

    def test_same_message_different_actual_size_is_idempotency_conflict(self):
        source = self.inbound / "conflict.txt"
        source.write_bytes(b"first\n")
        first = self.m.ingest_attachment(
            self._args(
                message_id="om_size_conflict",
                source_media_path=str(source),
                original_file_name="conflict.txt",
            )
        )
        source.write_bytes(b"second has a different size\n")
        second = self.m.ingest_attachment(
            self._args(
                message_id="om_size_conflict",
                source_media_path=str(source),
                original_file_name="conflict.txt",
            )
        )
        self.assertEqual(first["status"], "quarantined")
        self.assertEqual(second["error_code"], "idempotency_conflict")

    def test_legacy_size_claim_does_not_change_idempotency_identity(self):
        first = self.m.ingest_attachment(self._args(message_id="om_claim_idem", size_bytes=67))
        second = self.m.ingest_attachment(self._args(message_id="om_claim_idem"))
        self.assertEqual(first["status"], "quarantined")
        self.assertTrue(second["already_ingested"])
        self.assertEqual(second["actual_size_bytes"], first["actual_size_bytes"])

    def test_source_size_change_during_read_is_rejected(self):
        source = self.inbound / "mutate-size.txt"
        source.write_bytes(b"before\n")
        original = self.m._run_ingest_script

        def mutate_then_run(clean):
            Path(clean["source_media_path"]).write_bytes(b"after has more bytes\n")
            return original(clean)

        with mock.patch.object(self.m, "_run_ingest_script", side_effect=mutate_then_run):
            r = self.m.ingest_attachment(
                self._args(
                    message_id="om_mutate_size",
                    source_media_path=str(source),
                    original_file_name="mutate-size.txt",
                )
            )
        self.assertEqual(r["error_code"], "source_changed_during_read")

    def test_source_mtime_change_during_read_is_rejected(self):
        source = self.inbound / "mutate-mtime.txt"
        source.write_bytes(b"same bytes\n")
        original = self.m._run_ingest_script

        def mutate_then_run(clean):
            item = Path(clean["source_media_path"])
            stat = item.stat()
            os.utime(item, ns=(stat.st_atime_ns, stat.st_mtime_ns + 2_000_000_000))
            return original(clean)

        with mock.patch.object(self.m, "_run_ingest_script", side_effect=mutate_then_run):
            r = self.m.ingest_attachment(
                self._args(
                    message_id="om_mutate_mtime",
                    source_media_path=str(source),
                    original_file_name="mutate-mtime.txt",
                )
            )
        self.assertEqual(r["error_code"], "source_changed_during_read")

    def test_same_message_different_index_independent(self):
        r0 = self.m.ingest_attachment(
            self._args(message_id="om_sep", attachment_index=0, attachment_count=2)
        )
        r1 = self.m.ingest_attachment(
            self._args(
                message_id="om_sep",
                attachment_index=1,
                attachment_count=2,
                original_file_name="a2.txt",
            )
        )
        self.assertFalse(r0["already_ingested"])
        self.assertFalse(r1["already_ingested"])
        self.assertNotEqual(r0["stored_path"], r1["stored_path"])

    def test_path_traversal_rejected(self):
        # A path outside the inbound root (system file) must be rejected by the
        # MCP layer before reaching the PS script.
        r = self.m.ingest_attachment(
            self._args(
                message_id="om_trav",
                source_media_path=r"C:\Windows\win.ini",
                original_file_name="win.txt",
            )
        )
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["error_code"], "path_traversal")

    def test_unauthorized_chat_rejected(self):
        r = self.m.ingest_attachment(self._args(message_id="om_unauth", chat_id="oc_evil1234"))
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["error_code"], "unauthorized_route")

    def test_unauthorized_sender_rejected(self):
        r = self.m.ingest_attachment(self._args(message_id="om_unauth2", sender_id="ou_evil1234"))
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["error_code"], "unauthorized_route")

    def test_mime_mismatch_rejected(self):
        r = self.m.ingest_attachment(
            self._args(
                message_id="om_mime",
                source_media_path=str(self.inbound / "b.png"),
                original_file_name="b.png",
                content_type="text/plain",
            )
        )
        self.assertEqual(r["status"], "rejected")
        self.assertIn(r["error_code"], {"mime_conflict", "signature_mismatch"})

    def test_signature_mismatch_rejected(self):
        r = self.m.ingest_attachment(
            self._args(
                message_id="om_sig",
                source_media_path=str(self.inbound / "a.txt"),
                original_file_name="fake.png",
                content_type="image/png",
            )
        )
        self.assertEqual(r["status"], "rejected")
        self.assertIn(r["error_code"], {"signature_mismatch", "mime_conflict"})

    def test_unsafe_filename_rejected(self):
        r = self.m.ingest_attachment(
            self._args(message_id="om_unsafe", original_file_name="folder\\x.txt")
        )
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["error_code"], "unsafe_file_name")

    def test_double_extension_rejected(self):
        r = self.m.ingest_attachment(
            self._args(message_id="om_dbl", original_file_name="file.png.exe")
        )
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["error_code"], "unsafe_file_name")

    def test_missing_source_rejected(self):
        r = self.m.ingest_attachment(
            self._args(
                message_id="om_miss",
                source_media_path=str(self.inbound / "nope.txt"),
                original_file_name="nope.txt",
            )
        )
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["error_code"], "missing_source")

    def test_invalid_message_id_rejected(self):
        r = self.m.ingest_attachment(self._args(message_id="bad_id"))
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["error_code"], "invalid_message_id")

    def test_receipt_does_not_leak_source_path(self):
        r = self.m.ingest_attachment(self._args(message_id="om_leak"))
        # The tool RESULT must not echo the original inbound source_media_path.
        self.assertNotIn("source_media_path", r)
        receipt = json.loads(Path(r["receipt_path"]).read_text(encoding="utf-8"))
        # Receipt DOES contain source_path (it is the quarantine audit record),
        # but identifiers are masked.
        self.assertTrue(receipt["quarantined"])
        self.assertNotIn("source_path", receipt)
        self.assertIn("trusted_root_id", receipt)
        self.assertNotEqual(receipt["chat_id"], "oc_test1234")
        self.assertNotEqual(receipt["sender_id"], "ou_test1234")

    def test_chinese_filename_size_is_bytes_not_characters(self):
        source = self.inbound / "中文.txt"
        payload = "中文\n".encode("utf-8")
        source.write_bytes(payload)
        r = self.m.ingest_attachment(
            self._args(
                message_id="om_chinese_bytes",
                source_media_path=str(source),
                original_file_name="中文.txt",
            )
        )
        self.assertEqual(r["actual_size_bytes"], len(payload))
        self.assertNotEqual(r["actual_size_bytes"], len("中文\n"))

    def test_crlf_and_lf_use_their_distinct_filesystem_byte_counts(self):
        for suffix, payload in (("lf", b"a\nb\n"), ("crlf", b"a\r\nb\r\n")):
            with self.subTest(suffix=suffix):
                source = self.inbound / f"{suffix}.txt"
                source.write_bytes(payload)
                r = self.m.ingest_attachment(
                    self._args(
                        message_id=f"om_{suffix}_bytes",
                        source_media_path=str(source),
                        original_file_name=f"{suffix}.txt",
                    )
                )
                self.assertEqual(r["actual_size_bytes"], len(payload))

    def test_ui_and_model_size_values_never_enter_safety_contract(self):
        r = self.m.ingest_attachment(
            self._args(message_id="om_ui_model", size_bytes=999999, declared_size_bytes=12345)
        )
        receipt = json.loads(Path(r["receipt_path"]).read_text(encoding="utf-8"))
        self.assertEqual(r["status"], "quarantined")
        self.assertEqual(receipt["declared_size_bytes"], None)
        self.assertFalse(receipt["declared_size_trusted"])
        self.assertEqual(receipt["actual_size_bytes"], (self.inbound / "a.txt").stat().st_size)

    def test_success_receipt_has_complete_size_contract(self):
        r = self.m.ingest_attachment(self._args(message_id="om_contract_receipt"))
        receipt = json.loads(Path(r["receipt_path"]).read_text(encoding="utf-8"))
        required = {
            "declared_size_bytes",
            "declared_size_trusted",
            "declared_size_source",
            "actual_size_bytes",
            "stored_size_bytes",
            "size_match",
            "source_sha256",
            "stored_sha256",
            "source_stable_during_read",
            "trusted_root_id",
        }
        self.assertTrue(required.issubset(receipt))
        self.assertEqual(receipt["actual_size_bytes"], receipt["stored_size_bytes"])
        self.assertEqual(receipt["source_sha256"], receipt["stored_sha256"])

    def test_old_receipt_is_repaired_to_new_size_contract(self):
        first = self.m.ingest_attachment(self._args(message_id="om_old_receipt"))
        path = Path(first["receipt_path"])
        receipt = json.loads(path.read_text(encoding="utf-8"))
        for name in (
            "declared_size_bytes",
            "declared_size_trusted",
            "declared_size_source",
            "actual_size_bytes",
            "stored_size_bytes",
            "size_match",
            "source_sha256",
            "stored_sha256",
            "source_stable_during_read",
        ):
            receipt.pop(name, None)
        path.write_text(json.dumps(receipt), encoding="utf-8")
        second = self.m.ingest_attachment(self._args(message_id="om_old_receipt"))
        repaired = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(second["already_ingested"])
        self.assertTrue(repaired["source_stable_during_read"])
        self.assertIn("actual_size_bytes", repaired)

    def test_public_schema_hides_router_size_and_limit_inputs(self):
        props = self.m.TOOL_SCHEMA["inputSchema"]["properties"]
        required = self.m.TOOL_SCHEMA["inputSchema"]["required"]
        self.assertNotIn("size_bytes", props)
        self.assertNotIn("max_bytes", props)
        self.assertNotIn("size_bytes", required)
        self.assertNotIn("max_bytes", required)
        self.assertNotIn("caption", props)
        request_props = self.m.CONSUME_MEDIA_ACTION_TICKET_SCHEMA["inputSchema"]["properties"]
        self.assertEqual(
            set(request_props), {"raw_command", "current_chat_context", "current_sender_context"}
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
