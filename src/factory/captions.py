"""Deterministic Chinese captions with optional trusted TTS boundary timing."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


PROTECTED_TERMS = (
    "FreeRTOS",
    "Modbus",
    "MCU",
    "Flash",
    "watchdog",
    "看门狗",
    "互斥锁",
    "CRC",
    "DMA",
    "ISR",
    "xSemaphoreGiveFromISR",
)
MIN_CAPTION_SECONDS = 0.6
MAX_CAPTION_SECONDS = 4.0


def _timecode(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds_part, milliseconds = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{seconds_part:02},{milliseconds:03}"


def _split_line(text: str, max_chars: int = 18) -> list[str]:
    tokens = re.findall("|".join(map(re.escape, PROTECTED_TERMS)) + r"|.", text)
    lines: list[str] = []
    current = ""
    for token in tokens:
        if current and len(current) + len(token) > max_chars:
            lines.append(current)
            current = token
        else:
            current += token
    if current:
        lines.append(current)
    return lines


def _phrases(text: str, duration_seconds: float) -> list[str]:
    lines: list[str] = []
    for sentence in [part.strip() for part in re.split(r"(?<=[。！？])", text) if part.strip()]:
        lines.extend(_split_line(sentence))
    if not lines:
        raise ValueError("caption_text_required")
    grouped = ["\n".join(lines[index : index + 2]) for index in range(0, len(lines), 2)]
    return lines if duration_seconds / len(grouped) > MAX_CAPTION_SECONDS else grouped


def _boundary_ends(boundaries: list[dict[str, Any]] | None, duration_seconds: float) -> list[float]:
    if not boundaries:
        return []
    ends = {
        round(float(item["end"]), 3)
        for item in boundaries
        if isinstance(item, dict)
        and isinstance(item.get("end"), (int, float))
        and 0 < float(item["end"]) <= duration_seconds
    }
    return sorted(ends)


def _durations(weights: list[int], horizon: float) -> list[float]:
    minimum_total = MIN_CAPTION_SECONDS * len(weights)
    available = min(horizon, MAX_CAPTION_SECONDS * len(weights))
    if available < minimum_total:
        raise ValueError("caption_duration_too_short")
    remaining = available - minimum_total
    total_weight = sum(weights)
    durations = [MIN_CAPTION_SECONDS + remaining * weight / total_weight for weight in weights]
    for _ in range(len(durations)):
        overflow = sum(max(0.0, value - MAX_CAPTION_SECONDS) for value in durations)
        if overflow <= 0.0001:
            break
        capped = [min(MAX_CAPTION_SECONDS, value) for value in durations]
        recipients = [index for index, value in enumerate(capped) if value < MAX_CAPTION_SECONDS - 0.0001]
        if not recipients:
            return capped
        share = overflow / len(recipients)
        durations = [
            capped[index] + (share if index in recipients else 0.0)
            for index in range(len(capped))
        ]
    return [round(min(MAX_CAPTION_SECONDS, value), 3) for value in durations]


def build_captions(
    text: str,
    duration_seconds: float,
    boundaries: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Create non-overlapping two-line captions from boundaries or deterministic weights."""
    if duration_seconds <= 0:
        raise ValueError("caption_duration_required")
    phrases = _phrases(text, duration_seconds)
    endpoints = _boundary_ends(boundaries, duration_seconds)
    horizon = min(duration_seconds, endpoints[-1]) if endpoints else duration_seconds
    weights = [max(1, len(phrase.replace("\n", ""))) for phrase in phrases]
    durations = _durations(weights, horizon)
    captions: list[dict[str, Any]] = []
    start = 0.0
    for index, (phrase, length) in enumerate(zip(phrases, durations)):
        target = round(start + length, 3)
        candidates = [
            endpoint
            for endpoint in endpoints
            if start + MIN_CAPTION_SECONDS <= endpoint <= min(horizon, start + MAX_CAPTION_SECONDS)
        ]
        end = min(candidates, key=lambda endpoint: abs(endpoint - target)) if candidates else target
        if end <= start:
            end = target
        captions.append(
            {
                "index": index + 1,
                "start": round(start, 3),
                "end": round(end, 3),
                "text": phrase,
                "timing_source": "edge_boundary" if endpoints else "deterministic_fallback",
            }
        )
        start = end
    return captions


def write_srt(captions: list[dict[str, Any]], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    blocks = []
    for caption in captions:
        blocks.append(
            f"{caption['index']}\n{_timecode(caption['start'])} --> {_timecode(caption['end'])}\n{caption['text']}"
        )
    target.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
