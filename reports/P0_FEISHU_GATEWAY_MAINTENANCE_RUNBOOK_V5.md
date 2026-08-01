# Feishu Gateway Maintenance Runbook V5 — zhongshu

Status: prepared, not executed. This runbook is the controlled window after
the Shadow qualification; it is not a production command transcript.

## Preconditions

- Explicit Jovi authorization for the maintenance window is recorded.
- Current configuration and runtime snapshot is backed up and hashed.
- Agents, Bindings, Cron, Gateway, Sessions, Git state, and secret scan are
  recorded without persisting secrets.
- `zhongshu_preflight.py` passes; no active task is present.
- A tested rollback plan is present.

## Window

| Time | Action | Gate |
|---|---|---|
| T-30 | Back up configuration and record snapshot | Backup/hash present |
| T-10 | Run preflight and stop-condition checks | Healthy, no active task |
| T0 | Stop Core Feishu Binding for `zhongshu` through the approved account-level RPC | Consumer count becomes 0 |
| T+1 | Start Project Feishu Gateway | PID, health, ready |
| T+3 | Inspect ownership | Exactly 1 consumer; no Core socket |
| T+5 | Send one authorized text test | One reply, correct route |
| T+10 | Send TXT attachment test | receipt, SHA-256, quarantine, ingest_attachment |
| T+15 | Send PNG ingress test | receipt and quarantine; no implicit analysis |
| T+20 | Send card test | `card.action.trigger`, ticket, analysis request evidence |

## Immediate rollback

Rollback on Gateway not ready, RPC failure, missing text reply, duplicate
reply, consumer count above one, attachment failure, card verification
failure, or session anomaly:

1. stop Project Gateway;
2. restore Core Feishu Binding for `zhongshu`;
3. verify text, attachment receipt, and Session continuity;
4. record the result in `P0_ZHONGSHU_ROLLBACK_EXECUTION_030.md`.

The 033 repository scripts are read-only evaluators. They do not stop or start
anything and reject `--execute` until a separately reviewed production window
is authorized.
