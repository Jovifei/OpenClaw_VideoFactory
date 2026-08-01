# P0 Current Status V10 — Feishu Card Analysis Action 015

Status: `P0_FEISHU_CARD_ANALYSIS_BLOCKED`.

The current OpenClaw/Feishu runtime can send interactive cards and registers `card.action.trigger`, but the installed handler does not expose a direct deterministic project callback. It routes recognized internal envelopes to synthetic commands and rejects unknown structured actions. The generic plugin interactive handler surface is not wired into the Feishu monitor.

The `zhongshu` account is running in the default WebSocket mode. No local callback URL, Verification Token, or Encrypt Key is configured, and the Feishu developer-console subscription list cannot be read from the repository or local OpenClaw config. `card.action.trigger` subscription therefore requires backend verification before any live smoke; if absent, add it to the existing App's WebSocket callback subscriptions without adding a second `im.message.receive_v1` subscription.

No code/config/Gateway/Agent/Binding/Cron/model/consumer/PROJECT_STATUS change occurred. Config SHA remains `d6a97f1025698c08f086c1ee565e1aac1ad30116037e4f135688edbb1171be8c`; topology remains 17/14/4/1. R0/R1/repaired R2 and bare MP4 ingress remain valid; old R3 `R3_FAILED:ANALYSIS_INTENT_GATE` remains immutable; R4/R5 are not run.

Prerequisite token: `FEISHU_CARD_CALLBACK_ADMIN_ACTION_REQUIRED`.
