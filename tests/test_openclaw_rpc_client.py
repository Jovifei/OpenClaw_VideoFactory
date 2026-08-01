import json
import unittest

from services.feishu_gateway.openclaw_rpc.client import (
    OpenClawGatewayClient,
    OpenClawRpcSettings,
    SessionKeyMapper,
)
from services.feishu_gateway.runtime import GatewayLifecycle


def response(request, *, ok=True, payload=None, error=None):
    frame = {"type": "res", "id": request["id"], "ok": ok}
    if ok:
        frame["payload"] = payload
    else:
        frame["error"] = error
    return json.dumps(frame)


def hello(request):
    return response(
        request,
        payload={
            "type": "hello-ok",
            "protocol": 4,
            "server": {"version": "test", "connId": "test"},
            "features": {"methods": ["health", "agent", "sessions.create"], "events": []},
            "snapshot": {},
            "auth": {"role": "operator", "scopes": []},
        },
    )


def challenge(nonce="test-nonce"):
    return json.dumps({"type": "event", "event": "connect.challenge", "payload": {"nonce": nonce}})


class FakeSocket:
    def __init__(self, handler):
        self.handler, self.sent, self.incoming, self.closed = handler, [], [challenge()], False

    def send(self, raw):
        request = json.loads(raw)
        self.sent.append(request)
        self.incoming.extend(self.handler(request))

    def recv(self, timeout=None):
        if not self.incoming:
            raise TimeoutError()
        item = self.incoming.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def close(self):
        self.closed = True


class TestOpenClawGatewayClient(unittest.TestCase):
    def make_client(self, *handlers):
        sockets = [FakeSocket(handler) for handler in handlers]
        return OpenClawGatewayClient(
            OpenClawRpcSettings(
                "ws://127.0.0.1:18789",
                token_provider=lambda: "fake-token",
                retries=len(sockets) - 1,
            ),
            socket_factory=lambda _url, _timeout: sockets.pop(0),
        )

    def test_connect_and_health(self):
        seen = []

        def handler(request):
            seen.append(request)
            return (
                [hello(request)]
                if request["method"] == "connect"
                else [response(request, payload={"ok": True})]
            )

        client = self.make_client(handler)
        self.assertEqual("connected", client.connect()["status"])
        self.assertEqual("ok", client.health_check()["status"])
        connect = seen[0]
        self.assertEqual(
            ("operator", ["operator.read", "operator.write"], []),
            (connect["params"]["role"], connect["params"]["scopes"], connect["params"]["caps"]),
        )

    def test_gateway_lifecycle_starts_without_live_feishu(self):
        calls = []
        lifecycle = GatewayLifecycle(
            lambda: calls.append("connect"), lambda: calls.append("disconnect")
        )
        self.assertEqual("running", lifecycle.startup()["status"])
        self.assertEqual(["connect"], calls)

    def test_authentication_failure_is_mapped(self):
        client = self.make_client(
            lambda request: [response(request, ok=False, error={"code": "UNAUTHORIZED"})]
        )
        self.assertEqual("rpc_unauthorized", client.authenticate()["status"])

    def test_invalid_connect_challenge_fails_closed(self):
        socket = FakeSocket(lambda request: [hello(request)])
        socket.incoming = [
            json.dumps({"type": "event", "event": "connect.challenge", "payload": {}})
        ]
        client = OpenClawGatewayClient(
            OpenClawRpcSettings("ws://127.0.0.1:18789", token_provider=lambda: "fake-token"),
            socket_factory=lambda _url, _timeout: socket,
        )
        result = client.authenticate()
        self.assertEqual(
            ("rpc_protocol_error", "CONNECT_CHALLENGE_INVALID"),
            (result["status"], result["error_code"]),
        )
        self.assertEqual([], socket.sent)

    def test_connect_error_detail_is_classified_without_message(self):
        fixture_token = "fixture-token-must-not-appear"
        client = self.make_client(
            lambda request: [
                response(
                    request,
                    ok=False,
                    error={
                        "code": "INVALID_REQUEST",
                        "message": "gateway token mismatch: " + fixture_token,
                        "details": {"code": "AUTH_TOKEN_MISMATCH"},
                    },
                )
            ]
        )
        result = client.authenticate()
        self.assertEqual(
            ("rpc_unauthorized", "INVALID_REQUEST", "AUTH_TOKEN_MISMATCH"),
            (result["status"], result["error_code"], result["error_detail_code"]),
        )
        self.assertNotIn(fixture_token, json.dumps(result))

    def test_timeout_reconnects_and_retries(self):
        first = lambda request: (
            [hello(request)] if request["method"] == "connect" else [TimeoutError()]
        )
        second = lambda request: (
            [hello(request)]
            if request["method"] == "connect"
            else [response(request, payload={"ok": True})]
        )
        client = self.make_client(first, second)
        result = client.health_check()
        self.assertEqual(("ok", 2), (result["status"], result["attempts"]))

    def test_session_creation_is_forbidden_and_message_reply_is_received(self):
        seen = []

        def handler(request):
            seen.append(request)
            if request["method"] == "connect":
                return [hello(request)]
            return [
                json.dumps({"type": "event", "event": "agent"}),
                response(request, payload={"reply": "fake reply"}),
            ]

        client = self.make_client(handler)
        self.assertEqual(
            "rpc_method_not_allowed",
            client.create_session("agent:video-factory:feishu:a:b")["status"],
        )
        sent = client.send_message(
            "test", "agent:video-factory:feishu:tenant:a:chat:b:sender:c:thread:d"
        )
        self.assertEqual("fake reply", sent["payload"]["reply"])
        agent = [item for item in seen if item["method"] == "agent"][0]
        self.assertFalse(agent["params"]["deliver"])

    def test_agent_escalation_is_rejected(self):
        client = OpenClawGatewayClient(OpenClawRpcSettings("ws://127.0.0.1:18789"))
        self.assertEqual(
            "rpc_forbidden", client.send_message("test", "key", agent_id="another-agent")["status"]
        )

    def test_attachment_event_is_not_invented(self):
        client = OpenClawGatewayClient(OpenClawRpcSettings("ws://127.0.0.1:18789"))
        self.assertEqual("rpc_method_not_available", client.send_attachment_event({})["status"])

    def test_session_mapping_is_stable_and_isolates_users(self):
        mapper = SessionKeyMapper()
        first = mapper.session_key("tenant", "chat", "user-a", "thread-a")
        self.assertEqual(first, mapper.session_key("tenant", "chat", "user-a", "thread-a"))
        self.assertNotEqual(first, mapper.session_key("tenant", "chat", "user-b", "thread-a"))
        self.assertNotEqual(first, mapper.session_key("tenant", "chat", "user-a", "thread-b"))
        self.assertNotIn("user-a", first)

    def test_missing_credentials_fail_closed(self):
        client = OpenClawGatewayClient(OpenClawRpcSettings("ws://127.0.0.1:18789"))
        self.assertEqual("rpc_credentials_missing", client.health_check()["status"])
