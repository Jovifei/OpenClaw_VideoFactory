import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

from services.feishu_gateway.service import GatewayState, ProjectFeishuGateway


class TestGateway(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.calls, self.rpc_calls, self.outbound_calls = [], [], []
        self.g = self.gateway()

    def tearDown(self):
        self.tmp.cleanup()

    def gateway(self, *, rpc=None, state_name="state.json"):
        def ingest(payload):
            self.calls.append(payload)
            return {
                "status": "quarantined",
                "detected_kind": "png",
                "receipt_path": "receipt.json",
                "stored_path": "stored.png",
                "stored_sha256": "a" * 64,
            }

        def route(payload):
            self.rpc_calls.append(payload)
            return {"status": "routed"} if rpc is None else rpc(payload)

        return ProjectFeishuGateway(
            state=GatewayState(Path(self.tmp.name) / state_name),
            ingest=ingest,
            rpc=route,
            outbound=lambda payload: self.outbound_calls.append(payload),
            verify_signature=lambda event: event.get("signature") == "sig-ok",
            now=lambda: 1,
        )

    @staticmethod
    def event(
        *,
        event_id="ev_1",
        message_id="om_1",
        sender="ou_1",
        thread="thread_1",
        kind="image",
        signature="sig-ok",
        local_path=True,
    ):
        attachment = {
            "message_id": message_id,
            "file_key": "file_1",
            "filename": "a.png",
            "mime": "image/png",
            "size": 1,
            "media_type": "png",
        }
        if local_path:
            attachment["local_path"] = "E:/in/a.png"
        return {
            "event_id": event_id,
            "message_id": message_id,
            "tenant_id": "tenant_1",
            "chat_id": "oc_1",
            "sender_id": sender,
            "thread_id": thread,
            "message_type": kind,
            "text": "",
            "signature": signature,
            "attachments": [attachment] if kind != "text" else [],
            "timestamp": "t",
        }

    def card(
        self, ticket, *, event_id="card_1", sender="ou_1", thread="thread_1", signature="sig-ok"
    ):
        return {
            "event_id": event_id,
            "operator_id": sender,
            "tenant_id": "tenant_1",
            "chat_id": "oc_1",
            "thread_id": thread,
            "action_namespace": "video_factory",
            "action": "analyze_image",
            "ticket": ticket,
            "signature": signature,
            "timestamp": "t",
        }

    def test_text_routes_once_with_v2_session(self):
        event = self.event(event_id="text_1", message_id="om_text", kind="text")
        event["text"] = "hello"
        self.assertEqual("routed", self.g.message(event)["status"])
        self.assertEqual("duplicate", self.g.message(event)["status"])
        request = self.rpc_calls[0]
        self.assertEqual("video-factory", request["agent_id"])
        self.assertIn(":tenant:", request["session_key"])
        self.assertNotIn("tenant_1", request["session_key"])
        self.assertEqual(1, len(self.rpc_calls))

    def test_signature_is_fail_closed_and_replay_is_rejected(self):
        unsigned = self.event(event_id="unsigned", kind="text")
        unsigned.pop("signature")
        self.assertEqual("invalid_signature", self.g.message(unsigned)["status"])
        self.assertEqual(
            "invalid_signature",
            self.g.message(self.event(event_id="wrong", kind="text", signature="bad"))["status"],
        )
        good = self.event(event_id="good", kind="text")
        self.assertEqual("routed", self.g.message(good)["status"])
        self.assertEqual("duplicate", self.g.message(good)["status"])

    def test_attachment_ingests_and_card_submits_rpc_request_without_compute(self):
        self.assertEqual("quarantined", self.g.message(self.event())["status"])
        self.assertEqual("E:/in/a.png", self.calls[0]["source_media_path"])
        ticket = self.outbound_calls[-1]["ticket"]
        result = self.g.card(self.card(ticket))
        self.assertEqual("routed", result["status"])
        request = self.rpc_calls[-1]
        self.assertEqual(
            {"action", "receipt_path", "stored_path", "ticket_hash"},
            set(request["analysis_request"]),
        )
        self.assertNotIn("analyzer", request)
        self.assertEqual(
            "ticket_invalid", self.g.card(self.card(ticket, event_id="card_replay"))["status"]
        )

    def test_attachment_without_download_is_fail_closed_and_temporary_is_cleaned(self):
        self.assertEqual(
            "attachment_download_failed", self.g.message(self.event(local_path=False))["status"]
        )
        cleaned = []
        self.g.download, self.g.cleanup = lambda _: "E:/tmp/a.png", cleaned.append
        self.assertEqual(
            "quarantined",
            self.g.message(self.event(event_id="download", local_path=False))["status"],
        )
        self.assertEqual(["E:/tmp/a.png"], cleaned)

    def test_rpc_timeout_is_not_deduped(self):
        attempts = []
        self.g = self.gateway(
            rpc=lambda payload: attempts.append(payload) or {"status": "rpc_timeout"}
        )
        event = self.event(event_id="retry", kind="text")
        self.assertEqual("rpc_timeout", self.g.message(event)["status"])
        self.g.rpc = lambda payload: attempts.append(payload) or {"status": "routed"}
        self.assertEqual("routed", self.g.message(event)["status"])
        self.assertEqual(2, len(attempts))

    def test_card_signature_identity_and_thread_are_bound(self):
        self.g.message(self.event())
        ticket = self.outbound_calls[-1]["ticket"]
        self.assertEqual(
            "invalid_signature", self.g.card(self.card(ticket, signature="bad"))["status"]
        )
        self.assertEqual(
            "ticket_identity_mismatch", self.g.card(self.card(ticket, sender="ou_2"))["status"]
        )
        self.assertEqual(
            "ticket_identity_mismatch", self.g.card(self.card(ticket, thread="thread_2"))["status"]
        )
        self.assertEqual("routed", self.g.card(self.card(ticket))["status"])

    def test_state_hashes_all_subjects(self):
        self.g.message(self.event())
        state = json.loads((Path(self.tmp.name) / "state.json").read_text(encoding="utf-8"))
        ticket = next(iter(state["tickets"].values()))
        for value in state["seen"] + [
            ticket[key] for key in ("tenant", "chat", "sender", "thread")
        ]:
            self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", value))
        self.assertEqual(hashlib.sha256("tenant_1".encode()).hexdigest(), ticket["tenant"])
