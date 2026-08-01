from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.factory.db import CandidateStore
from src.factory.pipeline import cancel_job, run_job


class CandidatePipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.store = CandidateStore(self.root / "state" / "candidate.sqlite3")
        self.store.initialize()
        self.env = {
            "P1_CANDIDATE_STATE_ROOT": str(self.root / "state"),
            "P1_CANDIDATE_JOBS_ROOT": str(self.root / "jobs"),
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_completed_stage_can_resume_from_the_next_stage(self) -> None:
        job = self.store.create_job("FIX-001", "recovery-key", "protocol-frame", "Modbus")["job_id"]
        with patch.dict(os.environ, {**self.env, "P1_CANDIDATE_INTERRUPT_AFTER": "RESEARCHING"}, clear=False), patch(
            "src.factory.pipeline.PROJECT_ROOT", self.root
        ):
            result = run_job(self.store, job, "cpu", "sapi")

        self.assertEqual(result["status"], "interrupted_for_recovery_test")
        recovered = self.store.status(job)
        self.assertEqual(recovered["state"], "SCRIPTING")
        self.assertEqual(recovered["last_completed_state"], "RESEARCHING")
        self.assertTrue((self.root / "jobs" / job / "sources.json").exists())

    def test_render_cancel_removes_partial_render_outputs(self) -> None:
        job = self.store.create_job("FIX-001", "cancel-render-key", "protocol-frame", "Modbus")["job_id"]
        for state in ("RESEARCHING", "SCRIPTING", "VOICE", "CAPTIONS", "ASSETS", "RENDERING"):
            self.store.advance(job, state)
        package = self.root / "jobs" / job
        package.mkdir(parents=True)
        for name in ("render_raw.mp4", "final_master.mp4", "feishu_preview.mp4", "cover.png", "render_manifest.json"):
            (package / name).write_bytes(b"partial")
        temp_project = self.root / "project"
        runtime = temp_project / "remotion" / "public" / "runtime" / job
        runtime.mkdir(parents=True)
        (runtime / "voice.wav").write_bytes(b"runtime")

        with patch.dict(os.environ, self.env, clear=False), patch("src.factory.pipeline.PROJECT_ROOT", temp_project):
            cancelled = cancel_job(self.store, job)

        self.assertEqual(cancelled["state"], "CANCELLED")
        self.assertFalse(any(package.glob("*.mp4")))
        self.assertFalse((package / "cover.png").exists())
        self.assertFalse(runtime.exists())
