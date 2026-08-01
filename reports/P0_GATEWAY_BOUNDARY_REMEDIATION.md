# P0 Gateway Boundary Remediation (024)

Status: `PASS_OFFLINE_ARCHITECTURE`

## Corrected boundary

```text
Feishu event/card
  -> Project Gateway Channel Layer
  -> OpenClaw request (video-factory only)
  -> video-factory orchestration
  -> analysis_request
  -> matching Analyzer Compute Layer
```

`ProjectFeishuGateway.card()` now verifies the ticket and submits a bounded `analysis_request` context through its injected OpenClaw request callable. It no longer owns `request` or `analyze` dependencies and cannot call Analyzer MCP, model, whisper, ffmpeg, or GPU work.

The offline fixture was remediated identically. A source-level test confirms neither Channel Layer module contains `self.analyze`, `analyzer_mcp`, or `subprocess`; the direct-compute scan found zero matches.

## Layer ownership

| Layer | Owner | Permitted responsibility |
| --- | --- | --- |
| Channel | Project Gateway | event ingress, signature/identity, quarantine ingress, ticket, OpenClaw request, outbound reply/card |
| Orchestration | OpenClaw video-factory | session, deterministic analysis-request admission, Router policy, Analyzer dispatch |
| Compute | Analyzer MCP | bounded work against the quarantined receipt/stored copy |

The complete contract is [ARCHITECTURE_BOUNDARY.md](E:/project/OpenClaw_VideoFactory/services/feishu_gateway/ARCHITECTURE_BOUNDARY.md).

## Evidence

- `tests/test_project_feishu_gateway.py`: attachment/card creates an RPC request but no compute call.
- `tests/test_feishu_gateway_poc.py`: card submits only the bounded context.
- `tests/test_feishu_gateway_architecture_024.py`: direct-compute prohibition.
- Full Python regression: 171/171 PASS; Pester: 101/101 PASS.

No Feishu connection, Binding modification, Gateway restart, Agent/Cron/OAuth change, or production RPC request occurred.
