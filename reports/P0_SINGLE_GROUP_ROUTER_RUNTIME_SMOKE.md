# P0 Runtime Smoke (007)

Task: `P0-SINGLE-GROUP-MEDIA-ROUTER-007`
Method: Gateway RPC (`/tools/invoke`) + `openclaw agent` turns + staged inbound files. No real Feishu upload.

## Results

| Smoke | Method | Result |
| --- | --- | --- |
| Text | `openclaw agent --agent video-factory -m "..." --json` | PASS: status ok, reply "PONG", model `mimo-v2.5-pro`, model_call_count=1 |
| PNG attachment | `openclaw agent` turn -> call `ingest_attachment` on staged PNG | PASS: model `mimo-v2.5-pro` (no pixel read), receipt written, quarantined=true, content_parsed=false, sha256 present, analysis_allowed=true |
| MCP server | `openclaw mcp probe ingest --json` | PASS: 1 tool `ingest__ingest_attachment` live |
| Audio/MP4 | (same ingest path as PNG) | not individually event-smoked; analyzers offline-tested 11/11; deferred to real Feishu event |
| Failure cases | `test_ingest_attachment_core.py` | PASS: 17/17 (MIME/signature/path/oversize/unauthorized/unsafe-filename/missing/idempotency) |
| pre-ingest understanding=0 | config + behavior | config-verified (scope deny + text-only model + tool policy); behavior-consistent (router called ingest, not image understanding) |

## Text smoke detail

```
openclaw agent --agent video-factory -m "007 smoke: reply with exactly PONG and nothing else" --json
-> status: ok, summary: completed
-> result.payloads[0].text: "PONG"
-> result.meta.agentMeta.model: "mimo-v2.5-pro"
-> usage: input 17784, output 21 (single model call)
```

## PNG attachment smoke detail

A PNG fixture was staged in the real inbound root (`~/.openclaw/media/inbound/smoke_png_007.png`). An `openclaw agent` turn instructed the router to call `ingest_attachment` with the staged path and the real (config-derived) chat_id/sender_id. The router:

- used `mimo-v2.5-pro` (text-only; did NOT read image pixels)
- called `ingest_attachment`
- the tool returned `status: quarantined`, `content_parsed=false`, `quarantined=true`, `sha256` present, `analysis_allowed=true`
- the receipt landed at `input/feishu/<message-id>/attachment-000/receipt.json` (multi-attachment layout)
- on-disk receipt verified: `quarantined=True`, `content_parsed=False`, `sha256` present

This proves the production path: router (text-only) -> ingest_attachment MCP tool -> PS safety core -> quarantine receipt.

## Platform limitations (honest gaps)

1. **`/tools/invoke` does not expose MCP tools.** Direct Gateway RPC returns 404 for `ingest__ingest_attachment` (and bare/`bundle-mcp__` variants). Built-in tools (`session_status`) work via `/tools/invoke`. MCP tools are loaded per-agent-session lazily; a full `openclaw agent` turn DOES load and call them (the PNG smoke proves this). This is an OpenClaw platform behavior, not a config error.
2. **No fake Channel event injector.** A real Feishu attachment event (with `media://inbound/*` refs) could not be simulated without either a real user upload (forbidden this round) or a Channel test harness not available in this setup. The scope-deny (pre-ingest understanding=0) is therefore config-verified and behavior-consistent, but not measured as a live `applyMediaUnderstandingIfNeeded` call count for a real Channel event.
3. **Audio/MP4 event smoke deferred.** The ingest path is identical to PNG (proven). Audio/video analyzer dispatch is offline-tested (11/11). A real audio/MP4 Feishu event smoke is the user's next validation step.

## Metrics

| Metric | Value |
| --- | --- |
| router_model_call_count | 1 |
| ingest_tool_call_count | 1 |
| raw_media_path_forwarded | 0 |
| stored_path_forwarded | 1 |
| binding_count | 14 |
| consumer_count | 1 |
| pre_ingest_media_understanding_count | 0 (config-verified + behavior-consistent) |

## Anomaly / rollback

None. Config valid, invariants hold post-smoke, Gateway healthy.

## Evidence

- `scripts/smoke_007_ingest.py` (the /tools/invoke attempt - documents the platform limitation)
- `scripts/smoke_007_attachment.py` (the passing `openclaw agent` attachment smoke)
- `reports/P0_SINGLE_GROUP_ROUTER_RUNTIME_SMOKE.json`
