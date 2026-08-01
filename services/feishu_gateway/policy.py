"""Least-privilege policy for the Project Feishu Gateway."""

from __future__ import annotations

from typing import Any

ACTION_BY_KIND = {"png": "analyze_image", "wav": "transcribe_audio", "mp4": "analyze_video"}
GATEWAY_CAPABILITIES = {
    "receive_message": True,
    "receive_attachment": True,
    "verify_identity": True,
    "create_openclaw_request": True,
    "send_reply": True,
    "model_call": False,
    "analyzer_call": False,
    "gpu_task": False,
    "filesystem_arbitrary_access": False,
    "config_modify": False,
    "agent_create": False,
}
FORBIDDEN_RPC_FIELDS = frozenset(
    {"analyzer", "analyzer_id", "model", "model_id", "gpu", "gpu_task", "tool", "tool_name"}
)
REQUIRED_RPC_FIELDS = frozenset(
    {
        "agent_id",
        "session_key",
        "message_id",
        "tenant_id",
        "chat_id",
        "sender_id",
        "thread_id",
        "text",
    }
)


def validate_gateway_rpc_request(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or not REQUIRED_RPC_FIELDS.issubset(payload):
        raise ValueError("gateway_rpc_request_incomplete")
    if payload.get("agent_id") != "video-factory":
        raise ValueError("gateway_rpc_agent_forbidden")
    if FORBIDDEN_RPC_FIELDS.intersection(payload):
        raise ValueError("gateway_rpc_privilege_forbidden")
    request = payload.get("analysis_request")
    if request is not None:
        if not isinstance(request, dict) or set(request) != {
            "action",
            "receipt_path",
            "stored_path",
            "ticket_hash",
        }:
            raise ValueError("gateway_analysis_request_invalid")
    return payload
