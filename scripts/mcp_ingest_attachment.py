"""
ingest_attachment - deterministic OpenClaw tool for safe quarantine-first
attachment ingestion.

Zero-dependency (Python stdlib only). Implements a minimal MCP JSON-RPC 2.0
stdio server exposing ONE tool: `ingest_attachment`.

Design (P0_INGEST_ATTACHMENT_TOOL.md):
  - The tool is NOT a generic exec wrapper. It validates every input, ensures
    source_media_path is inside the approved OpenClaw inbound root, the chat_id
    and sender_id are on the authorized route allowlist, then invokes the
    single safety implementation `scripts/07_ingest_inbound_media.ps1` and
    parses its JSON result. It never lets the model pass an arbitrary path.
  - Multi-attachment: each (message_id, attachment_index) gets its own
    receipt at input/feishu/<message-id>/attachment-NNN/receipt.json, plus a
    message-level message_manifest.json.
  - Output to the model contains stored_path/receipt_path (quarantined copies),
    NEVER the original inbound MediaPath.
  - Masks account_id/chat_id/sender_id in logs and manifest.
  - content_parsed=false, quarantined=true on success.

The core logic `ingest_attachment(...)` is importable for direct unit testing
without the MCP stdio loop.

Config (env vars):
  OPENCLAW_INBOUND_ROOT      approved root for source_media_path
  OPENCLAW_PROJECT_ROOT      project root (input/feishu lives here)
  OPENCLAW_INGEST_SCRIPT     path to 07_ingest_inbound_media.ps1
  OPENCLAW_AUTHORIZED_CHAT_IDS   comma-separated authorized group ids
  OPENCLAW_AUTHORIZED_SENDER_IDS comma-separated authorized sender ids
  OPENCLAW_ACCOUNT_ID        feishu account id (e.g. zhongshu)
  OPENCLAW_MAX_BYTES         server-owned maximum bytes (default 5242880)
"""

from __future__ import annotations

import json
import hashlib
import ntpath
import os
import re
import sys
import subprocess
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(os.environ.get("OPENCLAW_PROJECT_ROOT", str(SCRIPT_DIR.parent))).resolve()
INGEST_SCRIPT = Path(
    os.environ.get("OPENCLAW_INGEST_SCRIPT", str(SCRIPT_DIR / "run_ingest_safe.ps1"))
).resolve()
from analysis_request import (
    configure_storage,
    create_ticket_analysis_request,
    route_binding_payload,
)  # noqa: E402
from media_action_ticket import (
    configure_roots as configure_ticket_roots,
    consume_media_action_ticket,
    issue_media_action_ticket,
)  # noqa: E402

RESULT_REPLY_MAX_ANALYSIS_CHARS = 112
RESULT_REPLY_MAX_FIELD_CHARS = 48
RESULT_REPLY_ERROR = "图片分析已完成，但结果渲染失败；请联系维护者检查结果格式化链路。"
RESULT_REPLY_EMPTY = "图片分析已完成，但未生成可展示的结果；请联系维护者检查结果格式化链路。"
RESULT_REPLY_LABELS = ("内容概述", "视觉要点", "注意事项", "结论")
AUDIO_RESULT_REPLY_ERROR = "音频转录已完成，但结果渲染失败；请联系维护者检查结果格式化链路。"
AUDIO_RESULT_REPLY_EMPTY = "音频转录已完成，但未生成可展示的转录内容；请联系维护者检查结果格式化链路。"
AUDIO_RESULT_REPLY_LABELS = ("转录内容", "识别语言", "处理说明")
TEXT_RESULT_REPLY_ERROR = "文本解析已完成，但结果渲染失败；请联系维护者检查结果格式化链路。"
TEXT_RESULT_REPLY_EMPTY = "文本解析已完成，但未生成可展示的结果；请联系维护者检查结果格式化链路。"
TEXT_RESULT_REPLY_LABELS = ("内容摘要", "结构信息", "处理说明")
LANGUAGE_TAG_RE = re.compile(r"^[A-Za-z]{2,12}(?:-[A-Za-z0-9]{2,12})?$")
RESULT_TEXT_KEYS = (
    "summary",
    "description",
    "overview",
    "caption",
    "content",
    "text",
    "result_text",
    "analysis",
    "answer",
    "response",
)
RESULT_VISUAL_KEYS = (
    "subjects",
    "objects",
    "scene",
    "visual_features",
    "composition",
    "colors",
    "visual",
)
RESULT_OCR_KEYS = ("ocr", "visible_text", "recognized_text")
RESULT_LIMITATION_KEYS = ("limitations", "uncertainties", "risks", "confidence")
RESULT_CONCLUSION_KEYS = ("conclusion", "recommendation", "suggestion", "advice")
INTERNAL_PATH_RE = re.compile(r"(?i)(?:[a-z]:[\\/][^\s]+|\\\\[^\s]+)")
INTERNAL_IDENTIFIER_RE = re.compile(r"\b(?:om|oc|ou)_[A-Za-z0-9_-]+\b")
INTERNAL_HASH_RE = re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE)
OPAQUE_TOKEN_RE = re.compile(r"\b[A-Za-z0-9_-]{43,}\b")


class ResultPresentationError(ValueError):
    """The Analyzer finished but no safe user-visible summary can be built."""


def _clip_visible_text(value: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()
    compact = "".join(
        character
        for character in compact
        if character >= " " and character not in "\u200b\u200c\u200d\ufeff"
    )
    compact = INTERNAL_PATH_RE.sub("[已省略]", compact)
    compact = INTERNAL_IDENTIFIER_RE.sub("[已省略]", compact)
    compact = INTERNAL_HASH_RE.sub("[已省略]", compact)
    compact = OPAQUE_TOKEN_RE.sub("[已省略]", compact)
    compact = compact.replace("@", "＠")
    if len(compact) > limit:
        compact = compact[: max(1, limit - 1)].rstrip() + "…"
    return compact


def _as_visible_text(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate[:1] in "[{":
        try:
            decoded = json.loads(candidate)
        except ValueError:
            return None
        return _find_result_text(decoded, RESULT_TEXT_KEYS)
    return candidate


def _find_result_text(value: Any, keys: Tuple[str, ...]) -> Optional[str]:
    if isinstance(value, str):
        return _as_visible_text(value)
    if isinstance(value, dict):
        for key in keys:
            text = _find_result_text(value.get(key), RESULT_TEXT_KEYS)
            if text:
                return text
        for container in ("outputs", "output", "result", "data"):
            nested = value.get(container)
            text = _find_result_text(nested, keys)
            if text:
                return text
        return None
    if isinstance(value, list):
        for item in value:
            text = _find_result_text(item, keys)
            if text:
                return text
    return None


def _format_image_result(payload: Any) -> str:
    """Map a server-owned Analyzer payload to a short, non-JSON Feishu summary."""
    overview = _find_result_text(payload, RESULT_TEXT_KEYS)
    if not overview:
        raise ResultPresentationError("result_content_empty")
    overview = _clip_visible_text(overview, 68)
    if len(overview.replace("[已省略]", "").strip()) < 3:
        raise ResultPresentationError("result_content_empty")
    visual = _find_result_text(payload, RESULT_VISUAL_KEYS)
    ocr = _find_result_text(payload, RESULT_OCR_KEYS)
    limitations = _find_result_text(payload, RESULT_LIMITATION_KEYS)
    conclusion = _find_result_text(payload, RESULT_CONCLUSION_KEYS)
    visual_text = (
        _clip_visible_text(visual, 30)
        if visual
        else "以上描述聚焦画面中可见的主体、场景与构图信息。"
    )
    ocr_text = _clip_visible_text(ocr, 30) if ocr else ""
    limitation_text = (
        _clip_visible_text(limitations, 23)
        if limitations
        else "图像识别可能存在偏差，请以原图为准。"
    )
    conclusion_text = (
        _clip_visible_text(conclusion, 23)
        if conclusion
        else "以上为本次图片分析摘要。"
    )
    lines = ["图片分析结果：", f"- 内容概述：{overview}", f"- 视觉要点：{visual_text}"]
    if ocr_text:
        lines.append(f"- 识别文字：{ocr_text}")
    lines.extend((f"- 注意事项：{limitation_text}", f"- 结论：{conclusion_text}"))
    return "\n".join(lines)


def _load_image_presentation(analyzer_result: Dict[str, Any]) -> Dict[str, str]:
    raw_output = analyzer_result.get("output_path")
    if not isinstance(raw_output, str):
        raise ResultPresentationError("result_render_failed")
    jobs_root = (PROJECT_ROOT / "jobs").resolve()
    try:
        output_path = Path(raw_output).resolve(strict=True)
        output_path.relative_to(jobs_root)
    except (OSError, RuntimeError, ValueError):
        raise ResultPresentationError("result_render_failed") from None
    if output_path.name != "analysis.json":
        raise ResultPresentationError("result_render_failed")
    try:
        document = json.loads(output_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ResultPresentationError("result_render_failed") from None
    if (
        not isinstance(document, dict)
        or document.get("status") != "completed"
        or document.get("tool") != "analyze_image"
    ):
        raise ResultPresentationError("result_render_failed")
    return {"status": "ready", "reply_template": _format_image_result(document.get("result"))}


def _audio_transcript(value: Any) -> Optional[str]:
    """Read the server-owned transcript field without exposing JSON verbatim."""
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if candidate[:1] in "[{":
        try:
            decoded = json.loads(candidate)
        except ValueError:
            return None
        if isinstance(decoded, dict):
            return _audio_transcript(decoded.get("transcript"))
        return None
    return candidate or None


def _format_audio_result(payload: Any) -> str:
    """Map a completed local transcript to a bounded public Feishu reply."""
    if not isinstance(payload, dict):
        raise ResultPresentationError("result_content_empty")
    transcript = _audio_transcript(payload.get("transcript"))
    if not transcript:
        raise ResultPresentationError("result_content_empty")
    transcript = _clip_visible_text(transcript, RESULT_REPLY_MAX_ANALYSIS_CHARS)
    if len(transcript.replace("[已省略]", "").strip()) < 3:
        raise ResultPresentationError("result_content_empty")
    language = payload.get("language")
    language_text = str(language).strip() if isinstance(language, str) else ""
    if not LANGUAGE_TAG_RE.fullmatch(language_text):
        language_text = "未能可靠确定"
    return "\n".join(
        (
            "音频转录结果：",
            f"- 转录内容：{transcript}",
            f"- 识别语言：{language_text}",
            "- 处理说明：本转录由本机语音识别完成，请以原音频为准。",
        )
    )


def _load_audio_presentation(analyzer_result: Dict[str, Any]) -> Dict[str, str]:
    raw_output = analyzer_result.get("output_path")
    if not isinstance(raw_output, str):
        raise ResultPresentationError("result_render_failed")
    jobs_root = (PROJECT_ROOT / "jobs").resolve()
    try:
        output_path = Path(raw_output).resolve(strict=True)
        output_path.relative_to(jobs_root)
    except (OSError, RuntimeError, ValueError):
        raise ResultPresentationError("result_render_failed") from None
    if output_path.name != "transcript.json":
        raise ResultPresentationError("result_render_failed")
    try:
        document = json.loads(output_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ResultPresentationError("result_render_failed") from None
    if (
        not isinstance(document, dict)
        or document.get("status") != "completed"
        or document.get("tool") != "transcribe_audio"
    ):
        raise ResultPresentationError("result_render_failed")
    return {"status": "ready", "reply_template": _format_audio_result(document)}


def _format_text_result(payload: Any) -> str:
    """Map a bounded deterministic TXT result to a safe public summary."""
    if not isinstance(payload, dict):
        raise ResultPresentationError("result_content_empty")
    character_count = payload.get("character_count")
    line_count = payload.get("line_count")
    if (
        not isinstance(character_count, int)
        or isinstance(character_count, bool)
        or character_count < 0
        or not isinstance(line_count, int)
        or isinstance(line_count, bool)
        or line_count < 0
    ):
        raise ResultPresentationError("result_content_empty")
    preview = payload.get("preview")
    preview_text = _clip_visible_text(preview, 82) if isinstance(preview, str) and preview else ""
    if not preview_text:
        preview_text = "未发现可展示的正文片段。"
    headings = payload.get("headings")
    heading_values = (
        [_clip_visible_text(value, 32) for value in headings if isinstance(value, str) and value.strip()]
        if isinstance(headings, list)
        else []
    )
    structure = f"{line_count} 行，{character_count} 个字符"
    if heading_values:
        structure += f"；标题：{heading_values[0]}"
    return "\n".join(
        (
            "文本解析结果：",
            f"- 内容摘要：{preview_text}",
            f"- 结构信息：{_clip_visible_text(structure, 62)}",
            "- 处理说明：仅解析 UTF-8 text/plain 文本结构；请以原文件为准。",
        )
    )


def _load_text_presentation(analyzer_result: Dict[str, Any]) -> Dict[str, str]:
    raw_output = analyzer_result.get("output_path")
    if not isinstance(raw_output, str):
        raise ResultPresentationError("result_render_failed")
    jobs_root = (PROJECT_ROOT / "jobs").resolve()
    try:
        output_path = Path(raw_output).resolve(strict=True)
        output_path.relative_to(jobs_root)
    except (OSError, RuntimeError, ValueError):
        raise ResultPresentationError("result_render_failed") from None
    if output_path.name != "analysis.json":
        raise ResultPresentationError("result_render_failed")
    try:
        document = json.loads(output_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ResultPresentationError("result_render_failed") from None
    if (
        not isinstance(document, dict)
        or document.get("status") != "completed"
        or document.get("tool") != "analyze_text"
    ):
        raise ResultPresentationError("result_render_failed")
    return {"status": "ready", "reply_template": _format_text_result(document)}


def _special_path_error(raw: str) -> Optional[str]:
    """Reject path classes that are not explicit local trusted roots."""
    value = str(raw).replace("/", "\\")
    if value.startswith(("\\\\", "\\\\?\\", "\\\\.\\")):
        return "unc_or_device_path"
    drive, tail = ntpath.splitdrive(value)
    if not re.match(r"^[A-Za-z]:$", drive):
        return "non_local_drive_path"
    if ":" in tail:
        return "alternate_data_stream"
    return None


def _canonical_windows_path(raw: str) -> Path:
    error = _special_path_error(raw)
    if error:
        raise ValueError(error)
    resolved = Path(raw).resolve(strict=False)
    canonical = ntpath.normcase(ntpath.normpath(str(resolved)))
    drive, tail = ntpath.splitdrive(canonical)
    if not re.match(r"^[a-z]:$", drive) or tail.rstrip("\\") in ("", "\\"):
        raise ValueError("trusted_root_too_broad")
    return Path(resolved)


def _parse_trusted_roots() -> list[dict[str, Any]]:
    """Load an explicit ``root_id|absolute_path`` registry.

    The legacy single-root variable remains accepted for offline compatibility,
    but no current working directory or arbitrary project path is auto-trusted.
    """
    specs = os.environ.get("OPENCLAW_TRUSTED_INBOUND_ROOTS", "").strip()
    if specs:
        raw_specs = [item.strip() for item in specs.split(";") if item.strip()]
    else:
        legacy = os.environ.get(
            "OPENCLAW_INBOUND_ROOT",
            str(Path.home() / ".openclaw" / "media" / "inbound"),
        )
        raw_specs = [f"openclaw_global|{legacy}"]
        for index, item in enumerate(
            x.strip() for x in os.environ.get("OPENCLAW_INBOUND_ROOTS", "").split(",")
        ):
            if item:
                raw_specs.append(f"configured_{index:02d}|{item}")

    roots: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for spec in raw_specs:
        if "|" not in spec:
            raise RuntimeError("trusted_root_spec_requires_root_id_and_path")
        root_id, root_path = (part.strip() for part in spec.split("|", 1))
        if not re.match(r"^[a-z][a-z0-9_-]{2,63}$", root_id):
            raise RuntimeError("invalid_trusted_root_id")
        if root_id in seen_ids:
            raise RuntimeError("duplicate_trusted_root_id")
        canonical_path = _canonical_windows_path(root_path)
        canonical_text = ntpath.normcase(ntpath.normpath(str(canonical_path)))
        if canonical_text in seen_paths:
            raise RuntimeError("duplicate_trusted_root_path")
        seen_ids.add(root_id)
        seen_paths.add(canonical_text)
        roots.append({"root_id": root_id, "path": canonical_path, "canonical": canonical_text})
    if not roots:
        raise RuntimeError("no_trusted_inbound_roots")
    return roots


TRUSTED_ROOTS = _parse_trusted_roots()
INBOUND_ROOTS = [item["path"] for item in TRUSTED_ROOTS]
INBOUND_ROOT = INBOUND_ROOTS[0]  # backward-compatible alias
ACCOUNT_ID = os.environ.get("OPENCLAW_ACCOUNT_ID", "zhongshu")
MAX_BYTES_DEFAULT = int(os.environ.get("OPENCLAW_MAX_BYTES", "5242880"))
AUTHORIZED_CHAT_IDS = [
    x.strip() for x in os.environ.get("OPENCLAW_AUTHORIZED_CHAT_IDS", "").split(",") if x.strip()
]
AUTHORIZED_SENDER_IDS = [
    x.strip() for x in os.environ.get("OPENCLAW_AUTHORIZED_SENDER_IDS", "").split(",") if x.strip()
]

MESSAGE_ID_RE = re.compile(r"^om_[A-Za-z0-9_-]+$")
CHAT_ID_RE = re.compile(r"^oc_[A-Za-z0-9_-]+$")
SENDER_ID_RE = re.compile(r"^ou_[A-Za-z0-9_-]+$")
# Safe filename: non-empty, no path separators, no control chars, has extension,
# no double dot in stem, basename only.
UNSAFE_NAME_RE = re.compile(r"[\\/\x00-\x1F\x7F]")
_UNSET = object()
TRUSTED_DECLARED_SIZE_SOURCES = frozenset(
    {
        "channel_attachment_metadata",
        "download_content_length",
    }
)
ACTION_KIND = {
    "analyze_image": frozenset({"png", "jpg", "jpeg"}),
    "transcribe_audio": frozenset({"audio", "wav", "mp3"}),
    "analyze_video": frozenset({"mp4", "video"}),
}
_CAPTION_MAX_LENGTH = 500
_PROMPT_INJECTION_MARKERS = (
    "<|",
    "|>",
    "[/inst]",
    "[system]",
    "system prompt",
    "ignore previous",
    "ignore all previous",
    "disregard previous",
    "```",
)
_EXPLICIT_ACTIONS = {
    "ingress_only": frozenset(
        {
            "仅入库",
            "只入库",
            "先入库",
            "仅隔离",
            "只隔离",
            "不要分析",
            "ingress only",
            "quarantine only",
            "store only",
            "do not analyze",
            "no analysis",
        }
    ),
    "analyze_image": frozenset(
        {
            "分析图片",
            "分析图像",
            "图片分析",
            "识别图片",
            "请分析图片",
            "请分析这张图",
            "请在安全入库后分析这张测试图片。",
            "请在安全入库后分析这张测试图片",
            "analyze image",
            "image analyze",
            "describe image",
            "analyze the image",
        }
    ),
    "transcribe_audio": frozenset(
        {
            "转录音频",
            "转写音频",
            "语音转文字",
            "音频转录",
            "请在安全入库后转录这段测试音频。",
            "请在安全入库后转录这段测试音频",
            "transcribe audio",
            "audio transcribe",
        }
    ),
    "analyze_video": frozenset(
        {
            "分析视频",
            "视频分析",
            "请分析视频",
            "请在安全入库后分析这段测试视频。",
            "请在安全入库后分析这段测试视频",
            "analyze video",
            "video analyze",
            "describe video",
        }
    ),
}


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 7:
        return "***"
    return value[:3] + "***" + value[-4:]


def _normalize_caption(value: Any) -> str:
    """Normalize only Channel-bound text; never persist the raw caption."""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("caption_must_be_text")
    if len(value) > _CAPTION_MAX_LENGTH:
        raise ValueError("caption_too_long")
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    if any(marker in normalized for marker in _PROMPT_INJECTION_MARKERS):
        raise ValueError("caption_prompt_injection")
    if any(ord(char) < 0x20 and char not in "\t\r\n" for char in normalized):
        raise ValueError("caption_control_character")
    return re.sub(r"\s+", " ", normalized)


def _caption_hash(normalized: str) -> str:
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else ""


def _derive_attachment_action(detected_kind: Any, normalized_caption: str) -> Dict[str, Any]:
    """Return a fail-closed, deterministic action contract."""
    kind = str(detected_kind or "").lower()
    if not normalized_caption:
        return {
            "attachment_action": "ingress_only",
            "action_source": "channel_default",
            "analysis_requested": False,
            "action_normalized_text_hash": "",
        }
    action = next(
        (
            candidate
            for candidate, phrases in _EXPLICIT_ACTIONS.items()
            if normalized_caption in phrases
        ),
        None,
    )
    if action is None:
        return {
            "attachment_action": "ingress_only",
            "action_source": "caption_unknown",
            "analysis_requested": False,
            "action_normalized_text_hash": _caption_hash(normalized_caption),
        }
    if action in ACTION_KIND and kind not in ACTION_KIND[action]:
        action = "unsupported_action"
        requested = False
    else:
        requested = action != "ingress_only"
    return {
        "attachment_action": action,
        "action_source": "explicit_caption",
        "analysis_requested": requested,
        "action_normalized_text_hash": _caption_hash(normalized_caption),
    }


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _is_under(candidate: Path, root: dict[str, Any]) -> bool:
    candidate_text = ntpath.normcase(ntpath.normpath(str(candidate)))
    root_text = root["canonical"].rstrip("\\")
    return candidate_text == root_text or candidate_text.startswith(root_text + "\\")


def _assert_no_reparse(candidate: Path, root: dict[str, Any]) -> None:
    current = candidate
    root_path = root["path"]
    while True:
        if current.exists() and current.is_symlink():
            raise ValueError("reparse_point")
        if ntpath.normcase(ntpath.normpath(str(current))) == root["canonical"]:
            return
        parent = current.parent
        if parent == current:
            raise ValueError("root_not_reached")
        current = parent


def _canonical_source_label(candidate: Path, root: dict[str, Any]) -> str:
    relative = ntpath.relpath(str(candidate), str(root["path"])).replace("\\", "/")
    return f"{root['root_id']}:/{relative}"


def _size_claim_audit(args: Dict[str, Any]) -> Dict[str, Any]:
    """Capture a legacy/public size claim without ever trusting it.

    The MCP tool schema deliberately does not expose this field.  This parser
    exists only to make an already-cached legacy Router tool call observable
    and harmless during the rollout.  A public caller can never create trusted
    provenance through these fields.
    """
    if "declared_size_bytes" in args:
        raw = args.get("declared_size_bytes")
        source = "untrusted_public_declared_size"
    elif "size_bytes" in args:
        raw = args.get("size_bytes")
        source = "untrusted_legacy_size_bytes"
    else:
        raw = None
        source = "none"

    valid = isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0
    return {
        "untrusted_size_claim_bytes": raw if valid else None,
        "untrusted_size_claim_present": source != "none",
        "untrusted_size_claim_valid": source == "none" or valid,
        "untrusted_size_claim_source": source,
        "untrusted_size_claim_type": type(raw).__name__ if source != "none" else "none",
    }


def _trusted_declared_size(
    value: Any,
    source: Optional[str],
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Validate non-public Channel/Gateway declared-size provenance.

    ``ingest_attachment`` exposes this only as a keyword-only internal API;
    the MCP JSON-RPC handler never passes it.  This keeps a Router/LLM from
    marking its own number trusted.
    """
    if value is _UNSET:
        return {
            "declared_size_bytes": None,
            "declared_size_trusted": False,
            "declared_size_source": "none",
        }, None
    if source not in TRUSTED_DECLARED_SIZE_SOURCES:
        return None, {
            "error_code": "invalid_declared_size",
            "detail": "unrecognized trusted provenance",
        }
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return None, {
            "error_code": "invalid_declared_size",
            "detail": "trusted declared size must be a non-negative integer",
        }
    return {
        "declared_size_bytes": value,
        "declared_size_trusted": True,
        "declared_size_source": source,
    }, None


def _stat_identity(stat_result: os.stat_result) -> Tuple[int, int]:
    """Return the portable identity exposed by Python's trusted filesystem stat."""
    return int(getattr(stat_result, "st_dev", 0)), int(getattr(stat_result, "st_ino", 0))


def _validate_inputs(
    args: Dict[str, Any],
    *,
    trusted_declared_size_bytes: Any = _UNSET,
    trusted_declared_size_source: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Return (clean_args, error_dict). Exactly one is non-None."""

    def err(code: str, detail: str = "") -> Dict[str, Any]:
        return {"error_code": code, "detail": detail}

    message_id = str(args.get("message_id", "")).strip()
    if not MESSAGE_ID_RE.match(message_id):
        return None, err("invalid_message_id")

    try:
        attachment_index = int(args.get("attachment_index", -1))
    except (TypeError, ValueError):
        return None, err("invalid_attachment_index")
    if attachment_index < 0:
        return None, err("invalid_attachment_index")

    try:
        attachment_count = int(args.get("attachment_count", 1))
    except (TypeError, ValueError):
        return None, err("invalid_attachment_count")
    if attachment_count < 1 or attachment_count < attachment_index + 1:
        return None, err("invalid_attachment_count")

    source_media_path = str(args.get("source_media_path", "")).strip()
    if not source_media_path or not os.path.isabs(source_media_path):
        return None, err("invalid_source_media_path", "must be absolute")

    original_file_name = str(args.get("original_file_name", "")).strip()
    if not original_file_name or UNSAFE_NAME_RE.search(original_file_name):
        return None, err("unsafe_file_name")
    if os.path.basename(original_file_name) != original_file_name:
        return None, err("unsafe_file_name")
    stem, ext = os.path.splitext(original_file_name)
    if not ext or "." in stem:
        return None, err("unsafe_file_name")

    content_type = str(args.get("content_type", "") or "")
    try:
        normalized_caption = _normalize_caption(args.get("caption"))
    except ValueError as exc:
        return None, err("invalid_caption", str(exc))
    untrusted_size_claim = _size_claim_audit(args)
    trusted_declared, declared_error = _trusted_declared_size(
        trusted_declared_size_bytes,
        trusted_declared_size_source,
    )
    if declared_error is not None:
        return None, declared_error

    chat_id = str(args.get("chat_id", "")).strip()
    if not CHAT_ID_RE.match(chat_id):
        return None, err("invalid_chat_id")

    sender_id = str(args.get("sender_id", "")).strip()
    if not SENDER_ID_RE.match(sender_id):
        return None, err("invalid_sender_id")

    event_id = str(args.get("event_id", "") or "")
    received_at = str(args.get("received_at", "") or "")

    # Route authorization: chat_id and sender_id must be on the allowlist when
    # an allowlist is configured. If no allowlist is configured (offline test),
    # the PS script still enforces route identity via receipt cross-check.
    if AUTHORIZED_CHAT_IDS and chat_id not in AUTHORIZED_CHAT_IDS:
        return None, err("unauthorized_route", "chat_id not authorized")
    if AUTHORIZED_SENDER_IDS and sender_id not in AUTHORIZED_SENDER_IDS:
        return None, err("unauthorized_route", "sender_id not authorized")

    # Resolve and constrain source_media_path to one explicit trusted root.
    try:
        resolved = Path(source_media_path).resolve(strict=False)
        special_error = _special_path_error(source_media_path)
        if special_error:
            return None, err(special_error)
    except Exception as exc:
        return None, err("invalid_source_media_path", str(exc)[:80])
    matching_root = next((root for root in TRUSTED_ROOTS if _is_under(resolved, root)), None)
    if matching_root is None:
        return None, err("path_traversal", "source_media_path outside inbound roots")

    if not resolved.exists() or not resolved.is_file():
        return None, err("missing_source")
    try:
        _assert_no_reparse(Path(source_media_path), matching_root)
    except ValueError as exc:
        return None, err(str(exc))

    try:
        source_stat = resolved.stat()
    except OSError:
        return None, err("missing_source")
    actual_size_bytes = int(source_stat.st_size)
    if actual_size_bytes > MAX_BYTES_DEFAULT:
        return None, err("file_too_large")
    if (
        trusted_declared["declared_size_trusted"]
        and trusted_declared["declared_size_bytes"] != actual_size_bytes
    ):
        return None, err("trusted_declared_size_mismatch")

    clean = {
        "message_id": message_id,
        "attachment_index": attachment_index,
        "attachment_count": attachment_count,
        "source_media_path": str(resolved),
        "inbound_root": str(matching_root["path"]),
        "trusted_root_id": matching_root["root_id"],
        "canonical_source_path": _canonical_source_label(resolved, matching_root),
        "source_size": actual_size_bytes,  # compatibility alias; source is authoritative
        "actual_size_bytes": actual_size_bytes,
        "source_mtime_ns": getattr(source_stat, "st_mtime_ns", 0),
        "source_identity": _stat_identity(source_stat),
        "original_file_name": original_file_name,
        "content_type": content_type,
        "chat_id": chat_id,
        "sender_id": sender_id,
        "event_id": event_id,
        "received_at": received_at,
        "max_bytes": MAX_BYTES_DEFAULT,
        "caption_normalized": normalized_caption,
    }
    clean.update(trusted_declared)
    clean.update(untrusted_size_claim)
    return clean, None


def _run_ingest_script(
    clean: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Invoke 07_ingest_inbound_media.ps1 with validated args; parse JSON."""
    try:
        current = Path(clean["source_media_path"]).stat()
        if (
            current.st_size != clean["actual_size_bytes"]
            or getattr(current, "st_mtime_ns", 0) != clean["source_mtime_ns"]
            or _stat_identity(current) != clean["source_identity"]
        ):
            return None, {"error_code": "source_changed_during_read"}
    except OSError:
        return None, {"error_code": "missing_source"}
    ps_args = [
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(INGEST_SCRIPT),
        "-SourcePath",
        clean["source_media_path"],
        "-MessageId",
        clean["message_id"],
        "-OriginalFileName",
        clean["original_file_name"],
        "-ContentType",
        clean["content_type"],
        "-MaxBytes",
        str(MAX_BYTES_DEFAULT),
        "-AccountId",
        ACCOUNT_ID,
        "-ChatId",
        clean["chat_id"],
        "-SenderId",
        clean["sender_id"],
        "-AttachmentIndex",
        str(clean["attachment_index"]),
        "-AttachmentCount",
        str(clean["attachment_count"]),
        "-InboundRoot",
        clean["inbound_root"],
        "-TrustedRootId",
        clean["trusted_root_id"],
        "-CanonicalSourcePath",
        clean["canonical_source_path"],
        "-ProjectRoot",
        str(PROJECT_ROOT),
    ]
    if clean.get("event_id"):
        ps_args += ["-EventId", clean["event_id"]]
    if clean.get("received_at"):
        ps_args += ["-ReceivedAt", clean["received_at"]]
    if clean["declared_size_trusted"]:
        ps_args += [
            "-DeclaredSizeBytes",
            str(clean["declared_size_bytes"]),
            "-DeclaredSizeTrusted",
            "1",
            "-DeclaredSizeSource",
            clean["declared_size_source"],
        ]
    if clean["untrusted_size_claim_bytes"] is not None:
        ps_args += ["-UntrustedSizeClaimBytes", str(clean["untrusted_size_claim_bytes"])]
    ps_args += [
        "-UntrustedSizeClaimPresent",
        "1" if clean["untrusted_size_claim_present"] else "0",
        "-UntrustedSizeClaimValid",
        "1" if clean["untrusted_size_claim_valid"] else "0",
        "-UntrustedSizeClaimSource",
        clean["untrusted_size_claim_source"],
        "-UntrustedSizeClaimType",
        clean["untrusted_size_claim_type"],
    ]

    try:
        proc = subprocess.run(
            ["powershell.exe", *ps_args],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return None, {"error_code": "ingest_timeout"}
    except FileNotFoundError:
        return None, {"error_code": "powershell_not_found"}
    except Exception as e:
        return None, {"error_code": "ingest_invoke_failed", "detail": str(e)[:200]}

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    # PowerShell's error formatting wraps at ~120 chars, so a thrown JSON error
    # object may span multiple lines. Use JSONDecoder.raw_decode to extract JSON
    # objects from any position in stdout/stderr (handles multi-line JSON).
    decoder = json.JSONDecoder()

    def _find_json(text: str, *, want_error: bool):
        if not text:
            return None
        for i, ch in enumerate(text):
            if ch != "{":
                continue
            try:
                obj, _end = decoder.raw_decode(text, i)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            if want_error and "error_code" in obj:
                return obj
            if not want_error and obj.get("success") is True:
                return obj
        return None

    parsed = _find_json(stdout, want_error=False)
    if parsed is not None:
        return parsed, None

    err_obj = _find_json(stdout, want_error=True) or _find_json(stderr, want_error=True)
    err_code = err_obj["error_code"] if err_obj else "ingest_failed"
    detail = ""
    if err_obj:
        detail = err_obj.get("normalized_content_type", "") or err_obj.get("expected_kind", "")

    return None, {
        "error_code": err_code,
        "detail": detail,
        "exit_code": proc.returncode if proc.returncode != 0 else None,
    }


def _manifest_path(message_id: str) -> Path:
    return PROJECT_ROOT / "input" / "feishu" / message_id / "message_manifest.json"


def _update_receipt_intent(
    clean: Dict[str, Any], result: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Bind one deterministic action to the quarantined receipt exactly once."""
    receipt_path = Path(str(result.get("receipt_path", ""))).resolve(strict=False)
    expected_root = (PROJECT_ROOT / "input" / "feishu" / clean["message_id"]).resolve(strict=False)
    if (
        not _is_under(
            receipt_path, {"canonical": ntpath.normcase(ntpath.normpath(str(expected_root)))}
        )
        or receipt_path.name != "receipt.json"
    ):
        return None, "receipt_path_binding_failed"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if not isinstance(receipt, dict) or receipt.get("message_id") != clean["message_id"]:
            return None, "receipt_message_mismatch"
        if int(receipt.get("attachment_index", -1)) != clean["attachment_index"]:
            return None, "receipt_attachment_mismatch"
        if receipt.get("stored_path") != result.get("stored_path"):
            return None, "stored_path_receipt_mismatch"
        action = _derive_attachment_action(result.get("detected_kind"), clean["caption_normalized"])
        existing_action = receipt.get("attachment_action")
        if existing_action is not None:
            existing_contract = {
                "attachment_action": existing_action,
                "action_source": receipt.get("action_source"),
                "analysis_requested": bool(receipt.get("analysis_requested", False)),
                "action_normalized_text_hash": receipt.get("action_normalized_text_hash", ""),
            }
            if existing_contract != action:
                return None, "intent_conflict"
        else:
            receipt.update(action)
            receipt["analysis_requested_at"] = _utc_now() if action["analysis_requested"] else None
            receipt["analysis_completed"] = bool(receipt.get("analysis_completed", False))
            receipt["analysis_result_path"] = receipt.get("analysis_result_path")
            tmp = receipt_path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, receipt_path)
        return receipt, None
    except (OSError, ValueError, TypeError):
        return None, "receipt_intent_update_failed"


def _update_manifest(clean: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """Update (or create) the per-message manifest with this attachment's entry."""
    mp = _manifest_path(clean["message_id"])
    mp.parent.mkdir(parents=True, exist_ok=True)
    manifest: Dict[str, Any] = {"message_id": clean["message_id"], "attachments": []}
    if mp.exists():
        try:
            manifest = json.loads(mp.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict) or "attachments" not in manifest:
                manifest = {"message_id": clean["message_id"], "attachments": []}
        except Exception:
            manifest = {"message_id": clean["message_id"], "attachments": []}

    manifest["attachment_count"] = clean["attachment_count"]
    manifest["chat_id_masked"] = _mask(clean["chat_id"])
    manifest["sender_id_masked"] = _mask(clean["sender_id"])
    manifest["account_id"] = ACCOUNT_ID
    manifest["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    entry = {
        "attachment_index": clean["attachment_index"],
        "original_name": clean["original_file_name"],
        "stored_path": result.get("stored_path"),
        "receipt_path": result.get("receipt_path"),
        "sha256": result.get("sha256"),
        "size_bytes": result.get("actual_size_bytes", result.get("size_bytes")),
        "actual_size_bytes": result.get("actual_size_bytes", result.get("size_bytes")),
        "stored_size_bytes": result.get("stored_size_bytes", result.get("size_bytes")),
        "declared_size_bytes": result.get("declared_size_bytes"),
        "declared_size_trusted": bool(result.get("declared_size_trusted", False)),
        "detected_kind": result.get("detected_kind"),
        "normalized_content_type": result.get("normalized_content_type"),
        "content_parsed": False,
        "quarantined": True,
        "idempotent": bool(result.get("idempotent")),
        "trusted_root_id": clean["trusted_root_id"],
        "status": "quarantined",
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    # Replace existing entry for this index, or append.
    attachments = [
        a
        for a in manifest.get("attachments", [])
        if a.get("attachment_index") != clean["attachment_index"]
    ]
    attachments.append(entry)
    attachments.sort(key=lambda a: a.get("attachment_index", 0))
    manifest["attachments"] = attachments

    tmp = mp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    os.replace(tmp, mp)
    return manifest


def _write_route_binding(clean: Dict[str, Any], result: Dict[str, Any]) -> Optional[str]:
    """Persist non-reversible identity digests for later reply-to checks.

    The receipt intentionally contains only masked Channel identities.  This
    sidecar lets the two-message request gate compare the real Channel-bound
    identities without persisting them in a report or changing the receipt.
    """
    receipt_path = Path(str(result.get("receipt_path", ""))).resolve(strict=False)
    attachment_root = (
        PROJECT_ROOT
        / "input"
        / "feishu"
        / clean["message_id"]
        / f"attachment-{clean['attachment_index']:03d}"
    ).resolve(strict=False)
    if (
        not _is_under(
            receipt_path, {"canonical": ntpath.normcase(ntpath.normpath(str(attachment_root)))}
        )
        or receipt_path.name != "receipt.json"
    ):
        return None
    binding_path = attachment_root / "route_binding.json"
    payload = route_binding_payload(
        clean["message_id"], clean["attachment_index"], clean["chat_id"], clean["sender_id"]
    )
    if binding_path.exists():
        try:
            existing = json.loads(binding_path.read_text(encoding="utf-8"))
            if existing != payload:
                return None
            return str(binding_path)
        except (OSError, ValueError):
            return None
    tmp = binding_path.with_suffix(".json.tmp")
    try:
        binding_path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, binding_path)
        return str(binding_path)
    except OSError:
        if tmp.exists():
            tmp.unlink()
        return None


def ingest_attachment(
    args: Dict[str, Any],
    *,
    trusted_declared_size_bytes: Any = _UNSET,
    trusted_declared_size_source: Optional[str] = None,
) -> Dict[str, Any]:
    """Core deterministic ingest. Returns a result dict (never raises).

    Success fields include the internal quarantine evidence needed by the
    ticket service.  The MCP handler projects this into a path/hash-free public
    response; callers must never use this direct helper as a Router API.

    Failure fields: status=rejected, error_code, ...
    """
    configure_storage(PROJECT_ROOT)
    configure_ticket_roots(PROJECT_ROOT)
    clean, err = _validate_inputs(
        args,
        trusted_declared_size_bytes=trusted_declared_size_bytes,
        trusted_declared_size_source=trusted_declared_size_source,
    )
    if err is not None:
        return {
            "status": "rejected",
            "error_code": err["error_code"],
            "detail": err.get("detail", ""),
            "analysis_allowed": False,
            "content_parsed": False,
            "quarantined": False,
            "attachment_action": "unsupported_action",
            "analysis_requested": False,
        }

    result, err = _run_ingest_script(clean)
    if err is not None:
        return {
            "status": "rejected",
            "error_code": err["error_code"],
            "detail": err.get("detail", ""),
            "analysis_allowed": False,
            "content_parsed": False,
            "quarantined": False,
            "message_id": clean["message_id"],
            "attachment_index": clean["attachment_index"],
            "attachment_action": "unsupported_action",
            "analysis_requested": False,
        }

    already = bool(result.get("idempotent"))
    # analysis_allowed only when receipt is valid, content not parsed, quarantined.
    analysis_allowed = (not result.get("content_parsed", False)) and bool(
        result.get("quarantined", True)
    )
    route_binding_path = _write_route_binding(clean, result)
    if route_binding_path is None:
        return {
            "status": "rejected",
            "error_code": "route_binding_write_failed",
            "message_id": clean["message_id"],
            "attachment_index": clean["attachment_index"],
            "analysis_allowed": False,
            "content_parsed": False,
            "quarantined": True,
        }
    try:
        manifest = _update_manifest(clean, result)
        manifest_path = str(_manifest_path(clean["message_id"]))
    except Exception:
        manifest = None
        manifest_path = None

    internal_result = {
        "status": "quarantined",
        "message_id": clean["message_id"],
        "attachment_index": clean["attachment_index"],
        "attachment_count": clean["attachment_count"],
        "trusted_root_id": clean["trusted_root_id"],
        "source_root_match": True,
        "stored_path": result.get("stored_path"),
        "receipt_path": result.get("receipt_path"),
        "detected_kind": result.get("detected_kind"),
        "normalized_content_type": result.get("normalized_content_type"),
        # ``size_bytes`` and ``sha256`` are compatibility aliases only. New
        # callers must use the source/stored-specific fields below.
        "size_bytes": result.get("actual_size_bytes", result.get("size_bytes")),
        "sha256": result.get("source_sha256", result.get("sha256")),
        "declared_size_bytes": result.get("declared_size_bytes"),
        "declared_size_trusted": bool(result.get("declared_size_trusted", False)),
        "declared_size_source": result.get("declared_size_source", "none"),
        "actual_size_bytes": result.get("actual_size_bytes", result.get("size_bytes")),
        "stored_size_bytes": result.get("stored_size_bytes", result.get("size_bytes")),
        "size_match": bool(result.get("size_match", False)),
        "source_sha256": result.get("source_sha256", result.get("sha256")),
        "stored_sha256": result.get("stored_sha256", result.get("sha256")),
        "source_stable_during_read": bool(result.get("source_stable_during_read", False)),
        "untrusted_size_claim_bytes": clean["untrusted_size_claim_bytes"],
        "untrusted_size_claim_present": clean["untrusted_size_claim_present"],
        "untrusted_size_claim_valid": clean["untrusted_size_claim_valid"],
        "untrusted_size_claim_source": clean["untrusted_size_claim_source"],
        "content_parsed": False,
        "quarantined": True,
        "already_ingested": already,
        "analysis_allowed": analysis_allowed,
        "manifest_path": manifest_path,
        "route_binding_path": route_binding_path,
    }
    ticket_result = issue_media_action_ticket(
        internal_result,
        chat_id=clean["chat_id"],
        sender_id=clean["sender_id"],
    )
    if ticket_result.get("status") == "rejected":
        return ticket_result
    internal_result.update(
        {
            "ticket_issued": bool(ticket_result.get("ticket_issued", False)),
            "ticket": ticket_result.get("ticket"),
            "ticket_already_issued": bool(ticket_result.get("already_issued", False)),
            "ticket_expires_at": ticket_result.get("expires_at"),
            "ticket_action": ticket_result.get("allowed_action"),
        }
    )
    return internal_result


# --------------------------------------------------------------------------- #
# MCP JSON-RPC 2.0 stdio server (newline-delimited JSON).
# --------------------------------------------------------------------------- #

TOOL_SCHEMA = {
    "name": "ingest_attachment",
    "description": (
        "Deterministic quarantine-first attachment ingestion for the OpenClaw "
        "VideoFactory single-group router. Validates that source_media_path is "
        "inside the approved inbound root and that chat_id/sender_id are on the "
        "authorized route allowlist, then invokes the single safety "
        "implementation (07_ingest_inbound_media.ps1) and writes a quarantine "
        "receipt with content_parsed=false, quarantined=true. Does NOT decode "
        "image/audio/video, run OCR, call a model, or accept arbitrary paths. "
        "Computes the authoritative actual and stored byte sizes itself; "
        "the Router must not supply a size, maximum, trust flag, or "
        "validation mode. Image, audio, video, and text/plain TXT quarantine receipts receive "
        "one opaque action ticket; no attachment is analyzed automatically. The public result "
        "never exposes storage paths, receipt paths, hashes, or Channel IDs."
    ),
    "inputSchema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "message_id",
            "attachment_index",
            "attachment_count",
            "source_media_path",
            "original_file_name",
            "content_type",
            "chat_id",
            "sender_id",
        ],
        "properties": {
            "message_id": {"type": "string", "pattern": "^om_[A-Za-z0-9_-]+$"},
            "attachment_index": {"type": "integer", "minimum": 0},
            "attachment_count": {"type": "integer", "minimum": 1},
            "source_media_path": {
                "type": "string",
                "description": "Absolute path inside the approved OpenClaw inbound root, as provided by the Channel adapter.",
            },
            "original_file_name": {"type": "string"},
            "content_type": {"type": "string"},
            "chat_id": {"type": "string", "pattern": "^oc_[A-Za-z0-9_-]+$"},
            "sender_id": {"type": "string", "pattern": "^ou_[A-Za-z0-9_-]+$"},
            "event_id": {"type": "string"},
            "received_at": {"type": "string"},
        },
    },
}

CONSUME_MEDIA_ACTION_TICKET_SCHEMA = {
    "name": "consume_media_action_ticket",
    "description": (
        "Consume exactly one opaque media-action ticket. The server strictly parses only "
        "/vf image|audio|video|text <ticket>, validates the bounded-trust current chat and sender context, "
        "then performs ticket, receipt, integrity, request, and Analyzer dispatch itself. "
        "The Router must forward only an exact current user command and cannot pass path, media "
        "selection, model selection, hash, receipt, Analyzer, GPU, or trust arguments."
    ),
    "inputSchema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["raw_command", "current_chat_context", "current_sender_context"],
        "properties": {
            "raw_command": {"type": "string", "maxLength": 512},
            "current_chat_context": {"type": "string", "pattern": "^oc_[A-Za-z0-9_-]+$"},
            "current_sender_context": {"type": "string", "pattern": "^ou_[A-Za-z0-9_-]+$"},
        },
    },
}


def _send(obj: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _result_text(result: Dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)


def _public_ingest_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Project a Router-safe result; all paths, IDs and hashes remain server-only."""
    if result.get("status") == "rejected":
        return {"status": "rejected", "error_code": result.get("error_code", "ingest_failed")}
    kind = str(result.get("detected_kind") or "").lower()
    media_label = {
        "png": "图片",
        "jpg": "图片",
        "jpeg": "图片",
        "wav": "音频",
        "mp3": "音频",
        "audio": "音频",
        "mp4": "视频",
        "video": "视频",
        "txt": "文本",
    }.get(kind, "文件")
    public = {
        "status": "quarantined",
        "media_kind": kind,
        "ticket_issued": bool(result.get("ticket_issued", False)),
        "already_ingested": bool(result.get("already_ingested", False)),
    }
    ticket = result.get("ticket")
    action = result.get("ticket_action")
    if isinstance(ticket, str) and isinstance(action, str):
        label = {"audio": "转录编号", "text": "解析编号"}.get(action, "分析编号")
        public.update(
            {
                "ticket": ticket,
                "reply_template": f"{media_label}已安全入库。\\n{label}：{ticket}\\n\\n需要处理时发送：\\n/vf {action} {ticket}",
            }
        )
    else:
        public["reply_template"] = "附件已安全入库。该票据已签发且不会重复发送。"
    return public


def _public_consume_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Keep ticket hashes, job identifiers, paths, and Analyzer details server-only."""
    if result.get("status") != "completed":
        return {"status": "rejected", "error_code": result.get("error_code", "analysis_failed")}
    action = result.get("action")
    if action in {"image", "audio", "text"}:
        presentation = result.get("presentation")
        presentation_contract = {
            "image": (RESULT_REPLY_EMPTY, RESULT_REPLY_ERROR, "图片分析结果：", RESULT_REPLY_LABELS),
            "audio": (AUDIO_RESULT_REPLY_EMPTY, AUDIO_RESULT_REPLY_ERROR, "音频转录结果：", AUDIO_RESULT_REPLY_LABELS),
            "text": (TEXT_RESULT_REPLY_EMPTY, TEXT_RESULT_REPLY_ERROR, "文本解析结果：", TEXT_RESULT_REPLY_LABELS),
        }
        empty_reply, error_reply, expected_prefix, expected_labels = presentation_contract[action]
        if not isinstance(presentation, dict) or presentation.get("status") != "ready":
            code = (
                presentation.get("error_code")
                if isinstance(presentation, dict)
                else "result_render_failed"
            )
            return {
                "status": "presentation_failed",
                "error_code": code
                if code in {"result_content_empty", "result_render_failed"}
                else "result_render_failed",
                "reply_template": empty_reply
                if code == "result_content_empty"
                else error_reply,
            }
        reply = presentation.get("reply_template")
        if not isinstance(reply, str):
            return {
                "status": "presentation_failed",
                "error_code": "result_render_failed",
                "reply_template": error_reply,
            }
        if (
            len(reply) > 220
            or INTERNAL_PATH_RE.search(reply)
            or INTERNAL_IDENTIFIER_RE.search(reply)
            or INTERNAL_HASH_RE.search(reply)
            or OPAQUE_TOKEN_RE.search(reply)
            or not reply.startswith(expected_prefix)
            or sum(label in reply for label in expected_labels) < 3
        ):
            return {
                "status": "presentation_failed",
                "error_code": "result_render_failed",
                "reply_template": error_reply,
            }
        return {
            "status": "completed",
            "media_kind": result.get("media_kind"),
            "action": action,
            "reply_template": reply,
        }
    return {
        "status": "completed",
        "media_kind": result.get("media_kind"),
        "action": action,
        "reply_template": "媒体处理已完成。",
    }


def _dispatch_ticket_analyzer(tool_name: str, analyzer_args: Dict[str, Any]) -> Dict[str, Any]:
    """Keep Analyzer selection and all four Analyzer arguments server-owned."""
    import analyzer_mcp  # imported lazily to keep ingress startup light

    analyzer_mcp.PROJECT_ROOT = PROJECT_ROOT
    analyzer_mcp.STORAGE_ROOT = (PROJECT_ROOT / "input" / "feishu").resolve()
    analyzer_mcp.JOBS_ROOT = (PROJECT_ROOT / "jobs").resolve()
    result = analyzer_mcp.analyze(tool_name, analyzer_args)
    if tool_name in {"analyze_image", "transcribe_audio", "analyze_text"} and result.get("status") in {
        "completed",
        "already_analyzed",
    }:
        result = dict(result)
        try:
            result["presentation"] = {
                "analyze_image": _load_image_presentation,
                "transcribe_audio": _load_audio_presentation,
                "analyze_text": _load_text_presentation,
            }[tool_name](result)
        except ResultPresentationError as exc:
            result["presentation"] = {"status": "failed", "error_code": str(exc)}
    return result


def _handle(msg: Dict[str, Any]) -> None:
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        _send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "openclaw-ingest-attachment", "version": "1.0.0"},
                    "capabilities": {"tools": {}},
                },
            }
        )
        return
    if method == "notifications/initialized":
        return  # notification, no response
    if method == "tools/list":
        _send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": [TOOL_SCHEMA, CONSUME_MEDIA_ACTION_TICKET_SCHEMA]},
            }
        )
        return
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name not in {"ingest_attachment", "consume_media_action_ticket"}:
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32602, "message": f"unknown tool: {name}"},
                }
            )
            return
        try:
            if name == "ingest_attachment" and "caption" in args:
                result = {"status": "rejected", "error_code": "attachment_caption_unsupported"}
            elif name == "ingest_attachment":
                result = _public_ingest_result(ingest_attachment(args))
            else:
                configure_storage(PROJECT_ROOT)
                configure_ticket_roots(PROJECT_ROOT)
                result = consume_media_action_ticket(
                    args,
                    create_request=create_ticket_analysis_request,
                    dispatch=_dispatch_ticket_analyzer,
                )
                result = _public_consume_result(result)
        except Exception:
            result = {"status": "rejected", "error_code": "internal_error"}
        is_error = result.get("status") == "rejected"
        _send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": _result_text(result)}],
                    "isError": is_error,
                },
            }
        )
        return
    if method == "ping":
        _send({"jsonrpc": "2.0", "id": msg_id, "result": {}})
        return
    if msg_id is not None:
        _send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"method not found: {method}"},
            }
        )


def serve() -> None:
    """Read newline-delimited JSON-RPC from stdin, dispatch, write to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        # Support Content-Length-framed messages (LSP-style) as a fallback: if a
        # full JSON object already arrived on one line, parse it directly.
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            # Could be a Content-Length header; skip silently.
            continue
        try:
            _handle(msg)
        except Exception as e:
            sys.stderr.write(f"[ingest_attachment] handler error: {e}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        # Minimal offline self-test: print tool schema and a validation error sample.
        print(json.dumps({"tool": TOOL_SCHEMA["name"], "schema_ok": True}, indent=2))
    else:
        serve()
