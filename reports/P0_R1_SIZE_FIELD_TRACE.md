# P0 R1 Size Field Trace

The original R1 failure is permanent negative evidence: `R1_FAILED:ingest.size_mismatch`, no receipt, and no Analyzer call.

| Field | Proven source | Value |
| --- | --- | --- |
| `declared_size_source` | Router MCP tool-call JSON in the retained R1 session | model-supplied `size_bytes` |
| `declared_size_value` | Router tool-call JSON | 67 bytes |
| `actual_size_source` | trusted downloaded `MediaPath` filesystem `stat` | 55 bytes |
| `router_supplied_value` | Router tool-call JSON | 67 bytes |

The normalized attachment carried `MediaPath` and `MediaType`, not a size field. The old Python tool required and compared `size_bytes`, so the model-provided 67 became a security-critical rejection basis. This is confirmed as `MODEL_SUPPLIED_SECURITY_FIELD_CONFIRMED`.

The original PowerShell quarantine script and copy path were correctly not reached: Python rejected before spawning them. Post-fix production smoke exercised both trusted roots and verified source size, stored size, SHA-256, receipt fields, and idempotency.

Evidence: `reports/P0_R1_EVENT_TRACE_20260718.json`, `reports/P0_R1_SIZE_CONTRACT_FIX.json`, `reports/P0_R1_SIZE_PRODUCTION_SMOKE.md`.
