import sys
import unittest
from pathlib import Path

from services.feishu_gateway.gateway import OfflineFeishuGateway


class FakeServices:
    def __init__(self):
        self.ingest_calls, self.rpc_calls = [], []

    def ingest(self, args):
        self.ingest_calls.append(args)
        kind = {"image/png": "png", "audio/wav": "wav", "video/mp4": "mp4", "text/plain": "txt"}[
            args["content_type"]
        ]
        return {
            "status": "quarantined",
            "quarantined": True,
            "content_parsed": False,
            "detected_kind": kind,
            "receipt_path": f"E:/isolated/receipt/{args['message_id']}.json",
            "stored_path": f"E:/isolated/store/{args['message_id']}.{kind}",
            "stored_sha256": "a" * 64,
        }

    def rpc(self, args):
        self.rpc_calls.append(args)
        return {"status": "routed"}


def message(
    event_id,
    kind="text",
    content_type="text/plain",
    *,
    sender="ou_user",
    thread="thread_1",
    signature="sig-ok",
):
    value = {
        "message_id": "om_msg",
        "tenant_id": "tenant",
        "chat_id": "oc_group",
        "sender_id": sender,
        "thread_id": thread,
        "message_type": kind,
        "text": "hello",
    }
    if kind != "text":
        value["attachment"] = {
            "index": 0,
            "local_path": "E:/isolated-inbound/file",
            "name": "fixture",
            "content_type": content_type,
        }
    return {
        "event_id": event_id,
        "type": "im.message.receive_v1",
        "message": value,
        "signature": signature,
    }


class GatewayPocTests(unittest.TestCase):
    def setUp(self):
        self.fakes, self.clock = FakeServices(), [1000.0]
        self.gateway = OfflineFeishuGateway(
            self.fakes.ingest,
            self.fakes.rpc,
            now=lambda: self.clock[0],
            verify_signature=lambda event: event.get("signature") == "sig-ok",
        )

    def ticket_for(self, event_id, content_type):
        return self.gateway.process(message(event_id, "file", content_type))["card"]["ticket"]

    def callback(
        self,
        event_id,
        token,
        action,
        *,
        operator="ou_user",
        chat="oc_group",
        tenant="tenant",
        thread="thread_1",
        signature="sig-ok",
    ):
        return self.gateway.process(
            {
                "event_id": event_id,
                "type": "card.action.trigger",
                "signature": signature,
                "callback": {
                    "operator": operator,
                    "tenant_id": tenant,
                    "open_chat_id": chat,
                    "thread_id": thread,
                    "action": action,
                    "ticket": token,
                },
            }
        )

    def test_text_routes_once_with_isolated_session(self):
        self.assertEqual("routed", self.gateway.process(message("evt-text"))["status"])
        key = self.fakes.rpc_calls[0]["session_key"]
        self.assertIn(":tenant:", key)
        self.assertNotIn("oc_group", key)
        self.assertEqual("duplicate", self.gateway.process(message("evt-text"))["status"])

    def test_all_media_is_ingress_only_until_card(self):
        for index, content_type in enumerate(("text/plain", "image/png", "audio/wav", "video/mp4")):
            self.assertEqual(
                "quarantined",
                self.gateway.process(message(f"evt-in-{index}", "file", content_type))["status"],
            )
        self.assertEqual([], self.fakes.rpc_calls)

    def test_cards_submit_bounded_orchestration_request(self):
        for index, (content_type, action) in enumerate(
            (
                ("image/png", "analyze_image"),
                ("audio/wav", "transcribe_audio"),
                ("video/mp4", "analyze_video"),
            )
        ):
            self.assertEqual(
                "routed",
                self.callback(
                    f"evt-card-{index}", self.ticket_for(f"evt-media-{index}", content_type), action
                )["status"],
            )
        self.assertEqual(3, len(self.fakes.rpc_calls))
        for request in self.fakes.rpc_calls:
            self.assertEqual(
                {"action", "receipt_path", "stored_path", "ticket_hash"},
                set(request["analysis_request"]),
            )
            self.assertNotIn("analyzer", request)

    def test_signature_ticket_and_replay_are_fail_closed(self):
        self.assertEqual(
            "invalid_signature",
            self.gateway.process(message("unsigned", signature="bad"))["status"],
        )
        token = self.ticket_for("evt-image", "image/png")
        self.assertEqual(
            "rejected",
            self.callback("bad-op", token, "analyze_image", operator="ou_other")["status"],
        )
        self.assertEqual("routed", self.callback("good", token, "analyze_image")["status"])
        self.assertEqual("rejected", self.callback("replay", token, "analyze_image")["status"])

    def test_expiry_reconnect_and_restore(self):
        token = self.ticket_for("evt-expire", "image/png")
        self.clock[0] += 121
        self.assertEqual("rejected", self.callback("expired", token, "analyze_image")["status"])
        snapshot = self.gateway.snapshot()
        restored = OfflineFeishuGateway.restore(
            snapshot,
            ingest=self.fakes.ingest,
            rpc=self.fakes.rpc,
            now=lambda: self.clock[0],
            verify_signature=lambda event: event.get("signature") == "sig-ok",
        )
        self.assertEqual(
            "reconnected",
            restored.process({"event_id": "reconnect", "type": "system.reconnected"})["status"],
        )

    def test_existing_mcp_contracts_remain_outside_gateway(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        from analyzer_mcp import TOOLS
        from mcp_ingest_attachment import TOOL_SCHEMA

        self.assertTrue(
            {"message_id", "source_media_path", "chat_id", "sender_id"}.issubset(
                TOOL_SCHEMA["inputSchema"]["required"]
            )
        )
        self.assertEqual(
            {"job_id", "receipt_path", "stored_path", "analysis_policy"},
            set(TOOLS[0]["inputSchema"]["required"]),
        )
