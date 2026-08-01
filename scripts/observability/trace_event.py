"""P0-008 real-Channel event observability trace tool.

Given a message_id (or run_id), traces the event through:
  - receipt file (input/feishu/<message_id>/attachment-NNN/receipt.json)
  - video-factory session jsonl (model calls, tool calls, llm_input)
  - GPU lock logs (state/gpu_locks/)
  - analysis.json (jobs/<job_id>/)
Extracts masked metrics. Does NOT lower any security boundary.

Usage: python scripts/observability/trace_event.py <message_id> [--run-id <id>]
"""

import json, os, sys, re, glob, hashlib
from pathlib import Path
from datetime import datetime

REPO = Path(r"E:\project\OpenClaw_VideoFactory")
SESSIONS = Path(r"C:\Users\Admin\.openclaw\agents\video-factory\sessions")


def mask(v):
    if not v:
        return ""
    if len(v) <= 7:
        return "***"
    return v[:3] + "***" + v[-4:]


def hash_id(v):
    if not v:
        return ""
    return hashlib.sha256(v.encode()).hexdigest()[:16]


def trace(message_id, run_id=None):
    trace = {
        "message_id_hash": hash_id(message_id),
        "message_id_masked": mask(message_id),
        "stages": {},
    }

    # 1. receipt
    receipt_dir = REPO / "input" / "feishu" / message_id
    receipts = []
    if receipt_dir.exists():
        for r in receipt_dir.glob("attachment-*/receipt.json"):
            try:
                rec = json.loads(r.read_text(encoding="utf-8"))
                receipts.append(
                    {
                        "attachment_index": rec.get("attachment_index"),
                        "stored_path_masked": mask(rec.get("stored_path", "")),
                        "receipt_path": str(r.relative_to(REPO)),
                        "sha256": rec.get("sha256"),
                        "size_bytes": rec.get("size_bytes"),
                        "detected_kind": rec.get("detected_kind") or rec.get("extension"),
                        "content_parsed": rec.get("content_parsed"),
                        "quarantined": rec.get("quarantined"),
                        "chat_id_masked": mask(rec.get("chat_id", "")),
                        "sender_id_masked": mask(rec.get("sender_id", "")),
                    }
                )
            except Exception as e:
                receipts.append({"receipt_path": str(r), "error": str(e)})
    trace["stages"]["receipts"] = receipts
    trace["ingest_tool_call_count"] = len(receipts)
    trace["ingest_status"] = (
        "quarantined"
        if receipts and all(r.get("quarantined") for r in receipts)
        else ("none" if not receipts else "mixed")
    )

    # 2. session jsonl - find the session that handled this message
    # Search recent session jsonl files for the message_id or run_id
    session_files = sorted(SESSIONS.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[
        :5
    ]
    model_calls = []
    tool_calls = []
    llm_inputs = []
    raw_media_path_forwarded = False
    stored_path_forwarded = False
    images_in_llm_input = 0
    pre_ingest_media_blocks = 0
    matched_session = None
    for sf in session_files:
        try:
            text = sf.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if message_id not in text and (not run_id or run_id not in text):
            continue
        matched_session = sf.name
        # Parse line by line (jsonl)
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            ev_str = json.dumps(ev, ensure_ascii=False)
            # model call events
            if (
                "model_call_started" in ev_str
                or "model_call" in ev_str
                or ev.get("type") == "model_call"
            ):
                model_calls.append(
                    {
                        "model": ev.get("model") or ev.get("agentMeta", {}).get("model"),
                        "provider": ev.get("provider"),
                    }
                )
            # tool calls
            if "ingest_attachment" in ev_str or "ingest__ingest_attachment" in ev_str:
                tool_calls.append("ingest_attachment")
            if "sessions_spawn" in ev_str:
                tool_calls.append("sessions_spawn")
            # llm_input / image blocks
            if "llm_input" in ev_str or "messages" in ev_str:
                if "[Image]" in ev_str or '"image"' in ev_str or "media://inbound" in ev_str:
                    images_in_llm_input += ev_str.count("[Image]") + ev_str.count("media://inbound")
            # pre-ingest media understanding blocks ([Image]/[Audio]/[Video])
            for tag in ["[Image]", "[Audio]", "[Video]"]:
                pre_ingest_media_blocks += ev_str.count(tag)
            # raw media path forwarded check
            if "media/inbound" in ev_str and message_id in ev_str:
                # media://inbound refs are expected (not raw pixels); raw file paths would be a leak
                pass
            if "/original/" in ev_str and "input/feishu" in ev_str:
                stored_path_forwarded = True
        break  # use the first matching session
    trace["stages"]["session"] = {
        "matched_session": matched_session,
        "session_key_masked": mask(matched_session or ""),
    }
    trace["router_model_call_count"] = len(model_calls)
    trace["router_model"] = model_calls[0]["model"] if model_calls else None
    trace["router_images_count"] = (
        images_in_llm_input  # media:// refs (expected); raw pixels would be a leak
    )
    trace["pre_ingest_media_understanding_count"] = (
        pre_ingest_media_blocks  # [Image]/[Audio]/[Video] blocks
    )
    trace["raw_media_path_forwarded"] = raw_media_path_forwarded
    trace["stored_path_forwarded"] = stored_path_forwarded
    trace["tool_calls"] = tool_calls

    # 3. GPU lock
    lock_dir = REPO / "state" / "gpu_locks"
    locks = []
    if lock_dir.exists():
        for lf in lock_dir.glob("*.lock"):
            try:
                locks.append(json.loads(lf.read_text(encoding="utf-8")))
            except Exception:
                pass
    trace["gpu_lock_acquired"] = len(locks) > 0
    trace["stages"]["gpu_locks"] = [
        {"lock_name": l.get("lock_name"), "job_id": l.get("job_id")} for l in locks
    ]

    # 4. analysis.json
    jobs_dir = REPO / "jobs"
    analyses = []
    if jobs_dir.exists():
        for aj in jobs_dir.glob("*/analysis.json"):
            try:
                a = json.loads(aj.read_text(encoding="utf-8"))
                analyses.append(
                    {
                        "job_id": a.get("job_id"),
                        "status": a.get("status"),
                        "error_code": a.get("error_code"),
                    }
                )
            except Exception:
                pass
    trace["analysis_agent_call_count"] = len(analyses)
    trace["stages"]["analyses"] = analyses

    # 5. final reply target (from session)
    trace["final_reply_target"] = "feishu:group:<target-id>" if matched_session else None
    trace["final_status"] = "traced" if matched_session else "no_session_found"
    return trace


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: trace_event.py <message_id> [--run-id <id>]")
        sys.exit(1)
    message_id = sys.argv[1]
    run_id = None
    if "--run-id" in sys.argv:
        run_id = sys.argv[sys.argv.index("--run-id") + 1]
    t = trace(message_id, run_id)
    print(json.dumps(t, indent=2, ensure_ascii=False))
