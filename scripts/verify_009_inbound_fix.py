"""Verify the INBOUND_ROOT bug fix in production: stage a file in the workspace
media/inbound (where the Feishu Channel stages), run an openclaw agent turn
that calls ingest_attachment, confirm quarantined (not path_traversal).
"""

import json, os, shutil, subprocess
from pathlib import Path

CFG = Path(r"C:\Users\Admin\.openclaw\openclaw.json")
REPO = Path(r"E:\project\OpenClaw_VideoFactory")
LARK = r"C:\Users\Admin\AppData\Roaming\npm\openclaw.cmd"
data = json.loads(CFG.read_text(encoding="utf-8"))
tb = next(
    b
    for b in data["bindings"]
    if b.get("agentId") == "video-factory"
    and b.get("match", {}).get("peer", {}).get("kind") == "group"
)
TARGET_ID = tb["match"]["peer"]["id"]
SENDER_ID = data["channels"]["feishu"]["accounts"]["zhongshu"]["groups"][TARGET_ID]["allowFrom"][0]

# Stage in the WORKSPACE media/inbound (mimics Channel staging)
ws_inbound = REPO / "media" / "inbound" / "openclaw-staged-verify"
ws_inbound.mkdir(parents=True, exist_ok=True)
src = ws_inbound / "p0-file-test.txt"
shutil.copy(REPO / "tests" / "fixtures" / "feishu_delivery" / "p0-file-test.txt", src)
size = src.stat().st_size
MESSAGE_ID = "om_verify009fix"

prompt = (
    f"VERIFY FIX: call ingest_attachment with EXACTLY: message_id={MESSAGE_ID}, "
    f"attachment_index=0, attachment_count=1, source_media_path={src}, "
    f"original_file_name=p0-file-test.txt, content_type=text/plain, size_bytes={size}, "
    f"chat_id={TARGET_ID}, sender_id={SENDER_ID}. Reply only with the status field."
)
proc = subprocess.run(
    [LARK, "agent", "--agent", "video-factory", "-m", prompt, "--json"],
    capture_output=True,
    text=True,
    timeout=180,
)
try:
    res = json.loads(proc.stdout)
    reply = res.get("result", {}).get("payloads", [{}])[0].get("text", "")[:300]
    model = res.get("result", {}).get("meta", {}).get("agentMeta", {}).get("model")
except Exception as e:
    reply = f"parse_err: {e}"
    model = None

# Check receipt
receipt = REPO / "input" / "feishu" / MESSAGE_ID / "attachment-000" / "receipt.json"
receipt_ok = receipt.exists()
if receipt_ok:
    rec = json.loads(receipt.read_text(encoding="utf-8"))
    quarantined = rec.get("quarantined")
    content_parsed = rec.get("content_parsed")
else:
    quarantined = content_parsed = None

# Cleanup
shutil.rmtree(ws_inbound, ignore_errors=True)
msg_root = REPO / "input" / "feishu" / MESSAGE_ID
if msg_root.exists():
    shutil.rmtree(msg_root, ignore_errors=True)

print(f"model: {model}")
print(f"reply: {reply}")
print(f"receipt_exists: {receipt_ok}")
print(f"quarantined: {quarantined}  content_parsed: {content_parsed}")
fixed = receipt_ok and quarantined is True and "path_traversal" not in reply.lower()
print(f"\nFIX_VERIFIED: {fixed}")
