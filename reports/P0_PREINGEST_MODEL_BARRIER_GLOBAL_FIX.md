# P0 pre-ingest model barrier global fix

Status: **rolled back; not installed**.

OpenClaw 2026.7.1 supports `inbound_claim` and `before_agent_run`, and the offline implementation passed before activation. The structured plugin patch also changed `meta.lastTouchedAt`; this lies outside the approved `plugins.allow` and `plugins.entries.video-factory-preingest-barrier` paths.

The stop condition therefore fired before a Gateway restart. The byte-identical backup was restored, configuration validation passed, and the plugin directory plus focused test were removed. The restored configuration hash is `c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d`.

Gateway health remains good. The host still has 14 Agents, 14 Bindings, and 4 Cron entries; none of the other 13 Agents was changed. P0 remains `conditional_not_passed`.
