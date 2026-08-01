from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CandidateCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "P1_CANDIDATE_STATE_ROOT": str(Path(self.temp_dir.name) / "state")}
        return subprocess.run(
            [sys.executable, "scripts/factory.py", "candidate", *arguments],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_production_entrypoint_stays_fail_closed(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/factory.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 78)
        self.assertIn("not implemented", result.stderr)

    def test_candidate_create_and_status_emit_single_json_document(self) -> None:
        initialized = self.run_cli("init-db")
        self.assertEqual(initialized.returncode, 0)
        self.assertEqual(json.loads(initialized.stdout)["status"], "initialized")

        created = self.run_cli("create", "--fixture", "FIX-001", "--idempotency-key", "cli-key")
        payload = json.loads(created.stdout)
        self.assertEqual(created.returncode, 0)
        self.assertTrue(payload["created"])
        self.assertEqual(payload["requested_duration_seconds"], 40)
        self.assertEqual(payload["render_contract_version"], "2.0")

        status = self.run_cli("status", "--job-id", payload["job_id"], "--json")
        self.assertEqual(json.loads(status.stdout)["state"], "NEW")

    def test_candidate_duration_accepts_range_and_rejects_outside_values(self) -> None:
        for duration in (25, 40, 60):
            result = self.run_cli(
                "create",
                "--fixture",
                "FIX-001",
                "--idempotency-key",
                f"duration-{duration}",
                "--duration-seconds",
                str(duration),
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["requested_duration_seconds"], duration)
        for duration in (24, 61):
            result = self.run_cli(
                "create",
                "--fixture",
                "FIX-001",
                "--idempotency-key",
                f"invalid-duration-{duration}",
                "--duration-seconds",
                str(duration),
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("candidate_duration_out_of_range", result.stderr)
