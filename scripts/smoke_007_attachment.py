"""Attachment smoke: stage a PNG, run an openclaw agent turn instructing the
video-factory router to call ingest_attachment, then verify the receipt.

This tests whether the MCP tool is callable inside a real Gateway agent turn
(unlike /tools/invoke which does not expose MCP tools). Reads real ids from
config. Cleans up the staged file and ingested copy afterward.
"""

import json, os, shutil, subprocess
from pathlib import Path

CFG = Path(r"C:\Users\Admin\.openclaw\openclaw.json")
REPO = Path(r"E:\project\OpenClaw_VideoFactory")
data = json.loads(CFG.read_text(encoding="utf-8"))
tb = next(
    b
    for b in data["bindings"]
    if b.get("agentId") == "video-factory"
    and b.get("match", {}).get("peer", {}).get("kind") == "group"
)
TARGET_ID = tb["match"]["peer"]["id"]
SENDER_ID = data["channels"]["feishu"]["accounts"]["zhongshu"]["groups"][TARGET_ID]["allowFrom"][0]
INBOUND = Path(data["mcp"]["servers"]["ingest"]["env"]["OPENCLAW_INBOUND_ROOT"])

INBOUND.mkdir(parents=True, exist_ok=True)
stage = INBOUND / "smoke_png_007.png"
shutil.copy(REPO / "tests" / "fixtures" / "feishu_delivery" / "p0-image-test.png", stage)
size = stage.stat().st_size
MESSAGE_ID = "om_smokeagent007"

prompt = (
    "SMOKE TEST: call the ingest_attachment tool with EXACTLY these arguments "
    f"and report the tool result: message_id={MESSAGE_ID}, attachment_index=0, "
    f"attachment_count=1, source_media_path={stage}, original_file_name=smoke_png_007.png, "
    f"content_type=image/png, size_bytes={size}, chat_id={TARGET_ID}, sender_id={SENDER_ID}. "
    "Do not read the image. Just call ingest_attachment and reply with its status field."
)

print("=== openclaw agent --agent video-factory (attachment smoke) ===")
OPENCLAW = r"C:\Users\Admin\AppData\Roaming\npm\openclaw.cmd"
proc = subprocess.run(
    [OPENCLAW, "agent", "--agent", "video-factory", "-m", prompt, "--json"],
    capture_output=True,
    text=True,
    timeout=180,
    shell=False,
)
out = proc.stdout
# Parse the JSON result (openclaw agent --json prints a JSON object).
try:
    res = json.loads(out)
    status = res.get("status")
    summary = res.get("summary")
    payloads = res.get("result", {}).get("payloads", [])
    text = payloads[0].get("text", "")[:400] if payloads else ""
    agent_meta = res.get("result", {}).get("meta", {}).get("agentMeta", {})
    print("status:", status, "| summary:", summary)
    print("model:", agent_meta.get("model"))
    print("reply_text:", text)
except Exception as e:
    print("parse_err:", e)
    print("raw_out:", out[:600])

# Check whether the receipt landed (proves the tool was actually called).
receipt = REPO / "input" / "feishu" / MESSAGE_ID / "attachment-000" / "receipt.json"
print("\n=== receipt on disk ===")
if receipt.exists():
    rec = json.loads(receipt.read_text(encoding="utf-8"))
    print("receipt exists: True")
    print("quarantined:", rec.get("quarantined"), "content_parsed:", rec.get("content_parsed"))
    print("sha256 present:", bool(rec.get("sha256")))
    smoke_ok = rec.get("quarantined") is True and rec.get("content_parsed") is False
else:
    print("receipt exists: False (path:", receipt, ")")
    smoke_ok = False

# Cleanup
try:
    stage.unlink()
except:
    pass
msg_root = REPO / "input" / "feishu" / MESSAGE_ID
if msg_root.exists():
    shutil.rmtree(msg_root, ignore_errors=True)

print("\nSMOKE_ATTACHMENT_OK:", smoke_ok)
