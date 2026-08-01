# zhongshu Feishu Gateway Maintenance Runbook V3

Status: `RUNBOOK_BLOCKED_BY_CONTROL_CONTRACT`

This is a future maintenance-window sequence, not execution authority. Every lifecycle, message, attachment, card, and rollback line below remains prohibited until the exact maintenance authorization phrase and all contract blockers are cleared.

| Time | Required action | Current 031 result |
| --- | --- | --- |
| T-30 | Capture sanitized configuration hash, inventory, task audit, Gateway status, Git state, and secret scan. Preserve an operator-controlled backup manifest. | Baseline captured; no new backup manifest was created. |
| T-10 | Run `zhongshu_preflight.py` against an operator snapshot; prove no active task; run the three-sample zero-consumer evaluator only after a future Core-stop action. | Active task gate passes; Core-stop and zero-consumer proof are blocked. |
| T0 | Execute the approved target-specific Core zhongshu stop method and record its timestamp. | `BLOCKED`: no qualified stop method. Do not substitute an entire Gateway stop. |
| T+1 | Supply three explicit, sanitized consumer observations at least five seconds apart and spanning at least ten seconds to `verify_zhongshu_zero_consumer.py`. | `ZERO_CONSUMER_NOT_PROVEN` without a collector. |
| T+2 | Execute an approved Project production Gateway start method. | `BLOCKED`: only an offline test runtime exists. |
| T+3 | Capture Project PID, lease, fresh heartbeat, one Feishu connection, Core stopped state, and no duplicate owner; evaluate with `verify_zhongshu_single_consumer.py`. | `SINGLE_CONSUMER_NOT_PROVEN`. |
| T+5 | Send the separately authorized `P0_TEXT_ROUTER_TEST` and verify exactly one response across Feishu → Project Gateway → OpenClaw RPC → video-factory. | Not authorized or executed. |
| T+10 | Send the separately authorized TXT attachment and verify ingress receipt, SHA, quarantine, and no automatic analysis. | Not authorized or executed. |
| T+15 | Send the separately authorized PNG attachment and verify ingress-only storage, then use valid reply metadata/card flow only. | Not authorized or executed. |
| T+20 | Send the separately authorized card action and verify one ticket-bound `analysis_request` with no direct Gateway Analyzer call. | Not authorized or executed. |

## Immediate rollback conditions

Rollback is mandatory for a non-ready Gateway, RPC failure, missing/duplicate text reply, consumer count above one, attachment failure, invalid card event, or session continuity failure.

## Current rollback boundary

`rollback_gateway.ps1` is simulation-only. Because Core stop/restore and Project production start/stop are not qualified, an executable rollback cannot be written without inventing control commands. On any future deviation, stop at the observed state, preserve the sanitized evidence, and invoke only a separately approved and tested restore method.

No command in this document was executed in 031.
