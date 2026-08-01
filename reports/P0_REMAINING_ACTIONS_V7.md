# P0 Remaining Actions V7

1. Preserve the real R2 failure: `R2_FAILED:ANALYZER_CALLED_AFTER_INGEST`.
2. Offline repair is complete under independent CRs 011 (intent gate) and 012 (stored hash integrity).
3. Require one new `p0-image-test.png` Feishu message_id with no caption for R2 requalification; do not reuse either failed event.
4. After the new R2 passes, stop for explicit sequencing authorization; do not enter R3, run the final Gate, or enter P1 in this task.

No production config, Agent, Binding, Cron, Gateway, model, or `PROJECT_STATUS.yaml` change is required for this offline repair.
