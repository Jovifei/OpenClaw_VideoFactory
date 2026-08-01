# P0 Feishu Card Production Smoke (015)

Status: NOT RUN.

No card was sent, no callback was simulated, no ticket was consumed, no Analyzer was called, no card was updated, and no outbound message was issued. This is intentional: the supported direct handler path is unresolved and code/config changes were not authorized.

The future fake smoke must prove PNG, audio, and video card construction; signed callback validation; operator/chat/ticket gates; three-second acknowledgement; atomic consume; one matching Analyzer; card success/failure update; original-group reply; duplicate-click idempotency; and unchanged receipt. It must run before any real R3 upload.
