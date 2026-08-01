# P0 Router Tool Policy

Task: `P0-SINGLE-GROUP-MEDIA-ROUTER-007`
Status: **prepared, pending production gate**
Applies to: `agents.list[video-factory]` only (the entry router). Other 13 agents untouched.

## Principle

The router is constrained by **OpenClaw tool policy** (allow non-empty => everything else blocked; deny always wins), NOT by prompt. AGENTS.md documents the flow; tool policy is the hard stop. `elevated` does NOT override `deny` (docs: "Elevated is not skill-scoped and does not override tool allow/deny").

## Durable model

`agents.list[video-factory].model`:
- `primary`: `xiaomimimo/mimo-v2.5-pro` (text_only)
- `fallbacks`: `["xiaomimimo/mimo-v2.5-pro"]` (text-only fallback; no multimodal in the chain)

With a text-only primary, image attachments arrive as `media://inbound/*` refs (not pixels). The session auto-override to `pro` (currently `source: auto, reason: timeout`) becomes consistent with the durable config and is cleared on the next session reset.

## allow (explicit allowlist)

```
ingest_attachment      # only ingestion channel; args bound by Channel adapter
ingest__ingest_attachment  # MCP-exposed name (bundle-mcp server prefix); added for safety
message                # reply to original group only
sessions_spawn         # dispatch to 3 analyzers (subagents.allowAgents whitelist)
sessions_send          # pass receipt-only args to analyzer sessions
sessions_history       # read analyzer job state
sessions_list          # list analyzer jobs
session_status         # poll job completion
memory_search          # P0 task management (optional)
memory_get             # P0 task management (optional)
```

When `allow` is non-empty, every tool not listed is blocked.

## deny (defense-in-depth; always wins)

```
group:runtime     # exec, process, code_execution, bash
group:fs          # read, write, edit, apply_patch
group:media       # image, image_generate, music_generate, video_generate, tts
group:web         # web_search, x_search, web_fetch
group:ui          # browser, canvas
group:agents      # agents_list, get_goal, create_goal, update_goal, update_plan, skill_workshop
group:automation  # heartbeat_respond, cron, gateway
group:plugins     # all plugin/MCP tools (ingest is allowlisted by exact name, not by this group)
group:nodes       # nodes
sessions_yield    # router does not yield
subagents         # only sessions_spawn is allowed, not the generic subagents tool
```

Also: remove `agents.list[video-factory].tools.exec.mode=full` to avoid audit ambiguity with `deny group:runtime`.

## subagents (dispatch whitelist)

```json5
subagents: {
  allowAgents: ["video-factory-image-analyzer", "video-factory-audio-analyzer", "video-factory-video-analyzer"],
  requireAgentId: true,
  maxConcurrent: 3,
  maxChildrenPerAgent: 3,
  maxSpawnDepth: 1
}
```

- No `"*"`: the router can only spawn the 3 analyzers, not main/taizi/zhongshu/etc.
- `requireAgentId`: forces explicit target on every spawn.
- `maxSpawnDepth: 1`: analyzers cannot spawn further.

## elevated (unchanged, documented)

`tools.elevated.enabled=true` + `allowFrom.feishu=["*"]` is global and NOT changed. With `deny group:runtime` on the router, `elevated` cannot grant `exec` to the router. Elevated only affects already-allowed `exec` (sandbox/approval bypass), which the router does not have.

## Global defaults NOT changed

`agents.defaults.model`, `agents.defaults.imageModel` (unset), `tools.exec`, `tools.elevated`, `tools.web`, `tools.sessions.visibility`, `skills.entries` are all unchanged. Only `agents.list[video-factory]` is tightened. The other 13 agents' config hashes are unchanged.

## Change order (production)

1. Create the 3 internal analyzer agent dirs + `agents.list` entries (no bindings).
2. Add `mcp.servers.ingest`.
3. Change `video-factory` model + tools + subagents.
4. Add `tools.media.*.scope` deny.
5. One Gateway restart.
6. Verify `agents_list` = 17, `bindings` = 14, `mcp probe ingest` lists `ingest_attachment`, `sandbox explain --agent video-factory` shows the allow/deny, other 13 agents unchanged.
