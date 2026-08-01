# P0 Lark-CLI Egress Dry-Run Evidence V2 (008)

Task: `P0-REAL-CHANNEL-QUALIFICATION-008`
Status: **PASS** - 4 dry-runs (markdown/png/txt/mp4+cover), all exit 0, no actual send.
Method: `lark-cli im +messages-send --dry-run --as bot --profile video-factory --chat-id <target> --idempotency-key <key>` with relative fixture paths. No actual outbound.

## Evidence summary

| Case | exit | elapsed | msg_type | receive_id | uuid (idempotency) | actual message_id | actual send |
| --- | --- | --- | --- | --- | --- | --- | --- |
| markdown | 0 | 295ms | post | oc_***1555 | p0-dryrun-markdown-... | none | no |
| png | 0 | 250ms | image | oc_***1555 | p0-dryrun-png-... | none | no |
| txt | 0 | 250ms | file | oc_***1555 | p0-dryrun-txt-... | none | no |
| mp4_cover | 0 | 250ms | media | oc_***1555 | p0-dryrun-mp4_cover-... | none | no |

## Per-case proof

Each dry-run printed the full API request to stdout (POST `/open-apis/im/v1/messages`, `receive_id_type=chat_id`, `receive_id=oc_***1555`, `uuid=<idempotency-key>`) and `=== Dry Run ===` on stderr. No `om_` message id was returned (no actual send). For media (`--image`/`--file`/`--video`), the dry-run uses placeholder media keys (e.g. `img_dryrun_upload`) and explicitly notes "dry-run uses placeholder media keys for --image local file input; execution uploads it before sending" - confirming no upload occurred. The MP4 case included `--video-cover` (cover required for video).

## Required fields (all satisfied)

- dry-run: `--dry-run` flag set; stderr `=== Dry Run ===`
- bot identity: `--as bot`
- target dedicated group: `--chat-id <target-id>` (masked as `oc_***1555`)
- idempotency key: `--idempotency-key p0-dryrun-<case>-<ts>`
- relative paths: fixtures referenced as `tests/fixtures/feishu_delivery/...` (not absolute)
- MP4 with video cover: `--video ... --video-cover ...`
- exit code: 0 for all 4
- no actual message_id: confirmed (no `om_` in output)
- no actual send: confirmed (dry-run only)
- no long-running lark-event started: confirmed (only `im +messages-send --dry-run`; no `lark-cli event consume`)

## Prohibitions honored

- No actual lark-cli outbound send.
- No `lark-cli event consume` (long-running listener) started.
- Real chat_id masked in all reports (`oc_***1555`).
- No file_key or appSecret recorded.

## Evidence files

- `reports/P0_LARK_EGRESS_DRY_RUN_EVIDENCE_V2.json` (full stdout/stderr/exit per case)
- `scripts/capture_lark_dry_run.py`

## Note on actual outbound

Actual lark-cli egress is **not authorized** this round. Status: `blocked_user_authorization_required` (see P0 Gate prereview). The dry-run evidence above proves the command structure, bot identity, target group, idempotency, relative paths, and cover handling are correct; it does NOT prove a real Feishu delivery succeeds.
