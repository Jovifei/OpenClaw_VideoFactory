# Gateway RPC Runtime Gap

Status: `RPC_RUNTIME_VERIFICATION_BLOCKED`.

`services/feishu_gateway/rpc_client.py` implements only an injected, fail-closed transport boundary. It supplies `send_message`, `send_attachment_event`, `create_session`, `send_agent_request`, bounded timeout/retry, normalization, and a connection check. With no injected transport it returns `rpc_runtime_verification_blocked`; it never guesses an endpoint, bearer format, WebSocket frame, cancellation, or streaming protocol.

Live protocol/authentication verification requires a separately approved maintenance-window probe against the official OpenClaw RPC surface. This task did not make that connection.
