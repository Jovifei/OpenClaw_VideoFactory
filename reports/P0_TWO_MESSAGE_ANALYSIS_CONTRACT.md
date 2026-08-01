# P0 Two-Message Analysis Contract (013)

Status: offline contract ready; live R3 not run.

## Message sequence

1. Feishu attachment message: Router calls `ingest_attachment` with Channel-bound metadata only. The result is quarantined and ingress-only; no Analyzer is dispatched.
2. Feishu text Reply: the Channel must provide `reply_to_message_id`. Router calls `create_analysis_request` with the Reply metadata and controlled text. This writes a separate request record; it does not rewrite the original receipt.
3. Analyzer: receives only `receipt_path`, `stored_path`, `job_id`, and `analysis_policy`. MCP derives message identity and attachment index from the receipt and requires a valid pending request.

## Association gates

The target must be an existing attachment receipt with `quarantined=true`, `content_parsed=false`, matching stored/source SHA-256, matching `attachment_index`, and a matching route-binding digest. The Reply must be from the original uploader in the same group, within 120 seconds, and use one normalized type-matching command.

Ordinary text, filename wording, bot summaries, non-Replies, cross-group or other-requester Replies, expired requests, unknown/prompt-injection text, and type mismatches are rejected. There is no filename, chronological, or model-inferred association.

## State boundary

Ingress facts (`analysis_requested`, `attachment_action`, `received_at`, source/stored hashes, quarantine, stored path) remain immutable. `analysis_request.json` carries pending/running/completed/failed/already_completed state. Analyzer may add only completion fields to the receipt.

The previous same-message R3 attempt remains `NOT_RUN_INVALID_MESSAGE_SHAPE`; it is preserved as negative evidence and is not a qualification result.
