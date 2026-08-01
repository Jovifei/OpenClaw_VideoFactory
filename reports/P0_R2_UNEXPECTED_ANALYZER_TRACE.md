# P0 R2 Unexpected Analyzer Trace

The preserved real PNG event had no caption beyond the media marker. The exact observed order was:

1. Feishu delivered an image and Channel-bound media metadata.
2. The text-only Router called `ingest__ingest_attachment` without `size_bytes` or `max_bytes`.
3. Ingest returned a quarantined receipt with `content_parsed=false`, `quarantined=true`, and `analysis_allowed=true`.
4. The Router called `analyzers__analyze_image` solely because the attachment was a PNG.
5. Analyzer rejected the call with `stored_hash_mismatch`.

The defect was not an automatic pre-reply media-understanding call. It was a post-ingest dispatch decision with no explicit intent field. The implementation conflated safety eligibility (`analysis_allowed`) with user intent. The new contract separates them and makes the Analyzer MCP reject a bare attachment even if a Router repeats the erroneous call.

Evidence: `reports/P0_R2_UNEXPECTED_ANALYZER_TRACE.json` and the preserved session/receipt references in `reports/P0_R2_EVENT_TRACE_20260720.json`.
