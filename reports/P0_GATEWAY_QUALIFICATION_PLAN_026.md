# P0 Feishu Gateway Qualification Plan 026

## Objective

Evaluate, under controlled local conditions, whether the Project Feishu Gateway has the evidence shape required to replace the OpenClaw Feishu Binding. This qualification is not a migration, a cutover, or a production-runtime claim.

## Scope and safety boundary

- All Gateway lifecycle, RPC, card, consumer, and rollback checks use in-process mocks or operator-supplied local mock snapshots.
- No Feishu SDK connection, OpenClaw RPC authentication, Binding command, Gateway process command, Agent/Cron/OAuth change, or production configuration read is performed.
- Every new migration script requires `--mock`; it has no live discovery or control capability.

## Qualification work

| Evidence area | Local evidence | Production evidence still required |
| --- | --- | --- |
| Gateway to RPC text path | Deterministic mock lifecycle, session admission, request correlation, response, retry, and post-accept timeout recovery | Authenticated loopback RPC handshake and bounded Agent request with a non-production credential |
| Card action | Official-SDK-shaped mock event preserves action/operator/chat and consumes its ticket | Signed Feishu test-app callback and reply-bound text intent created by OpenClaw |
| Single consumer | Pre/post mock snapshots reject overlap and duplicate events/replies | Atomic fenced owner integrated with old-Binding stop and Project start; independent long-connection observation |
| Rollback | Simulated start failure restores the old text/attachment path inside a 60-second modeled objective | Measured controlled-channel drain, restore, reconciliation, and recovery objective |

## Acceptance rules

1. A mock result is reported as `MOCK_ONLY`, never as live verification.
2. The four 025A high findings close only with the corresponding production evidence listed above.
3. Missing test-app/RPC authorization or an unproven architecture boundary blocks migration.
4. `PROJECT_STATUS.yaml` and the P0 final gate remain unchanged.

## Local execution evidence

- `tests.test_gateway_qualification_026`: 4 passed.
- Existing Feishu Gateway regression discovery: 37 passed.
- Existing migration-script regression: 3 passed.

## Exit decision

The local mock package is complete. It does not establish the required real reply-to admission, atomic single-consumer fence, production adapter, or measured rollback. The task therefore remains blocked from migration qualification until those separate gates are satisfied.
