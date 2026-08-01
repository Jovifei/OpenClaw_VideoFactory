# P0 evidence index V27

- `P0_WINDOWS_GATEWAY_SERVICE_AUDIT_045.md` / `.json` - bounded registration
  audit and concrete drift classification.
- `P0_WINDOWS_GATEWAY_SERVICE_BACKUP_045.md` - private rollback package and
  safe artifact hashes.
- `P0_SAFE_RESTART_ROOT_CAUSE_FINAL_045.md` - source-based safe-restart
  authentication boundary.
- `P0_WINDOWS_GATEWAY_SERVICE_REPAIR_045.md` / `.json` - install, restart,
  post-recovery, and fail-closed authentication evidence.
- `P0_MANAGED_RESTART_RESULT_045.md` - the one ordinary managed restart.
- `P0_RPC_AUTH_AFTER_SERVICE_REPAIR_045.md` - health-only Adapter result.

Focused standard-library verification passed 31 tests; `.venv` `pip check`
passed. The 045 private backup and generated reports contain zero detected
credential candidates.
