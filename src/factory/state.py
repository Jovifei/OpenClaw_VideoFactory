"""Strict state transitions for an offline candidate job."""

from __future__ import annotations


STAGES = (
    "NEW",
    "RESEARCHING",
    "SCRIPTING",
    "VOICE",
    "CAPTIONS",
    "ASSETS",
    "RENDERING",
    "QUALITY_CHECK",
    "PENDING_REVIEW",
)
TERMINAL_STATES = {"PENDING_REVIEW", "FAILED", "CANCELLED"}


def next_state(state: str) -> str | None:
    if state not in STAGES:
        return None
    index = STAGES.index(state)
    return STAGES[index + 1] if index + 1 < len(STAGES) else None


def validate_transition(current: str, target: str) -> None:
    expected = next_state(current)
    if expected != target:
        raise ValueError(f"invalid_transition:{current}->{target};expected:{expected}")
