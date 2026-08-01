"""Explicit trusted-root and path-boundary tests for 009A (offline only)."""

import importlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "tests" / "fixtures" / "feishu_delivery" / "p0-file-test.txt"


class TrustedMediaRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="trusted_roots_"))
        cls.global_root = cls.tmp / "openclaw" / "media" / "inbound"
        cls.workspace_root = cls.tmp / "project" / "media" / "inbound"
        cls.project_root = cls.tmp / "project"
        cls.outside_root = cls.tmp / "outside"
        for path in (cls.global_root, cls.workspace_root, cls.outside_root):
            path.mkdir(parents=True)
        cls.global_file = cls.global_root / "global.txt"
        cls.workspace_file = cls.workspace_root / "workspace.txt"
        cls.global_file.write_bytes(FIXTURE.read_bytes())
        cls.workspace_file.write_bytes(FIXTURE.read_bytes())
        cls.outside_file = cls.outside_root / "outside.txt"
        cls.outside_file.write_bytes(FIXTURE.read_bytes())
        os.environ["OPENCLAW_TRUSTED_INBOUND_ROOTS"] = (
            f"openclaw_global|{cls.global_root};video_factory_workspace|{cls.workspace_root}"
        )
        os.environ["OPENCLAW_PROJECT_ROOT"] = str(cls.project_root)
        os.environ["OPENCLAW_INBOUND_ROOT"] = str(cls.global_root)
        os.environ["OPENCLAW_AUTHORIZED_CHAT_IDS"] = "oc_test1234"
        os.environ["OPENCLAW_AUTHORIZED_SENDER_IDS"] = "ou_test1234"
        sys.path.insert(0, str(REPO / "scripts"))
        import mcp_ingest_attachment as module

        cls.m = importlib.reload(module)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _args(self, source, **overrides):
        args = {
            "message_id": "om_roots",
            "attachment_index": 0,
            "attachment_count": 1,
            "source_media_path": str(source),
            "original_file_name": "source.txt",
            "content_type": "text/plain",
            "size_bytes": Path(source).stat().st_size if Path(source).exists() else 55,
            "chat_id": "oc_test1234",
            "sender_id": "ou_test1234",
        }
        args.update(overrides)
        return args

    def _fake_run(self, clean):
        storage = self.project_root / "input" / "feishu" / clean["message_id"] / "attachment-000"
        storage.mkdir(parents=True, exist_ok=True)
        stored_path = storage / "original.txt"
        stored_path.write_bytes(Path(clean["source_media_path"]).read_bytes())
        receipt_path = storage / "receipt.json"
        receipt_path.write_text(
            json.dumps(
                {
                    "message_id": clean["message_id"],
                    "attachment_index": clean["attachment_index"],
                    "trusted_root_id": clean["trusted_root_id"],
                    "source_root_match": True,
                    "canonical_source_path": clean["canonical_source_path"],
                    "stored_path": str(stored_path),
                    "quarantined": True,
                    "content_parsed": False,
                }
            ),
            encoding="utf-8",
        )
        return (
            {
                "idempotent": False,
                "stored_path": str(stored_path),
                "receipt_path": str(receipt_path),
                "sha256": "a" * 64,
                "size_bytes": clean["source_size"],
                "detected_kind": "txt",
                "normalized_content_type": "text/plain",
                "content_parsed": False,
                "quarantined": True,
            },
            None,
        )

    def _accept(self, args):
        with mock.patch.object(self.m, "_run_ingest_script", side_effect=self._fake_run):
            return self.m.ingest_attachment(args)

    def test_global_root_file_is_accepted(self):
        result = self._accept(self._args(self.global_file))
        self.assertEqual(result["trusted_root_id"], "openclaw_global")

    def test_workspace_root_file_is_accepted(self):
        result = self._accept(self._args(self.workspace_file))
        self.assertEqual(result["trusted_root_id"], "video_factory_workspace")

    def test_chinese_filename_is_accepted(self):
        path = self.global_root / "中文.txt"
        path.write_bytes(FIXTURE.read_bytes())
        result = self._accept(self._args(path, original_file_name="中文.txt"))
        self.assertEqual(result["status"], "quarantined")

    def test_nested_directory_is_accepted(self):
        path = self.global_root / "a" / "b" / "nested.txt"
        path.parent.mkdir(parents=True)
        path.write_bytes(FIXTURE.read_bytes())
        result = self._accept(self._args(path, original_file_name="nested.txt"))
        self.assertEqual(result["status"], "quarantined")

    def test_trusted_root_directory_is_not_a_file(self):
        result = self.m.ingest_attachment(self._args(self.global_root))
        self.assertEqual(result["error_code"], "missing_source")

    def test_similar_prefix_directory_is_rejected(self):
        sibling = self.tmp / "openclaw" / "media" / "inbound2"
        sibling.mkdir(parents=True)
        path = sibling / "evil.txt"
        path.write_bytes(FIXTURE.read_bytes())
        result = self.m.ingest_attachment(self._args(path))
        self.assertEqual(result["error_code"], "path_traversal")

    def test_project_root_other_directory_is_rejected(self):
        path = self.project_root / "output.txt"
        path.write_bytes(FIXTURE.read_bytes())
        result = self.m.ingest_attachment(self._args(path))
        self.assertEqual(result["error_code"], "path_traversal")

    def test_workspace_other_directory_is_rejected(self):
        path = self.tmp / "project" / "output" / "x.txt"
        path.parent.mkdir(parents=True)
        path.write_bytes(FIXTURE.read_bytes())
        result = self.m.ingest_attachment(self._args(path))
        self.assertEqual(result["error_code"], "path_traversal")

    def test_outside_root_is_rejected(self):
        result = self.m.ingest_attachment(self._args(self.outside_file))
        self.assertEqual(result["error_code"], "path_traversal")

    def test_different_drive_is_rejected(self):
        result = self.m.ingest_attachment(self._args(r"D:\foreign\file.txt"))
        self.assertEqual(result["error_code"], "path_traversal")

    def test_unc_path_is_rejected(self):
        result = self.m.ingest_attachment(self._args(r"\\server\share\file.txt"))
        self.assertEqual(result["error_code"], "unc_or_device_path")

    def test_device_path_is_rejected(self):
        result = self.m.ingest_attachment(self._args(r"\\.\C:\file.txt"))
        self.assertEqual(result["error_code"], "unc_or_device_path")

    def test_alternate_data_stream_is_rejected(self):
        result = self.m.ingest_attachment(self._args(str(self.global_root / "global.txt:secret")))
        self.assertEqual(result["error_code"], "alternate_data_stream")

    def test_intermediate_reparse_is_rejected(self):
        with mock.patch.object(Path, "is_symlink", return_value=True):
            result = self.m.ingest_attachment(self._args(self.global_file))
        self.assertEqual(result["error_code"], "reparse_point")

    def test_source_file_reparse_is_rejected(self):
        with mock.patch.object(Path, "is_symlink", return_value=True):
            result = self.m.ingest_attachment(self._args(self.global_file))
        self.assertEqual(result["error_code"], "reparse_point")

    def test_drive_root_is_not_implicitly_trusted(self):
        result = self.m.ingest_attachment(self._args("C:\\"))
        self.assertIn(result["error_code"], {"path_traversal", "source_not_found"})

    def test_case_difference_matches_on_windows(self):
        path = Path(str(self.global_file).upper())
        result = self._accept(self._args(path))
        self.assertEqual(result["trusted_root_id"], "openclaw_global")

    def test_trailing_separator_in_root_spec_is_canonicalized(self):
        root = self.m.TRUSTED_ROOTS[0]
        self.assertEqual(root["canonical"].rstrip("\\"), str(self.global_root).lower().rstrip("\\"))

    def test_root_ids_are_stable_and_unique(self):
        ids = [root["root_id"] for root in self.m.TRUSTED_ROOTS]
        self.assertEqual(ids, ["openclaw_global", "video_factory_workspace"])

    def test_cwd_is_not_auto_trusted(self):
        path = REPO / "media" / "inbound" / "not_registered.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(FIXTURE.read_bytes())
        try:
            result = self.m.ingest_attachment(self._args(path))
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual(result["error_code"], "path_traversal")

    def test_untrusted_size_metadata_mismatch_is_not_a_rejection_basis(self):
        result = self._accept(self._args(self.global_file, size_bytes=1))
        self.assertEqual(result["status"], "quarantined")
        self.assertEqual(result["untrusted_size_claim_bytes"], 1)
        self.assertEqual(result["actual_size_bytes"], self.global_file.stat().st_size)

    def test_source_changed_before_subprocess_is_rejected(self):
        original = self.m._run_ingest_script

        def mutate_then_run(clean):
            Path(clean["source_media_path"]).write_bytes(b"changed")
            return original(clean)

        with mock.patch.object(self.m, "_run_ingest_script", side_effect=mutate_then_run):
            result = self.m.ingest_attachment(self._args(self.global_file))
        self.assertEqual(result["error_code"], "source_changed_during_read")
        self.global_file.write_bytes(FIXTURE.read_bytes())

    def test_same_message_different_root_has_distinct_root_id(self):
        first, first_error = self.m._validate_inputs(
            self._args(self.global_file, message_id="om_root_conflict")
        )
        second, second_error = self.m._validate_inputs(
            self._args(self.workspace_file, message_id="om_root_conflict")
        )
        self.assertIsNone(first_error)
        self.assertIsNone(second_error)
        self.assertNotEqual(first["trusted_root_id"], second["trusted_root_id"])

    def test_canonical_source_label_does_not_contain_absolute_root(self):
        result = self._accept(self._args(self.workspace_file))
        receipt = Path(result["receipt_path"])
        data = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertNotIn(str(self.workspace_root), data["canonical_source_path"])

    def test_model_path_outside_registered_roots_is_rejected(self):
        model_path = self.tmp / "models" / "model.bin"
        model_path.parent.mkdir(parents=True)
        model_path.write_bytes(b"model")
        result = self.m.ingest_attachment(self._args(model_path, original_file_name="model.bin"))
        self.assertEqual(result["error_code"], "path_traversal")


if __name__ == "__main__":
    unittest.main(verbosity=2)
