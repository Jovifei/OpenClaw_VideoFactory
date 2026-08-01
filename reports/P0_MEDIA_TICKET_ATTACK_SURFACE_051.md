# P0 Media Ticket Attack Surface 051

Mitigated offline surfaces: opaque random ticket guessing, token mutation,
ticket replay, TTL, cross-chat/sender reuse, cross-action/kind requests,
storage/receipt/hash tampering, path escape/reparse, partial state, stale
ticket lock, duplicate ingress, concurrent dispatch, Unicode confusables,
media-contained apparent commands, public hash leakage, GPU overlap, and
unbounded video audio extraction.

Unresolved boundary: `raw_command` reaches the MCP as a Router-supplied string
without a Channel-origin envelope.  The system cannot prove that a valid exact
command originated verbatim from the user rather than being constructed by the
Router.  This is a fail-closed qualification gap, not a claim that a live
rewrite has occurred.
