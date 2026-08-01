# P0 safe restart root cause final 045

043B recorded one `gateway restart --safe --json` exit `1`, unchanged PID, and
no retained structured result/stderr. Its timestamps are also unavailable, so
the corresponding log window cannot be correlated without guessing.

Installed OpenClaw 2026.7.1 source resolves `--safe` directly through the
authenticated `gateway.restart.request` RPC
(`lifecycle-CciWmoyE.js:209-227` → `call-dBhJbczL.js:740-741`). The same
injected maintenance child subsequently reached that authentication boundary on
the unchanged runtime and returned `AUTH_TOKEN_MISMATCH` in the v4 Adapter.
No service-manager path is used by `--safe`; plain managed restart is separate.

Classification: `SAFE_RESTART_RPC_AUTH_REJECTED`.

The original CLI stderr is unavailable, so this conclusion is source-path plus
same-child authentication evidence, not a reconstructed raw log. This task does
not retry `--safe`.
