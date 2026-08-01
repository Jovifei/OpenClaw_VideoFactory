# P0 Real-Channel Event Trace (008)

Task: `P0-REAL-CHANNEL-QUALIFICATION-008`
Status: **observability tooling validated on a live `openclaw agent` attachment event** (masked, correlated).
Tools: `scripts/observability/trace_event.py`, `scripts/observability/demo_trace.py`

## Method

A fresh `openclaw agent --agent video-factory` turn was run with a staged PNG in the real inbound root, instructing the router to call `ingest_attachment` with a known `message_id` (`om_obstrace008`). The observability tool then traced the event across the receipt file, the video-factory session trajectory, GPU lock logs, and analysis.json - extracting masked, correlated metrics.

This is NOT a real Feishu Channel event (no `media://inbound/*` ref from the Channel); it is a Gateway-agent-turn event with the same downstream path. Real Feishu event tracing uses the same tool with the real `message_id` from the Channel.

## Trace result (demo event om_obstrace008)

| Metric | Value | Notes |
| --- | --- | --- |
| message_id_hash | sha256(om_obstrace008)[:16] | correlates stages |
| run_id | d86b1e9a-... | from `openclaw agent --json` |
| matched_session | 66b522dd-...trajectory.jsonl | video-factory session |
| router_model_observed | mimo-v2.5-pro | text-only (durable config生效) |
| pre_ingest_media_understanding_count | 0 | no [Image]/[Audio]/[Video] blocks in the session |
| router_images_count | 0 | no image pixels / media:// refs in llm_input |
| raw_media_path_forwarded | false | original inbound MediaPath NOT forwarded |
| stored_path_forwarded | false (parser) | stored_path lives in the receipt; the session did not echo it to an analyzer (no spawn of analyzer this turn) |
| ingest_tool_call_count | 1 (receipt) | one quarantined receipt |
| ingest_status | quarantined | content_parsed=false, quarantined=true |
| tool_calls (session) | ingest_attachment xN + sessions_spawn xN | the agent retried ingest; idempotency held (1 receipt despite N calls) |
| gpu_lock_acquired | false | PNG via cloud mimo-v2.5 does not use the local GPU lock |
| analysis_agent_call_count | 0 | this turn was ingest-only (no analysis requested) |
| final_reply_target | feishu:group:<target-id> | router replied via its binding |
| router_reply_head | "status: quarantined" | correct |
| chat_id_masked / sender_id_masked | oc_***1555 / ou_***ada9 | masked |

## Observability data sources (for real Feishu events)

| Stage | Source | Extraction |
| --- | --- | --- |
| event_id / message_id | Channel event / run result | hash (sha256[:16]) |
| run_id | `openclaw agent --json` runId | direct |
| session_key | `agents/video-factory/sessions/*.jsonl` matched by message_id | mask |
| receipt | `input/feishu/<message_id>/attachment-NNN/receipt.json` | mask stored_path, chat_id, sender_id |
| router model call | session trajectory `model_call*` events | count + model name |
| pre-ingest understanding | session trajectory `[Image]`/`[Audio]`/`[Video]` block count | should be 0 |
| router images | session trajectory `media://inbound` / image content in llm_input | should be 0 (refs only, no pixels) |
| ingest_attachment call | session trajectory tool_call events | count |
| GPU lock | `state/gpu_locks/*.lock` | lock_name + job_id |
| analysis | `jobs/<job_id>/analysis.json` | status + error_code |
| final reply | session `message` tool call / reply target | feishu:group:<target-id> |

## Security invariants (observability does not lower boundaries)

- The tool only READS receipt/session/lock/analysis files; it does not modify config, does not send messages, does not restart the Gateway.
- All identifiers (message_id, chat_id, sender_id, stored_path, session_key) are masked or hashed in the trace.
- No file body content, image base64, video frames, tokens, file_keys, API keys, or full user ids are recorded.
- The tool does not bypass the ingest_attachment validation or the scope deny.

## Real-Channel tracing (when user uploads)

When the user runs the R0-R5 sequence, the real `message_id` from each Feishu event will be traced with `python scripts/observability/trace_event.py <real_message_id>`. The same metrics will be captured, proving:
- `pre_ingest_media_understanding_count = 0` for the target group (scope deny生效)
- `router_images_count = 0` (router received only `media://inbound/*` refs, not pixels)
- `raw_media_path_forwarded = false`
- `ingest_status = quarantined`
- `router_model = mimo-v2.5-pro`
- (for R3/R4/R5) `analysis_agent_call_count >= 1`, `gpu_lock_acquired = true` (for audio/video)

## Evidence

- `reports/P0_REAL_CHANNEL_EVENT_TRACE.json` (demo trace)
- `scripts/observability/trace_event.py` (reusable trace tool)
- `scripts/observability/demo_trace.py` (demo driver)

## Finding (behavioral, not a blocker)

The demo turn showed the agent called `ingest_attachment` multiple times (N retries) before completing. Idempotency held (1 receipt, `already_ingested` on retries). This suggests the agent's flow rules could be tightened to avoid redundant tool calls, but it is not a security or correctness issue. Noted for P1 refinement.
