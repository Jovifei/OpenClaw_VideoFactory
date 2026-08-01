# P0 Single-Group Router Migration (007)

## Pre-change baseline

- `openclaw.json` SHA-256: `c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d`
- 14 agents, 14 bindings, 4 cron, 1 target-group consumer
- video-factory durable model: `mimo-v2.5` (multimodal)
- target-group session override: `mimo-v2.5-pro` (auto, timeout)
- `tools.media`: absent
- video-factory tools: `exec.mode=full`, no allow/deny

## Backup

- Timestamped copy: `C:\Users\Admin\.openclaw\openclaw.json.bak-007-20260718-092424`
- Backup SHA-256 verified identical to baseline.
- Analyzer agent dirs + workspaces created before config edit.

## Apply sequence

1. `scripts/apply_007_config.py` - read real target-id/sender-id from config; applied 6 changes (tools.media scope, video-factory model, tools, subagents, 3 analyzers, mcp.servers.ingest).
2. `openclaw config validate` - initial run FAILED (subagents schema is strict: maxConcurrent/maxChildrenPerAgent/maxSpawnDepth not allowed at agent level; analyzer exec.mode "off" not in allowed enum).
3. Fix: subagents -> only `allowAgents`+`requireAgentId`; analyzer exec.mode -> `deny`. Restored backup, re-applied, validated OK.
4. `openclaw gateway restart` (restart #1).
5. Post-restart invariants verified (17 agents, 14 bindings, 4 cron, 1 consumer, 3 analyzers no binding, other 13 unchanged).
6. Smoke: `/tools/invoke` returned 404 for the MCP tool -> diagnosed `group:plugins` deny overriding the allow.
7. Fix: removed `group:plugins` from deny (`fix` script). Restart #2.
8. Smoke: still 404 -> diagnosed explicit allow lists don't implicitly allow MCP tools.
9. Fix: added `bundle-mcp` to allow. Restart #3.
10. Smoke: `openclaw agent` text turn PASS; `openclaw agent` attachment turn PASS (ingest_attachment called, receipt written).

## Post-restart verification (12 items)

| # | Check | Result |
| --- | --- | --- |
| 1 | Gateway port 18789 reachable | PASS |
| 2 | `openclaw config validate` | PASS (exit 0) |
| 3 | video-factory durable model | `mimo-v2.5-pro` |
| 4 | tools.media scope (image/audio/video) | present, deny target group, default allow |
| 5 | video-factory tool policy | allow=11 (incl bundle-mcp), deny=10, exec removed |
| 6 | ingest_attachment tool visible | `openclaw mcp probe ingest` -> 1 tool |
| 7 | 3 internal analyzers visible | in agents.list |
| 8 | internal analyzers have no binding | has_binding=False (all 3) |
| 9 | bindings count | 14 |
| 10 | cron count | 4 |
| 11 | target-group consumer count | 1 |
| 12 | other 13 agents config hash | unchanged (only video-factory model changed) |

## Restart budget

3 restarts used (1 planned + 2 smoke-driven fixes). The task's one-restart ideal was exceeded by two corrective restarts necessitated by smoke-discovered tool-policy details. Each fix was validated before restart. Future refinements should batch changes.

## Other 13 agents regression

`verify_007_invariants.py` compares model+tools of all pre-existing agents against the backup. Only `video-factory` model changed (intended). All other 12 non-new agents: 0 mismatches.
