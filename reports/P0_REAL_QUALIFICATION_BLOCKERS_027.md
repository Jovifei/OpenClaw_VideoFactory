# P0 Real Qualification Blockers 027

## Classification

This document reclassifies the 026 findings for the real-environment qualification plan. The 026 mock reports remain historical evidence and are not reused as real-runtime proof.

### A. Must be verified in a real, isolated environment

| Control | Why mock evidence is insufficient | Required real evidence |
| --- | --- | --- |
| Single-consumer fence | A local snapshot cannot prove old-Binding shutdown or prevent a stale consumer from resuming | Authenticated owner identity, one WebSocket, old consumer=0, new consumer=1, fence heartbeat/generation, and duplicate-free events/replies |
| RPC end-to-end | A fake transport cannot prove authentication, protocol compatibility, Router delivery, response correlation, or retry behavior against OpenClaw | Test Gateway -> OpenClaw RPC -> `video-factory` Router trace with redacted request id, stable session, response, retry, and timeout recovery |
| Rollback | A model cannot establish the real loss boundary, state restore, or recovery time | Failed-start or failed-health rehearsal with measured stop, old-entry restore, text/attachment verification, reconciliation, and RTO/RPO evidence |

### B. Not a blocker for this 027 qualification gate

| Item | Treatment |
| --- | --- |
| `reply_to_message_id` | Treated as an existing OpenClaw durable two-message contract and retained outside the Gateway ownership qualification. 027 does not change or waive that contract. |
| Text intent parsing | Treated as existing Router/OpenClaw behavior. 027 validates transport and ownership only; it does not reimplement or retest Router intent semantics as a Gateway feature. |

The 027 plan does not convert the card shortcut into a second intent protocol. Any future real card test must still produce evidence compatible with the retained OpenClaw analysis contract.

### C. Complete before 027 real execution

| Area | Evidence |
| --- | --- |
| Gateway architecture | 024 boundary remediation and 026 qualification reports; Gateway remains a Channel Layer with no Analyzer/model/GPU implementation |
| Analyzer isolation | Existing capability matrix and static compute-boundary tests |
| Security model | Fail-closed signature policy, hashed event identities, least-privilege RPC policy, trusted-root ingress controls |
| Offline testing | 026 recorded Python 175/175 and Pester 101/101 |

## Current decision

The remaining decision is `FEISHU_REAL_ENV_REQUIRED`: A-category controls require a non-production real environment, but this task intentionally does not create or connect one.
