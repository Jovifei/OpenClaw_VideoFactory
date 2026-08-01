# P0 current status V27

`WINDOWS_SERVICE_AUTH_REPAIR_BLOCKED:METADATA_OK_BUT_RUNTIME_TOKEN_DIFFERS`

The Windows Gateway service registration is now structurally healthy: the
official audit passes, the service is loaded, the official RPC probe passes,
and exactly one Gateway listener is present. The one authorized managed restart
completed normally.

Runtime authentication remains blocked. The maintenance-child Adapter received
`rpc_unauthorized` / `INVALID_REQUEST`, while a current CLI control request
reported a token mismatch. Core zhongshu ownership/count is consequently still
unknown. Project Gateway remains stopped and `PROJECT_STATUS.yaml` was not
changed.
