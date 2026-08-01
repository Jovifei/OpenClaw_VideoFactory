# Candidate A — official Lark plugin audit

Result: `OFFICIAL_PLUGIN_CANNOT_REPLACE_CORE_CHANNEL`.

The candidate is a complete Channel and directly registers `im.message.receive_v1` and `card.action.trigger` (`vendor_research/openclaw-lark/src/channel/monitor.ts:97-116`). It retains operator, chat, action, and raw event for a registered interactive handler (`src/channel/interactive-dispatch.ts:24-72, 194-226`). Its declared OpenClaw peer range (`>=2026.5.4`) includes installed 2026.7.1.

It cannot be an in-place replacement: its Channel is also `feishu`, its manifest/package metadata declares no `preferOver`, and the installed runtime rejects duplicate channel registration. More importantly, its `inject_prompt` path synthesizes a user text event (`event-handlers.ts:461-524`) and its media resolver downloads media before the project receipt contract; both violate this project’s hard boundary. Solving those defects requires a fork/new replacement contract and is not an approved temporary patch.
