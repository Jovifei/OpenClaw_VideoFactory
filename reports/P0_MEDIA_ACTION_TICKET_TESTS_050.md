# P0 Media Action Ticket Tests 050

`tests/test_media_action_ticket.py` provides offline coverage for:

- image/audio/video ticket issuance, random-token uniqueness, and hash-only
  server storage;
- TXT no-ticket behavior and duplicate-event no-resign behavior;
- the three strict commands and server-side image/audio/video Analyzer choice;
- natural language, prompt injection, OCR, and media-contained command text;
- bad ticket, expiry, consumed ticket, chat/sender/action/type mismatch,
  receipt change, stored-hash change, extra Router fields, and concurrency;
- ticket-bound request creation, receipt-ingress preservation, Analyzer result
  idempotency, and a real offline Analyzer invocation.

The existing ingress, Analyzer, trusted-root, schema, GPU-lock, and historical
Pester suites remain part of the full offline regression.  Historical 013
Reply tests are preserved as deferred evidence and are not accepted as the
050 authorization route.

Recorded final offline run:

- Python unittest discovery: 298/298 passed.
- PowerShell Pester discovery: 123/123 passed.
- `scripts/v28_schema_tests.py`: 88/88 passed.
- `.venv` `pip check`, `git diff --check`, and the scoped secret-pattern scan
  passed.

These are offline/synthetic proof only and do not establish R3-R5.
