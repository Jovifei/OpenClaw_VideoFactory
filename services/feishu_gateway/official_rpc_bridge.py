"""One-shot local IPC client for the official Node device-auth bridge.

Python supplies an ephemeral session credential over stdin/environment only. It
never opens the external device state directory and never reads a private key or
a device token.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

BRIDGE_ROOT = Path(__file__).with_name("openclaw_rpc_official")
BRIDGE_ENTRYPOINT = BRIDGE_ROOT / "src" / "rpc_bridge.mjs"
ALLOWED_METHODS = frozenset({"health", "session.resolve", "agent.request", "request.status"})
SAFE_STATUSES = frozenset(
    {
        "health_ok",
        "health_failed",
        "device_identity_missing",
        "pairing_required",
        "connect_failed",
        "connect_timeout",
        "bridge_session_unauthorized",
        "bridge_method_not_active",
        "bridge_request_failed",
        "bridge_unavailable",
        "bridge_invalid_response",
    }
)
Runner = Callable[..., subprocess.CompletedProcess[str]]


def _safe_environment(session: str, environ: Mapping[str, str] | None = None) -> dict[str, str]:
    source = os.environ if environ is None else environ
    allowed = (
        "APPDATA",
        "LOCALAPPDATA",
        "USERPROFILE",
        "USERNAME",
        "SystemRoot",
        "WINDIR",
        "ComSpec",
        "PATH",
        "TEMP",
        "TMP",
    )
    result = {
        name: source[name] for name in allowed if isinstance(source.get(name), str) and source[name]
    }
    result["VIDEO_FACTORY_BRIDGE_SESSION"] = session
    return result


def _safe_error(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    top_level = value.get("top_level_code")
    detail_code = value.get("details_code")
    reason = value.get("details_reason")
    next_step = value.get("recommended_next_step")
    return {
        "top_level_code": top_level
        if isinstance(top_level, str) and len(top_level) <= 64
        else None,
        "details_code": detail_code
        if isinstance(detail_code, str) and len(detail_code) <= 64
        else None,
        "details_reason": reason if isinstance(reason, str) and len(reason) <= 64 else None,
        "can_retry_with_device_token": value.get("can_retry_with_device_token")
        if isinstance(value.get("can_retry_with_device_token"), bool)
        else None,
        "recommended_next_step": next_step
        if isinstance(next_step, str) and len(next_step) <= 64
        else None,
        "pairing_request_id_redacted": value.get("pairing_request_id_redacted")
        if isinstance(value.get("pairing_request_id_redacted"), str)
        else None,
    }


def _safe_response(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"status": "bridge_invalid_response"}
    status = value.get("status")
    if status not in SAFE_STATUSES:
        return {"status": "bridge_invalid_response"}
    source = value.get("source") if isinstance(value.get("source"), dict) else {}
    scopes = value.get("scopes")
    return {
        "status": status,
        "operation": value.get("operation") if value.get("operation") == "health" else None,
        "client_id": value.get("client_id")
        if value.get("client_id") == "project-feishu-gateway"
        else None,
        "client_mode": value.get("client_mode") if value.get("client_mode") == "backend" else None,
        "role": value.get("role") if value.get("role") == "operator" else None,
        "scopes": [scope for scope in scopes if scope == "operator.read"]
        if isinstance(scopes, list)
        else [],
        "explicit_shared_token": value.get("explicit_shared_token")
        if isinstance(value.get("explicit_shared_token"), bool)
        else None,
        "device_identity": value.get("device_identity") is True,
        "challenge_signature": value.get("challenge_signature") is True,
        "error": _safe_error(value.get("error")),
        "source": {
            "package_name": source.get("package_name")
            if source.get("package_name") == "openclaw"
            else None,
            "package_version": source.get("package_version")
            if isinstance(source.get("package_version"), str)
            else None,
            "client_module": source.get("client_module")
            if isinstance(source.get("client_module"), str)
            and source.get("client_module").startswith("<openclaw-root>/")
            else None,
        },
    }


class OfficialDeviceBridge:
    """Call the Node bridge with a random one-shot local IPC credential."""

    def __init__(self, *, node: str | None = None, runner: Runner = subprocess.run) -> None:
        self.node = node or shutil.which("node")
        self.runner = runner

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if method not in ALLOWED_METHODS:
            return {"status": "bridge_method_not_active"}
        if not self.node or not BRIDGE_ENTRYPOINT.is_file():
            return {"status": "bridge_unavailable"}
        session = secrets.token_urlsafe(32)
        request = json.dumps(
            {"session": session, "method": method, "params": params or {}}, separators=(",", ":")
        )
        try:
            completed = self.runner(
                [self.node, str(BRIDGE_ENTRYPOINT)],
                input=request,
                text=True,
                capture_output=True,
                timeout=15,
                check=False,
                env=_safe_environment(session),
            )
        except (OSError, subprocess.SubprocessError, TimeoutError):
            return {"status": "bridge_unavailable"}
        try:
            response = json.loads(completed.stdout.strip())
        except (json.JSONDecodeError, TypeError):
            return {"status": "bridge_invalid_response"}
        return _safe_response(response)

    def health(self) -> dict[str, Any]:
        return self.call("health")
