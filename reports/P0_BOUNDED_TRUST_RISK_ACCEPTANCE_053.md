# P0 Bounded-Trust Risk Acceptance 053

Status: **ACCEPTED BY JOVI FOR P0 ONLY**

## Accepted residual risk

OpenClaw 2026.7.1 Core Feishu Binding does not expose a non-forgeable current
message capability to this local stdio MCP. Therefore the `video-factory`
Router could theoretically construct a syntactically valid historical
`/vf <kind> <ticket>` tool call when the current user message is not that exact
command.

This is a finite, explicitly accepted P0 risk only for Jovi's own `zhongshu`
bot in the current private OpenClaw VideoFactory group. It is not described as
equivalent to a trusted Channel-message provenance boundary.

## Why the limited P0 use is accepted

- Tickets bind to one chat, sender, attachment, media kind, and allowed action.
- Tickets are opaque 256-bit random values; server state stores only SHA-256.
- Default TTL is five minutes; the same chat/sender/kind has one pending ticket.
- New issuance cancels its older pending peer; consumption is atomic and one-time.
- A one-second `not_before` window prevents same-run immediate consumption.
- Receipt quarantine, `analysis_allowed`, stored-file existence, and stored SHA-256
  are revalidated before a server-selected Analyzer is called.
- A successful pre-dispatch redacted audit is mandatory. Audit failure leaves
  the ticket pending, creates no analysis request, and calls no Analyzer.
- The execution switch defaults closed and cannot be changed by the Router.

## Explicitly not accepted

Other-user, cross-chat, cross-attachment, expired, repeated, natural-language,
recent-attachment, path-supplied, hash-supplied, Analyzer-supplied, model-fallback,
or receipt/SHA-bypassing execution is rejected. The Router has no public input
for paths, receipt paths, hashes, kind, action, Analyzer, model, GPU settings, or
`trusted=true`.

## Deferred to P1 channel hardening

`DEFERRED_TO_P1_CHANNEL_HARDENING`: Project Feishu Gateway replacement, Device
Auth/Pairing, Windows Gateway service authentication, Trusted Command Envelope,
Reply association, cards, inbound claim, native slash registration, and
non-forgeable message provenance. None was modified, tested, or made a P0 gate
in this task.
