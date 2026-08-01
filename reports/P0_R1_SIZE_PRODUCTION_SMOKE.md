# P0 R1 Trusted-Size Production Smoke

This was a local deterministic MCP smoke after the one planned Gateway restart. It did not send a Feishu message or invoke an Analyzer.

| Trusted root | Router size input | Result | Actual / stored | SHA | Idempotent retry |
| --- | --- | --- | --- | --- | --- |
| `openclaw_global` | omitted | quarantined | 55 / 55 bytes | equal | true |
| `video_factory_workspace` | legacy `67` | quarantined | 55 / 55 bytes | equal | true |

The current MCP `tools/list` schema has no `size_bytes` or `max_bytes` property or requirement. The workspace-root legacy value is recorded as `untrusted_size_claim_bytes=67`; `declared_size_bytes=null` and `declared_size_trusted=false`. Both receipts contain the required declared/actual/stored/SHA/stability/root fields.

The smoke process exposed only `ingest_attachment`; no Analyzer MCP or Gateway agent session was invoked, so Analyzer call count is zero by construction. The staged fixture files remain as deterministic smoke artifacts in the two explicitly trusted roots; they were not associated with a Channel event and no automatic cleanup command was run after the host execution policy rejected a deletion attempt.

Post-restart: loopback Gateway port 18789 listening, status command exit 0, and OpenClaw config SHA-256 unchanged. No R2–R5 action was performed.
