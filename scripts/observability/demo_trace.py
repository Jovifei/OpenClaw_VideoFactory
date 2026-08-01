"""P0-008 observability demo: run a fresh attachment smoke, trace it, cleanup.
Generates a real event trace (masked) for the EVENT_TRACE evidence.
"""

import json, os, sys, shutil, subprocess, time
from pathlib import Path

sys.path.insert(0, str(Path(r"E:\project\OpenClaw_VideoFactory\scripts")))
import observability.trace_event as tr

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
INBOUND = Path(data["mcp"]["servers"]["ingest"]["env"]["OPENCLAW_INBOUND_ROOT"])

MESSAGE_ID = "om_obstrace008"
stage = INBOUND / "obs_trace_007.png"
shutil.copy(REPO / "tests" / "fixtures" / "feishu_delivery" / "p0-image-test.png", stage)
size = stage.stat().st_size

prompt = (
    f"OBSERVABILITY TRACE: call ingest_attachment with EXACTLY: message_id={MESSAGE_ID}, "
    f"attachment_index=0, attachment_count=1, source_media_path={stage}, original_file_name=obs_trace_007.png, "
    f"content_type=image/png, size_bytes={size}, chat_id={TARGET_ID}, sender_id={SENDER_ID}. "
    "Reply only with the tool's status field."
)
proc = subprocess.run(
    [LARK, "agent", "--agent", "video-factory", "-m", prompt, "--json"],
    capture_output=True,
    text=True,
    timeout=180,
)
try:
    res = json.loads(proc.stdout)
    agent_meta = res.get("result", {}).get("meta", {}).get("agentMeta", {})
    run_id = res.get("runId")
    model = agent_meta.get("model")
    reply = res.get("result", {}).get("payloads", [{}])[0].get("text", "")[:200]
except Exception as e:
    run_id = None
    model = None
    reply = f"parse_err: {e}"

# Trace the event
trace = tr.trace(MESSAGE_ID, run_id)
trace["run_id"] = run_id
trace["router_model_observed"] = model
trace["router_reply_head"] = reply

# Cleanup
try:
    stage.unlink()
except:
    pass
msg_root = REPO / "input" / "feishu" / MESSAGE_ID
if msg_root.exists():
    shutil.rmtree(msg_root, ignore_errors=True)

out = REPO / "reports" / "P0_REAL_CHANNEL_EVENT_TRACE.json"
out.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(trace, indent=2, ensure_ascii=False)[:1800])
print("\n=== wrote", out, "===")
