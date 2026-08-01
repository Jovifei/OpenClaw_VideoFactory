# P0-009 Recovery Baseline Before

Captured for `P0-LIVE-SEQUENCE-009-RECOVERY-AND-CLOSURE` before Analyzer MCP implementation.

## Confirmed live state

- OpenClaw config validates; current SHA-256 is `3001ec3b...`.
- Gateway probe is reachable on loopback port 18789. The service-version warning is retained as an observation; no repair was attempted.
- Topology is 17 Agents, 14 Bindings, 4 Cron, and one target-group consumer.
- Router is durable `xiaomimimo/mimo-v2.5-pro`; target-group media scope deny and router tool policy remain in place.
- Only the `ingest` MCP server is registered and it exposes `ingest__ingest_attachment`; no Analyzer MCP tools are registered.

## R1 recovery boundary

The previous real TXT upload failed with `path_traversal` because Feishu staged the file under the VideoFactory workspace `media/inbound`, while the original MCP check trusted only the global OpenClaw inbound root. The current code accepts the workspace root, but the new multi-root behavior has not yet passed the full trusted-root security matrix or a fresh real Feishu event.

## Evidence counts

- Existing P0 router/inbound/MCP tests: 45/45, 32/32, 17/17.
- V2.8 wrapper: 4/4; current generated schema report: 88/88.
- The P0 total remains 94/94 and excludes V2.8 schema checks.
- Current reports: 257 files; filename manifest SHA-256 is recorded in the JSON baseline.
- `PROJECT_STATUS.yaml` remains unchanged at P0 `not_started`; final P0 Gate and `P0_READY` are not run/created.

## Review boundary

This is a recovery baseline, not a pass claim. The 009 Change Request remains `in_progress`. No Feishu message, upload, outbound send, final P0 Gate, Binding change, Cron change, OAuth change, model download, or P1 action is authorized in this round.
