# P0 Single-Group Router Rollback (007)

Status: **not triggered** (no anomaly; production config valid and smoke-verified).

## Backup

- `C:\Users\Admin\.openclaw\openclaw.json.bak-007-20260718-092424`
- SHA-256: `c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d` (baseline)

## Rollback order (if triggered)

1. Restore `openclaw.json` from the backup (`Copy-Item` the `.bak-007-*` file over `openclaw.json`).
2. Remove the 3 analyzer agent dirs (`C:\Users\Admin\.openclaw\agents\video-factory-{image,audio,video}-analyzer\`) and their workspaces (`workspace-vf-{image,audio,video}`).
3. `openclaw config validate` (expect exit 0 with baseline config).
4. `openclaw gateway restart` (one emergency restart).
5. Verify: config SHA == `c7098b22...5660d`; 14 agents; 14 bindings; 4 cron; 1 target-group consumer; video-factory model == `mimo-v2.5`; ordinary text path works.
6. Remove the `ingest` MCP server artifacts (`scripts/mcp_ingest_attachment.py`, `scripts/run_ingest_safe.ps1` may stay as they are not referenced by the baseline config; the `mcp.servers.ingest` entry is removed by restoring the backup config).

## Rollback triggers (section 十九/二十)

- target-group attachment understood before ingestion (an `[Image]`/`[Audio]`/`[Video]` block appears before `ingest_attachment`).
- router receives raw attachment pixels.
- router directly reads the attachment.
- binding count != 14.
- consumer count > 1.
- ordinary text path broken.
- other 13 agents affected.
- unauthorized config semantic change.

## Not triggered

The smoke (text + PNG) passed; invariants hold; no anomaly. Rollback was not needed. The backup is retained for safety.

## No second approach

Per task, no second production modification approach is attempted. The 007 approach (scope deny + text-only router + tool allowlist + ingest_attachment + 3 binding-less analyzers) is the single approach; corrections within it (group:plugins removal, bundle-mcp allow) were refinements, not a different approach.
