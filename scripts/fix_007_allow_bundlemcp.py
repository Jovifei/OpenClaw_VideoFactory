"""Targeted fix: add bundle-mcp to video-factory tools.allow so the configured
MCP server (ingest) tool is visible to the agent. With an explicit allow list
(not a profile), bundle-mcp is not implicitly allowed per OpenClaw docs.
Only one MCP server (ingest, 1 tool) is configured, so allowing bundle-mcp is
equivalent to allowing ingest__ingest_attachment.
"""

import json, os, hashlib
from pathlib import Path

CFG = Path(r"C:\Users\Admin\.openclaw\openclaw.json")
data = json.loads(CFG.read_text(encoding="utf-8"))
vf = next(a for a in data["agents"]["list"] if a["id"] == "video-factory")
allow = vf["tools"].setdefault("allow", [])
if "bundle-mcp" not in allow:
    allow.append("bundle-mcp")
tmp = CFG.with_suffix(".json.tmp")
tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
os.replace(tmp, CFG)
print("video-factory.allow:", allow)
print("new sha:", hashlib.sha256(CFG.read_bytes()).hexdigest())
