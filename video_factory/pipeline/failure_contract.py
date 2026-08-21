"""Sanitized execution failures shared by the local video-job lifecycle.

Execution exceptions are intentionally reduced to a stable contract.  The
original exception message is never copied into a job snapshot or report: it
may contain a local path, command line, model output, or another sensitive
value.  Callers can still retain the Python exception as the cause while the
persisted diagnostic remains deterministic.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .errors import FactoryContractError


_STAGE_RE = re.compile(r"[^a-z0-9_]+")
_ABSOLUTE_PATH_RE = re.compile(r"^(?:[a-zA-Z]:[\\/]|\\\\|/)")
_STAGES = {"context", "planning", "storyboard", "job_validation", "rendering", "quality_check"}
_STAGE_ALIASES = {
    "job": "job_validation",
    "validation": "job_validation",
    "provider": "storyboard",
    "director": "storyboard",
    "render": "rendering",
    "quality": "quality_check",
}


def sanitize_stage(stage: object) -> str:
    """Return a short, allowlisted-ish stage token with no path syntax."""

    value = _STAGE_RE.sub("_", str(stage or "unknown").strip().lower()).strip("_")
    value = _STAGE_ALIASES.get(value, value)
    return value[:48] if value in _STAGES else "rendering"


def sanitize_reason(exc: BaseException) -> str:
    """Classify an exception without retaining its message or arguments."""

    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(exc, (OSError, IOError)):
        return "io_error"
    if isinstance(exc, json.JSONDecodeError):
        return "json_error"
    if isinstance(exc, ValueError):
        return "value_error"
    if isinstance(exc, RuntimeError):
        return "runtime_error"
    if isinstance(exc, (KeyError, IndexError, TypeError, AttributeError)):
        return "contract_error"
    return "unexpected_error"


def _looks_absolute_path(value: str) -> bool:
    return bool(_ABSOLUTE_PATH_RE.match(value.strip()))


def normalize_execution_error(exc: BaseException, *, stage: object) -> FactoryContractError:
    """Normalize a non-contract exception into the execution failure code."""

    if isinstance(exc, FactoryContractError):
        return exc
    return FactoryContractError(
        "video_job_execution_failed",
        "Video job execution failed.",
        {"stage": sanitize_stage(stage), "reason": sanitize_reason(exc)},
    )


def sanitize_error_payload(error: object, *, stage: object | None = None) -> dict[str, Any]:
    """Convert an exception/dict into a bounded, path-free error payload."""

    if isinstance(error, FactoryContractError):
        return sanitize_error_payload(error.to_dict(), stage=stage)
    if isinstance(error, BaseException):
        normalized = normalize_execution_error(error, stage=stage or "unknown")
        return normalized.to_dict()
    if isinstance(error, dict):
        code = str(error.get("code", "video_job_execution_failed"))[:96]
        raw_message = str(error.get("message", "Video job execution failed."))
        # Preserve stable contract prose, but do not persist arbitrary
        # exception text that looks like a command, URL, or filesystem path.
        message = (
            "Video job execution failed."
            if any(token in raw_message for token in ("\\", "/", "\r", "\n", "://"))
            else raw_message[:240]
        )
        raw_context = error.get("context")
        context: dict[str, Any] = {}
        if isinstance(raw_context, dict):
            # Keep only stable scalar diagnostics.  In particular, do not
            # persist arbitrary exception args, stdout, or filesystem paths.
            for key in ("stage", "reason", "provider", "attempt", "exit_code", "schema", "path", "validator", "status"):
                value = raw_context.get(key)
                if value is None:
                    continue
                if key == "stage":
                    context[key] = sanitize_stage(value)
                elif key == "reason":
                    text_value = str(value).strip()
                    if _looks_absolute_path(text_value):
                        context[key] = "redacted"
                    else:
                        text = _STAGE_RE.sub("_", text_value.lower()).strip("_")
                        context[key] = text[:240] or "unknown"
                elif isinstance(value, (str, int, float, bool)):
                    if isinstance(value, str) and key in {"path", "reason"} and _looks_absolute_path(value):
                        context[key] = "redacted"
                    else:
                        context[key] = str(value)[:240] if isinstance(value, str) else value
        if stage is not None:
            context.setdefault("stage", sanitize_stage(stage))
        return {"code": code, "message": message, "context": context}
    normalized = normalize_execution_error(TypeError("invalid_error"), stage=stage or "unknown")
    return normalized.to_dict()


# Friendly aliases for callers/tests that describe this operation as
# ``normalize_failure`` or ``execution_error``.
normalize_failure = normalize_execution_error
execution_error = normalize_execution_error


__all__ = [
    "execution_error",
    "normalize_execution_error",
    "normalize_failure",
    "sanitize_error_payload",
    "sanitize_reason",
    "sanitize_stage",
]
