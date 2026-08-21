"""Opaque, one-time media action tickets for the P0 Core Feishu route.

This module is deliberately independent of the Router and Analyzer MCP public
surfaces.  It creates tickets only after quarantine ingestion, stores only a
SHA-256 digest of each random ticket, and resolves the selected Analyzer on the
server side.  No raw ticket, model name, or storage path is ever derived from a
ticket value or returned through the public projection.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple


PROJECT_ROOT = Path(
    os.environ.get("OPENCLAW_PROJECT_ROOT", str(Path(__file__).resolve().parent.parent))
).resolve()
STORAGE_ROOT = (PROJECT_ROOT / "input" / "feishu").resolve()
TICKETS_ROOT = (PROJECT_ROOT / "state" / "media_action_tickets").resolve()
EXECUTION_CONFIG_PATH = (
    PROJECT_ROOT / "config" / "local" / "media_ticket_execution.json"
).resolve()
TICKET_TTL_SECONDS = int(os.environ.get("OPENCLAW_MEDIA_ACTION_TICKET_TTL_SECONDS", "300"))
TICKET_NOT_BEFORE_SECONDS = int(
    os.environ.get("OPENCLAW_MEDIA_ACTION_TICKET_NOT_BEFORE_SECONDS", "1")
)
TICKET_BYTES = 32  # 256 random bits; safely exceeds the required 128 bits.
TICKET_CLEANUP_SCAN_LIMIT = 512

HASH_RE = re.compile(r"^[0-9a-f]{64}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{43,128}$")
CHAT_RE = re.compile(r"^oc_[A-Za-z0-9_-]+$")
SENDER_RE = re.compile(r"^ou_[A-Za-z0-9_-]+$")
MESSAGE_RE = re.compile(r"^om_[A-Za-z0-9_-]+$")
ACTION_TO_ANALYZER = {
    "image": "analyze_image",
    "audio": "transcribe_audio",
    "video": "analyze_video",
    "text": "analyze_text",
}
KIND_TO_ACTION = {
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
    "audio": "audio",
    "wav": "audio",
    "mp3": "audio",
    "mp4": "video",
    "video": "video",
    "txt": "text",
}


def configure_roots(project_root: Path) -> None:
    """Align module state with an embedding MCP server's project root.

    Python test runners and the OpenClaw MCP host can retain imported modules
    across isolated invocations.  The server owns the root, so it refreshes
    these derived locations before any ticket operation.
    """
    global PROJECT_ROOT, STORAGE_ROOT, TICKETS_ROOT, EXECUTION_CONFIG_PATH
    PROJECT_ROOT = Path(project_root).resolve()
    STORAGE_ROOT = (PROJECT_ROOT / "input" / "feishu").resolve()
    TICKETS_ROOT = (PROJECT_ROOT / "state" / "media_action_tickets").resolve()
    EXECUTION_CONFIG_PATH = (
        PROJECT_ROOT / "config" / "local" / "media_ticket_execution.json"
    ).resolve()


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _epoch(value: Any) -> Optional[float]:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError, OverflowError):
        return None


def _error(code: str) -> Dict[str, Any]:
    return {"status": "rejected", "error_code": code}


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def _safe_existing_path(value: Any, root: Path, name: Optional[str] = None) -> Optional[Path]:
    raw = Path(str(value or ""))
    if not raw.is_absolute() or not _under(raw, root):
        return None
    current = raw.absolute()
    while True:
        if current.exists() and current.is_symlink():
            return None
        if current == root:
            break
        parent = current.parent
        if parent == current:
            return None
        current = parent
    try:
        resolved = raw.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if not _under(resolved, root) or (name is not None and resolved.name != name):
        return None
    return resolved


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _ticket_hash(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def _record_path(ticket_hash: str) -> Path:
    return (TICKETS_ROOT / "tickets" / f"{ticket_hash}.json").resolve(strict=False)


def _attachment_index_path(message_id: str, attachment_index: int) -> Path:
    digest = hashlib.sha256(f"{message_id}\x1f{attachment_index}".encode("utf-8")).hexdigest()
    return (TICKETS_ROOT / "attachments" / f"{digest}.json").resolve(strict=False)


def _lock_path(ticket_hash: str) -> Path:
    return (TICKETS_ROOT / "locks" / f"{ticket_hash}.lock").resolve(strict=False)


def _active_ticket_key(chat_id: str, sender_id: str, media_kind: str) -> str:
    return hashlib.sha256(f"{chat_id}\x1f{sender_id}\x1f{media_kind}".encode("utf-8")).hexdigest()


def _active_ticket_path(chat_id: str, sender_id: str, media_kind: str) -> Path:
    return (
        TICKETS_ROOT / "active" / f"{_active_ticket_key(chat_id, sender_id, media_kind)}.json"
    ).resolve(strict=False)


def _active_ticket_lock_path(chat_id: str, sender_id: str, media_kind: str) -> Path:
    return (
        TICKETS_ROOT / "active_locks" / f"{_active_ticket_key(chat_id, sender_id, media_kind)}.lock"
    ).resolve(strict=False)


def _audit_path() -> Path:
    return (TICKETS_ROOT / "audits" / f"{time.time_ns()}-{secrets.token_hex(8)}.json").resolve(
        strict=False
    )


def _safe_ticket_state_path(path: Path) -> bool:
    """Require private ticket state to remain below this project's state root."""
    raw = Path(path).absolute()
    if not _under(raw, TICKETS_ROOT) or not _under(TICKETS_ROOT, PROJECT_ROOT):
        return False
    current = raw
    while True:
        if current.exists() and current.is_symlink():
            return False
        if current == PROJECT_ROOT:
            return True
        parent = current.parent
        if parent == current:
            return False
        current = parent


def _acquire_lock(path: Path) -> bool:
    if not _safe_ticket_state_path(path):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        return False
    try:
        os.write(fd, f"{os.getpid()} {_utc_now()}".encode("ascii"))
    finally:
        os.close(fd)
    return True


def _release_lock(path: Path) -> None:
    if not _safe_ticket_state_path(path):
        return
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _lock_owner_is_alive(path: Path) -> bool:
    """Return true only for a well-formed lock whose process is still alive."""
    try:
        parts = path.read_text(encoding="ascii").strip().split()
        pid = int(parts[0])
        if len(parts) != 2 or pid <= 0:
            return False
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, IndexError, UnicodeError):
        return False


def _ticket_files() -> Tuple[Optional[list[Path]], Optional[str]]:
    tickets_dir = (TICKETS_ROOT / "tickets").resolve(strict=False)
    if not _safe_ticket_state_path(tickets_dir):
        return None, "ticket_store_invalid"
    if not tickets_dir.exists():
        return [], None
    try:
        files = sorted(tickets_dir.glob("*.json"))
    except OSError:
        return None, "ticket_store_invalid"
    if len(files) > TICKET_CLEANUP_SCAN_LIMIT:
        return None, "ticket_store_invalid"
    if any(not _safe_ticket_state_path(path) for path in files):
        return None, "ticket_store_invalid"
    return files, None


def _execution_enabled() -> bool:
    """Return an explicit operator setting, defaulting to disabled.

    A process-local environment value is useful for tests and ephemeral
    operations.  The ignored project-local file lets an on-demand stdio MCP
    process observe the production decision without a Gateway restart.  Any
    missing or malformed value remains disabled.
    """

    environment_value = os.environ.get("MEDIA_TICKET_EXECUTION_ENABLED")
    if environment_value is not None:
        return environment_value.strip() == "1"
    local_config = _load_json(EXECUTION_CONFIG_PATH)
    return bool(local_config and local_config.get("media_ticket_execution_enabled") is True)


def _bounded_positive_seconds(value: Any, default: int, maximum: int) -> Optional[int]:
    try:
        seconds = int(default if value is None else value)
    except (TypeError, ValueError):
        return None
    return seconds if 0 <= seconds <= maximum else None


def _identity_digest(value: Any) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def _write_consumption_audit(
    *,
    chat_id: Any,
    sender_id: Any,
    ticket_hash: Optional[str],
    ticket_state: Optional[str],
    media_kind: Optional[str],
    action: Optional[str],
    result: Dict[str, Any],
    now: str,
) -> bool:
    """Persist a redacted local audit record without raw ticket or path data."""
    path = _audit_path()
    if not _safe_ticket_state_path(path):
        return False
    safe_hash = (
        ticket_hash if isinstance(ticket_hash, str) and HASH_RE.fullmatch(ticket_hash) else None
    )
    try:
        _atomic_write(
            path,
            {
                "schema_version": "1.0",
                "recorded_at": now,
                "chat_binding_sha256": _identity_digest(chat_id),
                "sender_binding_sha256": _identity_digest(sender_id),
                "ticket_hash": safe_hash,
                "ticket_state": ticket_state,
                "media_kind": media_kind,
                "action": action,
                "result": str(result.get("status") or "rejected"),
                "error_code": result.get("error_code"),
            },
        )
        return True
    except OSError:
        return False


def _cancel_other_pending_tickets(
    *,
    chat_id: str,
    sender_id: str,
    media_kind: str,
    now: str,
) -> Optional[str]:
    """Keep at most one pending ticket for a chat/sender/media-kind tuple."""
    files, error = _ticket_files()
    if error:
        return error
    assert files is not None
    for path in files:
        record = _load_json(path)
        if record is None or record.get("status") != "pending":
            continue
        if (record.get("chat_id"), record.get("uploader_id"), record.get("media_kind")) != (
            chat_id,
            sender_id,
            media_kind,
        ):
            continue
        ticket_hash = str(record.get("ticket_hash") or "")
        if not HASH_RE.fullmatch(ticket_hash) or path.name != f"{ticket_hash}.json":
            return "ticket_store_invalid"
        lock_path = _lock_path(ticket_hash)
        if not _safe_ticket_state_path(lock_path) or not _acquire_lock(lock_path):
            return "ticket_store_busy"
        try:
            latest = _load_json(path)
            if latest is None:
                return "ticket_store_invalid"
            if latest.get("status") == "pending":
                latest["status"] = "cancelled"
                latest["cancelled_at"] = now
                latest["cancellation_reason"] = "newer_pending_ticket"
                _atomic_write(path, latest)
        finally:
            _release_lock(lock_path)
    return None


def _expire_pending_tickets(now_epoch: float) -> Optional[str]:
    """Lazily tombstone expired pending tickets without deleting replay state."""
    files, error = _ticket_files()
    if error:
        return error
    assert files is not None
    for path in files:
        record = _load_json(path)
        if record is None:
            # A malformed unrelated tombstone cannot be safely repaired here;
            # leave it for an exact-token lookup to reject, without turning
            # every independent attachment into a global denial of service.
            continue
        expires_at = _epoch(record.get("expires_at"))
        if expires_at is None:
            continue
        if record.get("status") != "pending" or now_epoch < expires_at:
            continue
        ticket_hash = str(record.get("ticket_hash") or "")
        if not HASH_RE.fullmatch(ticket_hash):
            continue
        lock_path = _lock_path(ticket_hash)
        if not _safe_ticket_state_path(lock_path):
            return "ticket_store_invalid"
        if not _acquire_lock(lock_path):
            continue
        try:
            latest = _load_json(path)
            if latest is not None and latest.get("status") == "pending":
                latest_expiry = _epoch(latest.get("expires_at"))
                if latest_expiry is not None and now_epoch >= latest_expiry:
                    latest["status"] = "expired"
                    _atomic_write(path, latest)
        finally:
            _release_lock(lock_path)
    return None


def _existing_attachment_ticket(
    message_id: str, attachment_index: int
) -> Tuple[Optional[str], Optional[str]]:
    """Recover a record-first issuance interrupted before its index commit."""
    files, error = _ticket_files()
    if error:
        return None, error
    assert files is not None
    for path in files:
        record = _load_json(path)
        if record is None:
            continue
        try:
            matches = (
                record.get("attachment_message_id") == message_id
                and int(record.get("attachment_index", -1)) == attachment_index
            )
        except (TypeError, ValueError):
            matches = False
        if not matches:
            continue
        ticket_hash = str(record.get("ticket_hash") or "")
        if not HASH_RE.fullmatch(ticket_hash) or path.name != f"{ticket_hash}.json":
            return None, "ticket_store_invalid"
        return ticket_hash, None
    return None, None


def parse_media_action_command(raw_command: Any) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    """Accept only the four documented commands and harmless normalization."""
    if not isinstance(raw_command, str) or len(raw_command) > 512:
        return None, "command_invalid"
    # The protocol permits only ASCII command syntax.  Unicode normalization
    # would turn visually similar input (for example a full-width slash) into
    # an accepted command, exceeding the deliberately small normalization
    # contract of trim, ASCII prefix case-folding, and space collapsing.
    if any(ord(char) > 0x7E for char in raw_command):
        return None, "command_invalid"
    if any(ord(char) < 0x20 for char in raw_command):
        return None, "command_invalid"
    text = re.sub(r" +", " ", raw_command.strip(" "))
    parts = text.split(" ")
    if len(parts) != 3 or parts[0].casefold() != "/vf":
        return None, "command_invalid"
    action = parts[1].casefold()
    token = parts[2]
    if action not in ACTION_TO_ANALYZER or not TOKEN_RE.fullmatch(token):
        return None, "command_invalid"
    return {"action": action, "token": token, "normalized": f"/vf {action} {token}"}, None


def _validate_ticket_material(
    result: Dict[str, Any], chat_id: str, sender_id: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    receipt_path = _safe_existing_path(result.get("receipt_path"), STORAGE_ROOT, "receipt.json")
    stored_path = _safe_existing_path(result.get("stored_path"), STORAGE_ROOT)
    if receipt_path is None or stored_path is None:
        return None, "receipt_invalid"
    receipt = _load_json(receipt_path)
    if receipt is None:
        return None, "receipt_invalid"
    message_id = str(receipt.get("message_id") or "")
    try:
        attachment_index = int(receipt.get("attachment_index", -1))
    except (TypeError, ValueError):
        attachment_index = -1
    kind = str(receipt.get("detected_kind") or "").lower()
    expected_hash = str(receipt.get("stored_sha256") or "").lower()
    source_hash = str(receipt.get("source_sha256") or "").lower()
    if not MESSAGE_RE.fullmatch(message_id) or attachment_index < 0:
        return None, "receipt_invalid"
    if receipt.get("quarantined") is not True or receipt.get("content_parsed") is not False:
        return None, "receipt_invalid"
    if receipt.get("stored_path") != str(stored_path):
        return None, "receipt_invalid"
    action = KIND_TO_ACTION.get(kind)
    # Unsupported media remain strictly ingress-only: no ticket is created and
    # no analysis-integrity claim is needed for this early return.
    if action is None:
        return {"issue": False, "kind": kind}, None
    if not HASH_RE.fullmatch(expected_hash) or source_hash != expected_hash:
        return None, "stored_hash_mismatch"
    if _sha256(stored_path) != expected_hash:
        return None, "stored_hash_mismatch"
    if not CHAT_RE.fullmatch(chat_id) or not SENDER_RE.fullmatch(sender_id):
        return None, "receipt_invalid"
    binding = _load_json(receipt_path.parent / "route_binding.json")
    event_id_hash = binding.get("ingress_event_id_hash") if binding else None
    if event_id_hash is not None and not HASH_RE.fullmatch(str(event_id_hash).lower()):
        return None, "receipt_invalid"
    return {
        "issue": True,
        "message_id": message_id,
        "attachment_index": attachment_index,
        "receipt_path": str(receipt_path),
        "stored_path": str(stored_path),
        "stored_sha256": expected_hash,
        "media_kind": kind,
        "allowed_action": action,
        "analyzer_action": ACTION_TO_ANALYZER[action],
        "chat_id": chat_id,
        "uploader_id": sender_id,
        "ingress_event_id_hash": str(event_id_hash).lower() if event_id_hash else None,
    }, None


def issue_media_action_ticket(
    result: Dict[str, Any],
    *,
    chat_id: str,
    sender_id: str,
    now: Optional[str] = None,
    ttl_seconds: Optional[int] = None,
    not_before_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """Issue exactly one opaque ticket for one safe non-text attachment.

    The raw ticket exists only in this return value.  The on-disk record and
    attachment index retain its SHA-256 digest, never the raw value.
    """
    operation_now = now or _utc_now()
    operation_epoch = _epoch(operation_now)
    if operation_epoch is None:
        return _error("ticket_clock_invalid")
    ttl = _bounded_positive_seconds(ttl_seconds, TICKET_TTL_SECONDS, 300)
    not_before_delay = _bounded_positive_seconds(not_before_seconds, TICKET_NOT_BEFORE_SECONDS, 60)
    if ttl is None or ttl < 1 or not_before_delay is None:
        return _error("ticket_policy_invalid")
    cleanup_error = _expire_pending_tickets(operation_epoch)
    if cleanup_error:
        return _error(cleanup_error)
    material, error = _validate_ticket_material(result, chat_id, sender_id)
    if error:
        return _error(error)
    assert material is not None
    if not material["issue"]:
        return {"status": "quarantined", "ticket_issued": False, "media_kind": material["kind"]}

    index_path = _attachment_index_path(material["message_id"], material["attachment_index"])
    index_lock = index_path.with_suffix(".lock")
    active_path = _active_ticket_path(
        material["chat_id"], material["uploader_id"], material["media_kind"]
    )
    active_lock = _active_ticket_lock_path(
        material["chat_id"], material["uploader_id"], material["media_kind"]
    )
    record_candidate = _record_path("0" * 64)
    if not all(
        _safe_ticket_state_path(path)
        for path in (index_path, index_lock, active_path, active_lock, record_candidate)
    ):
        return _error("ticket_store_invalid")
    if not _acquire_lock(index_lock):
        return {
            "status": "quarantined",
            "ticket_issued": False,
            "already_issued": True,
            "media_kind": material["media_kind"],
        }
    try:
        existing = _load_json(index_path)
        if existing and HASH_RE.fullmatch(str(existing.get("ticket_hash") or "")):
            return {
                "status": "quarantined",
                "ticket_issued": False,
                "already_issued": True,
                "media_kind": material["media_kind"],
            }
        if index_path.exists():
            return _error("ticket_store_invalid")
        recovered_hash, recovery_error = _existing_attachment_ticket(
            material["message_id"], material["attachment_index"]
        )
        if recovery_error:
            return _error(recovery_error)
        if recovered_hash is not None:
            _atomic_write(index_path, {"schema_version": "1.0", "ticket_hash": recovered_hash})
            return {
                "status": "quarantined",
                "ticket_issued": False,
                "already_issued": True,
                "media_kind": material["media_kind"],
            }

        if not _acquire_lock(active_lock):
            return _error("ticket_store_busy")
        try:
            cancellation_error = _cancel_other_pending_tickets(
                chat_id=material["chat_id"],
                sender_id=material["uploader_id"],
                media_kind=material["media_kind"],
                now=operation_now,
            )
            if cancellation_error:
                return _error(cancellation_error)

            created_at = operation_now
            token = secrets.token_urlsafe(TICKET_BYTES)
            ticket_hash = _ticket_hash(token)
            record_path = _record_path(ticket_hash)
            if not _safe_ticket_state_path(record_path):
                return _error("ticket_store_invalid")
            expires_at = datetime.fromtimestamp(operation_epoch + ttl, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            not_before = datetime.fromtimestamp(
                operation_epoch + not_before_delay, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            record = {
                "schema_version": "1.1",
                "ticket_hash": ticket_hash,
                "chat_id": material["chat_id"],
                "uploader_id": material["uploader_id"],
                "attachment_message_id": material["message_id"],
                "attachment_index": material["attachment_index"],
                "receipt_path": material["receipt_path"],
                "stored_path": material["stored_path"],
                "stored_sha256": material["stored_sha256"],
                "media_kind": material["media_kind"],
                "allowed_action": material["allowed_action"],
                "analyzer_action": material["analyzer_action"],
                "created_at": created_at,
                "not_before": not_before,
                "expires_at": expires_at,
                "status": "pending",
                "consumed_at": None,
                "analysis_request_path": None,
                "idempotency_key": f"ticket-{ticket_hash}",
                "analysis_status": None,
                "ingress_event_id_hash": material.get("ingress_event_id_hash"),
            }
            _atomic_write(record_path, record)
            _atomic_write(active_path, {"schema_version": "1.0", "ticket_hash": ticket_hash})
            _atomic_write(index_path, {"schema_version": "1.0", "ticket_hash": ticket_hash})
            return {
                "status": "quarantined",
                "ticket_issued": True,
                "ticket": token,
                "media_kind": material["media_kind"],
                "allowed_action": material["allowed_action"],
                "not_before": not_before,
                "expires_at": expires_at,
            }
        finally:
            _release_lock(active_lock)
    finally:
        _release_lock(index_lock)


def _validate_record_artifacts(
    record: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    receipt_path = _safe_existing_path(record.get("receipt_path"), STORAGE_ROOT, "receipt.json")
    stored_path = _safe_existing_path(record.get("stored_path"), STORAGE_ROOT)
    if receipt_path is None or stored_path is None:
        return None, "receipt_invalid"
    receipt = _load_json(receipt_path)
    if (
        receipt is None
        or receipt.get("quarantined") is not True
        or receipt.get("content_parsed") is not False
    ):
        return None, "receipt_invalid"
    if receipt.get("analysis_allowed") is not True:
        return None, "analysis_not_allowed"
    if receipt.get("message_id") != record.get("attachment_message_id"):
        return None, "receipt_invalid"
    try:
        if int(receipt.get("attachment_index", -1)) != int(record.get("attachment_index", -2)):
            return None, "receipt_invalid"
    except (TypeError, ValueError):
        return None, "receipt_invalid"
    if receipt.get("stored_path") != str(stored_path):
        return None, "receipt_invalid"
    recorded_hash = str(record.get("stored_sha256") or "").lower()
    receipt_hash = str(receipt.get("stored_sha256") or "").lower()
    source_hash = str(receipt.get("source_sha256") or "").lower()
    if (
        not HASH_RE.fullmatch(recorded_hash)
        or receipt_hash != recorded_hash
        or source_hash != recorded_hash
    ):
        return None, "stored_hash_mismatch"
    if _sha256(stored_path) != recorded_hash:
        return None, "stored_hash_mismatch"
    return {"receipt_path": receipt_path, "stored_path": stored_path, "receipt": receipt}, None


def consume_media_action_ticket(
    args: Dict[str, Any],
    *,
    create_request: Callable[[Dict[str, Any]], Dict[str, Any]],
    dispatch: Callable[[str, Dict[str, Any]], Dict[str, Any]],
    now: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate and consume a ticket, then server-side create and dispatch once."""
    operation_now = now or _utc_now()
    raw_args = args if isinstance(args, dict) else {}
    chat_id = str(raw_args.get("current_chat_context") or "")
    sender_id = str(raw_args.get("current_sender_context") or "")
    ticket_hash: Optional[str] = None
    record: Optional[Dict[str, Any]] = None
    command: Optional[Dict[str, str]] = None
    pre_dispatch_audited = False

    def finish(result: Dict[str, Any]) -> Dict[str, Any]:
        audit_written = _write_consumption_audit(
            chat_id=chat_id,
            sender_id=sender_id,
            ticket_hash=ticket_hash,
            ticket_state=str(record.get("status")) if record else None,
            media_kind=str(record.get("media_kind")) if record else None,
            action=command.get("action") if command else None,
            result=result,
            now=operation_now,
        )
        if not audit_written and not pre_dispatch_audited:
            return _error("ticket_audit_unavailable")
        return result

    required = {"raw_command", "current_chat_context", "current_sender_context"}
    if not isinstance(args, dict) or set(args) != required:
        return finish(_error("command_invalid"))
    command, command_error = parse_media_action_command(args.get("raw_command"))
    if command_error:
        return finish(_error(command_error))
    assert command is not None
    ticket_hash = _ticket_hash(command["token"])
    if not _execution_enabled():
        return finish(_error("media_ticket_execution_disabled"))
    operation_epoch = _epoch(operation_now)
    if operation_epoch is None:
        return finish(_error("receipt_invalid"))
    cleanup_error = _expire_pending_tickets(operation_epoch)
    if cleanup_error:
        return finish(_error(cleanup_error))
    record_path = _record_path(ticket_hash)
    if not _safe_ticket_state_path(record_path):
        return finish(_error("ticket_store_invalid"))
    record = _load_json(record_path)
    if record is None:
        return finish(
            _error("ticket_store_invalid" if record_path.exists() else "ticket_not_found")
        )
    if record.get("ticket_hash") != ticket_hash:
        return finish(_error("ticket_not_found"))
    expires_at = _epoch(record.get("expires_at"))
    now_epoch = operation_epoch
    if expires_at is None or now_epoch is None:
        return finish(_error("receipt_invalid"))
    if now_epoch >= expires_at:
        if _acquire_lock(_lock_path(ticket_hash)):
            try:
                record = _load_json(record_path) or record
                record["status"] = "expired"
                _atomic_write(record_path, record)
            finally:
                _release_lock(_lock_path(ticket_hash))
        return finish(_error("ticket_expired"))
    status = record.get("status")
    if status in {"cancelled", "consumed", "completed", "failed", "expired"}:
        return finish(_error("ticket_expired" if status == "expired" else "ticket_consumed"))
    if status == "consuming":
        lock_path = _lock_path(ticket_hash)
        if lock_path.exists():
            if _lock_owner_is_alive(lock_path):
                return finish(_error("ticket_in_progress"))
            try:
                lock_path.unlink()
            except OSError:
                return finish(_error("ticket_in_progress"))
        # A consuming record without its exclusive lock can only be the
        # aftermath of a process interruption.  Never replay the Analyzer;
        # atomically terminalize it as failed instead.
        if not _acquire_lock(lock_path):
            return finish(_error("ticket_in_progress"))
        try:
            interrupted = _load_json(record_path) or record
            if interrupted.get("status") == "consuming":
                interrupted["status"] = "failed"
                interrupted["analysis_status"] = "interrupted"
                interrupted["failure_code"] = "ticket_recovery_failed"
                interrupted["consumed_at"] = now or _utc_now()
                _atomic_write(record_path, interrupted)
            return finish(_error("ticket_consumed"))
        finally:
            _release_lock(lock_path)
    if status != "pending":
        return finish(_error("ticket_consumed"))

    not_before = _epoch(record.get("not_before"))
    if not_before is None:
        return finish(_error("ticket_policy_invalid"))
    if now_epoch < not_before:
        return finish(_error("ticket_not_ready"))

    lock_path = _lock_path(ticket_hash)
    if not _safe_ticket_state_path(lock_path):
        return finish(_error("ticket_store_invalid"))
    if not _acquire_lock(lock_path):
        return finish(_error("ticket_in_progress"))
    try:
        record = _load_json(record_path)
        if record is None:
            return finish(
                _error("ticket_store_invalid" if record_path.exists() else "ticket_not_found")
            )
        if record.get("ticket_hash") != ticket_hash:
            return finish(_error("ticket_not_found"))
        locked_expires_at = _epoch(record.get("expires_at"))
        locked_now_epoch = operation_epoch
        if locked_expires_at is None or locked_now_epoch is None:
            return finish(_error("receipt_invalid"))
        if locked_now_epoch >= locked_expires_at:
            record["status"] = "expired"
            _atomic_write(record_path, record)
            return finish(_error("ticket_expired"))
        if record.get("status") in {"cancelled", "consumed", "completed", "failed", "expired"}:
            return finish(_error("ticket_consumed"))
        if record.get("status") != "pending":
            return finish(_error("ticket_in_progress"))
        locked_not_before = _epoch(record.get("not_before"))
        if locked_not_before is None:
            return finish(_error("ticket_policy_invalid"))
        if locked_now_epoch < locked_not_before:
            return finish(_error("ticket_not_ready"))
        if record.get("chat_id") != chat_id:
            return finish(_error("chat_mismatch"))
        if record.get("uploader_id") != sender_id:
            return finish(_error("sender_mismatch"))
        if record.get("allowed_action") != command["action"]:
            return finish(_error("action_mismatch"))
        expected_action = KIND_TO_ACTION.get(str(record.get("media_kind") or "").lower())
        if (
            expected_action != command["action"]
            or record.get("analyzer_action") != ACTION_TO_ANALYZER[command["action"]]
        ):
            return finish(_error("media_kind_mismatch"))
        artifacts, artifact_error = _validate_record_artifacts(record)
        if artifact_error:
            return finish(_error(artifact_error))
        assert artifacts is not None

        record["status"] = "consuming"
        record["consumption_started_at"] = operation_now
        _atomic_write(record_path, record)
        if not _write_consumption_audit(
            chat_id=chat_id,
            sender_id=sender_id,
            ticket_hash=ticket_hash,
            ticket_state="consuming",
            media_kind=str(record.get("media_kind") or ""),
            action=command["action"],
            result={"status": "dispatch_authorized"},
            now=operation_now,
        ):
            record["status"] = "pending"
            record.pop("consumption_started_at", None)
            record["last_error"] = "ticket_audit_unavailable"
            _atomic_write(record_path, record)
            return finish(_error("ticket_audit_unavailable"))
        pre_dispatch_audited = True
        request = create_request(record)
        if request.get("status") not in {"pending", "already_completed"}:
            record["status"] = "failed"
            record["consumed_at"] = operation_now
            record["analysis_status"] = "rejected"
            record["failure_code"] = str(request.get("error_code") or "analyzer_failed")
            _atomic_write(record_path, record)
            return finish(_error("analyzer_failed"))

        record["status"] = "consumed"
        record["consumed_at"] = operation_now
        record["analysis_status"] = request.get("status")
        request_path = _safe_existing_path(request.get("request_path"), STORAGE_ROOT)
        if request_path is None:
            record["status"] = "failed"
            record["analysis_status"] = "rejected"
            record["failure_code"] = "analysis_request_invalid"
            _atomic_write(record_path, record)
            return finish(_error("analyzer_failed"))
        record["analysis_request_path"] = str(request_path)
        _atomic_write(record_path, record)
        job_id = f"media-{secrets.token_hex(12)}"
        analyzer_result = dispatch(
            record["analyzer_action"],
            {
                "job_id": job_id,
                "receipt_path": str(artifacts["receipt_path"]),
                "stored_path": str(artifacts["stored_path"]),
                "analysis_policy": "read_quarantine_copy_only",
            },
        )
        record["analysis_status"] = str(analyzer_result.get("status") or "rejected")
        if analyzer_result.get("status") not in {"completed", "already_analyzed"}:
            record["status"] = "failed"
            record["failure_code"] = str(analyzer_result.get("error_code") or "analyzer_failed")
            _atomic_write(record_path, record)
            return finish(_error("analyzer_failed"))
        record["status"] = "completed"
        _atomic_write(record_path, record)
        completed = {
            "status": "completed",
            "media_kind": record["media_kind"],
            "action": command["action"],
        }
        # Presentation is created only by the server-owned Analyzer dispatcher.
        # Keep every other Analyzer field, especially paths and hashes, private.
        presentation = analyzer_result.get("presentation")
        if isinstance(presentation, dict):
            completed["presentation"] = presentation
        return finish(completed)
    finally:
        _release_lock(lock_path)
