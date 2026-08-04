# P0 Landing Plan — 092

Status: `PROJECT_DIRECTION_RESET_COMPLETE`

## 1. What is complete now?

There is no honest single percentage because implementation and formal release evidence differ.

| Dimension | State |
| --- | --- |
| P0 media/security capability | Strong: receipts, Tickets, image/audio/video analysis, topology and real egress evidence exist |
| P0 formal readiness | Incomplete: V2 acceptance is proposed, not applied; no P0 Gate pass |
| P1 deterministic creator | Offline candidate implemented and independently requalified: state, TTS, captions, four visuals, mascot, NVENC/CPU output, quality and dry-run delivery |
| P1 real MVP | Incomplete: no factory live delivery, lifecycle proof, human acceptance or P1 Gate |
| P2 daily operation | Not implemented or validated |
| P3/P4 | Deferred by design |

The first usable-video engine is substantially implemented **as an offline candidate only**.
The daily operational factory is not implemented or released.

## 2. What remains?

1. Apply and test the P0 rebaseline without weakening safety.
2. Capture the new P0 evidence and close P0 once.
3. Promote the P1 candidate through real delivery, lifecycle and human review.
4. Implement P2 topic recommendation, selection/fallback and seven-day trial.
5. Add P3/P4 only for measured quality or publishing needs.

## 3. Next 30 days

| Window | Outcome | Guardrail |
| --- | --- | --- |
| Days 1–3 | Authorized P0 Gate/prereview/evidence-schema implementation | No Gateway/Binding/OAuth/Cron change |
| Days 4–6 | One P0 evidence run and one P0 Gate | No retry injection or second consumer |
| Days 7–14 | Revalidate candidate and verify factory-to-Feishu binding | One change category per Change Request |
| Days 15–21 | Three-fixture lifecycle, real idempotent delivery and human review; P1 Gate | No auto-publish |
| Days 22–30 | P2 sources/score/selection and dry-run 08:30/12:00 preparation | Cron only after P2 tests; trial begins after activation |

This sequence is not authorization to skip phase gates or to make runtime changes without a scoped approval.

## 4. Tasks stopped

- Further manual Feishu retry reproduction or ACK fault injection;
- Project Gateway replacement, Device Auth and RPC provenance as MVP blockers;
- repeated media qualification while R3/R4/R5 evidence remains valid;
- second scheduler/agent framework or broad open-source stack installation; and
- ComfyUI model/node download before P3 approval.

## 5. Priority order

1. P0 rebaseline implementation and fail-closed tests.
2. One P0 closure attempt with observable evidence.
3. Real P1 factory delivery, lifecycle and human review.
4. P2 topic and scheduling automation.
5. GPU, reference-video and publishing enhancements.

## Operating rule

Every future task must name product phase, user-visible outcome, evidence layer,
exact Gate advanced and what it does not advance. Otherwise it stays outside the active queue.
