# Plugin-owned Binding Upgrade Compatibility

Status: `risk_recorded_no_plugin_created`.

The requested design would depend on internal OpenClaw dispatch semantics: core Binding exclusivity, interactive approval lifecycle, plugin-owned inbound-claim outcomes, and embedded-agent runtime interfaces. Those surfaces can change with OpenClaw upgrades and are not protected here by a released plugin integration test.

The present source review shows that a plugin-owned Binding is not a transparent replacement for a core agent Binding. Before any future implementation, pin the OpenClaw version, re-run source/API compatibility checks, prove a supported full-agent forwarding route, test an allow-once lifecycle interactively, and prove rollback. No code, plugin artifact, dependency, or configuration was added in this task.
