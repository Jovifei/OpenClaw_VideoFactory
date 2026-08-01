from __future__ import annotations

import ast
import hashlib
import unittest
from pathlib import Path

from scripts.p1_dry_run_delivery_runner import (
    EVIDENCE_LEVEL,
    JOB_ID_RE,
    RUNNER_SOURCE_SHA256,
    TransportGuard,
    _database_delivery_matches,
    _parse_args,
    _proof_matches,
)


class DryRunDeliveryRunnerTests(unittest.TestCase):
    def test_only_a_job_id_and_json_switch_are_accepted(self) -> None:
        self.assertEqual(
            _parse_args(["--job-id", "job-0123456789abcdef01234567", "--json"]),
            ("job-0123456789abcdef01234567", True),
        )
        for argv in (
            [],
            ["--endpoint", "127.0.0.1"],
            ["--job-id", "job-short"],
            ["--job-id", "job-0123456789abcdef01234567", "--target", "group"],
        ):
            with self.assertRaisesRegex(ValueError, "invalid_arguments"):
                _parse_args(list(argv))

    def test_guard_classifies_and_denies_transport_without_network_io(self) -> None:
        guard = TransportGuard()
        with self.assertRaisesRegex(RuntimeError, "offline_transport_denied"):
            guard("socket.connect", ())
        with self.assertRaisesRegex(RuntimeError, "offline_process_launch_denied"):
            guard("subprocess.Popen", ())
        self.assertEqual(
            guard.proof(),
            {
                "policy": "deny_transport_runtime_v1",
                "socket_events": 1,
                "process_events": 1,
            },
        )

    def test_runner_has_no_transport_or_cli_import(self) -> None:
        runner = Path(__file__).resolve().parents[1] / "scripts" / "p1_dry_run_delivery_runner.py"
        tree = ast.parse(runner.read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in (node.names if isinstance(node, ast.Import) else [node])
            if isinstance(alias, ast.alias)
        }
        self.assertTrue(JOB_ID_RE.fullmatch("job-0123456789abcdef01234567"))
        self.assertFalse({"socket", "subprocess", "requests", "http", "lark"} & imports)

    def test_pending_review_proof_requires_existing_quality_delivery_record(self) -> None:
        job_id = "job-0123456789abcdef01234567"
        manifest = {
            "job_id": job_id,
            "delivery_key": "key",
            "candidate_state": "QUALITY_CHECK",
        }
        valid_record = {
            "job_id": job_id,
            "mode": "dry-run",
            "status": "recorded",
            "manifest": {key: value for key, value in manifest.items() if key != "delivery_key"},
        }
        self.assertTrue(_database_delivery_matches(valid_record, manifest, job_id))
        self.assertFalse(_database_delivery_matches(None, manifest, job_id))
        valid_record["manifest"]["candidate_state"] = "PENDING_REVIEW"
        self.assertFalse(_database_delivery_matches(valid_record, manifest, job_id))

    def test_runner_proof_is_explicitly_local_self_attestation(self) -> None:
        job_id = "job-0123456789abcdef01234567"
        artifacts: list[dict[str, object]] = []
        proof = {
            "schema_version": "1.0",
            "mode": "offline-dry-run",
            "status": "completed",
            "job_id": job_id,
            "delivery_key": hashlib.sha256(
                f"{job_id}|offline-dry-run|v2".encode("utf-8")
            ).hexdigest(),
            "delivery_manifest_sha256": "0" * 64,
            "runner_source_sha256": RUNNER_SOURCE_SHA256,
            "guard": {"policy": "deny_transport_runtime_v1", "socket_events": 0, "process_events": 0},
            "evidence_level": EVIDENCE_LEVEL,
            "artifacts": artifacts,
            "completed_at": "2026-07-30T00:00:00Z",
        }
        self.assertTrue(_proof_matches(proof, job_id=job_id, delivery_manifest_sha256="0" * 64, artifacts=artifacts))
        proof["evidence_level"] = "independent_runner_proof"
        self.assertFalse(_proof_matches(proof, job_id=job_id, delivery_manifest_sha256="0" * 64, artifacts=artifacts))
        proof["evidence_level"] = EVIDENCE_LEVEL
        proof["completed_at"] = "2026-07-30T00:00:00"
        self.assertFalse(_proof_matches(proof, job_id=job_id, delivery_manifest_sha256="0" * 64, artifacts=artifacts))


if __name__ == "__main__":
    unittest.main()
