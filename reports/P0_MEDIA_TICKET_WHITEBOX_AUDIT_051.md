# P0 Media Ticket White-box Audit 051

Result: `CHANGES_REQUIRED:raw_command_source_provenance_not_bound_to_channel_message`

This audit examined the active offline source only.  No Feishu, Gateway,
credential, protected path, or real Analyzer was accessed.

## Confirmed fail-closed controls

- `media_action_ticket.py` uses 256-bit random opaque tickets and stores only
  their SHA-256 values.  The state is Git-ignored.
- The public consumer accepts exactly `raw_command`, `current_chat_context`,
  and `current_sender_context`; paths, hash, action, model, and GPU fields are
  rejected before dispatch.
- Parsing accepts only ASCII `/vf image|audio|video <ticket>` with spaces.  It
  rejects Unicode confusables, zero-width characters, natural language, text
  found in media, multiple commands, and extra arguments.
- The server rechecks ticket state, TTL, chat/sender/action/kind, receipt,
  quarantine, `analysis_allowed`, stored path, and SHA-256 before atomically
  entering `consuming`.
- Interrupted records and orphaned locks terminalize as failed without replay;
  record-first issuance is recovered without a second ticket; expired pending
  records are tombstoned lazily.
- The public consume projection omits job IDs, ticket-hash material, paths,
  and Analyzer details.  GPU work has a heartbeat lease and video audio is
  explicitly capped at 300 seconds.

## Required unresolved change

The three-field MCP contract cannot independently attest that `raw_command`
is the original Channel message bytes.  A text Router that chooses to rewrite
natural language into an otherwise valid exact command is indistinguishable
from an original exact command.  Solving that requires a trusted
Channel-to-MCP immutable message binding, which is outside this task's frozen
Core Binding/channel boundary.  Therefore this audit cannot qualify the
“Router-rewritten command rejected” requirement.

No “latest attachment”, “previous image”, Router-supplied path/action, direct
Analyzer bypass, hard-coded ticket, raw ticket persistence, or fail-open
authorization route was accepted by this audit.  Static evidence does not
prove live Core MCP rediscovery or R3-R5.
