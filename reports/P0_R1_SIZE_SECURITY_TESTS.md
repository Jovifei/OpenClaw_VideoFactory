# P0 R1 Trusted-Size Security Tests

All required final regressions were rerun in this task. The updated counts are Analyzer MCP 23/23, trusted roots 25/25, ingest core 39/39, combined inbound/router Pester 81/81, V2.8 Pester 4/4, and V2.8 schema report 88/88.

The historical inbound/router Pester count was 77. It is now 81 because this task added four PowerShell receipt/copy-size/hash cases; this is not a substituted historical result.

The 25 new contract cases cover omitted and wrong Router sizes, the R1 67-vs-55 condition, trusted/untrusted declarations, invalid declarations, zero/oversize files, source and stored mutations, idempotency, byte semantics, schema hiding, and receipt compatibility. `scripts/mcp_ingest_attachment.py` compiled successfully before execution.

No real Feishu R2–R5 event, final P0 Gate, P0_READY, or P1 step was run.
