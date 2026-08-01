# P0 Final Operator Checklist 037

Status: `WAITING_RPC_TOKEN`. This checklist is not authority to execute T0.

## Before

- [ ] RPC Token has been injected into the authorized local operator process.
- [ ] Token is absent from the Project Gateway log scan.
- [ ] Token is absent from the Project Gateway child-process command line.
- [ ] OpenClaw configuration SHA-256 matches the approved maintenance value.
- [ ] Rollback plan and authorized restore control are available.
- [ ] Current Core Feishu state is confirmed with authenticated evidence and a
      manual uniqueness confirmation.
- [ ] Project Gateway is stopped.

## Cutover

1. Stop Core `feishu/zhongshu` using the authorized target-scoped control.
2. Confirm total consumer count is zero.
3. Start the Project Gateway only after the zero-consumer proof.
4. Confirm authenticated RPC readiness.
5. Confirm exactly one Project consumer and zero Core consumers.

## Smoke

Run in order; do not skip a failed or unknown stage:

1. R0: text routing and one reply.
2. R1: TXT ingestion, receipt, SHA, and quarantine.
3. R2: PNG ingestion, receipt, SHA, and quarantine.
4. Card: card event, ticket, and analysis-request binding.
5. R3: image analysis after R0/R1/R2/Card pass.
6. R4: audio analysis after R3 pass.
7. R5: video analysis after R4 pass.

## Rollback

On any failure: stop Project -> prove Project consumer zero -> restore Core
`feishu/zhongshu` -> verify text, then attachment and Session continuity. Never
leave both consumers connected.
