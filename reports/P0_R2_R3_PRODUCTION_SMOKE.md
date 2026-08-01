# P0 R2/R3 Production Smoke Boundary

No production smoke or live requalification was run in this task. The preserved real R2 remains `R2_FAILED:ANALYZER_CALLED_AFTER_INGEST`, and the old Analyzer `stored_hash_mismatch` response remains negative evidence.

Offline MCP probes succeeded:

- ingest server: one tool, zero diagnostics;
- analyzer server: three tools, zero diagnostics.

Fixture-only smoke also passed: bare PNG produced `attachment_action=ingress_only` and Analyzer `analysis_not_requested`; the controlled explicit image command produced `analyze_image` and completed against the quarantined copy with matching `receipt_expected_hash` and `analyzer_computed_hash`.

The local fixture contract proves that a bare PNG yields an ingress-only receipt and zero Analyzer dispatches, while an explicit matching action can pass the deterministic Analyzer gate. It does not qualify a real Feishu event. A new `p0-image-test.png` message with no caption is required before R2 can be requalified.

Production config SHA is unchanged; this task performed no Gateway restart, no Binding/Agent/Cron/model change, and no final P0 Gate.
