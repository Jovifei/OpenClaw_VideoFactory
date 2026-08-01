# P0 Current Status

> Superseded by `reports/P0_CURRENT_STATUS_V2.md`.

Overall status: **not passed**

## Passed

- Package
- Gateway, with its existing service-version warning retained
- `video-factory` Agent and exact dedicated-group Binding
- Skill visibility
- Text ingress
- Image ingress
- Media-path remediation required checks; the additional PNG MIME mismatch finding remains open

## Ready for user test

- TXT attachment ingress using `p0-file-test.txt`
- MP4 attachment ingress using `p0-video-test.mp4`

## Conditional

- lark-cli egress: profile, bot identity and target membership passed, but the four-command dry-run batch did not complete. No actual send occurred.

## Deferred

- Codex CLI upgrade
- Direct Codex CLI read-only and workspace-write smoke

These remain frozen until the exact phrase `开始Codex CLI维护窗口`.

## Blocked

- Final P0 Gate
- P1 entry

`PROJECT_STATUS.yaml` remains unchanged with P0 not started/not passed and P1 blocked by P0. No P0_READY marker, commit, tag or P1 branch was created.
