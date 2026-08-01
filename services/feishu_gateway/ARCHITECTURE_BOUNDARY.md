# Project Feishu Gateway architecture boundary

## Channel Layer — `services/feishu_gateway`

May receive Feishu events, verify signatures and identities, de-duplicate, download only the event-owned attachment into the existing ingress flow, send cards/replies, build an OpenClaw request, and maintain a local consumer lease.

It must not call a model, Analyzer MCP, whisper, ffmpeg, GPU workload, arbitrary filesystem path, OpenClaw configuration API, or Agent-management API.

## Orchestration Layer — OpenClaw `video-factory`

Owns the OpenClaw session, deterministic analysis-request admission, Router policy, and dispatch to the matching Analyzer. A verified card action reaches this layer only as a bounded `analysis_request` context carried by the OpenClaw request; it is not a Gateway-side Analyzer call.

## Compute Layer — Analyzer MCP

Owns image/audio/video computation and can read only the quarantined receipt/stored copy under its existing four-field contract. It has no Feishu connection and no direct reply capability.

## Enforcement

- Signature verification is required by default on message and card ingress.
- Gateway RPC requests are validated against `policy.py` and cannot select model, Analyzer, GPU, tool, or a non-`video-factory` Agent.
- `GatewayPayloadBuilder` derives tenant/chat/sender/thread-isolated session keys without exposing raw identifiers in the key.
