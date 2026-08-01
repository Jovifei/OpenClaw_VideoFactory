import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.migration.inspect_zhongshu_consumer import inspect
from scripts.migration.verify_zhongshu_single_consumer import check as single_check
from scripts.migration.verify_zhongshu_zero_consumer import check as zero_check
from services.feishu_gateway.runtime import GatewaySettings
from services.feishu_gateway.runtime_server import Runtime


NOW = "2026-07-23T00:00:10+00:00"


def observation(
    owner="none", consumers=0, connections=0, source="operator_verified_no_consumer", **extra
):
    item = {
        "source": source,
        "explicit": True,
        "binding_owner": owner,
        "consumer_count": consumers,
        "feishu_connection_count": connections,
    }
    item.update(extra)
    return {"account": "zhongshu", "observations": [item]}


def zero_samples(observed=None):
    observed = observed or observation()
    return {
        "samples": [
            {"sampled_at": "2026-07-23T00:00:00+00:00", "observation": observed},
            {"sampled_at": "2026-07-23T00:00:05+00:00", "observation": observed},
            {"sampled_at": "2026-07-23T00:00:10+00:00", "observation": observed},
        ]
    }


def single_snapshot(**extra):
    value = {
        "binding_owner": "project_gateway",
        "consumer_count": 1,
        "feishu_connection_count": 1,
        "core_binding_state": "stopped",
        "core_feishu_connection_count": 0,
        "owner_pid": 42,
        "lease_owner_pid": 42,
        "last_heartbeat_at": "2026-07-23T00:00:00+00:00",
        "observed_at": NOW,
        "other_owner_event_count": 0,
        "duplicate_reply_count": 0,
    }
    value.update(extra)
    return value


class ConsumerInspector031Tests(unittest.TestCase):
    def test_empty_snapshot_is_unknown(self):
        self.assertEqual("unknown", inspect({})["status"])

    def test_account_mismatch_is_unknown(self):
        self.assertIn(
            "account_not_zhongshu",
            inspect({"account": "other", "observations": []})["blocking_reasons"],
        )

    def test_explicit_core_consumer_is_healthy(self):
        result = inspect(
            observation(
                "core_feishu", 1, 1, "core_feishu_runtime", owner_pid=7, last_heartbeat_at=NOW
            )
        )
        self.assertEqual("healthy", result["status"])
        self.assertEqual("core_feishu", result["binding_owner"])

    def test_explicit_project_consumer_is_healthy(self):
        result = inspect(
            observation(
                "project_gateway",
                1,
                1,
                "project_gateway_runtime",
                owner_pid=8,
                last_heartbeat_at=NOW,
            )
        )
        self.assertEqual("project_gateway", result["binding_owner"])

    def test_explicit_none_is_stopped(self):
        self.assertEqual("stopped", inspect(observation())["status"])

    def test_conflicting_owner_is_unknown(self):
        value = observation(
            "core_feishu", 1, 1, "core_feishu_runtime", owner_pid=7, last_heartbeat_at=NOW
        )
        value["observations"].append(
            {
                "source": "project_gateway_runtime",
                "explicit": True,
                "binding_owner": "project_gateway",
                "consumer_count": 1,
                "feishu_connection_count": 1,
                "owner_pid": 8,
                "last_heartbeat_at": NOW,
            }
        )
        self.assertEqual("unknown", inspect(value)["status"])

    def test_non_integer_count_is_unknown(self):
        self.assertEqual("unknown", inspect(observation(consumers="0"))["status"])

    def test_none_owner_with_connection_is_not_stopped(self):
        self.assertEqual("unknown", inspect(observation(connections=1))["status"])

    def test_consumer_count_two_is_unhealthy(self):
        result = inspect(
            observation(
                "core_feishu", 2, 1, "core_feishu_runtime", owner_pid=7, last_heartbeat_at=NOW
            )
        )
        self.assertEqual("unhealthy", result["status"])

    def test_secret_named_field_is_rejected(self):
        value = observation()
        value["token"] = "fixture-only"
        self.assertEqual("unknown", inspect(value)["status"])


class ZeroConsumer031Tests(unittest.TestCase):
    def test_three_explicit_samples_prove_zero(self):
        self.assertEqual("ZERO_CONSUMER_PROVEN", zero_check(zero_samples())["status"])

    def test_unknown_sample_fails_closed(self):
        self.assertEqual(
            "ZERO_CONSUMER_NOT_PROVEN",
            zero_check(zero_samples({"account": "zhongshu", "observations": []}))["status"],
        )

    def test_live_consumer_fails_closed(self):
        self.assertEqual(
            "ZERO_CONSUMER_NOT_PROVEN",
            zero_check(
                zero_samples(
                    observation(
                        "core_feishu",
                        1,
                        1,
                        "core_feishu_runtime",
                        owner_pid=7,
                        last_heartbeat_at=NOW,
                    )
                )
            )["status"],
        )

    def test_connection_without_consumer_fails_closed(self):
        self.assertEqual(
            "ZERO_CONSUMER_NOT_PROVEN",
            zero_check(zero_samples(observation(connections=1)))["status"],
        )

    def test_short_interval_fails_closed(self):
        value = zero_samples()
        value["samples"][1]["sampled_at"] = "2026-07-23T00:00:04+00:00"
        self.assertEqual("ZERO_CONSUMER_NOT_PROVEN", zero_check(value)["status"])

    def test_short_window_fails_closed(self):
        value = zero_samples()
        value["samples"][2]["sampled_at"] = "2026-07-23T00:00:09+00:00"
        self.assertEqual("ZERO_CONSUMER_NOT_PROVEN", zero_check(value)["status"])

    def test_three_samples_required(self):
        self.assertEqual(
            "ZERO_CONSUMER_NOT_PROVEN",
            zero_check({"samples": zero_samples()["samples"][:2]})["status"],
        )

    def test_direct_observation_with_token_is_rejected(self):
        direct = {
            "status": "stopped",
            "binding_owner": "none",
            "consumer_count": 0,
            "feishu_connection_count": 0,
            "token": "fixture-only",
        }
        self.assertEqual("ZERO_CONSUMER_NOT_PROVEN", zero_check(zero_samples(direct))["status"])


class SingleConsumer031Tests(unittest.TestCase):
    def test_valid_project_owner_passes(self):
        self.assertEqual("SINGLE_CONSUMER_PROVEN", single_check(single_snapshot())["status"])

    def test_core_binding_must_be_stopped(self):
        self.assertEqual(
            "SINGLE_CONSUMER_NOT_PROVEN",
            single_check(single_snapshot(core_binding_state="running"))["status"],
        )

    def test_lease_must_match_pid(self):
        self.assertEqual(
            "SINGLE_CONSUMER_NOT_PROVEN",
            single_check(single_snapshot(lease_owner_pid=99))["status"],
        )

    def test_heartbeat_must_be_fresh(self):
        self.assertEqual(
            "SINGLE_CONSUMER_NOT_PROVEN",
            single_check(single_snapshot(last_heartbeat_at="2026-07-22T23:58:00+00:00"))["status"],
        )

    def test_other_owner_event_fails_closed(self):
        self.assertEqual(
            "SINGLE_CONSUMER_NOT_PROVEN",
            single_check(single_snapshot(other_owner_event_count=1))["status"],
        )

    def test_duplicate_reply_fails_closed(self):
        self.assertEqual(
            "SINGLE_CONSUMER_NOT_PROVEN",
            single_check(single_snapshot(duplicate_reply_count=1))["status"],
        )

    def test_wrong_owner_fails_closed(self):
        self.assertEqual(
            "SINGLE_CONSUMER_NOT_PROVEN",
            single_check(single_snapshot(binding_owner="core_feishu"))["status"],
        )

    def test_token_named_field_is_rejected(self):
        self.assertEqual(
            "SINGLE_CONSUMER_NOT_PROVEN",
            single_check(single_snapshot(token="fixture-only"))["status"],
        )


class RuntimeSafety031Tests(unittest.TestCase):
    def test_verifiers_have_no_live_control_import(self):
        root = Path(__file__).parents[1]
        source = "\n".join(
            (root / "scripts" / "migration" / name).read_text(encoding="utf-8")
            for name in (
                "inspect_zhongshu_consumer.py",
                "verify_zhongshu_zero_consumer.py",
                "verify_zhongshu_single_consumer.py",
            )
        )
        for forbidden in (
            "import subprocess",
            "from subprocess",
            "import socket",
            "from socket",
            "import requests",
            "from requests",
            "subprocess.",
            "socket.",
            "requests.",
            "openclaw config",
            "openclaw gateway",
            "Start-Process",
        ):
            self.assertNotIn(forbidden, source)

    def test_missing_environment_credentials_fail_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "gateway_runtime_secrets_missing"):
                GatewaySettings.from_env()

    def test_offline_ready_is_false_without_live_connections(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            runtime = Runtime(Path(directory) / "status.json", Path(directory) / "gateway.jsonl")
            self.assertFalse(runtime.ready()["ready"])
            self.assertEqual("fake_transport", runtime.ready()["feishu_connection"])

    def test_offline_launcher_has_no_token_argument(self):
        source = (
            Path(__file__).parents[1] / "scripts" / "feishu_gateway" / "start_gateway.ps1"
        ).read_text(encoding="utf-8")
        launch_arguments = source.split("$launchArguments = @(", 1)[1].split(")\n$process", 1)[0]
        self.assertNotIn("OPENCLAW_GATEWAY_TOKEN", launch_arguments)
        self.assertNotIn("--token", launch_arguments)

    def test_rollback_script_is_simulation_only(self):
        source = (
            Path(__file__).parents[1] / "scripts" / "migration" / "rollback_gateway.ps1"
        ).read_text(encoding="utf-8")
        self.assertIn("only -Simulate is available in P0", source)


if __name__ == "__main__":
    unittest.main()
