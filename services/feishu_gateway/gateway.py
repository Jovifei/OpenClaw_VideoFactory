"""Offline event fixture for the Channel Layer; it has no compute dependency."""

from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .policy import ACTION_BY_KIND, validate_gateway_rpc_request
from .runtime import GatewayPayloadBuilder


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass
class OfflineFeishuGateway:
    ingest: Callable[[dict[str, Any]], dict[str, Any]]
    rpc: Callable[[dict[str, Any]], dict[str, Any]]
    now: Callable[[], float] = time.time
    verify_signature: Callable[[dict[str, Any]], bool] | None = None
    verify_signature_required: bool = True
    seen: set[str] = field(default_factory=set)
    tickets: dict[str, dict[str, Any]] = field(default_factory=dict)

    def _signature_valid(self, event: dict[str, Any]) -> bool:
        if not self.verify_signature_required:
            return True
        if self.verify_signature is None or not event.get("signature"):
            return False
        try:
            return bool(self.verify_signature(event))
        except Exception:
            return False

    def process(self, event: dict[str, Any]) -> dict[str, Any]:
        event_id, event_type = event.get("event_id"), event.get("type")
        if (
            not isinstance(event_id, str)
            or not event_id
            or event_type
            not in {"im.message.receive_v1", "card.action.trigger", "system.reconnected"}
        ):
            return {"status": "rejected", "error": "invalid_raw_event"}
        if event_type != "system.reconnected" and not self._signature_valid(event):
            return {"status": "invalid_signature"}
        if event_id in self.seen:
            return {"status": "duplicate"}
        self.seen.add(event_id)
        if event_type == "system.reconnected":
            return {"status": "reconnected"}
        return self._message(event) if event_type == "im.message.receive_v1" else self._card(event)

    def _message(self, event: dict[str, Any]) -> dict[str, Any]:
        message = event.get("message") or {}
        required = ("message_id", "tenant_id", "chat_id", "sender_id", "thread_id", "message_type")
        if not all(isinstance(message.get(key), str) and message[key] for key in required):
            return {"status": "rejected", "error": "missing_message_metadata"}
        if message["message_type"] == "text":
            payload = GatewayPayloadBuilder.for_text(message)
            validate_gateway_rpc_request(payload)
            return self.rpc(payload)
        attachment = message.get("attachment") or {}
        receipt = self.ingest(
            {
                "message_id": message["message_id"],
                "attachment_index": attachment.get("index", 0),
                "attachment_count": 1,
                "source_media_path": attachment.get("local_path"),
                "original_file_name": attachment.get("name"),
                "content_type": attachment.get("content_type"),
                "chat_id": message["chat_id"],
                "sender_id": message["sender_id"],
                "event_id": event["event_id"],
            }
        )
        if receipt.get("status") != "quarantined":
            return {"status": "rejected", "error": "ingest_failed"}
        kind = receipt.get("detected_kind")
        if (
            kind not in ACTION_BY_KIND
            or not receipt.get("quarantined")
            or receipt.get("content_parsed") is not False
        ):
            return {"status": "quarantined", "card": None}
        token = secrets.token_urlsafe(32)
        self.tickets[_digest(token)] = {
            "tenant_id": message["tenant_id"],
            "chat_id": message["chat_id"],
            "sender_id": message["sender_id"],
            "thread_id": message["thread_id"],
            "kind": kind,
            "receipt": receipt,
            "expires_at": self.now() + 120,
            "used": False,
        }
        return {"status": "quarantined", "card": {"ticket": token, "action": ACTION_BY_KIND[kind]}}

    def _card(self, event: dict[str, Any]) -> dict[str, Any]:
        callback = event.get("callback") or {}
        required = ("operator", "tenant_id", "open_chat_id", "thread_id", "action", "ticket")
        if not all(isinstance(callback.get(key), str) and callback[key] for key in required):
            return {"status": "rejected", "error": "invalid_card_callback"}
        ticket_hash = _digest(callback["ticket"])
        ticket = self.tickets.get(ticket_hash)
        if ticket is None or ticket["used"] or self.now() > ticket["expires_at"]:
            return {"status": "rejected", "error": "ticket_invalid_or_expired"}
        if (
            any(
                callback[source] != ticket[target]
                for source, target in (
                    ("operator", "sender_id"),
                    ("tenant_id", "tenant_id"),
                    ("open_chat_id", "chat_id"),
                    ("thread_id", "thread_id"),
                )
            )
            or callback["action"] != ACTION_BY_KIND[ticket["kind"]]
        ):
            return {"status": "rejected", "error": "ticket_identity_mismatch"}
        payload = GatewayPayloadBuilder.for_analysis_request(
            {
                "event_id": event["event_id"],
                "tenant_id": callback["tenant_id"],
                "chat_id": callback["open_chat_id"],
                "sender_id": callback["operator"],
                "thread_id": callback["thread_id"],
                "action": callback["action"],
            },
            ticket["receipt"],
            ticket_hash,
        )
        validate_gateway_rpc_request(payload)
        result = self.rpc(payload)
        ticket["used"] = True
        return {
            "status": result.get("status", "rpc_malformed"),
            "analysis_request": {"action": callback["action"]},
        }

    def snapshot(self) -> dict[str, Any]:
        return {"seen": sorted(self.seen), "tickets": self.tickets}

    @classmethod
    def restore(cls, snapshot: dict[str, Any], **kwargs: Any) -> "OfflineFeishuGateway":
        gateway = cls(**kwargs)
        gateway.seen, gateway.tickets = (
            set(snapshot.get("seen", [])),
            dict(snapshot.get("tickets", {})),
        )
        return gateway
