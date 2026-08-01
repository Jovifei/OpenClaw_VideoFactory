# 016 rollback

No rollback was required because no plugin, source file, configuration, Binding, consumer, Gateway, Agent, model, or Cron write occurred.

The preserved baseline is `reports/P0_CARD_ACTION_BASELINE_BEFORE.json`; its configuration SHA remains unchanged. If a future authorized implementation is attempted and the claim gate fails, the safe rollback is to disable/unlink only the new plugin, restore its pre-change plugin registry state, restart at most once if the approved change requires it, and re-run the topology and existing regression checks. Never remove or rewrite the old 015/R3 failure evidence.
