# P0 Card Action Baseline Before (015)

This is a read-only baseline. No production configuration, code, Gateway, Agent, Binding, Cron, model, or project status was changed.

## Current runtime

- `openclaw.json` SHA-256: `d6a97f1025698c08f086c1ee565e1aac1ad30116037e4f135688edbb1171be8c`.
- Topology: 17 Agents, 14 Bindings, 4 Cron, one target-group consumer.
- Router: `video-factory` with `xiaomimimo/mimo-v2.5-pro` primary and identical text fallback.
- Gateway: OpenClaw 2026.7.1, loopback `127.0.0.1:18789`, running; no restart this task.
- MCP probes: two ingest tools and three Analyzer tools, zero diagnostics.

## Feishu and lark-cli

The `zhongshu` account is configured and running. It has no account-level `connectionMode`, webhook path, Verification Token, or Encrypt Key, so the effective mode is the Feishu channel default WebSocket. The local config does not expose the Feishu developer-console subscription list or callback URL. Logs show message events but no card-action event.

The installed OpenClaw core advertises Feishu interactive-card sending and registers `card.action.trigger`. Its parser extracts token, operator identity, action value/tag, open message id, and chat context. Its built-in handler, however, handles only internal quick/approval envelopes and otherwise dispatches a synthetic command to the Router or rejects the action. That does not satisfy the required direct deterministic project handler.

`lark-cli` is 1.0.9. Its message sender accepts generic interactive content JSON, but it has no dedicated card builder or card callback command. Its only configured profile is `video-factory`, and `doctor` reports no user token; this profile is not evidence for the target `zhongshu` App.

## Prior live boundary

R0/R1/repaired R2 and bare-MP4 ingress passed. The real R3 failure remains immutable as `R3_FAILED:ANALYSIS_INTENT_GATE` in `reports/P0_R3_TWO_MESSAGE_EVENT_20260720.json`; R4/R5 remain not run.

## Evidence sources

- `C:/Users/Admin/AppData/Roaming/npm/node_modules/openclaw/dist/channel-YrfEVd9X.js` — Feishu capabilities and card sending.
- `C:/Users/Admin/AppData/Roaming/npm/node_modules/openclaw/dist/monitor.account-BE_Pfm_n.js` — card action registration, parsing, signature path, and synthetic-command dispatch.
- `C:/Users/Admin/AppData/Roaming/npm/node_modules/openclaw/dist/send-result-Brv9re91.js` — card interaction envelope decoder.
- `reports/P0_R3_TWO_MESSAGE_EVENT_20260720.json` — preserved live R3 failure.
