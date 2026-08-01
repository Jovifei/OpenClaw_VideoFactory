# P0 Command Provenance Risk Decision 052

No choice is made by this task.  The installed Core transport cannot give the
local MCP consumer a non-forgeable binding to the current real Feishu message
without a prohibited Core or Binding change.

Choose exactly one of these two options:

1. **Strict blocked** — retain the required provenance rule.  Keep the media
   ticket consumer non-qualifying and do not allow real R3/R4/R5 through this
   command path until an approved Core/Binding integration supplies a
   runtime-issued current-message/current-turn envelope.
2. **Explicit risk acceptance: treat the Core Router as a trusted command
   forwarder** — authorize reliance on caller-provided command, chat, and
   sender fields.  This deliberately waives the requirement that a Router/LLM
   cannot self-declare command provenance; it is not a trusted message binding.
