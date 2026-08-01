# P0 One-Shot Analysis Intent Contract (014)

Status: BLOCKED_DETERMINISTIC_COMMAND_SOURCE_UNAVAILABLE

## Intended contract (design only; not applied)

The first message is a deterministic slash command and creates a separate pending intent. Supported commands are `/analyze-next image`, `/transcribe-next audio`, and `/analyze-next video`; optional aliases must be allowlisted and normalized without an LLM. The command must bind the original Channel event fields `command_message_id`, `chat_id`, and `sender_id`.

The next attachment is eligible only when the intent is pending, unexpired (120 seconds), same group, same sender, a different message id, and the detected media kind matches. Ingest must complete first and produce a quarantined receipt with matching source/stored SHA-256. A successful match creates one independent `analysis_request.json` outside the receipt with `action_source=one_shot_pre_authorization`; the receipt is byte immutable. A mismatch remains ingress-only and must not call an Analyzer.

The Analyzer accepts only `receipt_path`, `stored_path`, `job_id`, and `analysis_policy`. It requires a pending matching request, `analysis_allowed=true`, and a matching action. It reads only the isolated copy. Image analysis uses `xiaomimimo/mimo-v2.5`; a multimodal failure returns `multimodal_model_unavailable` and never falls back to `mimo-v2.5-pro`.

`/cancel-analysis-next` must atomically cancel a pending intent. `/analysis-next-status` may expose only redacted state. No new Feishu Binding, consumer, Cron, or channel route is part of this contract.

## Blocking finding

The installed OpenClaw command handler exposes raw command text and context fields such as sender and chat, but no real `command_message_id`. The installed command schema documents native registration for Discord, Slack, and Telegram; Feishu has no equivalent native command registration section. Workspace skill dispatch also passes only `command`, `commandName`, and `skillName` to the tool. Therefore the required binding cannot currently be proven without a deterministic adapter/source outside the supported surface.

Model-provided rewrites, filename matching, previous-message matching, timestamps, or a UI reply marker are not acceptable substitutes. No implementation was applied.
