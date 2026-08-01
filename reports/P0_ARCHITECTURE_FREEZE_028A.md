# P0 Architecture Freeze 028A

## Freeze result

`P0_ARCHITECTURE_FROZEN_READY_FOR_REAL_ENV`

This is a documentation-only freeze of the Project Feishu Gateway baseline. It does not authorize real-environment execution, production migration, or any runtime/configuration change.

## Frozen architecture

```text
Feishu Gateway
      |
      v
OpenClaw RPC
      |
      v
video-factory
      |
      v
analysis_request
      |
      v
Analyzer
```

### Layer responsibilities

- Feishu Gateway owns the Feishu channel boundary, event validation, dedupe, attachment ingress handoff, ticket/callback validation, and outbound channel delivery.
- OpenClaw RPC is the boundary into the OpenClaw execution layer.
- `video-factory` remains the Router/Orchestration path for text and approved requests.
- `analysis_request` is the durable admission contract for analysis.
- Analyzer performs media compute only after the approved request contract is present.

## Explicit no-regression decisions

The following alternatives are permanently excluded from the frozen architecture:

- Reply-as-a-new-Gateway-routing solution.
- Slash Command solution.
- Router parsing of card actions as a replacement for the durable analysis contract.
- `inbound_claim` solution.

The existing durable reply/text contract is retained where required by the project rules. This freeze does not create a second intent protocol and does not change the current Binding.

## Freeze boundary

No Gateway code, OpenClaw core, Binding, Agent, Cron, OAuth, model, production configuration, or `PROJECT_STATUS.yaml` was changed by 028A.
