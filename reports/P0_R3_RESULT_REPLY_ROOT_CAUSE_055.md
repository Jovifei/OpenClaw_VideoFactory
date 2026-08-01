# P0 R3 Result Reply Root Cause 055

Root-cause classification: `A+C+D`

## Confirmed chain

1. The latest real R3 result artifact contains a completed image-analysis payload. Its provider envelope has one output item with a text field; this report intentionally records only the schema shape, not analysis content or internal metadata.
2. `scripts/analyzer_mcp.py` persists that payload in `analysis.json`, but returns only technical completion metadata to its caller.
3. `scripts/media_action_ticket.py` records the successful Analyzer completion and returns only status, media kind, and action.
4. `scripts/mcp_ingest_attachment.py` then projects every successful consumption to the hard-coded Router reply template `媒体处理已完成。`.

## Root cause

The finished Analyzer result was neither absent nor too thin. It was dropped between the Analyzer result artifact and the public MCP result, then replaced by an unconditional generic completion string. The generic group reply observed in the real R3 run exactly matches that public projection.

This is a result-presentation defect, not a Ticket, receipt, SHA validation, model-routing, Analyzer-dispatch, or duplicate-execution defect.

## Repair boundary

The repair will build a server-owned, sanitized Chinese image-result presentation after the Analyzer succeeds. Only the presentation text may cross the public MCP boundary. Paths, receipts, hashes, job IDs, message IDs, chat IDs, sender IDs, raw JSON, and model-routing controls remain server-only.
