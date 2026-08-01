"""Deterministic, non-reversible Feishu session identities."""

from __future__ import annotations

import hashlib


def _digest(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("feishu_session_identity_required")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def build_session_key(
    tenant_id: str, chat_id: str, sender_id: str, thread_id: str, *, agent_id: str = "video-factory"
) -> str:
    if not agent_id:
        raise ValueError("agent_id_required")
    return (
        f"agent:{agent_id}:feishu:tenant:{_digest(tenant_id)}:chat:{_digest(chat_id)}:"
        f"sender:{_digest(sender_id)}:thread:{_digest(thread_id)}"
    )
