# P0 Media Action Ticket Implementation 050

## Changed offline components

- `scripts/media_action_ticket.py` implements hash-only ticket state,
  10-minute TTL, strict parsing, integrity validation, exclusive consumption,
  and server-side Analyzer selection.
- `scripts/mcp_ingest_attachment.py` issues tickets only after safe quarantine,
  stops the active receipt-intent mutation path, projects a path/hash-free MCP
  response, exposes `consume_media_action_ticket`, and removes the Reply
  constructor from `tools/list`.
- `scripts/analysis_request.py` adds a ticket-only request constructor outside
  the receipt.  The historical Reply constructor remains code evidence but is
  not exposed by the active MCP surface.
- `scripts/analyzer_mcp.py` accepts only `action_source=media_action_ticket`
  with ticket expiry; it retains the four fixed Analyzer inputs, integrity
  checks, local CUDA contract, bounded video path, GPU lock, and no cloud
  fallback.  Older `faster-whisper` APIs that cannot prove `local_files_only`
  now fail closed as `audio_model_unavailable` instead of retrying without the
  local-only guard.

## Core Binding constraint

Existing static configuration evidence records `bundle-mcp` for the existing
`ingest` MCP server.  The updated server's local `tools/list` now exposes
`ingest_attachment` and `consume_media_action_ticket`; no new server, Binding,
Agent, or Gateway change is needed in the code design.

This is not proof that the running Core session has rediscovered the new tool.
The first authorized real R3 event is the runtime qualification of that
existing route.  No Gateway restart was performed to force discovery.

