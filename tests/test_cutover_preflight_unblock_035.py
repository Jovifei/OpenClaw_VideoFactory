import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.migration.inspect_core_feishu_runtime import (
    UNAVAILABLE,
    build_command,
    inspect_core_feishu_runtime,
    inspect_payload,
)
from services.feishu_gateway.credentials import (
    TOKEN_ENVIRONMENT_VARIABLE,
    chained_token_provider,
    environment_token_provider,
)
from services.feishu_gateway.runtime_server import Runtime


class TestCredentialInjection035(unittest.TestCase):
    def runtime(self, directory, **kwargs):
        return Runtime(
            Path(directory) / "status.json",
            Path(directory) / "gateway.jsonl",
            **kwargs,
        )

    def test_missing_token_keeps_preflight_unready(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(
                os.environ,
                {"FEISHU_GATEWAY_CONFIG_FINGERPRINT": "fixture"},
                clear=True,
            ),
        ):
            runtime = self.runtime(
                directory,
                mode="production-preflight",
                rpc_probe=lambda provider: {
                    "status": "rpc_credentials_missing" if provider() is None else "unexpected"
                },
            )
            self.assertEqual("rpc_credentials_missing", runtime.openclaw_rpc)
            self.assertFalse(runtime.ready()["ready"])

    def test_rejected_token_fails_closed_without_logging_value(self):
        credential_value = "fixture-credential-value"
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(
                os.environ,
                {
                    "FEISHU_GATEWAY_CONFIG_FINGERPRINT": "fixture",
                    TOKEN_ENVIRONMENT_VARIABLE: credential_value,
                },
                clear=True,
            ),
        ):
            runtime = self.runtime(
                directory,
                mode="production-preflight",
                rpc_probe=lambda provider: {
                    "status": "rpc_unauthorized" if provider() else "unexpected"
                },
            )
            self.assertFalse(runtime.ready()["ready"])
            evidence = Path(directory, "status.json").read_text(encoding="utf-8") + Path(
                directory, "gateway.jsonl"
            ).read_text(encoding="utf-8")
            self.assertNotIn(credential_value, evidence)

    def test_valid_injected_provider_can_make_rpc_preflight_ready(self):
        credential_value = "fixture-credential-value"
        observed = []

        def probe(provider):
            observed.append(provider())
            return {"status": "reachable"}

        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(
                os.environ,
                {"FEISHU_GATEWAY_CONFIG_FINGERPRINT": "fixture"},
                clear=True,
            ),
        ):
            provider = chained_token_provider([lambda: None, lambda: credential_value])
            runtime = self.runtime(
                directory,
                mode="production-preflight",
                token_provider=provider,
                rpc_probe=probe,
            )
            self.assertEqual([credential_value], observed)
            self.assertTrue(runtime.ready()["ready"])
            self.assertNotIn(
                credential_value,
                Path(directory, "status.json").read_text(encoding="utf-8"),
            )

    def test_offline_mode_never_reads_credentials_or_calls_rpc(self):
        def forbidden():
            raise AssertionError("offline mode accessed a credential")

        with tempfile.TemporaryDirectory() as directory:
            runtime = self.runtime(
                directory,
                mode="offline",
                token_provider=forbidden,
                rpc_probe=lambda _provider: (_ for _ in ()).throw(
                    AssertionError("offline mode called RPC")
                ),
            )
            self.assertEqual("fake_transport", runtime.feishu_connection)
            self.assertEqual("offline_isolated", runtime.openclaw_rpc)
            self.assertFalse(runtime.ready()["ready"])

    def test_production_mode_is_guarded_without_reading_credentials(self):
        def forbidden():
            raise AssertionError("guarded production read a credential")

        with tempfile.TemporaryDirectory() as directory:
            runtime = self.runtime(
                directory,
                mode="production",
                token_provider=forbidden,
                rpc_probe=lambda _provider: (_ for _ in ()).throw(
                    AssertionError("guarded production called RPC")
                ),
            )
            self.assertEqual("production_guarded", runtime.feishu_connection)
            self.assertFalse(runtime.ready()["ready"])

    def test_environment_provider_is_lazy_and_empty_values_are_missing(self):
        environment = {}
        provider = environment_token_provider(environment)
        self.assertIsNone(provider())
        environment[TOKEN_ENVIRONMENT_VARIABLE] = "  fixture-value  "
        self.assertEqual("fixture-value", provider())


class TestCoreRuntimeObserver035(unittest.TestCase):
    @staticmethod
    def payload(account):
        return {"channelAccounts": {"feishu": [account]}}

    def test_explicit_single_consumer_is_healthy(self):
        result = inspect_payload(
            self.payload(
                {
                    "accountId": "zhongshu",
                    "running": True,
                    "consumerCount": 1,
                }
            )
        )
        self.assertEqual(
            ("openclaw_core_feishu", 1, "healthy"),
            (result["owner"], result["consumer_count"], result["runtime_state"]),
        )

    def test_explicit_stopped_runtime_is_stopped(self):
        result = inspect_payload(self.payload({"accountId": "zhongshu", "running": False}))
        self.assertEqual(
            ("none", 0, "stopped"),
            (
                result["owner"],
                result["consumer_count"],
                result["runtime_state"],
            ),
        )

    def test_running_without_explicit_count_is_unavailable(self):
        result = inspect_payload(self.payload({"accountId": "zhongshu", "running": True}))
        self.assertEqual("unknown", result["runtime_state"])
        self.assertEqual(UNAVAILABLE, result["evidence_source"])

    def test_timeout_and_invalid_json_fail_closed(self):
        def timeout(_command):
            raise subprocess.TimeoutExpired("openclaw", 12)

        self.assertEqual(
            UNAVAILABLE,
            inspect_core_feishu_runtime(timeout, executable="openclaw")["evidence_source"],
        )
        invalid = lambda _command: subprocess.CompletedProcess(
            [], 0, stdout="not-json", stderr="sensitive raw output"
        )
        self.assertEqual(
            "unknown",
            inspect_core_feishu_runtime(invalid, executable="openclaw")["runtime_state"],
        )

    def test_probe_command_is_read_only_and_contains_no_credential(self):
        command = build_command("openclaw")
        self.assertEqual("channels.status", command[3])
        self.assertNotIn("channels.stop", command)
        self.assertNotIn("channels.start", command)
        self.assertNotIn(TOKEN_ENVIRONMENT_VARIABLE, " ".join(command))

    def test_live_projection_emits_only_the_five_contract_fields(self):
        payload = self.payload(
            {
                "accountId": "zhongshu",
                "running": True,
                "consumerCount": 1,
            }
        )
        runner = lambda _command: subprocess.CompletedProcess(
            [], 0, stdout=json.dumps(payload), stderr=""
        )
        result = inspect_core_feishu_runtime(runner, executable="openclaw")
        self.assertEqual(
            {
                "owner",
                "consumer_count",
                "runtime_state",
                "evidence_source",
                "confidence",
            },
            set(result),
        )


if __name__ == "__main__":
    unittest.main()
