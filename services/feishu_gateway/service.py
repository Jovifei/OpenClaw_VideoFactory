"""Project-owned Channel Layer: ingress, tickets, and OpenClaw requests only."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import time
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator, RefResolver

from .policy import ACTION_BY_KIND, validate_gateway_rpc_request
from .runtime import GatewayPayloadBuilder

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas" / "feishu_gateway"


def _load(name: str) -> dict[str, Any]:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", value or ""))


class GatewayState:
    def __init__(self, path: Path):
        self.path = path
        self.data = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.exists()
            else {"seen": [], "tickets": {}}
        )
        self._sanitize()

    def _sanitize(self) -> None:
        tickets: dict[str, dict[str, Any]] = {}
        for ticket_id, entry in (self.data.get("tickets") or {}).items():
            if not isinstance(entry, dict):
                continue
            tickets[ticket_id] = {
                **entry,
                **{
                    field: _digest(entry[field])
                    if entry.get(field) and not _is_sha256(entry[field])
                    else entry.get(field)
                    for field in ("tenant", "chat", "sender", "thread")
                },
            }
        self.data["tickets"] = tickets
        self.data["seen"] = sorted(
            {
                _digest(item) if not _is_sha256(item) else item
                for item in self.data.get("seen", [])
                if isinstance(item, str)
            }
        )

    def save(self) -> None:
        self._sanitize()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")


class ProjectFeishuGateway:
    """The Channel Layer has no Analyzer, model, GPU, or direct compute dependency."""

    def __init__(
        self,
        *,
        state: GatewayState,
        ingest: Callable[[dict[str, Any]], dict[str, Any]],
        rpc: Callable[[dict[str, Any]], dict[str, Any]],
        outbound: Callable[[dict[str, Any]], Any],
        download: Callable[[dict[str, Any]], str] | None = None,
        cleanup: Callable[[str], None] | None = None,
        outbound_retries: int = 1,
        now: Callable[[], float] = time.time,
        verify_signature: Callable[[dict[str, Any]], bool] | None = None,
        verify_signature_required: bool = True,
    ):
        self.state, self.ingest, self.rpc, self.outbound, self.now = (
            state,
            ingest,
            rpc,
            outbound,
            now,
        )
        self.download, self.cleanup, self.outbound_retries = download, cleanup, outbound_retries
        self.verify_signature, self.verify_signature_required = (
            verify_signature,
            verify_signature_required,
        )

    def _signature_valid(self, event: dict[str, Any]) -> bool:
        if not self.verify_signature_required:
            return True
        if self.verify_signature is None or not event.get("signature"):
            return False
        try:
            return bool(self.verify_signature(event))
        except Exception:
            return False

    def _once(self, event_id: str) -> None:
        digest = _digest(event_id)
        if digest not in self.state.data["seen"]:
            self.state.data["seen"].append(digest)
            self.state.save()

    @staticmethod
    def _retryable(result: dict[str, Any]) -> bool:
        return result.get("status") in {
            "rpc_timeout",
            "rpc_transport_error",
            "attachment_download_failed",
            "outbound_failed",
        }

    def _send(self, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(1, self.outbound_retries + 2):
            try:
                result = self.outbound(payload)
                if (
                    result is None
                    or result is True
                    or (isinstance(result, dict) and result.get("status") in {None, "sent"})
                ):
                    return {"status": "sent", "attempts": attempt}
            except Exception:
                pass
        self.state.data.setdefault("dead_letters", []).append(
            {
                "kind": payload.get("kind"),
                "event": _digest(str(payload.get("event_id", ""))),
                "at": self.now(),
            }
        )
        self.state.save()
        return {"status": "outbound_failed", "attempts": self.outbound_retries + 1}

    def message(self, event: dict[str, Any]) -> dict[str, Any]:
        if not self._signature_valid(event):
            return {"status": "invalid_signature"}
        schema = _load("message_event.schema.json")
        Draft202012Validator(schema, resolver=RefResolver(SCHEMAS.as_uri() + "/", schema)).validate(
            event
        )
        if _digest(event["event_id"]) in self.state.data["seen"]:
            return {"status": "duplicate"}
        if event["message_type"] == "text":
            payload = GatewayPayloadBuilder.for_text(event)
            validate_gateway_rpc_request(payload)
            try:
                result = self.rpc(payload)
            except Exception:
                result = {"status": "rpc_transport_error"}
            if not self._retryable(result):
                self._once(event["event_id"])
            return result
        receipts = []
        for index, attachment in enumerate(event["attachments"]):
            Draft202012Validator(_load("attachment_event.schema.json")).validate(attachment)
            source, temporary = attachment.get("local_path"), False
            if not source:
                if self.download is None:
                    return {"status": "attachment_download_failed"}
                try:
                    source, temporary = self.download(attachment), True
                except Exception:
                    return {"status": "attachment_download_failed"}
            try:
                receipt = self.ingest(
                    {
                        "message_id": event["message_id"],
                        "attachment_index": index,
                        "attachment_count": len(event["attachments"]),
                        "source_media_path": source,
                        "original_file_name": attachment["filename"],
                        "content_type": attachment["mime"],
                        "chat_id": event["chat_id"],
                        "sender_id": event["sender_id"],
                        "event_id": event["event_id"],
                    }
                )
            finally:
                if temporary and self.cleanup is not None:
                    self.cleanup(source)
            if receipt.get("status") != "quarantined":
                return {"status": "ingest_failed"}
            kind = receipt.get("detected_kind")
            if kind in ACTION_BY_KIND:
                token = secrets.token_urlsafe(32)
                self.state.data["tickets"][_digest(token)] = {
                    "tenant": event["tenant_id"],
                    "chat": event["chat_id"],
                    "sender": event["sender_id"],
                    "thread": event["thread_id"],
                    "action": ACTION_BY_KIND[kind],
                    "receipt": receipt,
                    "until": self.now() + 120,
                    "used": False,
                }
                self.state.save()
                delivery = self._send(
                    {
                        "kind": "analysis_card",
                        "event_id": event["event_id"],
                        "ticket": token,
                        "action": ACTION_BY_KIND[kind],
                    }
                )
                if self._retryable(delivery):
                    return delivery
            receipts.append(receipt["receipt_path"])
        self._once(event["event_id"])
        return {"status": "quarantined", "receipts": receipts}

    def card(self, event: dict[str, Any]) -> dict[str, Any]:
        if not self._signature_valid(event):
            return {"status": "invalid_signature"}
        Draft202012Validator(_load("card_event.schema.json")).validate(event)
        if _digest(event["event_id"]) in self.state.data["seen"]:
            return {"status": "duplicate"}
        ticket_hash = _digest(event["ticket"])
        ticket = self.state.data["tickets"].get(ticket_hash)
        if not ticket or ticket["used"] or self.now() > ticket["until"]:
            return {"status": "ticket_invalid"}
        expected = {
            "tenant": _digest(event["tenant_id"]),
            "chat": _digest(event["chat_id"]),
            "sender": _digest(event["operator_id"]),
            "thread": _digest(event["thread_id"]),
        }
        if (
            any(ticket[field] != expected[field] for field in expected)
            or ticket["action"] != event["action"]
        ):
            return {"status": "ticket_identity_mismatch"}
        payload = GatewayPayloadBuilder.for_analysis_request(event, ticket["receipt"], ticket_hash)
        try:
            validate_gateway_rpc_request(payload)
            result = self.rpc(payload)
        except Exception:
            result = {"status": "rpc_transport_error"}
        if self._retryable(result):
            return result
        ticket["used"] = True
        self.state.save()
        self._once(event["event_id"])
        return {
            "status": result.get("status", "rpc_malformed"),
            "analysis_request": {"status": "submitted", "action": event["action"]},
        }
