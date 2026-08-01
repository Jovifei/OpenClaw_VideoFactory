# P0 Core Binding Command Provenance Audit 052

## Decision

`CORE_BINDING_TRUSTED_COMMAND_PROVENANCE_UNAVAILABLE`

Installed OpenClaw 2026.7.1 has runtime-owned Channel facts, but its stable
Default Runtime does not provide a non-forgeable current-message/current-turn
capability to the configured project stdio MCP `tools/call`.  The local
consumer receives only model-selected MCP `arguments`, so it cannot prove that
`raw_command` equals the original body of the current Feishu user message
without a prohibited Core or Binding change.

## Scope and proof layer

Read-only static inspection covered the installed package
`C:\Users\Admin\AppData\Roaming\npm\node_modules\openclaw` (version
`2026.7.1`) and the project-local MCP process.  No configuration, credential
store, session archive, Feishu payload, Gateway, or live media was accessed.
This is not a live Feishu/MCP-discovery claim.

The installed Core documentation identifies Feishu as the external
`@openclaw/feishu` plugin (`docs/channels/feishu.md:9,24`); that plugin source
was not present under this package root, and protected profile/config paths were
intentionally not inspected.  This does not weaken the transport conclusion:
even a plugin that supplies all listed inbound facts cannot prove them to this
local consumer when the Default Runtime forwards only MCP `arguments`.

## Core versus MCP boundary

Core's Channel turn types can hold original runtime facts.  In
`dist/types-DaHgOqFX.d.ts:7914-7991`, the turn/context parameters include the
channel event, message id, timestamp, sender, conversation, `RawBody`,
`BodyForCommands`, and `SessionKey`.  `:1963-1989` also gives an embedded run
message-channel, sender, chat, and current-message id.  These are runtime
values before model tool materialization.

That trust does not reach the project stdio server:

- `dist/selection-8ixiqbew.js:11925-11934` creates the MCP runtime only with
  `sessionId`, `sessionKey`, `workspaceDir`, and config.
- `dist/agent-bundle-mcp-materialize-MreR0YX9.js:275-278` passes model tool
  `input` directly to `runtime.callTool`.
- `dist/agent-bundle-mcp-runtime-DGeRg_-o.js:1314-1321` serializes that input
  as MCP `arguments` without current body/message/event/turn/run provenance.
- `dist/agent-bundle-mcp-runtime-DGeRg_-o.js:74-90,623-636,694-700` starts the
  stdio child from configured command/args/environment.  It has no per-call
  authenticated Channel-context injection.

The public inbound-envelope type is only a prompt formatter taking channel,
sender, body, and optional timestamp
(`dist/inbound-envelope-CyqvCT28.d.ts:4-44`), not a signed/current-turn MCP
capability.  Plugin-owned tool context is also not a substitute: it lacks raw
current message/event binding, and this project is an independent stdio MCP,
not a Core-owned plugin tool.

## Local MCP boundary

`scripts/mcp_ingest_attachment.py:826-843` requires caller-provided
`raw_command`, `current_chat_context`, and `current_sender_context`.
`:923-943` forwards `params.arguments`; `:962-979` reads JSON-RPC from stdin.
`scripts/media_action_ticket.py:284-304,467-490` only normalizes and validates
those caller-controlled values.  A Router/LLM can reconstruct a syntactically
valid command and matching identity values; this consumer has no independent
source with which to detect the rewrite.

| Field | Core Channel boundary | Local stdio MCP consume call | Trusted proof at consumer |
|---|---:|---:|---:|
| Original body / `RawBody` | Yes | No | No |
| Message id | Yes | No | No |
| Chat and sender ids | Yes | Model argument only | No |
| Session key | Yes | Runtime bookkeeping only | No |
| Event/turn/run binding | Internal/partial | No | No |
| Current-body hash or one-time handle | No transport | No | No |

## Consequence

The required `TrustedCommandEnvelope` cannot be created safely in P0.  Router
input, prompt parsing, a timestamp, a latest-session lookup, Project Gateway
data, or a model argument would be forgeable.  No source implementation, real
R3/R4/R5 action, or 052A independent review is allowed by this result.
