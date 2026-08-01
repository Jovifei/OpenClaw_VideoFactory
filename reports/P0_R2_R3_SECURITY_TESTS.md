# P0 R2/R3 Security Tests

All focused offline checks passed; these are not a replacement for a new real Feishu R2 event.

| Suite | Result |
| --- | --- |
| Python ingest core | 45/45 |
| Analyzer MCP | 31/31 |
| Trusted roots | 25/25 |
| Inbound Pester | 36/36 |
| Single-group Router Pester | 46/46 |
| V2.8 schema | 88/88 |
| GPU lock contract | 4/4 (included in Router Pester) |
| MCP probes | ingest 1 tool; analyzers 3 tools; diagnostics 0 |

Intent coverage includes bare/empty/unknown captions, explicit type-matching commands, type mismatch, prompt-injection rejection, multi-attachment defaults, same-message conflict, and `analysis_allowed` without request. Hash coverage includes uppercase normalization, strict full-length format, missing/invalid/truncated/prefixed values, source/stored mismatch, stored-copy/path/size binding, TOCTOU stability, and idempotent completion.

The old real R2 remains `FAIL`; R3–R5 remain `NOT_RUN`. No final P0 Gate or production configuration change was made.
