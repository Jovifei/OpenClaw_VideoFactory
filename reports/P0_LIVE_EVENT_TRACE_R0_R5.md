# P0 Live Event Trace R0–R5

| Step | Status | Evidence / boundary |
| --- | --- | --- |
| R0 `P0_TEXT_ROUTER_TEST` | PASS | `reports/P0_R0_EVENT_TRACE_20260718.json`: one text-only Router call, no tool/media/analyzer, same session and same group reply. |
| R1 original TXT | FAIL (preserved) | `reports/P0_R1_EVENT_TRACE_20260718.json`: Channel downloaded, Router called ingest with model-supplied 67 while trusted stat was 55; `size_mismatch`; no receipt/analyzer. |
| R1 trusted-size repair | COMPLETE OFFLINE/LOCAL | `reports/P0_R1_SIZE_CONTRACT_FIX.json`: new schema and two-root smoke pass. This does not change the old R1 result. |
| R1 replacement TXT | PASS | `reports/P0_R1_EVENT_TRACE_20260719.json`: new message hash `20fdee581d994e8c` differs from the preserved old failure; MCP-owned size/hash, receipt, no Analyzer, no pre-ingest media understanding, and same-group reply verified. |
| R2 PNG old event | FAIL (preserved) | `reports/P0_R2_EVENT_TRACE_20260720.json`: safe ingest completed, then Router called `analyzers__analyze_image`; this negative evidence is immutable. |
| R2 PNG replacement | PASS | `reports/P0_LIVE_MEDIA_R2_QUALIFICATION_012.json`: new message `om_***9de9`; text-only Router, no pre-ingest media understanding, one ingest, `ingress_only`, 17,247-byte full SHA match, receipt/quarantine, zero Analyzer calls, same-group reply. |
| Current MP4 ingress-only | PASS (not R5) | `reports/P0_LIVE_MEDIA_R2_QUALIFICATION_012.json`: new message `om_***27b7`; one ingest, `ingress_only`, 52,037-byte full SHA match, receipt/quarantine, zero video Analyzer calls, same-group reply. |
| R3 PNG with old same-message analysis request | NOT_RUN_INVALID_MESSAGE_SHAPE (preserved) | Feishu did not provide a reliable attachment+caption event; no PASS is inferred. |
| R3 PNG with two-message Reply protocol | FAIL | `reports/P0_R3_TWO_MESSAGE_EVENT_20260720.json`: the exact Chinese request was rejected twice as `analysis_intent_not_recognized`; Router then substituted `analyze image` and analysis completed. The raw Channel event had only a Reply display marker, not an explicit `reply_to_message_id` field. |
| R4 audio | NOT_RUN | Prohibited until R3 passes. |
| R5 video | NOT_RUN | Prohibited until R4 passes. |

The old R1 and R2 failures and the invalid same-message R3 shape remain immutable negative evidence. The R3 live attempt is also negative evidence: post-rejection command substitution is not an accepted intent path. Although the Analyzer later completed with `xiaomimimo/mimo-v2.5` and matching hashes, this cannot qualify R3. No R4/R5, production config, Gateway, Binding, Agent, Cron, final P0 Gate, P0_READY, PROJECT_STATUS update, egress qualification, Git publication, or P1 work is allowed after this failure.
