# P0 Feishu Card Callback Security Review (015)

## Required gates

1. Verify transport authentication: WebSocket SDK authentication for the current mode, or HTTP signature, Verification Token, Encrypt Key, timestamp, nonce, and replay window if HTTP mode is deliberately selected.
2. Require a unique event id and an opaque, at least 128-bit ticket. Store only a hash of the ticket for lookup; never put paths or identifiers in the button value.
3. Bind ticket to the original attachment message, receipt, stored SHA-256, attachment index, media kind, uploader, and chat. Require the callback operator and chat to match exactly.
4. Enforce pending and unexpired state, atomically transition to accepted, and make event id plus ticket consumption idempotent.
5. Verify receipt existence, immutable ingress fields, quarantine, `analysis_allowed`, stored/source hash equality, and stored-path binding before creating `analysis_request`.
6. Return an acknowledgement within three seconds. Queue all Analyzer work; never synchronously wait for a model, ffmpeg, Whisper, or GPU lock.
7. Redact paths, full IDs, file keys, secrets, and complete hashes from cards, toasts, logs, and error messages.

## Current security boundary

The core parser can extract operator and chat fields and its webhook mode contains signature verification code, but the target account is currently WebSocket mode and has no local callback credentials. The built-in Feishu card handler does not expose a project callback verifier or ticket store, and unknown actions do not reach a deterministic project handler. No security claim beyond the existing 013 receipt/Analyzer checks is accepted.
