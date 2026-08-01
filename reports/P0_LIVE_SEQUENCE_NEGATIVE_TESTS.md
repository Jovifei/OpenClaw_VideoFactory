# P0 Live Sequence Negative Tests

Current negative coverage is passing:

- trusted-root matrix: 25/25;
- inbound PowerShell and router Pester suite: 77/77;
- Analyzer MCP contract: 23/23;
- V2.8 wrapper: 4/4.

Covered rejection classes include traversal, similar-prefix roots, project/workspace non-inbound directories, drive mismatch, UNC/device paths, ADS, source and ancestor reparse points, source size/stat changes, receipt mismatch, hash mismatch, parsed/unquarantined receipts, wrong analyzer kind, raw inbound path, extra free-form fields, arbitrary policy, job traversal, and multimodal-to-text fallback.

No fake Feishu event or outbound message was used. Real Channel R0-R5 is pending.
