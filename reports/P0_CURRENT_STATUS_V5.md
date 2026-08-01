# P0 Current Status V5

Overall: **conditional_not_passed** (P0 Gate NOT run; PROJECT_STATUS NOT updated - both prohibited this round).

The 007 single-group media router production implementation is **complete and smoke-verified**. The OpenClaw VideoFactory Feishu group still has exactly one consumer (`zhongshu` -> `video-factory` core Binding) and one core Binding. No second group, no second consumer, no plugin-owned Binding, no core source change, no model download, no new runtime dependency.

## What changed this round (007)

- `tools.media.image/audio/video.scope` deny for the target group (pre-ingest media understanding closed for that group only; default allow elsewhere).
- `video-factory` durable model -> `xiaomimimo/mimo-v2.5-pro` (text-only); fallbacks text-only.
- `video-factory` tool policy: explicit allowlist (`ingest_attachment`, `message`, `sessions_*`, `memory_*`, `bundle-mcp`) + deny (`group:runtime/fs/media/web/ui/agents/automation/nodes`, `sessions_yield`, `subagents`); `exec.mode=full` removed.
- `video-factory.subagents`: `allowAgents` = 3 analyzers, `requireAgentId=true`.
- 3 binding-less internal analyzers added (`video-factory-image-analyzer` / `-audio-analyzer` / `-video-analyzer`); agents 14->17, bindings still 14, cron still 4.
- `mcp.servers.ingest` registered (zero-dependency Python stdlib MCP server exposing `ingest_attachment`).
- `scripts/07_ingest_inbound_media.ps1` extended for multi-attachment (backward compatible; 32/32 still pass).
- `scripts/gpu_media_lock.py` (zero-dependency GPU mutex).
- AGENTS.md updated with 12 router flow rules.

## Test results

- Single-group router offline: **45/45** (was 15/15; +30 new).
- Inbound media regression: **32/32** (unchanged).
- ingest_attachment core: **17/17** (new).
- Total: **94/94**.

## Runtime smoke

- Text: PASS (`mimo-v2.5-pro`, `model_call_count=1`, reply correct).
- PNG attachment: PASS (router called `ingest_attachment`, receipt `quarantined=true`/`content_parsed=false`, text-only model did not read pixels).
- MCP server: PASS (1 tool `ingest__ingest_attachment` live).
- Audio/MP4 event + direct pre-ingest count: config-verified + behavior-consistent; live Channel-event measurement deferred to user's real upload (forbidden to require this round).

## Config integrity

- Baseline SHA-256 `c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d` -> new `3001ec3b85a882deb382cb08f5ebdb1c6b285964ea9933f5f0d5c99bc7d89810`.
- Semantic diff: only the 7 authorized field groups changed (see `P0_SINGLE_GROUP_ROUTER_CONFIG_DIFF.json`).
- Other 13 agents: config hash unchanged (only video-factory model changed).
- Bindings 14, cron 4, target-group consumer 1.

## Gateway

3 restarts (initial apply + 2 smoke-driven config fixes: `group:plugins` deny removal, `bundle-mcp` allow addition). Each validated before restart. Gateway healthy (port 18789, config valid).

## Protected state (unchanged)

No P0 Gate run, no P0_READY, no PROJECT_STATUS update, no commit/tag/push, no P1, no model install/download, no real Feishu outbound send, no OAuth change, no Binding change, no Cron change.
