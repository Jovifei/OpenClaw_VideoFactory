# Candidate B — project-owned Feishu Gateway

Recommendation: one project-owned Feishu WebSocket connection receives raw `im.message.receive_v1` and `card.action.trigger`. It validates and persists raw metadata before any LLM. Text is sent through a local, authenticated OpenClaw Gateway bridge with a stable group session key. Attachments are downloaded to the managed inbound root and passed only to existing `ingest_attachment`; receipt success creates a server-side hashed, one-time ticket. Card callbacks validate event, operator, chat, ticket, SHA, kind, TTL, and idempotency, then create an analysis request and call only the matching Analyzer with `receipt_path`, `stored_path`, `job_id`, and `analysis_policy`.

The Feishu long connection is preferred: the official SDK supports separate message and card handlers, avoiding a public HTTPS callback surface. HTTPS is not required for the recommended design; if later required, it must add signature/token/encryption verification, replay protection, rate limiting, and a three-second acknowledgement.

Production persistence must be disk/SQLite-backed; the PoC snapshot/restore API demonstrates the required restart boundary but is not production storage.
