# P0 Windows Gateway service audit 045

## Read-only commands

- `openclaw gateway status --no-probe --deep --json` — structural parse passed.
- `openclaw gateway status --deep --json` — structural parse passed; Gateway RPC
  probe is healthy and service is loaded.

## Sanitized owner metadata

| Field | Result |
| --- | --- |
| Service owner | Windows Scheduled Task |
| Task | `OpenClaw Gateway` |
| Task state | `Ready` |
| Launcher | one existing `gateway.cmd` shim; content not retained |
| Run context | current interactive user, limited run level |
| Windows Service duplicate | none |
| Matching Scheduled Task count | 1 |
| Gateway listeners | 1 |
| Gateway process | `node.exe` |
| Task/launcher embedded token assignment | false |
| Task/launcher profile/config/state/wrapper override | false / false / false / false |
| Actual Gateway command contains current token | false |
| Current configuration path / state directory | default / default |
| Current CLI version | `2026.7.1` |

No Task XML, launcher content, configuration body, environment dump, token, or
path value is included in this report.

## Drift decision

The official service audit reports `gateway-service-version-mismatch` with one
service-audit issue. Current CLI version is `2026.7.1`; no alternative
profile/state/config/token override or duplicate install was found.

`SERVICE_BINARY_VERSION_DRIFT`

This is the concrete, authorized condition for a one-time private backup and
official `gateway install --force --json` regeneration. The backup must finish
before that command is run.
