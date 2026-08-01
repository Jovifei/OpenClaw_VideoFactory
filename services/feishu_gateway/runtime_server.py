"""Fail-closed Gateway runtime modes for offline and RPC preflight use."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from .credentials import TokenProvider
from .official_rpc_bridge import OfficialDeviceBridge

VERSION = "0.46.0"
RUNTIME_MODES = ("offline", "production-preflight", "production")
RpcProbe = Callable[[TokenProvider], dict[str, Any]]
OfficialDeviceProbe = Callable[[], dict[str, Any]]
RPC_READY = "RPC_READY"
RPC_CREDENTIAL_REQUIRED = "RPC_CREDENTIAL_REQUIRED"
RPC_AUTH_FAILED = "RPC_AUTH_FAILED"
PROJECT_GATEWAY_DEVICE_PAIRING_REQUIRED = "PROJECT_GATEWAY_DEVICE_PAIRING_APPROVAL_REQUIRED"
LEGACY_SHARED_TOKEN_ADAPTER_DISABLED = "legacy_shared_token_adapter_disabled"
PREFLIGHT_KEYS = (
    "rpc_endpoint_available",
    "token_present",
    "auth_valid",
    "session_ready",
)


def digest(value: str | None) -> str | None:
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else None


class JsonLogger:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        level: str,
        event: str,
        *,
        event_id: str | None = None,
        chat_id: str | None = None,
        sender_id: str | None = None,
        status: str = "ok",
    ) -> None:
        row = {
            "timestamp": time.time(),
            "level": level,
            "event": event,
            "event_id_hash": digest(event_id),
            "chat_hash": digest(chat_id),
            "sender_hash": digest(sender_id),
            "status": status,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")


def _preflight(
    result: str,
    *,
    endpoint: bool = False,
    token: bool = False,
    authenticated: bool = False,
    session: bool = False,
) -> dict[str, Any]:
    return {
        "result": result,
        "rpc_endpoint_available": endpoint,
        "token_present": token,
        "auth_valid": authenticated,
        "session_ready": session,
    }


def _token_format_valid(token: str) -> bool:
    """Reject only whitespace/control-bearing values without inventing a token format."""
    return bool(token) and all(
        not character.isspace() and ord(character) >= 32 for character in token
    )


def _endpoint_responded(status: str) -> bool:
    return status not in {"rpc_timeout", "rpc_transport_error", "rpc_network_error"}


def normalize_rpc_preflight(result: dict[str, Any]) -> dict[str, Any]:
    """Accept legacy injected probes while exposing the fixed 036 status contract."""
    if all(key in result for key in PREFLIGHT_KEYS) and isinstance(result.get("result"), str):
        return {
            "result": result["result"],
            **{key: result[key] is True for key in PREFLIGHT_KEYS},
        }
    status = str(result.get("status", "rpc_preflight_failed"))
    if status == "reachable":
        return _preflight(RPC_READY, endpoint=True, token=True, authenticated=True, session=True)
    if status == "rpc_credentials_missing":
        return _preflight(RPC_CREDENTIAL_REQUIRED)
    if status in {
        "device_identity_missing",
        "pairing_required",
        PROJECT_GATEWAY_DEVICE_PAIRING_REQUIRED,
    }:
        return _preflight(
            PROJECT_GATEWAY_DEVICE_PAIRING_REQUIRED,
            endpoint=status == "pairing_required",
        )
    return _preflight(RPC_AUTH_FAILED, endpoint=_endpoint_responded(status), token=True)


def probe_openclaw_rpc(_token_provider: TokenProvider | None = None) -> dict[str, Any]:
    """Historical shared-token adapter entrypoint; intentionally disabled."""
    return _preflight(LEGACY_SHARED_TOKEN_ADAPTER_DISABLED)


def probe_official_device_auth() -> dict[str, Any]:
    """Use the local Node bridge; it never exposes device private material to Python."""
    result = OfficialDeviceBridge().health()
    status = result.get("status")
    if status == "health_ok":
        return _preflight(RPC_READY, endpoint=True, token=True, authenticated=True, session=True)
    if status in {"device_identity_missing", "pairing_required"}:
        return _preflight(
            PROJECT_GATEWAY_DEVICE_PAIRING_REQUIRED,
            endpoint=status == "pairing_required",
            token=False,
        )
    return _preflight(
        RPC_AUTH_FAILED, endpoint=status not in {"bridge_unavailable", "connect_timeout"}
    )


class Runtime:
    def __init__(
        self,
        status_path: Path,
        log_path: Path,
        *,
        mode: str = "offline",
        token_provider: TokenProvider | None = None,
        rpc_probe: RpcProbe | None = None,
        official_device_probe: OfficialDeviceProbe | None = None,
    ):
        if mode not in RUNTIME_MODES:
            raise ValueError("gateway_runtime_mode_invalid")
        self.started = time.time()
        self.status_path, self.mode, self.logger = status_path, mode, JsonLogger(log_path)
        self.config_valid = bool(os.environ.get("FEISHU_GATEWAY_CONFIG_FINGERPRINT"))
        self.last_event_time: float | None = None
        self.port = int(os.environ.get("FEISHU_GATEWAY_PORT", "18990"))
        self.feishu_connection = "not_initialized"
        self.openclaw_rpc = "not_checked"
        self.rpc_preflight = _preflight("OFFLINE_ISOLATED")
        if mode == "offline":
            self.feishu_connection = "fake_transport"
            self.openclaw_rpc = "offline_isolated"
        elif mode == "production":
            self.feishu_connection = "production_guarded"
            self.openclaw_rpc = "not_checked"
            self.rpc_preflight = _preflight("PRODUCTION_TRANSPORT_UNAVAILABLE")
        else:
            self.feishu_connection = "not_started_preflight"
            if rpc_probe is not None:
                # Test-only compatibility seam. Production defaults never select
                # the shared-token adapter.
                provider = token_provider or (lambda: None)
                raw_preflight = rpc_probe(provider)
            else:
                raw_preflight = (official_device_probe or probe_official_device_auth)()
            self.rpc_preflight = normalize_rpc_preflight(raw_preflight)
            self.openclaw_rpc = (
                "reachable"
                if self.rpc_preflight["result"] == RPC_READY
                else (
                    "device_pairing_required"
                    if self.rpc_preflight["result"] == PROJECT_GATEWAY_DEVICE_PAIRING_REQUIRED
                    else (
                        "rpc_credentials_missing"
                        if self.rpc_preflight["result"] == RPC_CREDENTIAL_REQUIRED
                        else "rpc_auth_failed"
                    )
                )
            )
            self.logger.write(
                "info", "rpc_preflight_completed", status=self.rpc_preflight["result"]
            )
        self.write_status()

    def payload(self, ready: bool = False) -> dict[str, Any]:
        return {
            "status": "ready" if ready else "running",
            "version": VERSION,
            "mode": self.mode,
            "uptime": round(time.time() - self.started, 3),
            "pid": os.getpid(),
            "port": self.port,
            "feishu_connection": self.feishu_connection,
            "openclaw_rpc": self.openclaw_rpc,
            **{key: self.rpc_preflight[key] for key in PREFLIGHT_KEYS},
            "rpc_preflight_result": self.rpc_preflight["result"],
            "last_event_time": self.last_event_time,
        }

    def write_status(self) -> None:
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        self.status_path.write_text(
            json.dumps(
                {
                    **self.ready(),
                    "health": "healthy",
                    "config_valid": self.config_valid,
                    "log_path": str(self.logger.path.name),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def ready(self) -> dict[str, Any]:
        ready = (
            self.mode == "production-preflight"
            and self.config_valid
            and self.feishu_connection == "not_started_preflight"
            and self.rpc_preflight["result"] == RPC_READY
        )
        return self.payload(ready=ready) | {"ready": ready}


def serve(runtime: Runtime, host: str, port: int) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                body = runtime.payload() | {"health": "healthy"}
            elif self.path == "/ready":
                body = runtime.ready()
            else:
                self.send_error(404)
                return
            encoded = json.dumps(body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_POST(self):  # noqa: N802
            if self.path != "/shutdown":
                self.send_error(404)
                return
            self.send_response(202)
            self.end_headers()
            runtime.logger.write("info", "runtime_shutdown")
            threading.Thread(target=self.server.shutdown, daemon=True).start()

        def log_message(self, *_: Any) -> None:
            return

    runtime.logger.write("info", "runtime_started", status=runtime.mode)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18990)
    parser.add_argument("--status-file", type=Path, required=True)
    parser.add_argument("--log-file", type=Path, required=True)
    parser.add_argument("--mode", choices=RUNTIME_MODES, default="offline")
    args = parser.parse_args()
    runtime = Runtime(args.status_file, args.log_file, mode=args.mode)
    if args.mode == "production":
        runtime.logger.write(
            "warning", "production_runtime_guarded", status="production_transport_unavailable"
        )
        return 2
    serve(runtime, args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
