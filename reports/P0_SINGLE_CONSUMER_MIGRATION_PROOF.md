# Single-consumer migration proof (P0-019, offline-boundary phase)

## Objective

Prove the replacement model is prepared for maintenance cutover without dual active consumers:
- old: OpenClaw Core Feishu Binding remains disabled for the new phase,
- new: Project Feishu Gateway can run alone in rehearsed offline flow.

Current phase is offline-only. Real OpenClaw/WebSocket/identity probes are still pending.

## Offline evidence collected in repository

1. **Rehearsal sequencing**
   - `experiments/feishu_gateway_migration/rehearsal.py`
   - Steps: `stop_core_binding` → `start_project_gateway` → `verify_one_consumer` → `route_fake_message` → `rollback_core_binding`
2. **Deduplication in project gateway**
   - `services/feishu_gateway/service.py`
   - `GatewayState.seen` stores hashed event IDs and rejects repeat event IDs before any callback.
3. **Card replay protection**
   - `services/feishu_gateway/service.py`
   - Tickets are one-shot (`used=true` after first card action), and `card()` returns `ticket_invalid` on duplicates.
4. **Identity checks in card callback**
   - `services/feishu_gateway/service.py`
   - `card()` checks `chat_id`, `operator_id`, and `action` before invoking analyzer dispatch.
5. **State redaction**
   - `services/feishu_gateway/service.py`
   - `GatewayState._sanitize` persists only hashed `chat`/`sender` and hashed `event_id` for replay tracking.

## Required production proof not yet collected in this phase

- `zhongshu`/Project Gateway WebSocket count and identity (exact process identity).
- Developer-console subscription / callback identity for `im.message.receive_v1` and `card.action.trigger` in the live Consumer window.
- Cross-consumer replay evidence with redacted shared message ID proving only one consumer dispatch for the same event.

## Required production proof payload (planned)

After this offline phase:
- run one dedicated `P0_SINGLE_CONSUMER_TEST` with redacted message ID, then confirm:
  - one and only one receiver dispatch line for the same redacted message id,
  - no duplicate reply for same redacted message id at gateway output.
- run one dedicated consumer-restart rehearsal window and repeat the same id check.

## Current migration status

- `status`: `BLOCKED_OFFLINE_SAFE`
- `implementation_readiness`: `PROJECT_FEISHU_GATEWAY_BLOCKED`
- `next_action`: collect live OpenClaw/WebSocket + message-id evidence before production cutover.
