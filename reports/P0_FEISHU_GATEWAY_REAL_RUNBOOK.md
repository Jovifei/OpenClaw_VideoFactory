# P0 Feishu Gateway Real Qualification Runbook

## Scope

This is a future, operator-controlled non-production qualification runbook. It is not an instruction to run now. All commands that would stop an existing entry, start a Gateway, or send a Feishu message require explicit window authorization and an operator confirmation.

## Preconditions

- Dedicated Feishu test App, Bot and group are ready.
- Isolated OpenClaw instance/profile, RPC endpoint and non-production token provider are ready.
- Project Gateway configuration, PID, lease and log directories are isolated.
- The old-entry stop and restore commands have been reviewed and written into the window record.
- Backup hashes, rollback owner, observer and stop criteria are recorded.
- No production task, Cron, Binding, Agent, OAuth, or media operation is active.

## Minute-level sequence

| Time | Action | Required evidence / stop condition |
| --- | --- | --- |
| T-60 | Back up the isolated qualification config, lease/state manifests and Runbook record | Hashes only; missing backup stops the window |
| T-45 | Verify test App/Bot/group, RPC token-provider readiness and isolated paths | Any production identifier or shared path stops the window |
| T-30 | Run pre-cutover checks and record old/new consumer counts | Expected old=1, new=0; active work=0; no duplicate evidence |
| T-20 | Verify old-entry stop/restore commands and rollback owner | Unreviewed command stops the window |
| T-10 | Confirm stop conditions, observer, test data, recovery objective and explicit short-window approval | Any missing approval stops the window |
| T0 | Stop the approved old test entry, then start the isolated Project Gateway | Do not run against production; if start fails, begin rollback immediately |
| T+1 | Check health, readiness, PID, lease owner and WebSocket count | New=1, old=0, one owner; otherwise rollback |
| T+2 | Run post-cutover consumer check | Any overlap or stale owner triggers rollback |
| T+5 | Send one harmless text test | Verify session, request id, response and no duplicate |
| T+10 | Send TXT and PNG test fixtures | Verify quarantine, SHA, receipt and no unintended analysis |
| T+15 | Upload one test attachment and perform one approved card click | Verify ticket, action/operator/chat, durable OpenClaw request and one consumption |
| T+20 | Recheck consumer/event/reply hashes and logs | Any duplicate, raw secret, raw identifier or ambiguous response triggers rollback |
| T+30 | Record result and prepare restoration | No production status promotion is allowed |

## Rollback sequence

| Relative time | Action | Recovery evidence |
| --- | --- | --- |
| R+0 | Stop sending test events and stop the qualification Gateway using the reviewed operator command | New process and WebSocket exit confirmed |
| R+1 | Verify Project owner, lease and heartbeat are gone or fenced | No stale Project owner |
| R+2 | Restore the previously backed-up old test entry using the reviewed operator command | Configuration hash matches the backup |
| R+3 | Verify the old entry has one owner and one WebSocket | old=1, new=0 |
| R+5 | Send one text recovery test | Reply path and session continuity recorded |
| R+8 | Send one attachment recovery test | Receipt/SHA/quarantine path recorded |
| R+12 | Reconcile event/reply/request hashes and record loss/duplicate boundary | RTO/RPO and unresolved ambiguity explicitly recorded |

## Not-executed command placeholders

The exact old-entry stop/restore and isolated-start commands are intentionally operator-supplied placeholders until the environment design is approved. This report does not invent or execute commands that could affect the current Binding.
