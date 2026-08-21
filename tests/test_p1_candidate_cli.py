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

    def test_candidate_create_is_explicitly_retired_and_status_control_remains(self) -> None:
        initialized = self.run_cli("init-db")
        self.assertEqual(initialized.returncode, 0)
        self.assertEqual(json.loads(initialized.stdout)["status"], "initialized")

        created = self.run_cli("create", "--fixture", "FIX-001", "--idempotency-key", "cli-key")
        payload = json.loads(created.stdout)
        self.assertEqual(created.returncode, 2)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error"]["code"], "legacy_candidate_pipeline_retired")
        self.assertEqual(payload["error"]["context"]["command"], "create")

    def test_retired_candidate_operations_emit_structured_json(self) -> None:
        for arguments, operation in (
            (("create", "--fixture", "FIX-001", "--idempotency-key", "duration-40"), "create"),
            (("retry", "--job-id", "job-0123456789abcdef01234567"), "retry"),
            (("run", "--job-id", "job-0123456789abcdef01234567"), "run"),
            (("verify", "--job-id", "job-0123456789abcdef01234567"), "verify"),
            (("benchmark", "--fixture", "FIX-001"), "benchmark"),
        ):
            result = self.run_cli(
                *arguments,
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["error"]["code"], "legacy_candidate_pipeline_retired")
            self.assertEqual(payload["error"]["context"]["command"], operation)

    def test_doctor_reports_control_only_surface(self) -> None:
        result = self.run_cli("doctor", "--json")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "legacy_control_only")
        self.assertEqual(payload["render_pipeline"], "retired")
        self.assertEqual(payload["canonical_video_entrypoint"], "generate_video.py")
        self.assertEqual(set(payload["retired_commands"]), {"create", "retry", "run", "verify", "benchmark"})
        self.assertNotIn("ffmpeg_available", payload)

    def test_retired_create_ignores_duration_without_creating_state(self) -> None:
        result = self.run_cli("create", "--fixture", "FIX-001", "--idempotency-key", "x", "--duration-seconds", "24")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["error"]["code"], "legacy_candidate_pipeline_retired")
        self.assertFalse((Path(self.temp_dir.name) / "state" / "factory_candidate.sqlite3").exists())

    def test_retired_run_ignores_encoder_and_tts_controls(self) -> None:
        result = self.run_cli("run", "--job-id", "job-0123456789abcdef01234567", "--encoder", "cpu", "--tts", "sapi")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["error"]["context"]["replacement"], "generate_video.py")

    def test_retired_error_envelope_has_no_private_command_arguments(self) -> None:
        result = self.run_cli("verify", "--job-id", "C:/private/voice.wav")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["error"]["code"], "legacy_candidate_pipeline_retired")
        self.assertNotIn("C:/private/voice.wav", result.stdout)

    def test_retired_error_context_names_only_canonical_replacement(self) -> None:
        result = self.run_cli("benchmark", "--fixture", "FIX-001")
        error = json.loads(result.stdout)["error"]
        self.assertEqual(set(error["context"]), {"command", "replacement"})
