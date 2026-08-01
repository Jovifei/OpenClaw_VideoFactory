# P0 lark-cli Dry-run Evidence V3

Status: `dry_run_evidence_incomplete`.

This report only indexes existing dry-run evidence; it does not run lark-cli or send Feishu content.

| Type | Recorded command shape | Exit | Bot / target / idempotency | Media rule | Actual send |
| --- | --- | --- | --- | --- | --- |
| Markdown | `+messages-send --dry-run` | 0 | bot, unique `oc_***1555`, key `overnight-001-markdown` | N/A | no |
| PNG | `+messages-send --dry-run` | 0 | bot, unique target, key `overnight-001-png` | relative fixture path, placeholder media key | no upload/send |
| TXT | `+messages-send --dry-run` | 0 | bot, unique target, key `overnight-001-txt` | relative fixture path, placeholder media key | no upload/send |
| MP4 + cover | `+messages-send --dry-run` | 0 | bot, unique target, key `overnight-001-mp4` | relative video and `--video-cover`, placeholder keys | no upload/send |

The four independent dry-runs were recorded as `--dry-run`, `--as bot`, relative-path operations with no `--yes`, no message ID, no event listener, and no actual send. Earlier command-shape failures are retained in the source report and were not retried.

The stored existing evidence does **not** preserve the complete literal per-type CLI argument strings. It proves the command shape, flag set, identity, target, idempotency key, relative-path policy, MP4 cover use, and exit code, but not a copyable full command line for each type. Therefore this evidence is intentionally marked `dry_run_evidence_incomplete`; it is not real egress proof.
