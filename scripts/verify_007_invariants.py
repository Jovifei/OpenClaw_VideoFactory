"""Verify P0-007 post-restart invariants against the backup config."""

import json, hashlib
from pathlib import Path

CUR = Path(r"C:\Users\Admin\.openclaw\openclaw.json")
# Find the backup created earlier.
import glob, os

bak = sorted(glob.glob(r"C:\Users\Admin\.openclaw\openclaw.json.bak-007-*"))[-1]
cur = json.loads(CUR.read_text(encoding="utf-8"))
old = json.loads(Path(bak).read_text(encoding="utf-8"))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


print("=== topology ===")
print("agents_count:", len(cur["agents"]["list"]), "(was", len(old["agents"]["list"]), ")")
print("bindings_count:", len(cur["bindings"]), "(was", len(old["bindings"]), ")")
print("cron unchanged (not in config; registered separately)")

print("\n=== video-factory durable + tools ===")
vf = next(a for a in cur["agents"]["list"] if a["id"] == "video-factory")
print("model.primary:", vf["model"]["primary"])
print("model.fallbacks:", vf["model"]["fallbacks"])
print("tools.allow count:", len(vf["tools"].get("allow", [])))
print("tools.deny count:", len(vf["tools"].get("deny", [])))
print("tools.exec present:", "exec" in vf["tools"], "(should be False - removed)")
print("subagents.allowAgents:", vf.get("subagents", {}).get("allowAgents"))
print("subagents.requireAgentId:", vf.get("subagents", {}).get("requireAgentId"))

print("\n=== tools.media scope ===")
media = cur["tools"].get("media", {})
for cap in ("image", "audio", "video"):
    sc = media.get(cap, {}).get("scope", {})
    rules = sc.get("rules", [])
    kp = rules[0]["match"]["keyPrefix"] if rules else None
    print(
        f"{cap}.scope: rules={len(rules)} default={sc.get('default')} keyPrefix_endswith={kp[-12:] if kp else None}"
    )

print("\n=== 3 analyzer agents (no binding) ===")
binding_agent_ids = {b.get("agentId") for b in cur["bindings"]}
for aid in (
    "video-factory-image-analyzer",
    "video-factory-audio-analyzer",
    "video-factory-video-analyzer",
):
    a = next((x for x in cur["agents"]["list"] if x["id"] == aid), None)
    has_binding = aid in binding_agent_ids
    print(
        f"{aid}: in_list={a is not None} has_binding={has_binding} model={a['model']['primary'] if a else None} exec.mode={a['tools']['exec']['mode'] if a else None}"
    )

print("\n=== other 13 agents unchanged (model + tools hash) ===")
new_ids = {
    "video-factory-image-analyzer",
    "video-factory-audio-analyzer",
    "video-factory-video-analyzer",
}
old_by_id = {a["id"]: a for a in old["agents"]["list"]}
mismatches = 0
for a in cur["agents"]["list"]:
    if a["id"] in new_ids:
        continue
    o = old_by_id.get(a["id"])
    if o is None:
        print("NEW (unexpected):", a["id"])
        mismatches += 1
        continue
    # Compare model and tools (the fields we might have touched); everything else should be identical.
    if json.dumps(a.get("model"), sort_keys=True) != json.dumps(o.get("model"), sort_keys=True):
        print("MODEL CHANGED:", a["id"])
        mismatches += 1
    if a["id"] != "video-factory":
        # non-vf agents: tools must be byte-identical
        if json.dumps(a.get("tools"), sort_keys=True) != json.dumps(o.get("tools"), sort_keys=True):
            print("TOOLS CHANGED:", a["id"])
            mismatches += 1
print("other_agent_mismatches:", mismatches)

print("\n=== target group consumer count ===")
vf_group_bindings = [
    b
    for b in cur["bindings"]
    if b.get("agentId") == "video-factory"
    and b.get("match", {}).get("peer", {}).get("kind") == "group"
]
print("video-factory group bindings:", len(vf_group_bindings), "(should be 1)")

print("\n=== mcp.servers.ingest ===")
ingest = cur.get("mcp", {}).get("servers", {}).get("ingest", {})
print("command:", ingest.get("command"))
print("cwd:", ingest.get("cwd"))
print("env keys:", sorted(ingest.get("env", {}).keys()))

print("\n=== sha ===")
print("current:", sha(CUR))
print("baseline:", "c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d")
