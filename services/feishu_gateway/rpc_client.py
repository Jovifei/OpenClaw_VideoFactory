"""Fail-closed RPC boundary; a real OpenClaw protocol is never guessed."""

from __future__ import annotations

from typing import Any, Callable

from .runtime import GatewayRpcContract, map_error_code, normalize_status


class OpenClawRpcClient:
    def __init__(
        self,
        transport: Callable[[str, dict[str, Any], int], dict[str, Any]] | None = None,
        *,
        timeout: int = 20,
        retries: int = 1,
    ):
        self.transport, self.timeout, self.retries = transport, timeout, retries
        self.contract = GatewayRpcContract()

    def connection_check(self) -> dict[str, Any]:
        return (
            {"status": "rpc_runtime_verification_blocked"}
            if self.transport is None
            else self._request("health", {})
        )

    def create_session(self, session_key: str) -> dict[str, Any]:
        return self._request("create_session", {"session_key": session_key})

    def send_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(self.contract.rpc_method, payload)

    def send_attachment_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("attachment_event", payload)

    def send_agent_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(self.contract.rpc_method, payload)

    def _request(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.transport is None:
            return {"status": "rpc_runtime_verification_blocked", "method": method, "attempts": 0}
        result: dict[str, Any] = {"status": "rpc_timeout"}
        for attempt in range(1, self.retries + 2):
            try:
                result = map_error_code(
                    normalize_status(self.transport(method, payload, self.timeout), "rpc_timeout")
                )
            except Exception:
                result = {"status": "rpc_transport_error"}
            result["method"], result["attempts"] = method, attempt
            if result["status"] not in {"rpc_timeout", "rpc_transport_error", "rpc_network_error"}:
                return result
        return result
