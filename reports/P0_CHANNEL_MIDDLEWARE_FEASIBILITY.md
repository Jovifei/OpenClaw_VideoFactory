# P0 Channel Pre-agent Middleware Feasibility

Status: `not_feasible_via_supported_extension_surface`.

## Scope and invariants

This was a read-only review of the installed OpenClaw `2026.7.1 (2d2ddc4)` SDK and runtime. No project code, OpenClaw configuration, Gateway, Binding, agent, plugin, model, Feishu message, or Cron was changed.

The existing core Feishu Binding remains the single consumer for the dedicated `video-factory` group.

## Evidence

1. The installed plugin Hook catalog exposes `inbound_claim` as the sole pre-routing decision hook. `message_received` is observation-only. There is no Hook named or typed as Channel middleware for an existing Channel.
2. The installed SDK declaration types `message_received` as a handler returning `void`; it cannot block or replace dispatch. `inbound_claim` can decide, but it remains the plugin-owned conversation-Binding path already rejected by `P0_PLUGIN_OWNED_BINDING_MIGRATION.md`.
3. The installed core's `get-reply-CknL88Yv.js` calls `applyMediaUnderstandingIfNeeded(...)` before `emitPreAgentMessageHooks(...)`. A normal plugin Hook therefore cannot establish the required barrier before automatic media understanding.
4. The Channel inbound SDK is documented for a Channel plugin's own receive path (`platform event -> inbound facts/context -> agent reply -> message delivery`). It offers helpers to build or run a Channel's inbound pipeline; it does not register a middleware around the existing Feishu Channel.
5. The existing deterministic local regression remains fresh: `tests/Test-IngestInboundMedia.ps1` passed `32/32` under installed Pester `3.4.0`.

## Decision

The proposed Channel pre-agent middleware is not a supported extension surface for the current Feishu Channel. Implementing it would require replacing or modifying the Channel receive path, which is a different, high-risk channel implementation project and is outside P0 and the present authorization.

`before_agent_run` is not an alternative: it can block model submission, but it runs after the core media-understanding call observed above and therefore cannot prove the required pre-ingest safety boundary.

## Next decision required

Do not retry the unchanged plugin-owned Binding migration or create a pseudo-middleware plugin. If the attachment barrier remains mandatory, choose and separately authorize one architecture:

1. a distinct attachment-only bot or Feishu group, with an isolated intake route; or
2. a separately scoped replacement/extension of the Feishu Channel receive path, including a full compatibility, rollback, and credential-boundary plan.

Until that decision, P0 remains `conditional_not_passed`; no code change is proposed in this report.
