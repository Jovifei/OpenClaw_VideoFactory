# P0 Media Action Ticket Contract 050

## Issuance

After a quarantined image, audio, or video receipt passes the ingress checks,
the server creates a `secrets.token_urlsafe(32)` opaque ticket (256 random
bits).  The client receives that value once; the server stores only its
SHA-256 digest in `state/media_action_tickets/`.

Each record binds exactly one ticket hash to the chat, uploader, attachment
message ID/index, receipt path, stored path, stored SHA-256, media kind,
allowed action, creation time, 10-minute expiry, and status.  TXT is
ingress-only and receives no ticket.  A duplicate ingress event never re-signs
or re-sends a ticket.

The public ingress projection contains only safe status, media kind, opaque
ticket, and the fixed command template.  It contains no internal path, full
hash, chat ID, sender ID, file key, or secret.

## Commands

Only these forms are valid:

```text
/vf image <ticket>
/vf audio <ticket>
/vf video <ticket>
```

Allowed normalization is outer whitespace trim, `/vf` and action case folding,
and interior space/tab collapse to one space.  Newline commands, natural
language, OCR text, prompt injection, media content, and additional arguments
are `command_invalid`.

## Consumption

`consume_media_action_ticket` accepts exactly:

```text
raw_command
current_chat_context
current_sender_context
```

It validates command syntax, ticket hash/existence/TTL/state, chat and sender,
action and media kind, receipt quarantine, receipt/record bindings, and stored
SHA-256.  It locks the hash-named ticket record before transitioning it from
`pending` through `consuming` to `consumed`, creates a ticket-bound pending
`analysis_request.json`, and server-side selects the matching Analyzer.

Failures return one of `command_invalid`, `ticket_not_found`, `ticket_expired`,
`ticket_consumed`, `chat_mismatch`, `sender_mismatch`, `action_mismatch`,
`media_kind_mismatch`, `receipt_invalid`, `stored_hash_mismatch`, or
`analysis_in_progress`; none dispatches an Analyzer.

The receipt's ingress identity, timestamps, quarantine state, stored path, and
hashes remain unchanged.  An Analyzer may update only request status and the
approved receipt completion fields.

