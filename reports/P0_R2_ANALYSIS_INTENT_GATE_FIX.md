# P0 R2 Analysis Intent Gate Fix

Status: offline fix complete; real R2 remains FAIL and requires a new message_id.

## Root cause

The preserved PNG event had an empty caption. `ingest__ingest_attachment` quarantined the file and returned `analysis_allowed=true`, but there was no `attachment_action` or `analysis_requested` field. The Router then treated `detected_kind=png` plus a successful receipt as permission to call `analyzers__analyze_image`. This is a missing-intent/receipt-semantics defect amplified by model autonomy, not proof of a media-understanding failure.

## Contract now enforced

- Default and unknown/empty captions: `attachment_action=ingress_only`, `analysis_requested=false`.
- Explicit normalized, type-matching commands map only to `analyze_image`, `transcribe_audio`, or `analyze_video`.
- Type mismatch becomes `unsupported_action` and is never dispatched.
- Analyzer entry requires all three: `analysis_allowed=true`, `analysis_requested=true`, and matching `attachment_action`.
- Raw captions are not persisted; receipt/manifest store only controlled action metadata and a normalized-text SHA-256.
- Same-message action changes fail closed as `intent_conflict`.

## Evidence

The real failure remains in `reports/P0_R2_EVENT_TRACE_20260720.json`. Offline verification: Python ingest core 45/45, Router Pester 46/46, inbound Pester 36/36, and MCP probes with one ingest tool plus three Analyzer tools and zero diagnostics. No production configuration or Gateway state changed.

Next step: receive a new `p0-image-test.png` Feishu message with no caption and requalify R2 only.
