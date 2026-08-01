# P0-018 open-source reference audit

Five shallow source clones are locked in `P0_OPEN_SOURCE_REFERENCE_LOCK.json`. No package manager, installer, application entry point, real credential, or Feishu connection was used.

Adopt patterns only: official SDK WebSocket event dispatch, persistent replay/idempotency state, a local trusted bridge envelope, and a single WS owner. Do not copy `cc-connect` media base64 forwarding, its multi-platform fan-out, ComfyUI's process-local replay state, or Hermes's full runtime.

The target implementation must retain project-owned deterministic ingress and Analyzer contracts; third-party source is reference material only.
