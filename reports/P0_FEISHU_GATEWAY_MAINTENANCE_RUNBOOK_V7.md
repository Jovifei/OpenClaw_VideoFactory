# P0 Feishu Gateway Maintenance Runbook V7

This is an execution contract only. Task 036 stops before T0.

## T-60

- Inject RPC credentials only through inherited environment or a secure provider.
- Record sanitized configuration SHA, rollback artifact/control readiness, and
  current Core consumer evidence.

## T-30

- Require `RPC_READY`, authenticated health, and preflight `ready=true`.
- Require known Core consumer plus manual uniqueness confirmation.
- Require Project Gateway stopped and every final-precheck boolean true.

## T-10

Only an explicit target confirmation for `feishu/zhongshu` with
`can_cutover=true` is `READY_FOR_CUTOVER`; otherwise stop.

## T0 / T+1 / T+2 / T+5

1. T0: issue one authorized Core stop.
2. T+1: prove Core=0 and Project=0; unknown means rollback/stop.
3. T+2: start real Project Gateway only after T+1 proof.
4. T+5: prove Core=0 and exactly one Project consumer.

## T+10 / T+20 / T+30 / T+40

- T+10 R0 text; T+20 R1 TXT; T+30 R2 PNG; T+40 card.
- Any duplicate, loss, RPC, attachment, card, count, or Session failure triggers
  immediate Project stop -> proven zero -> Core restore -> text/attachment/
  Session verification.
