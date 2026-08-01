# P0 RPC Operator Setup 037

## Required operator action

Set `OPENCLAW_GATEWAY_TOKEN` only in the approved secure local execution
environment that will launch the Project Gateway preflight. Do not send the
value to Codex, paste it into chat, place it in YAML/JSON, write it to a
PowerShell parameter, or include it in a command line.

An inherited environment variable is the implemented provider. A Windows
Credential Manager or approved Secret-provider adapter is compatible with the
provider contract but is not configured by task 037.

## Verification during an authorized pre-window check

1. Confirm only that the token is present; do not display its value.
2. Run the approved `production-preflight` path and require `RPC_READY`,
   authenticated health, and `ready=true`.
3. Confirm Project Gateway JSON logs contain no token marker or value.
4. Confirm the launcher post-start command-line guard reports
   `command_line_secret_safe=true`.

Missing Token must remain `RPC_CREDENTIAL_REQUIRED`; rejected/unavailable Token
must remain `RPC_AUTH_FAILED`. Neither condition permits a fallback or T0.
