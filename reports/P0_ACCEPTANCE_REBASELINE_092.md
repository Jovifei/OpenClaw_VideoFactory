# P0 Acceptance Rebaseline — 092

Status: `PROPOSED_NOT_APPLIED`
Scope: acceptance design only; no Gate script, configuration, Binding, Gateway,
OAuth, Cron, media route or live Feishu behaviour changed.

## Decision

Remove **operator-manufactured Feishu retry** as a hard P0 gate. It is not a
reproducible platform control and P0-090's single authorized attempt produced no
retry observation. The safety objective remains unchanged: one configured
consumer must not create duplicate route, job, analysis, or delivery effects.

This proposal replaces the impossible observation with independently testable
controls. It does **not** claim that Feishu platform retry has been proven.

## New P0 definition

P0 proves a stable and safe AI-media entry layer, not daily video automation.
All nine requirements below are mandatory and must produce redacted evidence.

1. **Single consumer proof** — exactly one `video-factory` Feishu group Binding;
   no analyzer Binding and no second `lark-cli event consume` process.
2. **Real message entry** — one fresh ordinary-user group text event reaches
   `video-factory`, produces one visible fixed reply, and is correlated only by
   redacted identifiers.
3. **`event_id` idempotency** — a deterministic adapter/integration test sends
   the same canonical event envelope twice and proves one persisted ingress
   effect. A stable hash of `event_id` is recorded; raw IDs are never retained.
4. **Duplicate-event protection** — duplicate `message_id`/resource and repeat
   delivery-id paths produce neither a second analysis request nor a second
   outbound delivery. This is an application contract test, not a fabricated
   Feishu retry.
5. **Media safe ingress** — TXT, PNG, audio and MP4 are each isolated, hash-verified,
   quarantined and never treated as executable instructions.
6. **Image analysis** — a qualified PNG receipt is analyzed only after explicit
   reply/Ticket intent; result and failure states are retained.
7. **Audio analysis** — a qualified audio receipt is transcribed through the
   GPU lock with CPU fallback policy; result is non-empty or a classified
   failure, never a false success.
8. **Video analysis** — a qualified MP4 receipt is probed and sampled under the
   no-audio and analyzer-failure policy; result is classified.
9. **Restart recovery** — one ordinary managed Gateway restart preserves the
   one-consumer topology and the next fresh text event has exactly one route and
   one reply. Mid-render job recovery belongs to P1.

## Evidence model

| Evidence class | What it proves | What it cannot prove |
| --- | --- | --- |
| Unit | Pure ID normalization, key construction, MIME and state transitions | A live Channel route |
| Integration | Duplicate envelope produces one persisted side effect; restart-safe state handoff | Feishu platform redelivery |
| Real Feishu | One real user ingress, visible reply, media qualification and controlled egress | A platform retry that did not occur |
| Static topology | Binding singularity, tool policy, no analyzer Binding, zero extra consumer process | Runtime delivery history |

A P0 report must name its evidence class. Offline evidence may validate code
contracts, but only the real Feishu rows may validate a real Channel claim.

## Explicit removals

- No user or operator is asked to manually replay an Feishu event.
- No ACK fault injection is required or permitted by this P0 design.
- No second consumer, bot loopback, fabricated payload, or copied message ID
  may be used as ingress proof.
- Gateway/RPC/Device Auth/Project Gateway replacement are not P0 MVP gates.

## Required future implementation package

This proposal is not executable until separately authorized. The implementation
package must be limited to the Gate/prereview/acceptance tests and new redacted
evidence schema, expected to include:

- `scripts/90_acceptance_gate.py`;
- `scripts/p0_gate_prereview.py`;
- their focused tests; and
- the evidence producers named in `P0_ACCEPTANCE_MATRIX_V2.yaml`.

It may not weaken media safety, alter production configuration, or create a
passing marker without all required evidence. The current Gate remains in force
until this package is reviewed, tested and explicitly applied.

## Migration rules

- Existing V2.5 safe-ingress, Agent/Binding, egress and R3/R4/R5 evidence is
  reusable only where its check semantics match the new matrix.
- The existing aggregate safe-ingress report covers TXT/PNG/MP4. Audio receipt
  isolation/hash/quarantine evidence must be freshly added before this V2 row
  can pass; successful audio transcription alone is insufficient.
- New event-id and duplicate-protection tests must be fresh and versioned.
- Restart recovery and real ordinary-user ingress must be freshly observed after
  the new matrix is implemented.
- P0 passes only when the new Gate exits zero and writes `P0_READY.json`; the
  status script remains the sole phase-state updater.

## Risk control

The new contract reduces false blocking, not safety. Failure of the event-ID or
duplicate-protection integration test is a hard P0 failure. Absence of a
platform retry is recorded as `NOT_PROVEN_PLATFORM_RETRY` and is non-blocking.
