"""Turn a short line-based script into a deterministic SRT file."""

from __future__ import annotations

import textwrap
from pathlib import Path


def _timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03d}"


def build_srt(
    script_path: Path,
    timeline: list[dict[str, object]],
    target: Path,
    *,
    transition_seconds: float = 0.0,
    max_chars_per_line: int | None = None,
    max_lines: int = 2,
) -> list[dict[str, object]]:
    if not script_path.is_file():
        raise ValueError("script_missing")
    lines = [line.strip() for line in script_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError("script_empty")
    if not timeline:
        raise ValueError("timeline_empty")
    if not 0 <= transition_seconds < min(float(item["duration"]) for item in timeline):
        raise ValueError("subtitle_transition_duration_invalid")
    captions = []
    cursor = 0.0
    for index, item in enumerate(timeline, start=1):
        text = lines[(index - 1) % len(lines)]
        if max_chars_per_line is not None:
            text = _wrap_caption(text, max_chars_per_line, max_lines)
        end = cursor + float(item["duration"])
        captions.append({"index": index, "start": round(cursor, 3), "end": round(end, 3), "text": text})
        cursor = end - transition_seconds
    captions[-1]["end"] = round(captions[-1]["end"], 3)
    # Video scenes cross-fade, but captions must not stack during that visual
    # overlap.  End each caption when the next one starts so the safe band
    # contains at most one readable caption block.
    for previous, current in zip(captions, captions[1:]):
        previous["end"] = min(float(previous["end"]), float(current["start"]))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(
            f"{caption['index']}\n{_timestamp(float(caption['start']))} --> {_timestamp(float(caption['end']))}\n{caption['text']}\n"
            for caption in captions
        ),
        encoding="utf-8",
    )
    return captions


def _wrap_caption(text: str, max_chars_per_line: int, max_lines: int) -> str:
    """Wrap a knowledge caption without allowing an oversized text block."""

    if max_chars_per_line < 8 or max_lines < 1:
        raise ValueError("subtitle_wrap_invalid")
    chunks = textwrap.wrap(
        text.strip(),
        width=max_chars_per_line,
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=False,
    )
    if len(chunks) > max_lines:
        raise ValueError("subtitle_text_too_long")
    return "\n".join(chunks)


def build_srt_from_timeline(timeline_doc: dict, target: Path) -> list[dict]:
    """Build an SRT subtitle file from a compiled timeline document.

    Unlike ``build_srt()`` (which reads a separate ``script.txt`` and cycles
    lines via modulo), this function derives **one caption per scene** from
    each scene's ``caption`` field — the productized approach that avoids
    silent repetition when scene count ≠ line count.

    Parameters
    ----------
    timeline_doc : dict
        A compiled timeline document (output of ``compile_storyboard()``).
    target : Path
        Destination path for the ``.srt`` file.

    Returns
    -------
    list[dict]
        List of caption dicts with ``index``, ``start``, ``end``, ``text``.
    """
    scenes = timeline_doc.get("scenes", [])
    if not scenes:
        raise ValueError("timeline_empty")

    transition_seconds = float(timeline_doc.get("transition_seconds", 0.4))
    if not 0 <= transition_seconds < min(float(s["duration"]) for s in scenes):
        raise ValueError("subtitle_transition_duration_invalid")

    captions: list[dict] = []
    cursor = 0.0
    for idx, scene in enumerate(scenes, start=1):
        text = str(scene.get("caption", ""))
        duration = float(scene["duration"])
        end = cursor + duration
        captions.append({
            "index": idx,
            "start": round(cursor, 3),
            "end": round(end, 3),
            "text": text,
        })
        cursor = end - transition_seconds

    # Fix last caption end time (no overlap subtraction on final scene)
    if captions:
        last_scene_end = sum(float(s["duration"]) for s in scenes[:-1]) + float(scenes[-1]["duration"])
        captions[-1]["end"] = round(last_scene_end, 3)
        for previous, current in zip(captions, captions[1:]):
            previous["end"] = min(float(previous["end"]), float(current["start"]))

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(
            f"{c['index']}\n{_timestamp(float(c['start']))} --> {_timestamp(float(c['end']))}\n{c['text']}\n"
            for c in captions
        ),
        encoding="utf-8",
    )
    return captions
