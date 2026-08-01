# P0 Code Ownership Map 028A

## Ownership table

| Layer / owner | Owns | Must not own or call |
| --- | --- | --- |
| Feishu Gateway | Feishu channel connection, event receipt, signature/identity validation, dedupe, attachment ingress handoff, ticket/callback validation, card update/reply delivery | Agent logic, session state semantics, model calls, Analyzer calls, GPU, ffmpeg/whisper/mimo, arbitrary filesystem or config mutation |
| OpenClaw | Agent, session, tool policy, RPC boundary, orchestration and lifecycle ownership | Feishu Gateway compute, direct media analysis, duplicate channel consumer |
| `video-factory` | Text Router/orchestration and creation/forwarding of approved `analysis_request` work | Channel ownership, direct Feishu second consumer, direct model/Analyzer bypass |
| Analyzer | Image/audio/video compute against an approved request and quarantined stored media | Feishu connection, Router ownership, raw inbound channel identifiers, arbitrary media instructions |

## Frozen call direction

```text
Channel Layer: Feishu Gateway
        -> OpenClaw RPC
        -> video-factory orchestration
        -> analysis_request admission
        -> Analyzer compute
```

No reverse or cross-layer call may be introduced without a new architecture decision and change request. In particular, Gateway must not call Analyzer, model providers, GPU tools, ffmpeg, whisper, or an Analyzer MCP directly.
