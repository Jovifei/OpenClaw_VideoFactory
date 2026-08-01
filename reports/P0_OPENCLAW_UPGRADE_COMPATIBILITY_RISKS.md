# P0 OpenClaw Upgrade Compatibility Risks

Status: `risk_recorded_no_plugin_created`.

Future OpenClaw upgrades can change the following surfaces needed by a plugin-owned Binding design:

- core-route and plugin-owned Binding exclusivity;
- interactive `allow-once` approval lifecycle and persistence;
- `inbound_claim` dispatch ordering and its handled/declined/error/no-handler outcomes;
- `before_agent_run` failure behavior and timeout behavior;
- conversation-access permissions and Binding storage;
- trusted Plugin SDK runtime APIs, including embedded-agent execution and reply delivery.

The current source review establishes no version-stable full-agent forwarding contract for this design. Before a future implementation, pin and record the exact OpenClaw version, rerun SDK and dispatch compatibility checks, verify allow-once without persistent approval, prove pre-agent failure closure, prove session/reply equivalence for ordinary text, and rehearse official-API rollback. No plugin artifact, dependency, configuration, or core source change was made.
