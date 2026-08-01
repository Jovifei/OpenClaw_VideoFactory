# Next User Action

## Current — P0-PROJECT-GATEWAY-DEVICE-PAIRING-REQUEST-047

Authorize a **Project-identity-provisioning-only** task. It will create a fresh Project-owned official Ed25519 identity in `C:\Users\Admin\.openclaw-video-factory\device`, verify the public-key/device-id consistency without displaying key material, and stop. It will not connect to the Gateway or request pairing.

## Current — P0-PROJECT-GATEWAY-OFFICIAL-DEVICE-AUTH-046

Authorize exactly one fresh **Project pairing-request-only** connection after the ACL repair. It will create a Project-owned Ed25519 identity, submit at most one request for `operator.read`, record only a redacted request reference, and stop for approval.

It will not restart OpenClaw, use or change the shared Gateway token, start the Project Gateway, change Core Feishu, send Feishu traffic, or perform a migration.

Current result: `WINDOWS_SERVICE_AUTH_REPAIR_BLOCKED:METADATA_OK_BUT_RUNTIME_TOKEN_DIFFERS`.

Authorize one narrow credential-source maintenance task: reconcile the
OpenClaw CLI control credential with the running Gateway authentication source
using a secure host mechanism, then perform one health-only Adapter handshake
and one read-only structured `channels.status` check. Do not provide a token in
chat and do not retry installation, restart, Core lifecycle, Project Gateway,
or zhongshu migration first.
