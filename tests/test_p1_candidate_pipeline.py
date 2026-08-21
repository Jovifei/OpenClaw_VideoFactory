from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.factory.db import CandidateStore
from src.factory.legacy_candidate_control import cancel_job


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

    def test_retired_pipeline_module_is_not_importable(self) -> None:
        with self.assertRaises(ModuleNotFoundError):
            __import__("src.factory.pipeline")

    def test_cancel_control_remains_importable_from_legacy_control(self) -> None:
        from src.factory.legacy_candidate_control import cancel_job as preserved_cancel

        self.assertIs(preserved_cancel, cancel_job)

    def test_cancel_control_does_not_require_render_module(self) -> None:
        job = self.store.create_job("FIX-001", "cancel-control-only", "protocol-frame", "Modbus")["job_id"]
        cancelled = cancel_job(self.store, job)
        self.assertEqual(cancelled["state"], "CANCELLED")

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

        with patch.dict(os.environ, self.env, clear=False), patch("src.factory.legacy_candidate_control.PROJECT_ROOT", temp_project):
            cancelled = cancel_job(self.store, job)

        self.assertEqual(cancelled["state"], "CANCELLED")
        self.assertFalse(any(package.glob("*.mp4")))
        self.assertFalse((package / "cover.png").exists())
        self.assertFalse(runtime.exists())
