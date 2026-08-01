import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.migration.final_cutover_precheck import evaluate
from services.feishu_gateway.runtime_server import (
    RPC_AUTH_FAILED,
    PROJECT_GATEWAY_DEVICE_PAIRING_REQUIRED,
    RPC_READY,
    Runtime,
)


SHA256 = "a" * 64


def valid_snapshot(**updates):
    snapshot = {
        "account": "zhongshu",
        "expected_config_sha256": SHA256,
        "observed_config_sha256": SHA256,
        "rpc": {
            "token_present": True,
            "ready": True,
            "rpc_endpoint_available": True,
            "auth_valid": True,
            "session_ready": True,
            "rpc_preflight_result": RPC_READY,
        },
        "core_consumer": {
            "owner": "openclaw_core_feishu",
            "consumer_count": 1,
            "runtime_state": "healthy",
            "confidence": "high",
        },
        "project_gateway": {"running": False},
        "rollback_artifact_exists": True,
        "rollback_control_ready": True,
    }
    snapshot.update(updates)
    return snapshot


class TestRpcPreflight036(unittest.TestCase):
    def runtime(self, directory, **kwargs):
        return Runtime(
            Path(directory) / "status.json",
            Path(directory) / "gateway.jsonl",
            mode="production-preflight",
            **kwargs,
        )

    def test_default_device_auth_requires_pairing_without_reading_shared_token(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"FEISHU_GATEWAY_CONFIG_FINGERPRINT": "fixture"}, clear=True),
        ):
            runtime = self.runtime(
                directory,
                token_provider=lambda: (_ for _ in ()).throw(AssertionError("legacy token read")),
                official_device_probe=lambda: {"status": "device_identity_missing"},
            )
            payload = runtime.ready()
            self.assertEqual(
                PROJECT_GATEWAY_DEVICE_PAIRING_REQUIRED, payload["rpc_preflight_result"]
            )
            self.assertEqual(
                (False, False, False, False, False),
                tuple(
                    payload[field]
                    for field in (
                        "rpc_endpoint_available",
                        "token_present",
                        "auth_valid",
                        "session_ready",
                        "ready",
                    )
                ),
            )

    def test_device_pairing_is_fail_closed_before_health(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"FEISHU_GATEWAY_CONFIG_FINGERPRINT": "fixture"}, clear=True),
        ):
            runtime = self.runtime(
                directory, official_device_probe=lambda: {"status": "pairing_required"}
            )
            self.assertEqual(
                PROJECT_GATEWAY_DEVICE_PAIRING_REQUIRED, runtime.ready()["rpc_preflight_result"]
            )
            self.assertFalse(runtime.ready()["token_present"])
            self.assertFalse(runtime.ready()["auth_valid"])

    def test_unreachable_rpc_fails_closed(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"FEISHU_GATEWAY_CONFIG_FINGERPRINT": "fixture"}, clear=True),
        ):
            runtime = self.runtime(
                directory,
                token_provider=lambda: "fixture-value",
                rpc_probe=lambda _provider: {"status": "rpc_transport_error"},
            )
            payload = runtime.ready()
            self.assertEqual(RPC_AUTH_FAILED, payload["rpc_preflight_result"])
            self.assertFalse(payload["rpc_endpoint_available"])
            self.assertFalse(payload["ready"])

    def test_authenticated_rpc_is_ready_without_logging_token(self):
        fixture_value = "fixture-value"
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"FEISHU_GATEWAY_CONFIG_FINGERPRINT": "fixture"}, clear=True),
        ):
            runtime = self.runtime(
                directory,
                token_provider=lambda: fixture_value,
                rpc_probe=lambda _provider: {
                    "result": RPC_READY,
                    "rpc_endpoint_available": True,
                    "token_present": True,
                    "auth_valid": True,
                    "session_ready": True,
                },
            )
            self.assertTrue(runtime.ready()["ready"])
            evidence = Path(directory, "status.json").read_text(encoding="utf-8") + Path(
                directory, "gateway.jsonl"
            ).read_text(encoding="utf-8")
            self.assertNotIn(fixture_value, evidence)


class TestFinalCutoverPrecheck036(unittest.TestCase):
    def test_consumer_unknown_blocks_cutover(self):
        snapshot = valid_snapshot(
            core_consumer={
                "owner": "unknown",
                "consumer_count": None,
                "runtime_state": "unknown",
                "confidence": "low",
            }
        )
        result = evaluate(snapshot)
        self.assertFalse(result["core_consumer_known"])
        self.assertFalse(result["can_cutover"])

    def test_known_consumer_and_all_gates_pass(self):
        result = evaluate(valid_snapshot())
        self.assertTrue(result["core_consumer_known"])
        self.assertTrue(result["can_cutover"])

    def test_missing_rollback_artifact_blocks_cutover(self):
        result = evaluate(valid_snapshot(rollback_artifact_exists=False))
        self.assertFalse(result["rollback_ready"])
        self.assertFalse(result["can_cutover"])

    def test_wrong_account_is_rejected(self):
        result = evaluate(valid_snapshot(account="other"))
        self.assertFalse(result["can_cutover"])

    def test_wrong_config_hash_is_rejected(self):
        result = evaluate(valid_snapshot(observed_config_sha256="b" * 64))
        self.assertFalse(result["can_cutover"])

    def test_output_has_only_the_required_contract_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot_path = Path(directory) / "snapshot.json"
            snapshot_path.write_text(json.dumps(valid_snapshot()), encoding="utf-8")
            completed = subprocess.run(
                [
                    ".venv/Scripts/python.exe",
                    "scripts/migration/final_cutover_precheck.py",
                    "--snapshot",
                    str(snapshot_path),
                ],
                cwd=Path(__file__).parents[1],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode)
            self.assertEqual(
                {
                    "token_ready",
                    "rpc_ready",
                    "core_consumer_known",
                    "rollback_ready",
                    "gateway_ready",
                    "can_cutover",
                },
                set(json.loads(completed.stdout)),
            )


if __name__ == "__main__":
    unittest.main()
