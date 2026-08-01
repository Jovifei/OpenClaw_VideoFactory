# P0 Single-Group Router Config Diff (007)

Baseline SHA-256: `c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d`
New SHA-256: `3001ec3b85a882deb382cb08f5ebdb1c6b285964ea9933f5f0d5c99bc7d89810`

JSON formatting changed (Python `json.dumps` round-trip); the **semantic** diff contains only the 7 authorized field groups below. The real target-group id is masked as `<target-id>`; the live config uses the real id (read from the binding at apply time).

## 1. `tools.media` (new section)

```json5
tools.media.image.scope = { rules:[{action:"deny", match:{channel:"feishu",chatType:"group",keyPrefix:"agent:video-factory:feishu:group:<target-id>"}}], default:"allow" }
tools.media.audio.scope = { /* same */ }
tools.media.video.scope = { /* same */ }
```

## 2. `agents.list[video-factory].model`

```json5
// before
{ primary: "xiaomimimo/mimo-v2.5", fallbacks: ["xiaomimimo/mimo-v2.5-pro"] }
// after
{ primary: "xiaomimimo/mimo-v2.5-pro", fallbacks: ["xiaomimimo/mimo-v2.5-pro"] }
```

## 3. `agents.list[video-factory].tools`

```json5
// before
{ exec: { mode: "full" } }
// after
{
  allow: ["ingest_attachment","ingest__ingest_attachment","bundle-mcp","message",
          "sessions_spawn","sessions_send","sessions_history","sessions_list",
          "session_status","memory_search","memory_get"],
  deny: ["group:runtime","group:fs","group:media","group:web","group:ui",
         "group:agents","group:automation","group:nodes","sessions_yield","subagents"]
}
// NOTE: group:plugins intentionally NOT denied (would override allowlisted MCP tool)
```

## 4. `agents.list[video-factory].subagents` (new)

```json5
{ allowAgents: ["video-factory-image-analyzer","video-factory-audio-analyzer","video-factory-video-analyzer"], requireAgentId: true }
// maxConcurrent/maxChildrenPerAgent/maxSpawnDepth NOT set at agent level (schema strict; left at defaults to avoid affecting other agents)
```

## 5. `agents.list` (append 3, NOT in bindings)

```json5
{ id:"video-factory-image-analyzer",  model:{primary:"xiaomimimo/mimo-v2.5",fallbacks:[]},     tools:{exec:{mode:"deny"},allow:["read","write"],deny:[...]}, subagents:{allowAgents:[]}, ... }
{ id:"video-factory-audio-analyzer",  model:{primary:"xiaomimimo/mimo-v2.5-pro",fallbacks:[]}, tools:{exec:{mode:"deny"},allow:["read","write"],deny:[...]}, subagents:{allowAgents:[]}, ... }
{ id:"video-factory-video-analyzer",  model:{primary:"xiaomimimo/mimo-v2.5",fallbacks:[]},     tools:{exec:{mode:"deny"},allow:["read","write"],deny:[...]}, subagents:{allowAgents:[]}, ... }
```
agents.list length: 14 -> 17.

## 6. `mcp.servers.ingest` (new)

```json5
{ command:"python", args:["scripts/mcp_ingest_attachment.py"], cwd:"E:\\project\\OpenClaw_VideoFactory",
  env:{ OPENCLAW_INBOUND_ROOT, OPENCLAW_PROJECT_ROOT, OPENCLAW_INGEST_SCRIPT, OPENCLAW_AUTHORIZED_CHAT_IDS:<target-id>, OPENCLAW_AUTHORIZED_SENDER_IDS:<allowFrom>, OPENCLAW_ACCOUNT_ID:"zhongshu" } }
```

## 7. `meta.lastTouchedAt` (automatic)

## Unchanged (verified)

14 bindings (incl. zhongshu->video-factory target-group route); zhongshu account credentials/groups/requireMention; gateway port/auth/mode; OAuth; 4 cron; other 13 agents; plugins; skills; agents.defaults.model/imageModel; tools.exec/elevated/web/sessions/agentToAgent (global).

## Verification

`scripts/verify_007_invariants.py` confirms: 17 agents, 14 bindings, 3 analyzers has_binding=False, other_agent_mismatches=1 (only video-factory model, intended), video-factory group bindings=1.
