# P0 Evidence Index V2

## Current authoritative evidence

- Media MIME/signature fix: `reports/P0_MEDIA_MIME_FIX.json`
- Root-walk fix and real TXT idempotency: `reports/P0_MEDIA_ROOT_WALK_FIX.json`
- Overnight media regression: `reports/P0_MEDIA_LOCAL_REGRESSION_OVERNIGHT.json`
- Feishu ingress baseline: `reports/FEISHU_INGRESS_BASELINE.json`
- lark-cli independent dry-runs: `reports/P0_LARK_EGRESS_TIMEOUT_DIAGNOSTIC.json`
- V2.7 decision and merge: `reports/ADR_VIDEO_USE_OPENMONTAGE.md`, `reports/ARCHITECTURE_UPDATE_V2.7.json`
- Overnight baseline: `reports/OVERNIGHT_BASELINE.json`
- Current P0 classification: `reports/P0_CURRENT_STATUS_V2.json`

## Superseded conclusions

- `reports/FEISHU_EGRESS_TEST.json`: its batch-timeout dry-run conclusion is superseded by the four independent dry-runs; actual send remains pending.
- `reports/P0_CURRENT_STATUS.json` and `.md`: superseded by V2 status classification.
- Previous root-walk stopped report content was replaced in place by the verified final report while preserving the Change Request history.

Original command logs and historical reports remain preserved. Child-agent output is not listed as acceptance evidence.
