# Gateway rollback

If an authorized cutover fails:

1. Stop the project-owned Gateway process and clear in-memory pending tickets.
2. Restore the backed-up core Binding/configuration snapshot.
3. Start only the existing OpenClaw-owned Feishu consumer and verify one connected WebSocket plus one message consumer.
4. Run a single read-only status probe and verify no duplicate consumer is active.
5. Keep both old and new pending replies/callback states disabled during rollback window.
6. Resume with the pre-cutover known-good runbook only after validation.

Do not run both consumers, replay callbacks, or start Analyzer jobs during rollback.
