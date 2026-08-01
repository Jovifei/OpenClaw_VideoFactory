# P0-013 Offline Implementation

The authorized implementation is complete offline. `scripts/analysis_request.py` validates Channel-bound Reply metadata, resolves only an existing quarantined attachment, writes an independent request record, and preserves receipt ingress facts. `scripts/mcp_ingest_attachment.py` exposes `create_analysis_request` and rejects captions on the public ingest MCP surface. `scripts/analyzer_mcp.py` requires a pending request and exposes only four safe dispatch fields.

The Router memory contract in `AGENTS.md` now treats attachment and analysis intent as separate messages. No Binding, Agent, Cron, media scope, model, Gateway, `PROJECT_STATUS.yaml`, or production configuration changed. The config SHA remains `d6a97f...1be8c` (full value in the JSON evidence).

The public MCP probe reports two ingest tools and three analyzer tools. The live Router allowlist was not edited or reloaded in this turn; if the new namespaced tool is not already exposed through the existing MCP bundle, that is a separate operator-authorized config/restart step before real R3.
