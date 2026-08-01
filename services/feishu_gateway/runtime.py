"""Fail-closed runtime boundaries; no network starts at import time."""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from typing import Any, Callable

from .policy import validate_gateway_rpc_request
from .session import build_session_key


def masked_digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]


@dataclass(frozen=True)
class GatewaySettings:
    app_id: str
    app_secret: str
    rpc_url: str
    rpc_token: str
    timeout_seconds: int = 20
    retries: int = 1

    @classmethod
    def from_env(cls) -> "GatewaySettings":
        values = {
            key: os.environ.get(key, "")
            for key in (
                "FEISHU_APP_ID",
                "FEISHU_APP_SECRET",
                "OPENCLAW_GATEWAY_URL",
                "OPENCLAW_GATEWAY_TOKEN",
            )
        }
        if not all(values.values()):
            raise RuntimeError("gateway_runtime_secrets_missing")
        return cls(
            values["FEISHU_APP_ID"],
            values["FEISHU_APP_SECRET"],
            values["OPENCLAW_GATEWAY_URL"],
            values["OPENCLAW_GATEWAY_TOKEN"],
        )


@dataclass(frozen=True)
class GatewayRpcContract:
    rpc_method: str = "agent"
    timeout_seconds: int = 20
    request_fields: tuple[str, ...] = (
        "agent_id",
        "session_key",
        "message_id",
        "tenant_id",
        "chat_id",
        "sender_id",
        "thread_id",
        "text",
    )
    success_status: str = "routed"
    timeout_status: str = "rpc_timeout"


def normalize_status(result: dict[str, Any], fallback_status: str) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {"status": "rpc_malformed", "error": "non_dict_result"}
    status = result.get("status", fallback_status)
    return (
        {"status": str(status), **{key: value for key, value in result.items() if key != "status"}}
        if status is not None
        else {"status": "rpc_malformed", "error": "missing_status"}
    )


def map_error_code(result: dict[str, Any]) -> dict[str, Any]:
    code = result.get("error_code") or result.get("code") or ""
    normalized = normalize_status(result, "rpc_unknown_error")
    mapping = {
        "UNAUTHORIZED": "rpc_unauthorized",
        "BAD_REQUEST": "rpc_bad_request",
        "FORBIDDEN": "rpc_forbidden",
        "NOT_FOUND": "rpc_not_found",
        "TIMEOUT": "rpc_timeout",
        "NETWORK": "rpc_network_error",
    }
    if code:
        normalized.update(
            status=mapping.get(code, "rpc_error"),
            error_code=code,
            error=result.get("error") or "openclaw_gateway_error",
        )
    return normalized


class RpcBridge:
    """Gateway may submit only a least-privilege video-factory request."""

    def __init__(
        self,
        call: Callable[[str, dict[str, Any], int], dict[str, Any]],
        retries: int = 1,
        contract: GatewayRpcContract = GatewayRpcContract(),
    ):
        self.call, self.retries, self.contract = call, retries, contract

    def route_text(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            validate_gateway_rpc_request(payload)
        except ValueError as exc:
            return {
                "status": "rpc_forbidden",
                "error": str(exc),
                "rpc_method": self.contract.rpc_method,
                "attempts": 0,
            }
        normalized: dict[str, Any] = {"status": "rpc_malformed", "error": "not_started"}
        for attempt in range(1, self.retries + 2):
            try:
                raw = self.call(self.contract.rpc_method, payload, self.contract.timeout_seconds)
            except Exception:
                raw = {"status": "rpc_transport_error", "error": "transport_error"}
            normalized = map_error_code(normalize_status(raw, self.contract.timeout_status))
            normalized["attempts"] = attempt
            if normalized["status"] != self.contract.timeout_status:
                normalized["rpc_method"] = self.contract.rpc_method
                return normalized
        normalized["rpc_method"] = self.contract.rpc_method
        return normalized


class GatewayPayloadBuilder:
    @staticmethod
    def _identity(event: dict[str, Any]) -> dict[str, str]:
        fields = ("message_id", "tenant_id", "chat_id", "sender_id", "thread_id")
        missing = [field for field in fields if not event.get(field)]
        if missing:
            raise ValueError(f"gateway_payload_incomplete:{','.join(missing)}")
        return {field: str(event[field]) for field in fields}

    @classmethod
    def for_text(cls, event: dict[str, Any], agent_id: str = "video-factory") -> dict[str, Any]:
        identity = cls._identity(event)
        return {
            "agent_id": agent_id,
            "session_key": build_session_key(
                identity["tenant_id"],
                identity["chat_id"],
                identity["sender_id"],
                identity["thread_id"],
                agent_id=agent_id,
            ),
            **identity,
            "text": str(event.get("text", "")),
        }

    @classmethod
    def for_analysis_request(
        cls,
        event: dict[str, Any],
        receipt: dict[str, Any],
        ticket_hash: str,
        *,
        agent_id: str = "video-factory",
    ) -> dict[str, Any]:
        payload = cls.for_text(
            {
                **event,
                "message_id": event["event_id"],
                "sender_id": event.get("sender_id") or event.get("operator_id"),
                "text": "",
            },
            agent_id=agent_id,
        )
        payload["analysis_request"] = {
            "action": event["action"],
            "receipt_path": receipt["receipt_path"],
            "stored_path": receipt["stored_path"],
            "ticket_hash": ticket_hash,
        }
        return payload


class LarkLongConnection:
    @staticmethod
    def require_sdk() -> Any:
        try:
            import lark_oapi

            return lark_oapi
        except ImportError as exc:
            raise RuntimeError("official_lark_sdk_not_installed") from exc


class GatewayLifecycle:
    def __init__(
        self,
        connect: Callable[[], None],
        disconnect: Callable[[], None],
        now: Callable[[], float] = time.time,
    ):
        self.connect, self.disconnect, self.now = connect, disconnect, now
        self.running = False
        self.reconnects = 0
        self.last_heartbeat: float | None = None

    def startup(self) -> dict[str, Any]:
        if not self.running:
            self.connect()
            self.running = True
        return {"status": "running", "reconnects": self.reconnects}

    def heartbeat(self) -> dict[str, Any]:
        if not self.running:
            return {"status": "stopped"}
        self.last_heartbeat = self.now()
        return {"status": "healthy", "timestamp": self.last_heartbeat}

    def reconnect(self) -> dict[str, Any]:
        if self.running:
            self.disconnect()
        self.connect()
        self.running, self.reconnects = True, self.reconnects + 1
        return {"status": "reconnected", "reconnects": self.reconnects}

    def shutdown(self) -> dict[str, Any]:
        if self.running:
            self.disconnect()
            self.running = False
        return {"status": "stopped"}
