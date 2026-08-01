from __future__ import annotations

import tempfile
import unittest
import sqlite3
from pathlib import Path

from src.factory.db import CandidateStore


class CandidateStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = CandidateStore(Path(self.temp_dir.name) / "candidate.sqlite3")
        self.store.initialize()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_idempotent_create_uses_the_same_deterministic_job_id(self) -> None:
        first = self.store.create_job(
            "FIX-001", "fixture:modbus:2026-07-29", "protocol-frame", "Modbus"
        )
        second = self.store.create_job(
            "FIX-001", "fixture:modbus:2026-07-29", "protocol-frame", "Modbus"
        )

        self.assertEqual(first["job_id"], second["job_id"])
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(first["requested_duration_seconds"], 40)
        self.assertEqual(first["render_contract_version"], "2.0")
        self.assertEqual(self.store.events(first["job_id"])[0]["event_type"], "job_created")

    def test_initialize_migrates_legacy_job_without_rewriting_it(self) -> None:
        legacy_path = Path(self.temp_dir.name) / "legacy.sqlite3"
        connection = sqlite3.connect(legacy_path)
        connection.execute(
            """CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY, idempotency_key TEXT NOT NULL UNIQUE, fixture_id TEXT NOT NULL,
            template TEXT NOT NULL, topic TEXT NOT NULL, state TEXT NOT NULL, last_completed_state TEXT,
            attempt INTEGER NOT NULL DEFAULT 0, metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"""
        )
        connection.execute(
            "INSERT INTO jobs VALUES ('job-0123456789abcdef01234567','legacy','FIX-001','protocol-frame','Modbus','NEW',NULL,0,'{}','now','now')"
        )
        connection.commit()
        connection.close()

        legacy = CandidateStore(legacy_path)
        legacy.initialize()
        job = legacy.status("job-0123456789abcdef01234567")

        self.assertIsNone(job["requested_duration_seconds"])
        self.assertIsNone(job["resolved_duration_seconds"])
        self.assertEqual(job["render_contract_version"], "1.0")

    def test_resolved_duration_is_an_evented_v2_field(self) -> None:
        job = self.store.create_job("FIX-001", "duration-key", "protocol-frame", "Modbus")["job_id"]
        updated = self.store.set_resolved_duration(job, 42.0)

        self.assertEqual(updated["resolved_duration_seconds"], 42.0)
        self.assertEqual(self.store.events(job)[-1]["event_type"], "duration_resolved")

    def test_state_moves_forward_append_events_and_rejects_skips(self) -> None:
        job = self.store.create_job("FIX-001", "state-key", "protocol-frame", "Modbus")["job_id"]
        self.store.advance(job, "RESEARCHING")
        self.store.advance(job, "SCRIPTING")

        self.assertEqual(self.store.status(job)["state"], "SCRIPTING")
        self.assertEqual(self.store.status(job)["last_completed_state"], "RESEARCHING")
        self.assertEqual(
            [item["event_type"] for item in self.store.events(job)],
            ["job_created", "state_advanced", "state_advanced"],
        )
        with self.assertRaisesRegex(ValueError, "invalid_transition"):
            self.store.advance(job, "ASSETS")

    def test_cancel_retry_and_recovery_never_overwrite_event_history(self) -> None:
        job = self.store.create_job("FIX-002", "cancel-key", "engineering-case", "Flash")["job_id"]
        self.store.advance(job, "RESEARCHING")
        self.store.cancel(job, "operator_requested")
        self.assertEqual(self.store.status(job)["state"], "CANCELLED")

        resumed = self.store.retry(job, "candidate_retry")
        self.assertEqual(resumed["state"], "RESEARCHING")
        self.assertEqual(resumed["attempt"], 1)
        self.assertEqual(
            [item["event_type"] for item in self.store.events(job)][-2:],
            ["job_cancelled", "job_retried"],
        )

    def test_database_enables_wal_foreign_keys_and_busy_timeout(self) -> None:
        settings = self.store.connection_settings()
        self.assertEqual(settings["journal_mode"].lower(), "wal")
        self.assertEqual(settings["foreign_keys"], 1)
        self.assertGreaterEqual(settings["busy_timeout"], 5000)
