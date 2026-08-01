# P0-013 Test Evidence

Offline results:

- Python discovery: 122/122 passed.
- New request contract: 8/8; fake two-message flow: 2/2; MCP public surface: 5/5; Analyzer MCP: 32/32.
- Pester two-message contract: 15/15; existing router: 46/46; inbound media: 36/36; V2.8 wrapper: 4/4.
- V2.8 schema suite: 88/88.
- `py_compile` for the three modified MCP/request modules: pass.
- `openclaw config validate`: pass.
- MCP probe: 2 ingest tools and 3 analyzer tools.

The tests cover ingress-only attachment handling, standalone text, Reply targeting, receipt/hash/type/identity/expiry gates, prompt-injection rejection, idempotency, concurrent-running rejection, immutable ingress fields, four-field Analyzer dispatch, raw-path exclusion, and topology invariants.

These are offline/fake-event tests. They do not prove a real Feishu event supplies `reply_to_message_id`, do not qualify R3, and do not justify a production restart or configuration change.
