# P0 Dependency Gate Fix 039

## Result

`DEPENDENCY_GATE_READY`

The Project OpenClaw RPC Adapter imports `websockets.sync.client`, but the
package was absent from both `requirements-bootstrap.txt` and the project
`.venv`. This prevented the adapter from opening a WebSocket before RPC
authentication could be attempted.

039 adds the one direct, pinned requirement `websockets==16.1.1` and extends
the existing package gate import to `yaml`, `jsonschema`, and
`websockets.sync.client`. No business/Gateway/Router/Analyzer code changed.

## Artifact and installation boundary

| Field | Value |
| --- | --- |
| Package | `websockets` |
| Version | `16.1.1` |
| Wheel | `websockets-16.1.1-cp312-cp312-win_amd64.whl` |
| Source | PyPI simple index |
| Captured directory | `E:\Claude_allow\Download\p0-039-websockets-20260726` |
| SHA-256 | `B436F6EC4FC3A6B4237C84D3F83170ED2B40BB584222F0AC47A0C8A5921980C7` |
| License | `BSD-3-Clause` |

The wheel was downloaded once to the permitted directory, then installed into
`E:\project\OpenClaw_VideoFactory\.venv` from that local artifact with
`--no-index --no-deps`. No global/system Python or OpenClaw environment was
changed.

## Verification

| Check | Result |
| --- | --- |
| `import websockets.sync.client` | PASS, `16.1.1` |
| Package gate import command | PASS |
| Package gate PowerShell syntax | PASS |
| `python -m pip check` | PASS |
| Schema tests | PASS, 88/88 |
| Python tests | PASS, 269/269 in isolated module batches |
| Scoped secret candidate files | 0 |
| Project Gateway runtime processes | 0 |

## Shared package acceptance boundary

The generic `90_acceptance_gate.py --gate package` is **not accepted as this
task's evidence**. Its existing scan includes third-party and Shadow trees and
an already-stale `SHA256SUMS.txt`, so it fails for worktree-wide reasons outside
this single dependency repair. This task neither changes those trees nor claims
a P0/package release pass.

## Stop boundary

No live RPC preflight was retried after the install. No Core Feishu action,
Project Gateway start, Feishu traffic, Binding/Agent/Cron/configuration change,
commit, or push occurred.
