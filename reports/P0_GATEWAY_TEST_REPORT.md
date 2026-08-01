# Gateway test report

Implementation 019 offline coverage is green:

- `tests.test_project_feishu_gateway.py`: 13/13
  - text routing, attachment ingress fallback, card action flow, duplicate filtering, reconnect dedupe restoration, invalid signature reject, state redaction assertions, and fail-closed transport.
- `tests.test_feishu_gateway_runtime.py`: 6/6
  - payload contract, payload rejection, retry/until-success, transport fail-closed, code mapping, malformed status handling.
- `tests.test_feishu_gateway_poc.py`: 7/7
  - ingress quarantine only, card->analyzer bypass, expiry/reconnect/replay, wrong operator/chat binding, timeout behavior.
- Schema parse checks: `schemas/feishu_gateway/{message,attachment,card}_event.schema.json` all valid JSON.

All tests use injected handlers only; they do not prove official SDK connectivity, real attachment download, production RPC transport, or real Feishu delivery.
