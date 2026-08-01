"""Fail-closed analysis-request persistence for quarantined Feishu media.

The historical reply-to constructor remains here as deferred evidence.  The
active P0 route creates requests only from a validated media-action ticket;
both constructors store the request outside the immutable ingress receipt.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

PROJECT_ROOT = Path(
    os.environ.get("OPENCLAW_PROJECT_ROOT", str(Path(__file__).resolve().parent.parent))
).resolve()
STORAGE_ROOT = (PROJECT_ROOT / "input" / "feishu").resolve()
SCHEMA_VERSION = "1.0"
ANALYSIS_POLICY = "read_quarantine_copy_only"
REQUEST_WINDOW_SECONDS = 120
MESSAGE_ID_RE = re.compile(r"^om_[A-Za-z0-9_-]+$")
CHAT_ID_RE = re.compile(r"^oc_[A-Za-z0-9_-]+$")
SENDER_ID_RE = re.compile(r"^ou_[A-Za-z0-9_-]+$")
HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ACTION_KINDS = {
    "analyze_image": {"png", "jpg", "jpeg"},
    "transcribe_audio": {"audio", "wav", "mp3"},
    "analyze_video": {"mp4", "video"},
    "analyze_text": {"txt"},
}
PROMPT_MARKERS = (
    "ignore previous",
    "忽略之前",
    "绕过",
    "系统提示",
    "system prompt",
    "developer message",
)
COMMANDS = {
    "analyze_image": {
        "analyze image",
        "please analyze this image",
        "请分析这张图片",
        "请分析这张图片。",
        "请在安全入库后分析这张图片",
        "请在安全入库后分析这张图片。",
    },
    "transcribe_audio": {
        "transcribe audio",
        "please transcribe this audio",
        "请转录这段音频",
        "请转录这段音频。",
        "请在安全入库后转录这段音频",
        "请在安全入库后转录这段音频。",
    },
    "analyze_video": {
        "analyze video",
        "please analyze this video",
        "请分析这段视频",
        "请分析这段视频。",
        "请在安全入库后分析这段视频",
        "请在安全入库后分析这段视频。",
    },
}


def configure_storage(project_root: Path) -> None:
    """Refresh the server-owned receipt root for a retained module instance."""
    global PROJECT_ROOT, STORAGE_ROOT
    PROJECT_ROOT = Path(project_root).resolve()
    STORAGE_ROOT = (PROJECT_ROOT / "input" / "feishu").resolve()


def _error(code: str, detail: str = "") -> Dict[str, Any]:
    return {"status": "rejected", "error_code": code, "detail": detail[:200]}


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def _message_id(value: Any, pattern: re.Pattern[str]) -> Optional[str]:
    text = str(value or "").strip()
    return text if pattern.fullmatch(text) else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def identity_digest(value: str) -> str:
    """Digest a Channel identity without persisting the real ID."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_request_text(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("analysis_intent_not_recognized")
    text = unicodedata.normalize("NFKC", value).strip().casefold()
    if len(text) > 256:
        raise ValueError("analysis_intent_not_recognized")
    if any(marker in text for marker in PROMPT_MARKERS):
        raise ValueError("analysis_intent_not_recognized")
    return re.sub(r"\s+", " ", text)


def action_for(kind: str, request_text: str) -> Optional[str]:
    normalized = normalize_request_text(request_text)
    action = next(
        (candidate for candidate, phrases in COMMANDS.items() if normalized in phrases), None
    )
    if action is None:
        return None
    return action if kind in ACTION_KINDS[action] else "__type_mismatch__"


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _epoch(value: str) -> float:
    text = str(value).replace("Z", "+00:00")
    from datetime import datetime

    return datetime.fromisoformat(text).timestamp()


def _atomic_write(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _target_context(
    target_id: str, attachment_index: int
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    target_dir = (STORAGE_ROOT / target_id).resolve(strict=False)
    if not _under(target_dir, STORAGE_ROOT):
        return None, _error("reply_target_not_attachment")
    manifest_path = target_dir / "message_manifest.json"
    manifest = _load_json(manifest_path)
    if not manifest or manifest.get("message_id") != target_id:
        return None, _error("reply_target_not_attachment")
    try:
        index = int(attachment_index)
    except (TypeError, ValueError):
        return None, _error("invalid_attachment_index")
    entries = manifest.get("attachments") or []
    entry = None
    for item in entries:
        if not isinstance(item, dict):
            continue
        try:
            if int(item.get("attachment_index", -1)) == index:
                entry = item
                break
        except (TypeError, ValueError):
            continue
    if not isinstance(entry, dict):
        return None, _error("reply_target_not_attachment")
    receipt_path = Path(str(entry.get("receipt_path") or ""))
    if not receipt_path.is_absolute():
        receipt_path = target_dir / f"attachment-{index:03d}" / "receipt.json"
    receipt_path = receipt_path.resolve(strict=False)
    if not _under(receipt_path, target_dir) or receipt_path.name != "receipt.json":
        return None, _error("receipt_not_found")
    receipt = _load_json(receipt_path)
    if not receipt:
        return None, _error("receipt_not_found")
    stored_path = Path(str(receipt.get("stored_path") or "")).resolve(strict=False)
    if not _under(stored_path, STORAGE_ROOT) or not stored_path.is_file():
        return None, _error("stored_path_invalid")
    try:
        receipt_index = int(receipt.get("attachment_index", -1))
    except (TypeError, ValueError):
        return None, _error("receipt_target_mismatch")
    if receipt.get("message_id") != target_id or receipt_index != index:
        return None, _error("receipt_target_mismatch")
    if receipt.get("quarantined") is not True or receipt.get("content_parsed") is not False:
        return None, _error("receipt_not_quarantined")
    expected = str(receipt.get("stored_sha256") or "").lower()
    source = str(receipt.get("source_sha256") or "").lower()
    if not HASH_RE.fullmatch(expected) or expected != source or _sha256(stored_path) != expected:
        return None, _error("stored_hash_mismatch")
    binding = _load_json(receipt_path.parent / "route_binding.json")
    try:
        binding_index = int(binding.get("attachment_index", -1)) if binding else -1
    except (TypeError, ValueError):
        binding_index = -1
    if not binding or binding.get("message_id") != target_id or binding_index != index:
        return None, _error("requester_binding_missing")
    return {
        "target_dir": target_dir,
        "manifest": manifest,
        "entry": entry,
        "receipt_path": receipt_path,
        "receipt": receipt,
        "stored_path": stored_path,
        "stored_sha256": expected,
        "binding": binding,
        "request_dir": receipt_path.parent / "analysis_requests",
        "active_path": receipt_path.parent / "analysis_request.json",
    }, None


def create_analysis_request(args: Dict[str, Any], *, now: Optional[str] = None) -> Dict[str, Any]:
    """Create a pending request from Channel-bound reply metadata only."""
    required = {
        "request_message_id",
        "target_attachment_message_id",
        "reply_to_message_id",
        "attachment_index",
        "chat_id",
        "requester_id",
        "request_text",
    }
    if set(args) != required:
        return _error("invalid_arguments")
    request_id = _message_id(args.get("request_message_id"), MESSAGE_ID_RE)
    target_id = _message_id(args.get("target_attachment_message_id"), MESSAGE_ID_RE)
    reply_id = _message_id(args.get("reply_to_message_id"), MESSAGE_ID_RE)
    chat_id = _message_id(args.get("chat_id"), CHAT_ID_RE)
    requester_id = _message_id(args.get("requester_id"), SENDER_ID_RE)
    if not request_id:
        return _error("invalid_request_message_id")
    if not target_id or not reply_id:
        return _error("reply_target_missing")
    if reply_id != target_id:
        return _error("reply_target_not_attachment")
    if not chat_id or not requester_id:
        return _error("invalid_channel_identity")
    if request_id == target_id:
        return _error("invalid_request_message_id")
    ctx, error = _target_context(target_id, args.get("attachment_index"))
    if error:
        return error
    assert ctx is not None
    binding = ctx["binding"]
    if binding.get("chat_id_sha256") != identity_digest(chat_id):
        return _error("chat_mismatch")
    if binding.get("sender_id_sha256") != identity_digest(requester_id):
        return _error("requester_mismatch")
    kind = str(ctx["receipt"].get("detected_kind") or "").lower()
    try:
        action = action_for(kind, args.get("request_text"))
    except ValueError:
        return _error("analysis_intent_not_recognized")
    if action is None:
        return _error("analysis_intent_not_recognized")
    if action == "__type_mismatch__":
        return _error("action_type_mismatch")
    requested_at = now or _utc_now()
    try:
        if abs(time.time() - _epoch(requested_at)) > REQUEST_WINDOW_SECONDS:
            return _error("attachment_expired")
    except (TypeError, ValueError, OverflowError):
        return _error("invalid_requested_at")
    request_dir: Path = ctx["request_dir"]
    request_dir.mkdir(parents=True, exist_ok=True)
    request_path = request_dir / f"{request_id}.json"
    existing = _load_json(request_path)
    if existing is not None:
        return {
            **existing,
            "status": existing.get("status", "pending"),
            "request_path": str(request_path),
        }
    prior_completed = None
    for candidate in request_dir.glob("om_*.json"):
        previous = _load_json(candidate)
        if (
            previous
            and previous.get("status") in {"completed", "already_completed"}
            and previous.get("action") == action
        ):
            prior_completed = previous
            break
    if prior_completed:
        status = "already_completed"
        completed_at = prior_completed.get("completed_at")
        result_path = prior_completed.get("result_path")
    else:
        active = _load_json(ctx["active_path"])
        if active and active.get("status") in {"pending", "running"}:
            return _error("analysis_in_progress")
        status = "pending"
        completed_at = None
        result_path = None
    request = {
        "schema_version": SCHEMA_VERSION,
        "request_message_id": request_id,
        "target_attachment_message_id": target_id,
        "attachment_index": int(args["attachment_index"]),
        "chat_id": chat_id,
        "requester_id": requester_id,
        "action": action,
        "action_source": "reply_to_attachment",
        "requested_at": requested_at,
        "status": status,
        "receipt_path": str(ctx["receipt_path"]),
        "stored_sha256": ctx["stored_sha256"],
        "analysis_policy": ANALYSIS_POLICY,
        "completed_at": completed_at,
        "result_path": result_path,
        "error_code": None,
    }
    _atomic_write(request_path, request)
    if status == "pending":
        _atomic_write(ctx["active_path"], request)
    return {**request, "request_path": str(request_path)}


def create_ticket_analysis_request(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """Create the single server-owned request associated with a consumed ticket.

    ``ticket`` is never an MCP argument.  It is the server-side record that was
    validated by ``consume_media_action_ticket``; only its digest is persisted
    in the request.
    """
    required = {
        "ticket_hash",
        "attachment_message_id",
        "attachment_index",
        "receipt_path",
        "stored_path",
        "stored_sha256",
        "media_kind",
        "analyzer_action",
        "chat_id",
        "uploader_id",
        "created_at",
        "expires_at",
    }
    if not required.issubset(ticket):
        return _error("receipt_invalid")
    ticket_hash = str(ticket.get("ticket_hash") or "").lower()
    if not HASH_RE.fullmatch(ticket_hash):
        return _error("receipt_invalid")
    target_id = _message_id(ticket.get("attachment_message_id"), MESSAGE_ID_RE)
    chat_id = _message_id(ticket.get("chat_id"), CHAT_ID_RE)
    requester_id = _message_id(ticket.get("uploader_id"), SENDER_ID_RE)
    if not target_id or not chat_id or not requester_id:
        return _error("receipt_invalid")
    try:
        attachment_index = int(ticket.get("attachment_index", -1))
    except (TypeError, ValueError):
        attachment_index = -1
    if attachment_index < 0:
        return _error("receipt_invalid")
    action = str(ticket.get("analyzer_action") or "")
    kind = str(ticket.get("media_kind") or "").lower()
    if action not in ACTION_KINDS or kind not in ACTION_KINDS[action]:
        return _error("media_kind_mismatch")
    receipt_path = Path(str(ticket.get("receipt_path") or "")).resolve(strict=False)
    stored_path = Path(str(ticket.get("stored_path") or "")).resolve(strict=False)
    if (
        not _under(receipt_path, STORAGE_ROOT)
        or receipt_path.name != "receipt.json"
        or not _under(stored_path, STORAGE_ROOT)
    ):
        return _error("receipt_invalid")
    receipt = _load_json(receipt_path)
    if (
        not receipt
        or receipt.get("message_id") != target_id
        or receipt.get("stored_path") != str(stored_path)
    ):
        return _error("receipt_invalid")
    try:
        if int(receipt.get("attachment_index", -1)) != attachment_index:
            return _error("receipt_invalid")
    except (TypeError, ValueError):
        return _error("receipt_invalid")
    if receipt.get("quarantined") is not True or receipt.get("content_parsed") is not False:
        return _error("receipt_invalid")
    expected_hash = str(ticket.get("stored_sha256") or "").lower()
    if (
        not HASH_RE.fullmatch(expected_hash)
        or str(receipt.get("stored_sha256") or "").lower() != expected_hash
    ):
        return _error("stored_hash_mismatch")
    binding = _load_json(receipt_path.parent / "route_binding.json")
    if not binding or binding.get("message_id") != target_id:
        return _error("receipt_invalid")
    try:
        if int(binding.get("attachment_index", -1)) != attachment_index:
            return _error("receipt_invalid")
    except (TypeError, ValueError):
        return _error("receipt_invalid")
    if binding.get("chat_id_sha256") != identity_digest(chat_id):
        return _error("chat_mismatch")
    if binding.get("sender_id_sha256") != identity_digest(requester_id):
        return _error("sender_mismatch")

    request_dir = receipt_path.parent / "analysis_requests"
    request_key = f"ticket-{ticket_hash}"
    request_path = request_dir / f"{request_key}.json"
    existing = _load_json(request_path)
    if existing is not None:
        return {**existing, "request_path": str(request_path)}
    active_path = receipt_path.parent / "analysis_request.json"
    active = _load_json(active_path)
    if active and active.get("status") in {"pending", "running"}:
        return _error("analysis_in_progress")
    request = {
        "schema_version": SCHEMA_VERSION,
        "request_key": request_key,
        "request_message_id": None,
        "target_attachment_message_id": target_id,
        "attachment_index": attachment_index,
        "chat_id": chat_id,
        "requester_id": requester_id,
        "action": action,
        "action_source": "media_action_ticket",
        "ticket_hash": ticket_hash,
        "ticket_expires_at": ticket["expires_at"],
        "requested_at": _utc_now(),
        "status": "pending",
        "receipt_path": str(receipt_path),
        "stored_sha256": expected_hash,
        "analysis_policy": ANALYSIS_POLICY,
        "completed_at": None,
        "result_path": None,
        "error_code": None,
    }
    _atomic_write(request_path, request)
    _atomic_write(active_path, request)
    return {**request, "request_path": str(request_path)}


def load_active_request(receipt_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    path = Path(receipt_path).resolve(strict=False).parent / "analysis_request.json"
    if not _under(path, STORAGE_ROOT) or path.name != "analysis_request.json":
        return None, "analysis_request_path_invalid"
    request = _load_json(path)
    if not request:
        return None, "analysis_request_required"
    return request, None


def update_request_status(
    receipt_path: Path,
    status: str,
    *,
    result_path: Optional[str] = None,
    error_code: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    request, error = load_active_request(receipt_path)
    if error or request is None:
        return None
    request = dict(request)
    request["status"] = status
    if result_path is not None:
        request["result_path"] = result_path
    request["error_code"] = error_code
    if status in {"completed", "already_completed", "failed", "rejected"}:
        request["completed_at"] = _utc_now()
    active_path = Path(receipt_path).resolve(strict=False).parent / "analysis_request.json"
    request_key = request.get("request_key")
    if not isinstance(request_key, str) or not re.fullmatch(
        r"(?:om_[A-Za-z0-9_-]+|ticket-[0-9a-f]{64})", request_key
    ):
        request_key = str(request.get("request_message_id") or "")
    request_path = (
        Path(receipt_path).resolve(strict=False).parent
        / "analysis_requests"
        / f"{request_key}.json"
    )
    _atomic_write(active_path, request)
    if _under(request_path, STORAGE_ROOT):
        _atomic_write(request_path, request)
    return request


def route_binding_payload(
    message_id: str, attachment_index: int, chat_id: str, sender_id: str
) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "message_id": message_id,
        "attachment_index": int(attachment_index),
        "chat_id_sha256": identity_digest(chat_id),
        "sender_id_sha256": identity_digest(sender_id),
    }
