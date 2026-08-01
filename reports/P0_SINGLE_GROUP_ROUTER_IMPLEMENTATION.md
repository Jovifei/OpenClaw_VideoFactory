# P0 Single-Group Media Router - Implementation (007)

Task: `P0-SINGLE-GROUP-MEDIA-ROUTER-007`
Status: **SINGLE_GROUP_ROUTER_PRODUCTION_READY** (with documented smoke coverage and platform limitations)
Date: 2026-07-18

## Outcome

The single-Feishu-group, single-consumer, text-only video-factory media router is implemented in production. One group, one `zhongshu` consumer, one core Binding preserved. Pre-ingest media understanding is closed for the target group via `tools.media.*.scope` deny; the durable router model is `xiaomimimo/mimo-v2.5-pro` (text-only); the router tool surface is an explicit allowlist; a deterministic `ingest_attachment` MCP tool does quarantine-first ingestion; three binding-less internal analyzers handle post-receipt image/audio/video analysis; a GPU media lock serializes heavy GPU work. No core source change, no new Binding, no second consumer, no model download, no new runtime dependency.

## 1. Haiku sub-agents (A-F)

All six read-only Haiku reviews completed and wrote reports under `reports/child_claude/`:

| Agent | Report | Key conclusion |
| --- | --- | --- |
| A | `SINGLE_GROUP_MEDIA_SCOPE_REVIEW.md` | scope deny schema verified; keyPrefix `agent:video-factory:feishu:group:<target-id>`; default allow; 3 capabilities separate; durable+scope must ship together |
| B | `SINGLE_GROUP_ROUTER_TOOL_POLICY_REVIEW.md` | minimal allowlist; deny by group shorthands; subagents.allowAgents 3 analyzers + requireAgentId; elevated does not override deny; change order: analyzers first |
| C | `INGEST_ATTACHMENT_CONTRACT_REVIEW.md` | input contract; multi-attachment extension points; receipt schema; masking; not exec wrapper |
| D | `INTERNAL_ANALYZER_AGENTS_REVIEW.md` | no reusable binding-less agent; 3 new needed; isolated workspace/agentDir; 4-field data flow; no pro fallback |
| E | `RTX4070S_MEDIA_RUNTIME_REVIEW.md` | PyTorch 2.11+cu128 + faster-whisper 1.2.1 + ffmpeg 8.1.1 (at C:\ffmpeg\bin, not PATH); no local VLM (Ollama CLI missing); GPU lock needed |
| F | `SINGLE_GROUP_ROUTER_MIGRATION_REVIEW.md` | backup/restart/rollback plan; 12 post-restart verifications; smoke order; rollback triggers |

Main-agent independent re-review: the six reports align with and were incorporated into the implementation. No unresolved critical issues.

## 2. Durable router model

`agents.list[video-factory].model` changed from `{primary: mimo-v2.5 (multimodal), fallbacks: [mimo-v2.5-pro]}` to `{primary: mimo-v2.5-pro (text-only), fallbacks: [mimo-v2.5-pro]}`. The target-group session's prior `auto` override to `pro` (reason: timeout) is now consistent with the durable config and clears on session reset. Verified live: a `openclaw agent` turn reported `model: mimo-v2.5-pro`.

## 3. media scope

`tools.media.image/audio/video.scope` added: each has one `deny` rule matching `{channel: feishu, chatType: group, keyPrefix: agent:video-factory:feishu:group:<target-id>}`, `default: allow`. Only the target group is denied; other groups, DMs, other agents, other channels keep default behavior. The scope is evaluated inside `applyMediaUnderstandingIfNeeded` (before pre-agent hooks), so it is the only mechanism that can block pre-ingest understanding (confirmed by `P0_CHANNEL_MIDDLEWARE_FEASIBILITY` call-order evidence).

## 4. Router tool policy

`agents.list[video-factory].tools`:
- `allow`: `ingest_attachment`, `ingest__ingest_attachment`, `bundle-mcp`, `message`, `sessions_spawn`, `sessions_send`, `sessions_history`, `sessions_list`, `session_status`, `memory_search`, `memory_get`
- `deny`: `group:runtime`, `group:fs`, `group:media`, `group:web`, `group:ui`, `group:agents`, `group:automation`, `group:nodes`, `sessions_yield`, `subagents` (NOTE: `group:plugins` intentionally NOT denied - it would override the allowlisted MCP tool since deny wins; the explicit allow already blocks all other plugin tools)
- removed `tools.exec.mode=full`
- `subagents`: `{allowAgents: [3 analyzers], requireAgentId: true}` (per-agent schema is strict; maxConcurrent/maxChildrenPerAgent/maxSpawnDepth left at defaults to avoid affecting other agents)

Enforced by OpenClaw tool policy (hard stop), not by prompt. Elevated does not override deny.

## 5. ingest_attachment tool

Zero-dependency Python stdlib MCP server (`scripts/mcp_ingest_attachment.ps1` wrapper + `scripts/mcp_ingest_attachment.py` + `scripts/run_ingest_safe.ps1` adapter + `scripts/07_ingest_inbound_media.ps1` single safety implementation). Registered as `mcp.servers.ingest`. Validates source_media_path inside the inbound root, chat_id/sender_id on the authorized allowlist (read from config), then invokes the PS safety core. Outputs `stored_path`/`receipt_path` (never the original MediaPath). `content_parsed=false`, `quarantined=true`. Multi-attachment: `input/feishu/<message-id>/attachment-NNN/receipt.json` + `message_manifest.json`. Not a generic exec wrapper. `openclaw mcp probe ingest`: 1 tool `ingest__ingest_attachment` live.

## 6. Multi-attachment

`07_ingest_inbound_media.ps1` extended with optional `AttachmentIndex`/`AttachmentCount`/`EventId` (backward compatible: legacy single-attachment layout unchanged, 32/32 still pass). MCP server writes `message_manifest.json`. Idempotency per `(message_id, attachment_index, hash)`. See `P0_MULTI_ATTACHMENT_CONTRACT.md`.

## 7. GPU lock

`scripts/gpu_media_lock.py` (zero-dependency stdlib; file mutex + PID + heartbeat + stale recovery via ctypes OpenProcess on Windows). Single concurrency for GPU-heavy work (faster-whisper CUDA, VLM, ComfyUI). ffprobe/CPU frame extraction do not take the lock. See `P0_GPU_MEDIA_LOCK_CONTRACT.md`.

## 8. Internal analyzers

3 binding-less agents added to `agents.list` (NOT to `bindings`): `video-factory-image-analyzer` (mimo-v2.5), `video-factory-audio-analyzer` (mimo-v2.5-pro + faster-whisper CUDA), `video-factory-video-analyzer` (mimo-v2.5 + ffprobe/CPU frames/VLM). Each: isolated workspace/agentDir, `subagents.allowAgents: []`, `tools.allow: [read, write]`, `tools.exec.mode: deny`, no identity, no heartbeat. Dispatched only by the router via `sessions_spawn` (whitelisted). See `P0_INTERNAL_MEDIA_AGENTS.md`.

## 9. Test results

- `Test-SingleGroupMediaRouter.ps1`: **45/45** (15 original + 5 scope + 10 router-policy + 11 internal-analyzer + 4 GPU-lock)
- `Test-IngestInboundMedia.ps1`: **32/32** (legacy, unchanged)
- `test_ingest_attachment_core.py`: **17/17** (ingest tool contract)
- Total: **94/94**

## 10. Config semantic diff

See `P0_SINGLE_GROUP_ROUTER_CONFIG_DIFF.json` / `.md`. Allowed changes only:
1. `tools.media.image/audio/video.scope` (deny target group)
2. `agents.list[video-factory].model` -> mimo-v2.5-pro
3. `agents.list[video-factory].tools` (allow/deny, exec removed)
4. `agents.list[video-factory].subagents` (whitelist)
5. 3 internal analyzer agents appended (no bindings)
6. `mcp.servers.ingest`
7. `meta.lastTouchedAt` (auto)

Unchanged: 14 bindings, zhongshu account/credentials, gateway port/auth, OAuth, other 13 agents, other plugins, 4 cron, P0 Gate, PROJECT_STATUS. SHA-256 baseline `c7098b22...5660d` -> new `3001ec3b...` (only the authorized fields changed semantically).

## 11. Gateway restarts

3 restarts total (the task's one-restart ideal was exceeded by two smoke-driven config fixes):
1. Initial config apply (group:plugins deny bug present)
2. Fix: removed `group:plugins` from deny (it overrode the allowlisted ingest tool)
3. Fix: added `bundle-mcp` to allow (explicit allow lists do not implicitly allow MCP tools; needed for the ingest tool to be visible to the agent)

Each fix was validated (`openclaw config validate` exit 0) before restart. All restarts via `openclaw gateway restart` (Scheduled Task). Gateway healthy after each.

## 12. Runtime smoke

- **Text**: `openclaw agent --agent video-factory -m "..." --json` -> status ok, reply "PONG", model `mimo-v2.5-pro`, model_call_count=1. PASS.
- **PNG attachment**: `openclaw agent` turn instructed to call `ingest_attachment` with a staged PNG in the real inbound root -> status ok, model `mimo-v2.5-pro` (did not read pixels), tool called, receipt written (`quarantined=true`, `content_parsed=false`, sha256 present, `analysis_allowed=true`). PASS.
- **MCP server**: `openclaw mcp probe ingest` -> 1 tool `ingest__ingest_attachment`. PASS.
- **Audio/MP4**: not individually event-smoked (ingest path identical to PNG and proven; analyzers offline-tested 11/11; audio uses verified faster-whisper CUDA; video uses ffprobe+CPU frames). Deferred: requires a real Feishu audio/MP4 event (user upload forbidden this round).
- **Failure cases**: covered by 17/17 ingest-tool failure tests (MIME/signature/path/oversize/unauthorized/unsafe-filename/missing-source/idempotency).
- **pre_ingest_media_understanding_count = 0**: config-verified (scope deny + text-only model + tool policy deny media) and behavior-consistent (router called ingest_attachment, not image understanding; model was text-only). Direct live count of `applyMediaUnderstandingIfNeeded` for a real Channel attachment event was not measured (no fake Channel event injector available without real user upload); the scope deny is evaluated inside `applyMediaUnderstandingIfNeeded` per core call-order evidence.

See `P0_SINGLE_GROUP_ROUTER_RUNTIME_SMOKE.md`.

## 13. Other agents / Binding / Cron

- Other 13 agents: config hash unchanged (only video-factory model changed; verified by `verify_007_invariants.py`).
- Bindings: 14 (unchanged).
- Cron: 4 (unchanged; next run ~22h away).
- Target group consumer: 1 (zhongshu -> video-factory route).
- 3 internal analyzers: no binding (verified `has_binding=False`).

## 14. Rollback

Prepared (backup `openclaw.json.bak-007-20260718-092424`, SHA `c7098b22...5660d`). Rollback not triggered (no anomaly). See `P0_SINGLE_GROUP_ROUTER_ROLLBACK.md`.

## 15. P0 status / next user action

P0 remains `conditional_not_passed` (the P0 Gate was NOT run and PROJECT_STATUS was NOT updated, per task prohibition). The 007 production implementation is complete and smoke-verified. The user's only next action: **re-upload `p0-file-test.txt`** to the VideoFactory Feishu group to validate the full live attachment path end-to-end.

## Secrets policy

All apiKeys, appSecrets, the gateway token, the real target-group id, and file_keys are masked (`<target-id>`) in every report. Real identifiers are used only inside the live config and the MCP server env (read from config at apply time, never printed).
