# P0 Gateway lifecycle owner 044

| Field | Observed value |
| --- | --- |
| Owner | Windows Task Scheduler |
| Task | `OpenClaw Gateway` |
| Task state | `Ready` |
| Launcher basename | `gateway.cmd` |
| Task principal | present, redacted |
| Logon / run level | `Interactive` / `Limited` |
| Windows Service owner | none found |
| Listener | one loopback listener on `18789` |
| Gateway process | `node.exe`, PID `13144` |
| Parent process | unavailable (launcher has exited) |
| Task arguments contain token | false |
| Process command has token/profile/state/config override | false / false / false / false |

Installed OpenClaw source uses the Windows scheduled-task handoff for a
supervised restart (`restart-CaWcmhHJ.js:20-108`). The officially supported
ordinary managed target is therefore `openclaw gateway restart --json`, not a
manual process chain. It was not executed because the 044 preflight did not
qualify it.
