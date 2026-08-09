"""Structured, stable errors for video-factory contracts."""

from __future__ import annotations

from typing import Any


class FactoryContractError(ValueError):
    """A fail-closed error with a stable code and safe diagnostic context."""

    def __init__(self, code: str, message: str, context: dict[str, Any] | None = None) -> None:
        if not code or not isinstance(code, str):
            raise ValueError("error_code_invalid")
        if not message or not isinstance(message, str):
            raise ValueError("error_message_invalid")
        if context is not None and not isinstance(context, dict):
            raise ValueError("error_context_invalid")
        self.code = code
        self.message = message
        self.context = dict(context or {})
        super().__init__(code)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "context": dict(self.context),
        }

    def __str__(self) -> str:
        return self.code
