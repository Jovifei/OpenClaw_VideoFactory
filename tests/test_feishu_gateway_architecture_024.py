import inspect
import tempfile
import unittest
from pathlib import Path

from scripts.migration.verify_single_consumer import ConsumerLease, check
from services.feishu_gateway import gateway, service
from services.feishu_gateway.policy import GATEWAY_CAPABILITIES, validate_gateway_rpc_request
from services.feishu_gateway.runtime import GatewayPayloadBuilder


class TestArchitecture024(unittest.TestCase):
    def test_gateway_source_has_no_direct_compute_call(self):
        for module in (gateway, service):
            source = inspect.getsource(module)
            self.assertNotIn("self.analyze", source)
            self.assertNotIn("analyzer_mcp", source)
            self.assertNotIn("subprocess", source)

    def test_capability_matrix_is_least_privilege(self):
        self.assertTrue(
            all(
                GATEWAY_CAPABILITIES[key]
                for key in (
                    "receive_message",
                    "receive_attachment",
                    "verify_identity",
                    "create_openclaw_request",
                    "send_reply",
                )
            )
        )
        self.assertTrue(
            all(
                not GATEWAY_CAPABILITIES[key]
                for key in (
                    "model_call",
                    "analyzer_call",
                    "gpu_task",
                    "filesystem_arbitrary_access",
                    "config_modify",
                    "agent_create",
                )
            )
        )

    def test_privileged_rpc_fields_are_rejected(self):
        payload = GatewayPayloadBuilder.for_text(
            {
                "message_id": "m",
                "tenant_id": "t",
                "chat_id": "c",
                "sender_id": "s",
                "thread_id": "th",
                "text": "x",
            }
        )
        for key in ("analyzer", "model", "gpu", "tool"):
            candidate = {**payload, key: "forbidden"}
            with self.assertRaisesRegex(ValueError, "gateway_rpc_privilege_forbidden"):
                validate_gateway_rpc_request(candidate)

    def test_session_isolates_tenants_and_threads(self):
        first = GatewayPayloadBuilder.for_text(
            {
                "message_id": "m",
                "tenant_id": "t1",
                "chat_id": "c",
                "sender_id": "s",
                "thread_id": "th1",
                "text": "x",
            }
        )["session_key"]
        other_tenant = GatewayPayloadBuilder.for_text(
            {
                "message_id": "m",
                "tenant_id": "t2",
                "chat_id": "c",
                "sender_id": "s",
                "thread_id": "th1",
                "text": "x",
            }
        )["session_key"]
        other_thread = GatewayPayloadBuilder.for_text(
            {
                "message_id": "m",
                "tenant_id": "t1",
                "chat_id": "c",
                "sender_id": "s",
                "thread_id": "th2",
                "text": "x",
            }
        )["session_key"]
        self.assertNotEqual(first, other_tenant)
        self.assertNotEqual(first, other_thread)

    def test_analysis_request_context_has_exact_safe_fields(self):
        payload = GatewayPayloadBuilder.for_analysis_request(
            {
                "event_id": "e",
                "tenant_id": "t",
                "chat_id": "c",
                "operator_id": "s",
                "thread_id": "th",
                "action": "analyze_image",
            },
            {"receipt_path": "receipt.json", "stored_path": "stored.png"},
            "a" * 64,
        )
        self.assertEqual(
            {"action", "receipt_path", "stored_path", "ticket_hash"},
            set(payload["analysis_request"]),
        )
        self.assertIs(validate_gateway_rpc_request(payload), payload)

    def test_default_signature_policy_rejects_ingress(self):
        offline = gateway.OfflineFeishuGateway(
            lambda _: {"status": "quarantined"}, lambda _: {"status": "routed"}
        )
        self.assertEqual(
            "invalid_signature",
            offline.process({"event_id": "e", "type": "im.message.receive_v1", "message": {}})[
                "status"
            ],
        )

    def test_consumer_lease_ownership_heartbeat_and_stale_takeover(self):
        clock = [1.0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "consumer.lock.json"
            binding = ConsumerLease(
                path, "openclaw_binding", now=lambda: clock[0], stale_after_seconds=10
            )
            project = ConsumerLease(
                path, "project_gateway", now=lambda: clock[0], stale_after_seconds=10
            )
            self.assertEqual("consumer_lock_acquired", binding.acquire()["status"])
            self.assertEqual("consumer_lock_held", project.acquire()["status"])
            self.assertEqual("consumer_heartbeat_recorded", binding.heartbeat()["status"])
            clock[0] += 11
            self.assertEqual("consumer_lock_acquired", project.acquire()["status"])

    def test_single_consumer_proof_rejects_overlap_stale_and_duplicates(self):
        good = {
            "connection_owners": ["project_gateway"],
            "websocket_count": 1,
            "event_ids": ["e"],
            "reply_ids": ["r"],
            "lease": {"owner": "project_gateway", "heartbeat_at": 10},
            "now": 10,
        }
        self.assertEqual("pass", check(good)["status"])
        self.assertEqual(
            "fail",
            check({**good, "binding_running": True, "project_gateway_running": True})["status"],
        )
        self.assertEqual(
            "fail",
            check({**good, "lease": {"owner": "project_gateway", "heartbeat_at": -100}})["status"],
        )
        self.assertEqual("fail", check({**good, "event_ids": ["e", "e"]})["status"])
