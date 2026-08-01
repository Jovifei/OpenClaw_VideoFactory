# P0 Route A — existing Feishu account with exact group peer binding

Target group and identities are redacted in this report: `oc_***1555`, `zho***`, and `ou_***`.

## Applied configuration

- A current global config backup was created outside the repository; source and backup SHA-256 matched.
- The existing `zhongshu` Feishu account was reused without reading, copying, or printing its App Secret.
- The 13 existing account-level bindings were preserved. One additional exact route was added: `feishu + zhongshu + group oc_***1555 → video-factory`.
- `zhongshu` retains its old account fallback and old group allowlist. The new group has its own explicit allowlist entry, one configured owner sender, `enabled: true`, and `requireMention: true`.
- `video-factory` now has `xiaomimimo/mimo-v2.5` with `xiaomimimo/mimo-v2.5-pro` fallback, matching zhongshu. An earlier Codex model setting failed at real embedded runtime and was removed. No existing agent model was changed.

## Command evidence

| Step | Result | Evidence | Risk and rollback |
|---|---|---|---|
| Backup and baseline | Backup hashes matched; bindings, account structure, and channel probe exited 0; target peer was absent. | `74_route_a_config_backup.txt`, `75_route_a_*.txt`, `76_route_a_*.txt` | Restore the external timestamped backup only with explicit approval. |
| Live Schema lookup | Gateway `config.schema.lookup` verified exact peer fields and per-group controls. Initial PowerShell-to-CMD quoting attempts failed before reaching the RPC; CMD-isolated retry succeeded. | `76_route_a_live_schema.txt`, `78_route_a_*.txt`, `78a_route_a_*.txt`, `78b_route_a_schema_lookup_cmd_quoting_test.txt`, `78c_route_a_groups_schema_lookup.txt`, `80_route_a_remaining_schema_lookups.txt` | Do not infer field names from documentation alone. |
| Route patch | First local deserialization guard stopped before dry-run; corrected dry-run passed schema/resolvability. Apply exited 0 with five updates. | `81_route_a_patch_dry_run.txt`, `81a_route_a_patch_dry_run_retry.txt`, `82_route_a_patch_apply.txt` | Binding array was explicitly replaced only after preserving all 13 baseline entries; restore external backup to revert. |
| Route regression | Config validation, Gateway restart/status, binding re-read, probe, relevant log inspection, and post-apply doctor all exited 0. | `83_route_a_validate_restart_and_logs_help.txt`, `84a_route_a_post_apply_regression_retry.txt`, `85a_route_a_openclaw_doctor_post_apply_retry.txt` | Existing global doctor warnings remain visible; none was changed to force a pass. |
| Codex runtime config | `openai/gpt-5.3-codex` was reported available. Schema dry-run and apply preserved the other 13 agents; validate/restart/readback exited 0. | `88_route_a_lark_and_codex_runtime_inventory.txt`, `89_route_a_codex_model_schema_lookup.txt`, `90a_route_a_codex_model_patch_dry_run_retry.txt`, `91_route_a_codex_model_patch_apply.txt`, `92_route_a_codex_model_verify.txt` | Restore external backup to remove the per-agent model override. |
| lark-cli dry-run | No send was attempted; named profile is not configured. Project scripts were made compatible with the installed CLI and no longer auto-create a new app. | `86_route_a_lark_dry_run_and_auth_status.txt`, `87_route_a_lark_cli_current_help.txt` | User must configure the named profile interactively with existing-bot credentials; do not copy OpenClaw secrets. |

## Real inbound correction

User-provided logs exposed a real sender mismatch and a second bot delivery. The correction was Schema-dry-run, applied, validated, restarted, and read back: `zhongshu` now allows the real group sender while `hubu` is disabled only for this group. The active `video-factory` lark-cli bot profile then passed no-send dry-run previews for all four outbound media types. Evidence: `reports/FEISHU_ROUTE_A_INBOUND_DIAGNOSIS.md`, `reports/command_logs/98_route_a_sender_correction_schema_dry_run.txt` through `102_route_a_lark_bot_dry_run_after_config.txt`.

## Runtime-model recovery

The first real post-fix group message proved exact routing but exposed `Unknown model: openai/gpt-5.3-codex` before reply. The project did not use a user-supplied credential. After a backup and passing dry-run, only `video-factory.model` was restored to the same MiMo primary/fallback pair used by zhongshu. Validation, Gateway restart, channel probe, and readback exited 0. Evidence: `reports/command_logs/103_route_a_mimo_model_recovery_dry_run.txt` through `105_route_a_mimo_model_recovery_verify.txt`.

## Agent display-name recovery

The initial full `agents.list` patches were delivered through Windows PowerShell native stdin. Their non-ASCII display fields were converted to question marks by the local code page. The current config had 12 corrupted names; the clean Route A pre-model backup had all 14 original display fields. A display-only UTF-8 file patch restored them without changing non-display agent fields, MiMo, Route A binding, or group controls. Config validation and Gateway connectivity are now verified. Evidence: `reports/command_logs/107_agent_display_name_corruption_assessment.txt` through `111_agent_display_restore_final_verify.txt`.

## Pending real smoke

The user must add the `zhongshu` bot to the dedicated group if it is not already a member, then send the required mention commands, one ordinary text, one small file, and one small video. Only the resulting observed message IDs, route logs, dedup evidence, and Codex responses can turn the two smoke reports green.

No model download, driver modification, Cron creation, Jianying automation, or Douyin publication occurred.
