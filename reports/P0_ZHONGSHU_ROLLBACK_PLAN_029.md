# P0 Zhongshu Rollback Plan 029

## Purpose

This is the only recovery sequence for a failed, separately authorized zhongshu maintenance-window cutover. It preserves a single consumer and restores the existing Core Feishu Binding from the T-30 backup. It is a plan, not an executable operation.

## Trigger

Start rollback immediately if Project Gateway startup/readiness fails, either consumer remains after T+1, consumers overlap at any point, a duplicate event/reply is observed, session continuity is unproven, or the text/attachment/card qualification fails.

## Sequence

| Relative time | Operator action | Required evidence |
| --- | --- | --- |
| R+0 | Stop further test events and stop the approved Project Gateway. | Project process and WebSocket are absent; no new Project event is accepted. |
| R+1 | Confirm all zhongshu consumers are zero. | Core=0, Project=0, combined=0. Do not restore while any consumer remains. |
| R+2 | Restore only the backed-up Core Binding. | Backup-manifest hash matches the T-30 record. |
| R+3 | Confirm the restored Core entrance is the exclusive owner. | Core=1, Project=0, combined=1, one Core WebSocket. |
| R+5 | Run one authorized text recovery test. | One reply and the preserved session lineage are recorded as hashes only. |
| R+8 | Run one authorized attachment recovery test. | One ingress/receipt path with no duplicate delivery or unintended analysis. |
| R+12 | Reconcile event, reply, and session hashes. | Any loss, duplicate, or uncertainty is explicitly recorded; do not claim success by inference. |

## Boundaries

- Never start Project Gateway until the Core consumer count is zero.
- Never restore Core Binding until the Project consumer count is zero.
- Do not introduce another Bot, connection, Binding, or consumer as a rollback shortcut.
- The configuration backup is restored only by the separately approved operator command; no script in 029 edits configuration.
- `zhongshu_preflight.py` and `zhongshu_postcheck.py` may validate sanitized local snapshots but cannot perform this sequence.
