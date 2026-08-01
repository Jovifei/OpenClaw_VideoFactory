# P0 Minimum Completion Plan 056

Date: 2026-07-29  
Current phase: P0  
Current decision: **BLOCKED; do not start P1**

## What “complete first” means

The first product-complete target is the P2 baseline:

1. 08:30 sends 3–5 qualified topic candidates.
2. A user selection starts production; at 12:00 a valid highest-score fallback
   starts production when no selection exists.
3. A topic becomes one verified vertical MP4 with TTS, captions, deterministic
   technical visuals, quality evidence, and one idempotent Feishu delivery.
4. Douyin publication remains manual.

P3 GPU/ComfyUI enhancement, P4 reference-video recreation, and P5 Jianying
export are product improvements, not prerequisites for this first complete
baseline.

## Current distance from the target

### Wave 0 — finish P0 truthfully

Run in this order:

1. Fresh real R3 image retest. It must return actual analysis content beginning
   with `图片分析结果：`, not a generic completion notice.
2. Real R4 audio qualification, only after R3 passes.
3. Real R5 video qualification, only after R4 passes.
4. Complete or normalize current-schema P0 evidence:
   - single Feishu consumer plus message-id deduplication;
   - TXT/PNG/MP4 safe ingress;
   - lark-cli Markdown/PNG/TXT/MP4 egress plus idempotency;
   - Direct Codex CLI read/workspace-write isolation smoke;
   - existing Agent/Binding regression.
5. Refresh `SHA256SUMS.txt` only after the intended P0 candidate is frozen.
6. Run the real P0 acceptance gate and create `P0_READY.json` only on exit 0.

The current machine still resolves `codex-cli 0.142.4`; its prior smoke failed
because the configured model requires a newer CLI. No upgrade was attempted in
this task.

### Wave 1 — P1 deterministic video MVP

Implement strictly after `P0_READY.json`:

1. SQLite state/event/artifact store and CLI with idempotency, cancellation,
   and restart recovery.
2. Render one fixed JSON fixture to a decodable 10-second 1080x1920 MP4.
3. Add stable TTS and monotonic safe captions.
4. Add the four deterministic Remotion templates one at a time.
5. Add deterministic Pink Pig assets and safe fallback.
6. Qualify the Modbus, Flash/watchdog, and FreeRTOS fixtures.
7. Add Feishu delivery last and pass the P1 gate.

This wave produces the first manually triggered, repeatable video-generation
vertical slice.

### Wave 2 — P2 minimum automated factory

1. Add allowlisted topic sources and history.
2. Generate at least 10 raw candidates; score/deduplicate to 3–5.
3. Implement selection parsing and safe modifications.
4. Implement the 12:00 fallback, immediate production, cancellation, and
   recovery.
5. Register production Cron only after its dry-run and P2 gate pass.
6. Complete a seven-day trial and record success/duplicate/manual-time metrics.

This wave reaches the minimum form of the final product goal.

## Current evidence-driven blockers

The refreshed prereview reports 14 passed, 1 conditional, and 8 blocked checks.
The eight blocking checks are:

1. single consumer plus deduplication evidence;
2. canonical safe TXT/PNG/MP4 ingress evidence;
3. canonical lark-cli multi-format egress/idempotency evidence;
4. Direct Codex CLI isolation smoke;
5. existing Agent/Binding regression evidence;
6. fresh real R3 result;
7. real R4 result;
8. real R5 result.

Release checksums are conditional and must be refreshed only at the frozen P0
candidate boundary.

## Work completed in this task

- Replaced the stale hard-coded P0 prereview with evidence-driven classification.
- Preserved R0/R1/R2 as passed based on real event trace evidence.
- Added ordered next-action behavior and an explicit P1 phase lock.
- Added five focused readiness tests.
- Verified 319/319 Python, 123/123 Pester, 88/88 Schema, and `pip check`.

No Feishu message, Gateway lifecycle action, OpenClaw configuration change,
P1 implementation, model download, Cron registration, phase promotion, commit,
push, or tag occurred.

## Unique next action

Perform one fresh real R3 image retest in the existing Feishu group. Stop and
freeze evidence if the visible result is not a single substantive
`图片分析结果：` reply.
