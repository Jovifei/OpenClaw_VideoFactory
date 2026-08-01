# P0 Evidence Index

| Evidence | State | Use |
|---|---|---|
| `reports/CODEX_CLI_UPGRADE_DEFERRED.json/.md` | current | Authoritative CLI deferral, resume phrase and blocked gates |
| `reports/CODEX_CLI_UPGRADE.json/.md` | superseded | Earlier canonical-upgrade verification failure; retained as history only |
| `reports/CODEX_CLI_INSTALL_SOURCE.json/.md` | historical-valid | npm/WindowsApps source discovery; WindowsApps remains excluded from project automation |
| `reports/CODEX_CLI_CANONICAL_ENTRY.json/.md` | historical-valid | Canonical npm `codex.cmd`, last verified current version and planned target |
| `reports/P0_FIXTURE_PREPARATION.json/.md` | current | Non-sensitive TXT/PNG/MP4/cover Fixture hashes and media properties |
| `tests/fixtures/feishu_delivery/fixture_manifest.json` | current | File-level manifest, generation commands, hashes and sensitivity flags |
| `reports/P0_MEDIA_PATH_REMEDIATION_AUDIT.json/.md` | current | Existing 8/8 Pester result and 14 fixture-backed validation results; PNG MIME gap disclosed |
| `reports/FEISHU_MEDIA_TEST_READINESS.json/.md` | current | Live exact Binding, group override, allowlist count and local-consumer readiness |
| `reports/FEISHU_SINGLE_CONSUMER_DIAGNOSTIC.json/.md` | superseded | Earlier diagnostic; retained for historical fault context |
| `reports/READY_FOR_FEISHU_MEDIA_TEST.md` | current | Exact three-file user upload procedure |
| `reports/FEISHU_EGRESS_TEST.json/.md` | current-blocked | Profile/bot/membership passed; dry-run batch incomplete; actual sends zero |
| `reports/OPENCLAW_EXISTING_AGENTS_REGRESSION.json/.md` | current | Gateway, Agent, Binding, Channel, Cron, Skill, Git and Secret regression |
| `reports/gate_p0.json/.md` | historical-only | Old Gate artifacts dated 2026-07-13; no final Gate was run in N0–N7 |

All existing files under `reports/command_logs/` are retained. Historical failure records were not deleted. Child-agent summaries, timeouts and partial results are excluded from acceptance evidence; only parent-executed commands and file-backed artifacts are indexed above.
