# P0 Live Media Qualification 012 — R2 and MP4 Ingress

## Verdict

`R2=PASS` for the new PNG event. The current bare MP4 is `R2V_VIDEO_INGRESS_ONLY=PASS`; it is explicitly not R5.

The earlier real R2 failure (`R2_FAILED:ANALYZER_CALLED_AFTER_INGEST`) remains preserved and is not relabeled.

## PNG R2

- New Feishu message: `om_***9de9`.
- Router: `xiaomimimo/mimo-v2.5-pro`, one model call.
- Pre-ingest image understanding: 0; no raw pixel block was present in the Router session input.
- `ingest_attachment`: one call; `attachment_action=ingress_only`; `analysis_requested=false`; `analysis_allowed=true`.
- MCP independently recorded `actual_size_bytes=17247` and `stored_size_bytes=17247`.
- Source SHA-256, stored SHA-256, and fixture manifest SHA-256 are identical (full 64-hex comparison).
- `trusted_root_id=video_factory_workspace`; source-root match true.
- Receipt exists; `content_parsed=false`; `quarantined=true`; status `quarantined`.
- Analyzer calls: 0. Router did not read or summarize image pixels.
- Reply activity returned through the original Feishu group context.

## Bare MP4 ingress-only

- New Feishu message: `om_***27b7`.
- Router: `xiaomimimo/mimo-v2.5-pro`, one model call.
- Pre-ingest video understanding: 0.
- `ingest_attachment`: one call; `attachment_action=ingress_only`; `analysis_requested=false`.
- MCP independently recorded `actual_size_bytes=52037` and `stored_size_bytes=52037`.
- Source SHA-256, stored SHA-256, and fixture manifest SHA-256 are identical.
- Receipt exists; `content_parsed=false`; `quarantined=true`; status `quarantined`.
- Video Analyzer calls: 0. This event is not counted as R5.
- Reply activity returned through the original Feishu group context.

## Invariants and stop boundary

Agents=17, Bindings=14, Cron=4, target-group consumers=1, and the configuration SHA are unchanged from the baseline. R3-R5, egress, final P0 Gate, and Git publication remain unrun. The next permitted boundary is `READY_FOR_R3`, awaiting a new `p0-image-test.png` with the exact approved analysis caption.
