"""Translate stable MVP transition names to FFmpeg xfade names."""

from __future__ import annotations


TRANSITIONS = {"fade": "fade", "zoom": "zoomin", "slide": "slideleft"}


def ffmpeg_transition(name: str) -> str:
    try:
        return TRANSITIONS[name]
    except KeyError as exc:
        raise ValueError(f"transition_unsupported:{name}") from exc
