# P0-MEDIA-ANALYSIS-065 — TXT Receipt MIME Compatibility

**Status:** `PASS_OFFLINE_REPAIR`  
**Change request:** `P0-MEDIA-ANALYSIS-065`

## Root cause

The live TXT Ticket passed server-side validation and was dispatched to
`analyze_text`. Its quarantined receipt persisted `content_type=text/plain`,
but did not persist `normalized_content_type`. P0-064 checked only the latter,
so it rejected the file before UTF-8 parsing.

## Repair

The Analyzer now prefers a present `normalized_content_type`. Only when that
field is absent does it normalize the established receipt `content_type`; the
result must still equal exactly `text/plain`. No other MIME is admitted.

## Evidence

- Focused Analyzer suite: 39 passed.
- Target suite: 167 passed.
- `analyzer_mcp.py` compiled successfully.
- Tests cover persisted `content_type=text/plain; charset=utf-8`, present-field
  precedence, `application/octet-stream`, `application/pdf`, and invalid UTF-8.

## Boundaries

The consumed live Ticket was not retried. No new Feishu message, service
lifecycle action, configuration change, model download, DOCX/PDF parse, P0
Gate, phase promotion, or Git action occurred. P0 remains `not_started`.
