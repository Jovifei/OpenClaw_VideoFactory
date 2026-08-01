# Not-applied production migration plan

1. Obtain separate authorization and a maintenance window; back up and hash redacted configuration.
2. Stop the production Gateway, disable the core Feishu Binding, then start the project Gateway with the existing `zhongshu` credentials in its secure local store.
3. Start/resume OpenClaw without a Feishu consumer; verify one WebSocket owner/process and no duplicate event/download/reply/Analyzer keys.
4. Run R0 text, R1 TXT, R2 PNG, card probe, then R3 image. Stop on any failure; only R3 PASS permits R4/R5.
5. Retain logs and restore the old Binding before reopening traffic if any step fails.

This plan is not authorization to change production.
