import unittest

from services.feishu_gateway.runtime import (
    GatewayLifecycle,
    GatewayPayloadBuilder,
    GatewayRpcContract,
    RpcBridge,
    map_error_code,
    normalize_status,
)


class FakeCaller:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, method, payload, timeout_seconds):
        self.calls.append(
            {"method": method, "payload": payload, "timeout_seconds": timeout_seconds}
        )
        if not self.responses:
            return {"status": "routed"}
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class TestRuntimeBridge(unittest.TestCase):
    def test_payload_builder_matches_contract(self):
        event = {
            "message_id": "m1",
            "tenant_id": "t1",
            "chat_id": "c1",
            "sender_id": "u1",
            "thread_id": "th1",
            "text": "hi",
        }
        payload = GatewayPayloadBuilder.for_text(event)
        self.assertEqual("video-factory", payload["agent_id"])
        self.assertIn(":tenant:", payload["session_key"])
        self.assertNotIn("c1", payload["session_key"])
        self.assertEqual(
            {
                "agent_id",
                "session_key",
                "message_id",
                "tenant_id",
                "chat_id",
                "sender_id",
                "thread_id",
                "text",
            },
            set(GatewayRpcContract.request_fields),
        )

    def test_payload_builder_rejects_incomplete_event(self):
        self.assertRaises(
            ValueError, GatewayPayloadBuilder.for_text, {"chat_id": "c1", "sender_id": "u1"}
        )

    def test_bridge_retries_until_success(self):
        caller = FakeCaller(
            [
                {"status": "rpc_timeout", "error": "timeout"},
                {"status": "routed", "request_id": "r2"},
            ]
        )
        bridge = RpcBridge(caller, retries=1, contract=GatewayRpcContract(timeout_seconds=20))
        result = bridge.route_text(
            GatewayPayloadBuilder.for_text(
                {
                    "message_id": "m",
                    "tenant_id": "t",
                    "chat_id": "c",
                    "sender_id": "s",
                    "thread_id": "th",
                    "text": "hi",
                }
            )
        )
        self.assertEqual("routed", result["status"])
        self.assertEqual(2, len(caller.calls))
        self.assertEqual("agent", result["rpc_method"])

    def test_bridge_returns_transport_error(self):
        def fail(method, payload, timeout):  # type: ignore[override]
            raise RuntimeError("socket down")

        bridge = RpcBridge(fail, retries=0, contract=GatewayRpcContract(timeout_seconds=20))
        result = bridge.route_text(
            GatewayPayloadBuilder.for_text(
                {
                    "message_id": "m",
                    "tenant_id": "t",
                    "chat_id": "c",
                    "sender_id": "s",
                    "thread_id": "th",
                    "text": "hi",
                }
            )
        )
        self.assertEqual("rpc_transport_error", result["status"])

    def test_bridge_rejects_privileged_request(self):
        payload = GatewayPayloadBuilder.for_text(
            {
                "message_id": "m",
                "tenant_id": "t",
                "chat_id": "c",
                "sender_id": "s",
                "thread_id": "th",
                "text": "hi",
            }
        )
        payload["model"] = "forbidden"
        self.assertEqual("rpc_forbidden", RpcBridge(FakeCaller([])).route_text(payload)["status"])

    def test_bridge_maps_error_codes(self):
        mapped = map_error_code(
            {"status": "failed", "error_code": "UNAUTHORIZED", "error": "denied"}
        )
        self.assertEqual("rpc_unauthorized", mapped["status"])
        self.assertEqual("UNAUTHORIZED", mapped["error_code"])

    def test_bridge_normalizes_non_dict_result(self):
        self.assertEqual("rpc_malformed", normalize_status("bad", "rpc_unknown")["status"])

    def test_lifecycle_start_heartbeat_reconnect_shutdown(self):
        calls = []
        lifecycle = GatewayLifecycle(
            lambda: calls.append("connect"), lambda: calls.append("disconnect"), now=lambda: 7
        )
        self.assertEqual("running", lifecycle.startup()["status"])
        self.assertEqual("healthy", lifecycle.heartbeat()["status"])
        self.assertEqual("reconnected", lifecycle.reconnect()["status"])
        self.assertEqual("stopped", lifecycle.shutdown()["status"])
        self.assertEqual(["connect", "disconnect", "connect", "disconnect"], calls)


if __name__ == "__main__":
    unittest.main()
