# P0 R3 Stored Hash Integrity Fix

The preserved Analyzer failure had two independent integrity defects. The old code compared the receipt's legacy `sha256` field rather than the stored-copy contract field `stored_sha256`, and it compared PowerShell's uppercase digest to Python's lowercase `hashlib.hexdigest()` case-sensitively.

The repaired Analyzer requires full 64-character hexadecimal hashes, canonicalizes them to lowercase, uses `stored_sha256` as the primary expected value, requires `source_sha256 == stored_sha256`, recomputes the hash from the receipt-bound quarantined `stored_path`, checks stat/hash/stat stability and stored size, then revalidates after the GPU lock. Manifests, UI prefixes, source-only values, URLs, base64, and raw inbound paths cannot satisfy the contract.

Offline Analyzer coverage is 31/31, including uppercase receipt acceptance, missing/invalid/prefixed/truncated hashes, source/stored mismatch, missing stored copy, changed-file and size checks, receipt/path binding, and completed-output idempotency. The real R3 remains NOT_RUN; the old R2 `stored_hash_mismatch` is preserved as negative evidence.
