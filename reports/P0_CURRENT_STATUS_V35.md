# P0 Current Status V35

`CORE_BINDING_TRUSTED_COMMAND_PROVENANCE_UNAVAILABLE`

Installed OpenClaw 2026.7.1 has trusted Channel facts inside its inbound path,
but exposes no per-call non-forgeable current-message/current-turn capability
to the configured local stdio MCP consumer.  The consumer cannot prove
`raw_command` provenance.  No source remediation, real-media run, or 052A
independent review occurred.
