# P0 Windows Gateway service-auth repair 045

## Terminal status

`WINDOWS_SERVICE_AUTH_REPAIR_BLOCKED:METADATA_OK_BUT_RUNTIME_TOKEN_DIFFERS`

The official Windows service registration is healthy after repair, but the
runtime authentication paths are not mutually usable. No token value,
derivative, command-line argument, configuration value, or credential-store
content is recorded here.

## Authorized work performed

- Preflight passed: one Core Gateway listener, zero Project Gateway processes,
  no active/unknown task, and the configuration SHA-256 matched the 030
  baseline.
- Concrete registration drift was classified as `SERVICE_BINARY_VERSION_DRIFT`.
  A private, local rollback package was created at the approved state-root
  backup location; it contains four files and zero credential candidates.
- `openclaw gateway install --force --json` was invoked once in a maintenance
  child. Its structured result timed out, so it is not represented as a command
  success. Post-command evidence proves the resulting registration changed,
  the official service audit passed, and no installer process remained.
- `openclaw gateway restart --wait 30s --json` was invoked once. It returned
  exit code 0 with `restarted`; PID changed from 67516 to 45180. The command
  elapsed time was 31.505 seconds; port outage duration was not independently
  sampled.

## Post-restart evidence

| Check | Result |
| --- | --- |
| Gateway service loaded | pass |
| Official RPC probe | pass |
| Service configuration audit | pass |
| Port 18789 listeners | 1 |
| Project Gateway processes | 0 |
| Config SHA-256 | `D6A97F1025698C08F086C1EE565E1AAC1AD30116037E4F135688EDBB1171BE8C` (matches 030) |
| Agents / Bindings / Cron | 17 / 14 / 4 preserved by unchanged baseline configuration SHA; direct runtime enumeration remains authentication-blocked |
| Core zhongshu consumer | `unknown`; no ownership/count claim made |

No recovery start was needed. No Core Feishu stop/start, Project Gateway start,
migration, Feishu traffic, configuration mutation, Agent/Binding/Cron/OAuth/model
change, commit, push, or tag occurred.

## Health-only RPC result

The injected maintenance child had the token and its command line did not.
The Adapter performed only the protocol connect path and received
`rpc_unauthorized` / `INVALID_REQUEST` before it could request `health`.
It created no business session and made no Agent, tool, analyzer, or Feishu
call. Separately, the current OpenClaw CLI classified its authenticated control
request as a token mismatch. This is runtime-source divergence, not a reason to
repeat installation or restart.

## Verification

- Standard-library focused tests: 31 passed.
- `.venv` dependency integrity: `pip check` passed.
- The configured `pytest` runner is absent from the project `.venv`; no
  dependency was installed for this task.
- Gateway and maintenance-child command lines contained no token; the private
  backup scan found zero credential candidates.
