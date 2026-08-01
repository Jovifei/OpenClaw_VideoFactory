# P0 Zhongshu Migration Plan 029

## Status and scope

Preparation status: `ZHONGSHU_MIGRATION_READY`.

Execution status: `ZHONGSHU_MIGRATION_WAITING_AUTH`.

`zhongshu` is the final Feishu entrance. This plan prepares a short, operator-controlled maintenance window that transfers its exclusive channel ownership from the existing OpenClaw Core Feishu Binding to the Project Feishu Gateway. It does not create a test App, Bot, group, second connection, or alternate entrance.

This document and its scripts are preparation-only. They do not stop a Binding, start or restart a Gateway, send a message, or modify configuration.

## Required pre-cutover record

Before any future window, create a sanitized, read-only snapshot with no credentials or raw Feishu identifiers. It must record:

- Agents, Bindings, and Cron inventory were observed.
- Core Gateway and Project Gateway state.
- Current Core Binding count, consumer count, and WebSocket count.
- Project Gateway consumer and WebSocket count.
- Active task and pending-media counts.
- A one-way session-lineage hash.
- A configuration-backup manifest hash and the rollback-plan identifier.

`scripts/migration/zhongshu_preflight.py` accepts that snapshot and checks only local artifact presence. It has no network, OpenClaw, Feishu, process-control, or mutation capability.

## Controlled sequence for a separately authorized window

| Time | Operator action | Required condition; failure handling |
| --- | --- | --- |
| T-30 | Create the configuration backup and sanitized baseline record. | Backup manifest and rollback plan exist; no raw secret or identifier is recorded. |
| T-10 | Run the preflight check and confirm no active work. | Core consumer=1, Project consumer=0, combined=1, Project Gateway stopped. Any failure cancels the window. |
| T0 | Stop only the approved existing Core Feishu Binding for `zhongshu`. | This action needs the separate authorization checklist. |
| T+1 | Observe the entrance after Core shutdown. | Combined consumers=0. Any residual consumer or WebSocket starts rollback. |
| T+2 | Start the approved Project Feishu Gateway once. | One launcher, one lease owner, no parallel Core recovery. |
| T+3 | Capture the post-cutover snapshot. | Core consumer=0, Project consumer=1, combined=1, one Project WebSocket. |
| T+5 | Send one authorized harmless text test. | One event and one unique reply correlation; session lineage remains continuous. |
| T+10 | Send one authorized harmless attachment test. | One ingress record, one consumer, no duplicate delivery, and no unintended analysis. |
| T+15 | Perform one authorized card test. | One event, one unique delivery correlation, preserved session lineage, and no second intent protocol. |

`scripts/migration/zhongshu_postcheck.py` validates each sanitized post-cutover snapshot against the preflight snapshot. Any duplicate event/reply, multiple consumers, missing delivery evidence, or lineage mismatch is a failure.

## Stop conditions

- Preflight fails or its backup/rollback artifacts are absent.
- Active task or pending media is nonzero.
- Combined Feishu consumer count is not exactly one before or after the intended handoff, or is not zero at T+1.
- A Core and Project WebSocket overlap.
- Gateway readiness, Project lease ownership, unique delivery, or session continuity cannot be proven from sanitized evidence.
- Any output would contain a secret, token, raw Feishu identifier, or raw attachment path.

On any stop condition, perform the separately authorized rollback plan. Do not retry the cutover speculatively in the same window.
