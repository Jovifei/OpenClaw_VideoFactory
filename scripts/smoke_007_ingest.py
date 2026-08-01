"""P0-007 runtime smoke: call ingest_attachment through the Gateway /tools/invoke.

Proves the production path: Gateway auth -> video-factory tool policy -> MCP
server (ingest) -> 07 ingest script -> quarantine receipt. Reads the gateway
token, target group id, and allowFrom sender id from the live config (no
hardcoded secrets/ids). Stages a throwaway TXT in the real inbound root.
"""

import json, os, sys, shutil, urllib.request, urllib.error
from pathlib import Path

CFG = Path(r"C:\Users\Admin\.openclaw\openclaw.json")
REPO = Path(r"E:\project\OpenClaw_VideoFactory")
data = json.loads(CFG.read_text(encoding="utf-8"))
TOKEN = data["gateway"]["auth"]["token"]
vf_binding = next(
    b
    for b in data["bindings"]
    if b.get("agentId") == "video-factory"
    and b.get("match", {}).get("peer", {}).get("kind") == "group"
)
TARGET_ID = vf_binding["match"]["peer"]["id"]
SENDER_ID = data["channels"]["feishu"]["accounts"]["zhongshu"]["groups"][TARGET_ID]["allowFrom"][0]
INBOUND = Path(data["mcp"]["servers"]["ingest"]["env"]["OPENCLAW_INBOUND_ROOT"])

INBOUND.mkdir(parents=True, exist_ok=True)
stage = INBOUND / "smoke_007.txt"
stage.write_text("p0-007 runtime smoke attachment\n", encoding="utf-8")

MESSAGE_ID = "om_smoke007a"
payload = {
    "tool": "ingest__ingest_attachment",
    "agentId": "video-factory",
    "args": {
        "message_id": MESSAGE_ID,
        "attachment_index": 0,
        "attachment_count": 1,
        "source_media_path": str(stage),
        "original_file_name": "smoke_007.txt",
        "content_type": "text/plain",
        "size_bytes": stage.stat().st_size,
        "chat_id": TARGET_ID,
        "sender_id": SENDER_ID,
        "event_id": "evt_smoke007",
    },
}

req = urllib.request.Request(
    "http://127.0.0.1:18789/tools/invoke",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    method="POST",
)
print("=== /tools/invoke ingest__ingest_attachment (agentId=video-factory) ===")
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.loads(r.read().decode("utf-8"))
    print("http_status: 200")
    print("ok:", body.get("ok"))
    result = body.get("result", {})
    content = result.get("content", [{}])
    text = content[0].get("text", "{}") if content else "{}"
    parsed = json.loads(text)

    # Mask ids in output.
    def mask(v):
        return v[:3] + "***" + v[-4:] if v and len(v) > 7 else "***"

    parsed_safe = dict(parsed)
    if "message_id" in parsed_safe:
        parsed_safe["message_id"] = mask(parsed_safe["message_id"])
    print("tool_result:", json.dumps(parsed_safe, ensure_ascii=False, indent=2))
    smoke_ok = parsed.get("status") == "quarantined" and parsed.get("quarantined") is True
except urllib.error.HTTPError as e:
    print("http_status:", e.code)
    print("error_body:", e.read().decode("utf-8")[:500])
    smoke_ok = False
except Exception as e:
    print("exception:", type(e).__name__, str(e)[:300])
    smoke_ok = False

# Verify the receipt file landed in the project.
receipt_path = parsed.get("receipt_path") if "parsed" in dir() else None
print("\n=== receipt on disk ===")
if receipt_path and Path(receipt_path).exists():
    rec = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    print("receipt exists: True")
    print("quarantined:", rec.get("quarantined"), "content_parsed:", rec.get("content_parsed"))
    print("detected_kind:", rec.get("detected_kind") or parsed.get("detected_kind"))
    print("sha256 present:", bool(rec.get("sha256")))
else:
    print("receipt exists: False (path:", receipt_path, ")")
    smoke_ok = False

# Cleanup the staged inbound file + the ingested copy (smoke only).
try:
    stage.unlink()
except Exception:
    pass
msg_root = REPO / "input" / "feishu" / MESSAGE_ID
if msg_root.exists():
    shutil.rmtree(msg_root, ignore_errors=True)

print("\nSMOKE_INGEST_OK:", smoke_ok)
