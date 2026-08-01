# P0 One-Shot Analysis Intent Implementation Audit (014)

Status: NOT APPLIED; blocked before code authorization.

The repository currently contains the 013 Reply-based `analysis_request` contract. It has no `pending_intent` store, no `/analyze-next`, `/transcribe-next`, `/cancel-analysis-next`, or `/analysis-next-status` implementation, and no one-shot atomic consume path. The existing receipt and Analyzer gates remain unchanged and the old R3 failure remains preserved.

The parent audit found that OpenClaw can expose deterministic raw command text to a command/skill tool, but the supported context does not include the original Feishu `command_message_id`. The Feishu schema also does not expose native command registration. Implementing 014 without that field would permit model or message heuristics and would violate the contract, so no code or production registration was attempted.

Production invariants observed: config SHA `d6a97f1025698c08f086c1ee565e1aac1ad30116037e4f135688edbb1171be8c`, 17 Agents, 14 Bindings, 4 Cron, one target-group consumer, router model `xiaomimimo/mimo-v2.5-pro`; no Gateway restart this turn.
