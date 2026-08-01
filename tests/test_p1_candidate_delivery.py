from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from src.factory.db import CandidateStore
from src.factory.delivery import load_json_object, record_dry_run_delivery, valid_delivery_manifest
from src.factory.state import next_state


class CandidateDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.store = CandidateStore(self.root / "candidate.sqlite3")
        self.store.initialize()
        self.job = self.store.create_job("FIX-001", "delivery-key", "protocol-frame", "Modbus")[
            "job_id"
        ]
        state = "NEW"
        while state != "QUALITY_CHECK":
            state = next_state(state) or "QUALITY_CHECK"
            self.store.advance(self.job, state)
        self.package = self.root / "job"
        self.package.mkdir()
        for name in (
            "final_master.mp4",
            "feishu_preview.mp4",
            "cover.png",
            "captions.srt",
            "quality_report.json",
        ):
            (self.package / name).write_bytes(b"candidate")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_dry_run_delivery_is_idempotent_and_has_no_send_command(self) -> None:
        first = record_dry_run_delivery(self.store, self.job, self.package)
        second = record_dry_run_delivery(self.store, self.job, self.package)

        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(first["delivery_key"], second["delivery_key"])
        self.assertEqual(first["mode"], "dry-run")
        self.assertNotIn("command", first["manifest"])
        self.assertEqual(first["manifest"]["schema_version"], "2.0")
        self.assertEqual(first["manifest"]["preview"]["relative_path"], "feishu_preview.mp4")
        self.assertNotIn("target", first["manifest"])

    def test_delivery_manifest_rejects_unknown_and_unsafe_nested_fields(self) -> None:
        result = record_dry_run_delivery(self.store, self.job, self.package)
        manifest = {**result["manifest"], "delivery_key": result["delivery_key"]}
        self.assertTrue(valid_delivery_manifest(manifest, self.job, include_delivery_key=True))
        manifest["artifacts"] = [dict(item) for item in manifest["artifacts"]]
        manifest["artifacts"][0]["unexpected"] = "value"
        self.assertFalse(valid_delivery_manifest(manifest, self.job, include_delivery_key=True))

    def test_json_loader_rejects_duplicate_keys(self) -> None:
        path = self.package / "duplicate.json"
        path.write_text('{"candidate_state":"C:/private","candidate_state":"QUALITY_CHECK"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            load_json_object(path)

    def test_database_delivery_manifest_rejects_duplicate_keys(self) -> None:
        result = record_dry_run_delivery(self.store, self.job, self.package)
        duplicate_manifest = (
            '{"candidate_state":"C:/private","candidate_state":"QUALITY_CHECK"}'
        )
        with self.store._transaction() as connection:
            connection.execute(
                "UPDATE deliveries SET manifest_json = ? WHERE delivery_key = ?",
                (duplicate_manifest, result["delivery_key"]),
            )
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            self.store.delivery(result["delivery_key"])
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            record_dry_run_delivery(self.store, self.job, self.package)

    def test_non_quality_state_rejects_before_delivery_or_event_mutation(self) -> None:
        self.store.advance(self.job, "PENDING_REVIEW")
        delivery_key = hashlib.sha256(
            f"{self.job}|offline-dry-run|v2".encode("utf-8")
        ).hexdigest()
        events_before = self.store.events(self.job)
        with self.assertRaisesRegex(RuntimeError, "delivery_requires_quality_check"):
            record_dry_run_delivery(self.store, self.job, self.package)
        self.assertIsNone(self.store.delivery(delivery_key))
        self.assertEqual(events_before, self.store.events(self.job))
