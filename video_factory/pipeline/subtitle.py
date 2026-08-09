"""Turn a short line-based script into a deterministic SRT file."""

from __future__ import annotations

import re
import textwrap
from typing import Any
from pathlib import Path

from .errors import FactoryContractError


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


def build_srt_from_timeline(
    timeline_doc: dict,
    target: Path,
    *,
    composition: dict[str, Any] | None = None,
) -> list[dict]:
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

    composition = composition or timeline_doc.get("composition")
    if isinstance(composition, dict):
        captions = SubtitleLayoutEngine(composition).build_cues(timeline_doc)
        _write_srt(captions, target)
        return captions

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

    _write_srt(captions, target)
    return captions


def _write_srt(captions: list[dict[str, object]], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(
            f"{caption['index']}\n"
            f"{_timestamp(float(caption['start']))} --> {_timestamp(float(caption['end']))}\n"
            f"{caption['text']}\n"
            for caption in captions
        ),
        encoding="utf-8",
    )


class SubtitleLayoutEngine:
    """Deterministic subtitle layout for a composition contract.

    The engine performs text layout and safe-region validation before FFmpeg is
    invoked.  It deliberately does not inspect pixels: the renderer receives
    the same validated region and style values, so the contract remains
    deterministic and testable.
    """

    DEFAULT_MIN_CHARS = 14
    DEFAULT_MAX_CHARS = 18
    DEFAULT_MAX_LINES = 2
    DEFAULT_FONT_SIZE = 56
    MIN_CUE_SECONDS = 1.0

    def __init__(self, composition: dict[str, Any]) -> None:
        self.composition = composition
        regions = composition.get("regions")
        style = composition.get("subtitle_style")
        if not isinstance(regions, dict) or not isinstance(style, dict):
            raise FactoryContractError(
                "subtitle_layout_invalid",
                "Composition does not contain subtitle layout settings.",
                {"field": "regions/subtitle_style"},
            )
        self.regions = regions
        self.style = style
        self._validate_safe_regions()

    def _validate_safe_regions(self) -> None:
        content = self._rect("content_area")
        subtitle = self._rect("subtitle_area")
        if self._overlap(content, subtitle):
            raise FactoryContractError(
                "subtitle_overlap_content",
                "Subtitle region overlaps the content region.",
                {"content_region": "content_area", "subtitle_region": "subtitle_area"},
            )
        font_size = int(self.style.get("font_size", self.DEFAULT_FONT_SIZE))
        min_chars = int(self.style.get("min_chars_per_line", self.DEFAULT_MIN_CHARS))
        max_chars = int(self.style.get("max_chars_per_line", self.DEFAULT_MAX_CHARS))
        max_lines = int(self.style.get("max_lines", self.DEFAULT_MAX_LINES))
        if not 52 <= font_size <= 60 or min_chars < 1 or not min_chars <= max_chars or max_lines != 2:
            raise FactoryContractError(
                "subtitle_layout_invalid",
                "Subtitle style is outside the knowledge layout contract.",
                {"field": "subtitle_style"},
            )

    def _rect(self, name: str) -> tuple[float, float, float, float]:
        value = self.regions.get(name)
        if not isinstance(value, dict):
            raise FactoryContractError(
                "subtitle_layout_invalid",
                "Composition region is missing.",
                {"region": name},
            )
        try:
            x, y = float(value["x"]), float(value["y"])
            width, height = float(value["width"]), float(value["height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise FactoryContractError(
                "subtitle_layout_invalid",
                "Composition region has invalid geometry.",
                {"region": name},
            ) from exc
        return x, y, width, height

    @staticmethod
    def _overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah

    def build_cues(self, timeline_doc: dict[str, Any]) -> list[dict[str, object]]:
        scenes = timeline_doc.get("scenes")
        if not isinstance(scenes, list) or not scenes:
            raise FactoryContractError(
                "subtitle_layout_invalid",
                "Timeline has no scenes for subtitle layout.",
                {"field": "timeline.scenes"},
            )
        transition = float(timeline_doc.get("transition_seconds", 0.4))
        max_chars = int(self.style.get("max_chars_per_line", self.DEFAULT_MAX_CHARS))
        max_lines = int(self.style.get("max_lines", self.DEFAULT_MAX_LINES))
        max_units = max_chars * max_lines
        captions: list[dict[str, object]] = []
        cursor = 0.0
        for scene_index, scene in enumerate(scenes):
            duration = float(scene["duration"])
            scene_end = cursor + duration
            visible_end = scene_end if scene_index == len(scenes) - 1 else scene_end - transition
            text = _normalize_caption(str(scene.get("caption", "")))
            if not text:
                cursor = visible_end
                continue
            parts = _split_caption_parts(text, max_units=max_units)
            weights = [max(1, len(part.replace("\n", ""))) for part in parts]
            visible_duration = max(0.0, visible_end - cursor)
            if visible_duration < self.MIN_CUE_SECONDS * len(parts):
                raise FactoryContractError(
                    "subtitle_layout_invalid",
                    "Subtitle scene does not have enough time for its cues.",
                    {"scene_order": scene_index + 1, "cue_count": len(parts)},
                )
            total_weight = sum(weights)
            cue_cursor = cursor
            for part_index, (part, weight) in enumerate(zip(parts, weights)):
                cue_end = visible_end if part_index == len(parts) - 1 else cue_cursor + visible_duration * weight / total_weight
                if cue_end - cue_cursor < self.MIN_CUE_SECONDS:
                    raise FactoryContractError(
                        "subtitle_layout_invalid",
                        "Subtitle cue is shorter than the readable minimum.",
                        {"scene_order": scene_index + 1, "cue_index": part_index + 1},
                    )
                captions.append({
                    "index": len(captions) + 1,
                    "start": round(cue_cursor, 3),
                    "end": round(cue_end, 3),
                    "text": _wrap_caption(part, max_chars, max_lines),
                    "scene_id": scene.get("scene_id", f"s{scene_index + 1:02d}"),
                    "region": "subtitle_area",
                })
                cue_cursor = cue_end
            cursor = visible_end
        for previous, current in zip(captions, captions[1:]):
            if float(previous["end"]) > float(current["start"]):
                raise FactoryContractError(
                    "subtitle_layout_invalid",
                    "Subtitle cues overlap during a transition.",
                    {"previous_index": previous["index"], "current_index": current["index"]},
                )
        return captions


def _normalize_caption(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _split_caption_parts(text: str, *, max_units: int) -> list[str]:
    if len(text) <= max_units:
        return [text]
    sentences = [part for part in re.split(r"(?<=[。！？；，、：])", text) if part]
    parts: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) <= max_units and len(current) + len(sentence) <= max_units:
            current += sentence
            continue
        if current:
            parts.append(current)
            current = ""
        while len(sentence) > max_units:
            parts.append(sentence[:max_units])
            sentence = sentence[max_units:]
        current = sentence
    if current:
        parts.append(current)
    return parts or [text[:max_units]]
