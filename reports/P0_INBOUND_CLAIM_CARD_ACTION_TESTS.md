# 016 test plan and gate

The requested card-action tests remain blocked because the installed runtime fails the precondition: the current core route never calls generic `inbound_claim`, and the synthetic event does not carry the trusted card callback fields. The existing offline regressions were rerun and passed: Python 122/122; Pester 15/15, 46/46, and 36/36; V2.8 wrapper 4/4; V2.8 schema 88/88; `py_compile` pass; MCP ingest 2 tools and Analyzer 3 tools with zero diagnostics; GPU lock coverage included in Router 46/46. No fake card was sent, no Analyzer was called, and no Router/LLM counter was altered by this task.

The existing 015 regression evidence remains the applicable offline baseline; it is not promoted to card-action proof. A future test may proceed only after an independently supported pre-Router seam is available and explicitly authorized.
