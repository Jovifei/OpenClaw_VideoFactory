# P0 Pre-ingest Architecture Options

Status: `design_blocked_no_production_changes`.

## Option 1 — plugin-owned conversation Binding (requested)

The current target is one core Feishu group route: `zhongshu` account, group `oc_***1555`, agent `video-factory`. OpenClaw's supported conversation-binding implementation rejects a plugin claim while that core route exists: `This conversation is already bound by core routing and cannot be claimed by a plugin.` Removing the route first leaves an interactive `allow-once` approval step; this task permits neither an `allow-always` approval nor internal Binding-state edits.

The plugin-owned dispatch path calls `inbound_claim` before normal agent processing. A plugin could return a terminal reply, but returning a non-handled/failed result does not prove a transparent return to the original `video-factory` dispatch. The public runtime exposes a low-level embedded-agent runner, not a supported host re-dispatch API that preserves the existing session, workspace, skills/tools, reply dispatcher, and agent behavior. Therefore Option 1 cannot safely migrate in this task.

## Option 2 — Channel pre-agent middleware

Put the deterministic attachment barrier at a Channel-layer pre-agent interception point, before the normal core Binding resolves to the agent. This retains the existing core route and has the best architectural fit for a fail-closed attachment policy. It requires a separately authorized feasibility/design task; it is not implemented here.

## Option 3 — independent attachment entry Bot or group

Use a separate attachment-only Bot or a separate dedicated group, leaving the current video-factory conversation on its existing core route. This avoids proxying ordinary text through a plugin but splits the user experience and requires a separate intake topology and authorization boundary. It is not implemented here.

## Decision

| Criterion | Option 1: plugin Binding | Option 2: Channel middleware | Option 3: separate intake |
| --- | --- | --- | --- |
| Attachment safety | strong only if proxy is proven | strong, pre-agent | strong, separate boundary |
| Text-agent compatibility | currently unproven | retains core route | retains core route |
| User experience | single group | single group | split entry point |
| Single-consumer proof | migration-sensitive | core route remains | needs distinct intake proof |
| Change / rollback | Binding lifecycle and plugin | Channel integration | topology and routing |
| Upgrade risk | high | medium/high | medium |

No production migration, plugin, config change, gateway restart, Binding edit, model change, or test upload was performed. The current core Binding remains the sole target consumer. The recommended next task is a separate, read-only feasibility review for Option 2.
