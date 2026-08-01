from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.factory.db import CandidateStore
from src.factory.inventory import build_inventory, build_retention_plan
from src.factory.state import next_state


class CandidateInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.store = CandidateStore(self.root / "candidate.sqlite3")
        self.store.initialize()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_inventory_uses_relative_artifact_paths_only(self) -> None:
        job = self.store.create_job("FIX-001", "inventory", "protocol-frame", "Modbus")["job_id"]
        self.store.record_artifact(job, "final_master.mp4", "jobs/p1_candidate/job/final_master.mp4", "a" * 64)

        inventory = build_inventory(self.store)

        self.assertFalse(inventory["destructive_actions"])
        self.assertEqual(inventory["jobs"][0]["artifacts"][0]["relative_path"], "jobs/p1_candidate/job/final_master.mp4")
        self.assertNotIn(str(self.root), str(inventory))

    def test_retention_plan_only_marks_evidence_and_never_deletes(self) -> None:
        pending = self.store.create_job("FIX-001", "pending", "protocol-frame", "Modbus")["job_id"]
        state = "NEW"
        while state != "PENDING_REVIEW":
            state = next_state(state) or "PENDING_REVIEW"
            self.store.advance(pending, state)
        failed = self.store.create_job("FIX-002", "failed", "engineering-case", "Flash")["job_id"]
        self.store.fail(failed, "test")
        reports = self.root / "reports"
        reports.mkdir()
        (reports / "index.md").write_text(pending, encoding="utf-8")

        plan = build_retention_plan(self.store, reports)

        self.assertFalse(plan["destructive_actions"])
        self.assertFalse(plan["deletion_performed"])
        by_job = {item["job_id"]: item for item in plan["entries"]}
        self.assertIn("pending_review", by_job[pending]["reasons"])
        self.assertIn("failure_or_cancellation_evidence", by_job[failed]["reasons"])
        self.assertTrue((self.root / "candidate.sqlite3").exists())
