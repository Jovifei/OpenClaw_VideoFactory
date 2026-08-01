import json
import tempfile
import unittest
from pathlib import Path

from experiments.feishu_gateway_migration.rehearsal_v2 import all_scenarios
from scripts.migration.verify_consumer_state import check as consumer_state
from services.feishu_gateway.rpc_client import OpenClawRpcClient
from services.feishu_gateway.runtime_server import JsonLogger, Runtime


class TestRuntime022(unittest.TestCase):
    def test_health_and_unready_without_verified_transports(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory) / "status.json", Path(directory) / "gateway.jsonl")
            self.assertEqual("running", runtime.payload()["status"])
            self.assertFalse(runtime.ready()["ready"])

    def test_json_logs_hash_identifiers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.jsonl"
            JsonLogger(path).write(
                "info", "event", event_id="event", chat_id="chat", sender_id="sender"
            )
            line = path.read_text(encoding="utf-8")
            self.assertNotIn('chat"', line)
            self.assertEqual(64, len(json.loads(line)["chat_hash"]))

    def test_rpc_blocks_without_verified_transport(self):
        self.assertEqual(
            "rpc_runtime_verification_blocked", OpenClawRpcClient().connection_check()["status"]
        )

    def test_rpc_retries_injected_timeout(self):
        calls = []

        def transport(method, payload, timeout):
            calls.append(method)
            return {"status": "routed"} if len(calls) == 2 else {"error_code": "TIMEOUT"}

        result = OpenClawRpcClient(transport, retries=1).send_message({"text": "test"})
        self.assertEqual("routed", result["status"])
        self.assertEqual(2, result["attempts"])

    def test_consumer_state_and_all_scenarios(self):
        self.assertEqual(
            "pass",
            consumer_state(
                {
                    "connection_owners": ["project_gateway"],
                    "websocket_count": 1,
                    "event_ids": ["e"],
                    "reply_ids": ["r"],
                    "lease": {"owner": "project_gateway", "heartbeat_at": 1},
                    "now": 1,
                }
            )["status"],
        )
        self.assertEqual(6, len(all_scenarios()))
        self.assertEqual("core_restored", all_scenarios()[-1]["recovery"])
