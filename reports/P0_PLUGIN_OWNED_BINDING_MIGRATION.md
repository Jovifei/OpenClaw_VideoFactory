# P0 Plugin-owned Binding Migration

Result: **OVERNIGHT_PLUGIN_BINDING_DESIGN_BLOCKED**.

No migration was attempted. The supported plugin Binding request refuses to claim a conversation that remains core-bound. After removing the core Binding, the supported flow waits for a real interactive `allow-once` approval. This task may not use `allow-always`, fabricate approval, or edit internal Binding state.

The runtime also lacks a proven supported mechanism to forward every normal message to the existing `video-factory` agent while preserving the host's session, workspace, skills/tools, reply dispatcher, and original agent behavior. The lower-level embedded-agent runner is insufficient evidence for that guarantee. In addition, the expected existing `tests/Test-PreIngestModelBarrier.ps1` shadow test is absent, so the required 16/16 barrier regression cannot be claimed.

The baseline remains intact: config SHA-256 `c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d`, 14 agents, 14 Bindings, one target consumer, and four Cron entries. `openclaw config validate` exited 0 and the gateway port remained reachable. No restart, plugin file, core-Binding change, plugin-owned Binding, allow-once request, persistent approval, model call, attachment forwarding, or production configuration change occurred. No rollback was needed.
