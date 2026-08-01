# P0 Feishu Card Analysis Contract (015)

Status: DESIGN ONLY; blocked before implementation.

## Required flow

`ingest_attachment` succeeds with a quarantined receipt, then a deterministic service creates a card with safe metadata and one fixed action for the detected media kind. The button value contains only an opaque ticket, a fixed protocol version, and a fixed button type. It never contains a path, URL, file key, model, command, or user-controlled media option.

The card action handler must receive the original Feishu callback event, verify the callback transport, event id, operator, chat, ticket, receipt, stored hash, media kind, `quarantined=true`, and `analysis_allowed=true`, then atomically consume the ticket and create one independent `analysis_request.json`. The receipt remains byte immutable. The callback returns within three seconds and queues the Analyzer; it never waits for model, ffmpeg, Whisper, or GPU work.

The worker accepts only `receipt_path`, `stored_path`, `job_id`, and `analysis_policy`. It calls exactly one matching Analyzer, updates the ticket/card state idempotently, and sends the result to the original group. Duplicate event or ticket delivery must not call a model twice.

## Runtime finding

The installed Feishu monitor registers `card.action.trigger` and parses the needed identity and chat fields. In the current WebSocket mode, SDK transport handles authentication; the local account has no HTTP callback URL, Verification Token, or Encrypt Key. The built-in handler then routes known quick/approval envelopes to synthetic commands and rejects unknown structured actions. No project-level Feishu card action handler or Feishu dispatch to `registerPluginInteractiveHandler` is wired; that generic plugin surface is used by Discord/Telegram paths, not this Feishu monitor.

Therefore the contract is technically well-defined but cannot be safely applied in the current supported extension surface without either modifying OpenClaw core, competing for the App's event stream, or replacing the current message transport. All three are outside this task's rules.

Official Feishu references used for the audit: [WebSocket event/callback subscription](https://open.feishu.cn/document/server-docs/event-subscription-guide/event-subscription-configure-/request-url-configuration-case) and [callback overview](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/event-subscription-guide/callback-subscription/callback-overview).
