# P0 One-Shot Analysis Intent Test Audit (014)

The existing repository regressions pass, but they validate 013 Reply intent and the established ingress/analyzer contracts, not 014. No new tests were added because the deterministic command source is not yet available and code changes require Jovi's authorization.

Observed baseline: Python 122/122; two-message Pester 15/15; router 46/46; inbound 36/36; V2.8 wrapper 4/4; V2.8 schema 88/88; `py_compile` pass; MCP probe exposes two ingest and three Analyzer tools with zero diagnostics.

The mandatory 014 cases remain unproven: exact command event binding, same-chat/same-sender/120-second checks, persistence across restart, cancel/status, atomic single consume, kind mismatch, ingest failure fail-closed, one independent analysis request, Analyzer stored-path-only access, replay idempotency, and no text-model fallback.
