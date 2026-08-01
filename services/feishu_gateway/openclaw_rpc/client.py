"""Legacy shared-token OpenClaw Gateway v4 client with injectable transport.

It is retained for historical protocol tests only. Production preflight now uses
the official device-auth bridge and must not select this adapter by default.
"""

from __future__ import annotations

import json
import platform
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from ..session import build_session_key

PROTOCOL_VERSION = 4
ADAPTER_VERSION = "0.23.0"
OPERATOR_SCOPES = ("operator.read", "operator.write")
SAFE_CONNECT_ERROR_DETAILS = frozenset(
    {
        "AUTH_TOKEN_MISSING",
        "AUTH_TOKEN_MISMATCH",
        "AUTH_SCOPE_MISMATCH",
        "DEVICE_IDENTITY_REQUIRED",
        "PAIRING_REQUIRED",
        "PROTOCOL_MISMATCH",
    }
)
LEGACY_SHARED_TOKEN_ADAPTER_DISABLED = True


class GatewaySocket(Protocol):
    def send(self, message: str) -> Any: ...
    def recv(self, timeout: float | None = None) -> str: ...
    def close(self) -> Any: ...


SocketFactory = Callable[[str, float], GatewaySocket]
TokenProvider = Callable[[], str | None]


@dataclass(frozen=True)
class OpenClawRpcSettings:
    endpoint: str
    token_provider: TokenProvider | None = None
    timeout_seconds: float = 20.0
    retries: int = 1
    client_id: str = "gateway-client"
    client_mode: str = "backend"
    client_version: str = ADAPTER_VERSION
    platform_name: str = "windows"

    def __post_init__(self) -> None:
        if not self.endpoint.startswith(("ws://", "wss://")):
            raise ValueError("openclaw_rpc_endpoint_invalid")
        if self.timeout_seconds <= 0:
            raise ValueError("openclaw_rpc_timeout_invalid")
        if self.retries < 0:
            raise ValueError("openclaw_rpc_retries_invalid")


class SessionKeyMapper:
    """Produces deterministic, non-reversible keys without exposing Feishu IDs."""

    def __init__(self, agent_id: str = "video-factory") -> None:
        if not agent_id:
            raise ValueError("agent_id_required")
        self.agent_id = agent_id

    def session_key(self, tenant_id: str, chat_id: str, sender_id: str, thread_id: str) -> str:
        return build_session_key(tenant_id, chat_id, sender_id, thread_id, agent_id=self.agent_id)


def _default_socket_factory(endpoint: str, timeout_seconds: float) -> GatewaySocket:
    try:
        from websockets.sync.client import connect
    except ImportError as exc:  # pragma: no cover - asserted by deployment preflight
        raise RuntimeError("openclaw_rpc_websocket_dependency_missing") from exc
    return connect(endpoint, open_timeout=timeout_seconds, close_timeout=timeout_seconds)


class OpenClawGatewayClient:
    """Official v4 wire contract only; unknown methods fail closed."""

    def __init__(
        self,
        settings: OpenClawRpcSettings,
        *,
        socket_factory: SocketFactory | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.settings = settings
        self._socket_factory = socket_factory or _default_socket_factory
        self._clock = clock
        self._socket: GatewaySocket | None = None
        self._hello: dict[str, Any] | None = None

    def connect(self) -> dict[str, Any]:
        if self._socket is not None and self._hello is not None:
            return {"status": "connected", "protocol": self._hello["protocol"]}
        token = self.settings.token_provider() if self.settings.token_provider else None
        if not token:
            return {"status": "rpc_credentials_missing"}
        try:
            self._socket = self._socket_factory(
                self.settings.endpoint, self.settings.timeout_seconds
            )
            if not self._receive_connect_challenge():
                self.close()
                return {"status": "rpc_protocol_error", "error_code": "CONNECT_CHALLENGE_INVALID"}
            request_id = self._send(
                "connect",
                {
                    "minProtocol": PROTOCOL_VERSION,
                    "maxProtocol": PROTOCOL_VERSION,
                    "client": {
                        "id": self.settings.client_id,
                        "version": self.settings.client_version,
                        "platform": self.settings.platform_name or platform.system().lower(),
                        "mode": self.settings.client_mode,
                    },
                    "caps": [],
                    "role": "operator",
                    "scopes": list(OPERATOR_SCOPES),
                    "auth": {"token": token},
                },
            )
            response = self._receive_response(request_id)
        except TimeoutError:
            self.close()
            return {"status": "rpc_timeout"}
        except Exception:
            self.close()
            return {"status": "rpc_transport_error"}
        if not response.get("ok"):
            self.close()
            return self._error_result(response.get("error"))
        payload = response.get("payload")
        if (
            not isinstance(payload, dict)
            or payload.get("type") != "hello-ok"
            or not isinstance(payload.get("protocol"), int)
        ):
            self.close()
            return {"status": "rpc_malformed"}
        self._hello = payload
        return {"status": "connected", "protocol": payload["protocol"]}

    def authenticate(self) -> dict[str, Any]:
        """Authentication is the protocol-required connect handshake."""
        return self.connect()

    def health_check(self) -> dict[str, Any]:
        return self._request("health", {})

    def create_session(
        self, session_key: str, *, agent_id: str = "video-factory"
    ) -> dict[str, Any]:
        return {"status": "rpc_method_not_allowed", "method": "sessions.create"}

    def send_message(
        self,
        message: str,
        session_key: str,
        *,
        agent_id: str = "video-factory",
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        if not message:
            return {"status": "rpc_bad_request", "error_code": "INVALID_REQUEST"}
        if agent_id != "video-factory":
            return {"status": "rpc_forbidden", "error_code": "AGENT_NOT_ALLOWED"}
        return self._request(
            "agent",
            {
                "message": message,
                "agentId": agent_id,
                "sessionKey": session_key,
                "deliver": False,
                "timeout": timeout_seconds or int(self.settings.timeout_seconds),
            },
        )

    def send_attachment_event(self, _event: dict[str, Any]) -> dict[str, Any]:
        """There is no audited attachment-event RPC method in OpenClaw v4."""
        return {"status": "rpc_method_not_available", "method": "attachment_event"}

    def close(self) -> None:
        socket, self._socket, self._hello = self._socket, None, None
        if socket is not None:
            try:
                socket.close()
            except Exception:
                pass

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        attempts = 0
        result: dict[str, Any] = {"status": "rpc_transport_error", "method": method}
        for _ in range(self.settings.retries + 1):
            attempts += 1
            connected = self.connect()
            if connected["status"] != "connected":
                result = {**connected, "method": method, "attempts": attempts}
            else:
                try:
                    response = self._receive_response(self._send(method, params))
                    result = self._result_from_response(response, method, attempts)
                except TimeoutError:
                    result = {"status": "rpc_timeout", "method": method, "attempts": attempts}
                except Exception:
                    result = {
                        "status": "rpc_transport_error",
                        "method": method,
                        "attempts": attempts,
                    }
            if result["status"] not in {"rpc_timeout", "rpc_transport_error", "rpc_network_error"}:
                return result
            self.close()
        return result

    def _send(self, method: str, params: dict[str, Any]) -> str:
        if self._socket is None:
            raise RuntimeError("openclaw_rpc_not_connected")
        request_id = uuid.uuid4().hex
        self._socket.send(
            json.dumps(
                {"type": "req", "id": request_id, "method": method, "params": params},
                separators=(",", ":"),
            )
        )
        return request_id

    def _receive_response(self, request_id: str) -> dict[str, Any]:
        if self._socket is None:
            raise RuntimeError("openclaw_rpc_not_connected")
        deadline = self._clock() + self.settings.timeout_seconds
        while True:
            remaining = deadline - self._clock()
            if remaining <= 0:
                raise TimeoutError("openclaw_rpc_timeout")
            raw = self._socket.recv(timeout=remaining)
            frame = json.loads(raw)
            if (
                isinstance(frame, dict)
                and frame.get("type") == "res"
                and frame.get("id") == request_id
            ):
                return frame

    def _receive_connect_challenge(self) -> bool:
        """Require the server challenge without retaining or exposing its nonce."""
        if self._socket is None:
            raise RuntimeError("openclaw_rpc_not_connected")
        deadline = self._clock() + self.settings.timeout_seconds
        while True:
            remaining = deadline - self._clock()
            if remaining <= 0:
                raise TimeoutError("openclaw_rpc_timeout")
            raw = self._socket.recv(timeout=remaining)
            try:
                frame = json.loads(raw)
            except (TypeError, json.JSONDecodeError):
                return False
            if not isinstance(frame, dict) or frame.get("type") != "event":
                return False
            if frame.get("event") != "connect.challenge":
                continue
            payload = frame.get("payload")
            return (
                isinstance(payload, dict)
                and isinstance(payload.get("nonce"), str)
                and bool(payload["nonce"].strip())
            )

    @staticmethod
    def _error_result(error: Any) -> dict[str, Any]:
        code = error.get("code") if isinstance(error, dict) else ""
        details = error.get("details") if isinstance(error, dict) else None
        detail_code = details.get("code") if isinstance(details, dict) else ""
        statuses = {
            "UNAUTHORIZED": "rpc_unauthorized",
            "FORBIDDEN": "rpc_forbidden",
            "INVALID_REQUEST": "rpc_bad_request",
            "NOT_FOUND": "rpc_not_found",
            "TIMEOUT": "rpc_timeout",
            "NETWORK": "rpc_network_error",
        }
        if detail_code in {"AUTH_TOKEN_MISSING", "AUTH_TOKEN_MISMATCH"}:
            status = "rpc_unauthorized"
        elif detail_code == "PROTOCOL_MISMATCH":
            status = "rpc_protocol_error"
        else:
            status = statuses.get(code, "rpc_gateway_error")
        result = {"status": status, "error_code": code or "UNKNOWN"}
        if detail_code in SAFE_CONNECT_ERROR_DETAILS:
            result["error_detail_code"] = detail_code
        return result

    def _result_from_response(
        self, response: dict[str, Any], method: str, attempts: int
    ) -> dict[str, Any]:
        if not isinstance(response, dict) or not isinstance(response.get("ok"), bool):
            return {"status": "rpc_malformed", "method": method, "attempts": attempts}
        if not response["ok"]:
            return {
                **self._error_result(response.get("error")),
                "method": method,
                "attempts": attempts,
            }
        return {
            "status": "ok",
            "method": method,
            "attempts": attempts,
            "payload": response.get("payload"),
        }
