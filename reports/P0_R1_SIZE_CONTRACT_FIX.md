# P0 R1 Trusted-Size Contract Fix

`P0_R1_SIZE_CONTRACT_FIXED`

The old R1 event stays failed: Router supplied 67 bytes while trusted filesystem `stat` found 55; the old tool returned `size_mismatch`, created no receipt, and invoked no Analyzer. The session proves that 67 came from the text-only Router tool call, not retained Channel size metadata: `MODEL_SUPPLIED_SECURITY_FIELD_CONFIRMED`.

The public `ingest_attachment` MCP schema no longer exposes or requires `size_bytes` or `max_bytes`. The server-owned `OPENCLAW_MAX_BYTES` policy and trusted source `Path.stat` now determine the limit. A cached legacy `size_bytes` remains accepted only as receipt audit data with `declared_size_bytes=null` and `declared_size_trusted=false`.

The isolation script independently verifies source size/mtime around hashing, stored size after copy, source/stored SHA-256 equality, and source stability through the copy. It deletes a partial stored copy on stored-size or stored-hash failure. Trusted Channel/Gateway declared size is a non-public keyword-only adapter API with allowlisted provenance; a mismatch returns `trusted_declared_size_mismatch`.

One planned Gateway restart loaded the new schema. Config SHA, 17 Agents, 14 Bindings, 4 Cron jobs, router model, and one target consumer are unchanged. Final regressions and two-root production smoke pass. R0 remains PASS; R2–R5 remain NOT_RUN.

The only next action is a fresh R1 upload with a new message id. Do not reuse the failed event.
