# P0 Media Ticket Adversarial Tests 051

Offline result: 29/30 requested attack categories have fail-closed fixture
coverage.  Category 11 (a Router-rewritten but syntactically valid command)
is intentionally **not qualified**: the current three-field MCP contract has
no immutable Channel-message provenance with which to distinguish it.

Covered fail-closed attacks include guessed/modified/expired/consumed tickets,
cross-user and cross-group attempts, cross-media actions, concurrent consume,
duplicate ingress, forged Router fields, partial state, interrupted consume,
receipt/stored/hash changes, path escape, Unicode/zero-width/full-width input,
multiple actions, media-content command text, copied bot tickets, duplicate
results, Analyzer timeout, GPU timeout, and restart recovery.

Evidence:

- `tests/test_media_action_ticket.py`: opaque ticket, strict command, context,
  artifact, concurrent, crash/restart, partial-store, expiry, public-response,
  and timeout fixtures.
- `tests/test_analyzer_mcp.py`: request provenance, hash/path, CUDA/local-only,
  GPU lease, and bounded video fixture checks.
- `tests/test_trusted_media_roots.py`: source/intermediate reparse rejection.

Every exercised failed gate asserted zero Analyzer dispatch.  These are
synthetic/offline tests; they do not execute R3-R5.
