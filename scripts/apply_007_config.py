"""Apply P0-SINGLE-GROUP-MEDIA-ROUTER-007 config changes to openclaw.json.

Reads the real target-group id and allowFrom sender id FROM the current config
(binding peer.id + zhongshu groups.<id>.allowFrom[0]), so no real identifiers
are hardcoded in this script. Writes atomically (temp + os.replace).

Run once. Records the semantic changes to reports/P0_SINGLE_GROUP_ROUTER_CONFIG_DIFF_APPLIED.json.
"""

import json, os, sys
from pathlib import Path

CFG = Path(r"C:\Users\Admin\.openclaw\openclaw.json")
REPO = Path(r"E:\project\OpenClaw_VideoFactory")
APPLIED = REPO / "reports" / "P0_SINGLE_GROUP_ROUTER_CONFIG_DIFF_APPLIED.json"


def mask(v):
    if not v or len(v) <= 7:
        return "***"
    return v[:3] + "***" + v[-4:]


def main():
    data = json.loads(CFG.read_text(encoding="utf-8"))

    # Locate video-factory agent and target group id (from its binding).
    agents = data["agents"]["list"]
    vf_idx = next(i for i, a in enumerate(agents) if a.get("id") == "video-factory")
    vf_binding = next(
        b
        for b in data["bindings"]
        if b.get("agentId") == "video-factory"
        and b.get("match", {}).get("peer", {}).get("kind") == "group"
    )
    target_id = vf_binding["match"]["peer"]["id"]
    zhongshu = data["channels"]["feishu"]["accounts"]["zhongshu"]
    sender_id = zhongshu["groups"][target_id]["allowFrom"][0]
    keyprefix = f"agent:video-factory:feishu:group:{target_id}"

    def fresh_scope():
        return {
            "rules": [
                {
                    "action": "deny",
                    "match": {"channel": "feishu", "chatType": "group", "keyPrefix": keyprefix},
                }
            ],
            "default": "allow",
        }

    # 1. tools.media scope deny (target group only)
    data["tools"]["media"] = {
        "image": {"scope": fresh_scope()},
        "audio": {"scope": fresh_scope()},
        "video": {"scope": fresh_scope()},
    }

    # 2. video-factory durable model -> text-only pro
    agents[vf_idx]["model"] = {
        "primary": "xiaomimimo/mimo-v2.5-pro",
        "fallbacks": ["xiaomimimo/mimo-v2.5-pro"],
    }

    # 3. video-factory tool policy (replace exec.mode=full with allow/deny)
    agents[vf_idx]["tools"] = {
        "allow": [
            "ingest_attachment",
            "ingest__ingest_attachment",
            "message",
            "sessions_spawn",
            "sessions_send",
            "sessions_history",
            "sessions_list",
            "session_status",
            "memory_search",
            "memory_get",
        ],
        "deny": [
            "group:runtime",
            "group:fs",
            "group:media",
            "group:web",
            "group:ui",
            "group:agents",
            "group:automation",
            "group:nodes",
            "sessions_yield",
            "subagents",
        ],
    }
    # NOTE: group:plugins is intentionally NOT denied. The explicit allow list
    # permits only ingest__ingest_attachment; all other plugin/MCP tools are
    # blocked by "allow non-empty => everything else blocked". A group:plugins
    # deny would override the allow (deny wins) and block the ingest tool too.

    # 4. video-factory subagents whitelist (per-agent schema is strict: only
    #    delegationMode/allowAgents/model/thinking/requireAgentId allowed here;
    #    maxConcurrent/maxChildrenPerAgent/maxSpawnDepth belong on agents.defaults
    #    and are left at their defaults to avoid affecting other agents).
    agents[vf_idx]["subagents"] = {
        "allowAgents": [
            "video-factory-image-analyzer",
            "video-factory-audio-analyzer",
            "video-factory-video-analyzer",
        ],
        "requireAgentId": True,
    }

    # 5. append 3 binding-less internal analyzer agents (idempotent)
    existing = {a["id"] for a in agents}
    analyzer_tools = {
        "exec": {"mode": "deny"},
        "allow": ["read", "write"],
        "deny": [
            "exec",
            "process",
            "browser",
            "image",
            "image_generate",
            "video_generate",
            "music_generate",
            "pdf",
            "web",
            "gateway",
            "nodes",
            "cron",
            "feishu",
            "sessions_spawn",
            "sessions_send",
        ],
    }
    new_agents = [
        (
            "video-factory-image-analyzer",
            "VF Image Analyzer",
            "workspace-vf-image",
            "agents\\video-factory-image-analyzer\\agent",
            {"primary": "xiaomimimo/mimo-v2.5", "fallbacks": []},
        ),
        (
            "video-factory-audio-analyzer",
            "VF Audio Analyzer",
            "workspace-vf-audio",
            "agents\\video-factory-audio-analyzer\\agent",
            {"primary": "xiaomimimo/mimo-v2.5-pro", "fallbacks": []},
        ),
        (
            "video-factory-video-analyzer",
            "VF Video Analyzer",
            "workspace-vf-video",
            "agents\\video-factory-video-analyzer\\agent",
            {"primary": "xiaomimimo/mimo-v2.5", "fallbacks": []},
        ),
    ]
    added = []
    for aid, name, ws, ad, model in new_agents:
        if aid in existing:
            continue
        agents.append(
            {
                "id": aid,
                "name": name,
                "workspace": f"C:\\Users\\Admin\\.openclaw\\{ws}",
                "agentDir": f"C:\\Users\\Admin\\.openclaw\\{ad}",
                "model": model,
                "contextInjection": "continuation-skip",
                "skills": [],
                "subagents": {"allowAgents": []},
                "tools": analyzer_tools,
            }
        )
        added.append(aid)

    # 6. mcp.servers.ingest
    data.setdefault("mcp", {}).setdefault("servers", {})
    data["mcp"]["servers"]["ingest"] = {
        "command": "python",
        "args": ["scripts/mcp_ingest_attachment.py"],
        "cwd": str(REPO),
        "env": {
            "OPENCLAW_INBOUND_ROOT": str(Path.home() / ".openclaw" / "media" / "inbound"),
            "OPENCLAW_PROJECT_ROOT": str(REPO),
            "OPENCLAW_INGEST_SCRIPT": str(REPO / "scripts" / "run_ingest_safe.ps1"),
            "OPENCLAW_AUTHORIZED_CHAT_IDS": target_id,
            "OPENCLAW_AUTHORIZED_SENDER_IDS": sender_id,
            "OPENCLAW_ACCOUNT_ID": "zhongshu",
        },
    }

    # Atomic write
    tmp = CFG.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, CFG)

    import hashlib

    sha = hashlib.sha256(CFG.read_bytes()).hexdigest()
    applied = {
        "applied": True,
        "new_config_sha256": sha,
        "target_id_masked": mask(target_id),
        "sender_id_masked": mask(sender_id),
        "keyprefix_masked": f"agent:video-factory:feishu:group:{mask(target_id)}",
        "agents_count": len(agents),
        "bindings_count": len(data["bindings"]),
        "analyzers_added": added,
        "mcp_server": "ingest",
        "video_factory_model": agents[vf_idx]["model"]["primary"],
        "video_factory_allow_count": len(agents[vf_idx]["tools"]["allow"]),
        "video_factory_deny_count": len(agents[vf_idx]["tools"]["deny"]),
    }
    APPLIED.write_text(json.dumps(applied, indent=2), encoding="utf-8")
    print(json.dumps(applied, indent=2))


if __name__ == "__main__":
    main()
