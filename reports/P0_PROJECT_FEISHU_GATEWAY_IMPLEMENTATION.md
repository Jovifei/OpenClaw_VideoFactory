# P0-019 implementation

Status: `PROJECT_FEISHU_GATEWAY_BLOCKED`.

Completed offline:
- Feishu message/attachment/card schemas under `schemas/feishu_gateway/`.
- Offline payload contract in `services/feishu_gateway/runtime.py` with fail-closed transport mapping.
- Deterministic event dedupe and text/attachment/card adapter boundaries in `services/feishu_gateway/service.py`.
- Offline migration rehearsal in `experiments/feishu_gateway_migration/rehearsal.py`.
- Focused tests and schema checks: `25` total tests passed (no failures), including explicit signature reject and state redaction assertions.

Not yet proven in this phase:
- Official Lark SDK presence.
- Official OpenClaw Gateway RPC production method.
- Production single-consumer cutover and production P0 final gate.

No production state changed, and no real Feishu credentials/network were used.
