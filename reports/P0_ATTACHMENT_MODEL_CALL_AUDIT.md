# P0 attachment-to-model audit

Status: `failed_pre_ingest_model_analysis_confirmed`

The real PNG event reached the `video-factory` session with Channel-supplied `MediaPath`/`MediaPaths` and `MediaTypes=image/png`. The trajectory then recorded `context.compiled` and `prompt.submitted` before the session recorded one `image` tool call and one image-tool result. No invocation of `scripts/07_ingest_inbound_media.ps1` exists for the message; no original copy or receipt was created.

The first verified injection point is the installed OpenClaw core reply pipeline: `get-reply-CknL88Yv.js` calls `applyMediaUnderstandingIfNeeded` when `hasInboundMediaForUnderstanding(finalized)` is true. `inbound-media-BABB4m9T.js` makes that predicate true when inbound media fields are present. This precedes the project script and cannot be corrected by prompt or Skill wording.

OpenClaw exposes `inbound_claim` as a pre-agent interception point with the required metadata, but enabling a workspace plugin requires a global `plugins.allow`/`plugins.entries` change and Gateway restart. That change is outside this authorization.

The failed PNG remains permanently failed evidence and is not eligible for a receipt or an `PNG_INGRESS_OK` marker.
