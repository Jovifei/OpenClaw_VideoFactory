# P0 Media Ticket Final Implementation 053

## Production route

`zhongshu -> OpenClaw Core Feishu Binding -> video-factory Router -> consume_media_action_ticket -> Analyzer`

The Project Feishu Gateway route remains stopped and deferred to P1.

## Implemented controls

- PNG, WAV, and MP4 quarantine ingress issue a 256-bit opaque Ticket; TXT remains
  ingress-only and issues none.
- The Ticket store retains only a SHA-256 Ticket digest and durable bindings for
  chat, sender, attachment message/index, kind, action, receipt, stored path,
  stored SHA-256, expiry, and state.
- Only strict `/vf image|audio|video <ticket>` is parsed. Natural language,
  extra text, multiple commands, newlines, Unicode/full-width/zero-width variants,
  OCR/content text, and malformed commands fail closed.
- The public consumer accepts only `raw_command`, current chat context, and current
  sender context. It refuses Router-supplied path, receipt, hash, kind, action,
  Analyzer, model, GPU, or trust fields.
- Default TTL is 300 seconds, `not_before` defaults to one second, and a newer
  pending Ticket cancels an older pending Ticket for the same chat/sender/kind.
- Consumption locks the hash-named record. It revalidates quarantine, receipt
  bindings, `analysis_allowed`, file existence, and SHA before creating a separate
  ticket-bound `analysis_request` and choosing the Analyzer server-side.
- Every call attempts a redacted audit. Before request creation or Analyzer
  dispatch, a successful `dispatch_authorized` audit is mandatory; failure restores
  `pending`, returns `ticket_audit_unavailable`, and dispatches zero Analyzers.
- `MEDIA_TICKET_EXECUTION_ENABLED` is fail-closed: a one-process environment value
  takes precedence, otherwise the ignored project-local
  `config/local/media_ticket_execution.json` explicitly enables production use.
  The committed example is disabled.

## Router limited-trust rule

The Router is instructed to forward the Ticket tool only for an exact current
`/vf` command. This is an operational constraint within the accepted finite
risk, not a claim of non-forgeable current-message provenance.

## Runtime application

At the final gate, Project Gateway processes = 0 and one resident Ticket-MCP
child was present. Its start time was later than the final Ticket-source write,
so it loaded the current source without a Gateway restart. The local project
activation setting evaluated enabled without an environment override. The first
authorized R3 command remains the live proof of end-to-end tool invocation; no
real Feishu action occurred here.
