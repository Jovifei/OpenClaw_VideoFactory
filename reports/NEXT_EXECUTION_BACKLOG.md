# Next Execution Backlog

Status: `ORDERED_AFTER_092`

Each future code, configuration or runtime change needs a new scoped Change Request.

## P0 blocker

| Priority | Goal | Dependencies | Test | Done |
| --- | --- | --- | --- | --- |
| P0-1 | Implement V2 P0 evidence schema and Gate/prereview readers | Explicit rebaseline authorization | Focused unit/schema tests | Missing event-ID, duplicate or restart evidence fails closed |
| P0-2 | Add event-ID and duplicate-effect contracts | P0-1 | Same event twice yields one effect; duplicate message/resource/delivery yields no extra effect | Redacted V2 evidence is reproducible |
| P0-3 | Capture real entry and restart recovery | P0-1/P0-2; live-test authorization | Normal-user text routes/replies once; restart then fresh text routes/replies once | No extra consumer or duplicate effect |
| P0-4 | Close P0 once | P0-1..3 and reusable media/egress evidence | Regression, skills, prereview, one Gate | Zero exit and `P0_READY.json` |

## P1 MVP

| Priority | Goal | Dependencies | Test | Done |
| --- | --- | --- | --- | --- |
| P1-1 | Freeze/revalidate offline candidate | P0-4 | Regression, typecheck, decode, secret scan | Versioned baseline |
| P1-2 | Bind factory state to actual Feishu delivery | P1-1; narrow code/live scope | One fixture delivery and same-key resend | One visible package and one delivery record |
| P1-3 | Validate lifecycle | P1-2 | Clean/rerun/cancel/retry/restart across three fixtures | No orphan or duplicate delivery |
| P1-4 | Human review and P1 Gate | P1-3 | Visual/contact sheet, listening, formal Gate | `P1_READY.json`; output remains review-only |

## P2 automation

| Priority | Goal | Dependencies | Test | Done |
| --- | --- | --- | --- | --- |
| P2-1 | Allowed source adapters and history | P1-4 | Allowlist, date/source, quota and dedup | >=10 attributable raw candidates |
| P2-2 | 08:30 cards and selection parser | P2-1 | 3–5 cards, rank/title edit and cancel | One choice maps to one job |
| P2-3 | 12:00 fallback then Cron | P2-2; Cron authorization | Dry-run schedule and duplicate/late/cancel recovery | <=1 job/day, qualified fallback only |
| P2-4 | Seven-day trial | P2-3 | Daily metrics | >=90% completion, zero duplicate jobs |

## P3 enhancement

| Priority | Goal | Dependencies | Test | Done |
| --- | --- | --- | --- | --- |
| P3-1 | Approve/pin workflow and model manifest | P2 stable; rights, license and <=30 GB budget approval | Hash/license/VRAM/no-download checks | Approved manifest and rollback record |
| P3-2 | Serialize GPU production queue | P3-1 | Concurrent Whisper/ComfyUI queue and OOM/timeout fallback | No overlapping heavy work or lost job |
| P3-3 | Add optional visual inserts | P3-2 | Quality/latency benchmark and CPU/static fallback | Measurable improvement without delivery regression |
| P3-4 | Evaluate advanced subtitle alignment | P3-2 | Chinese-caption benchmark and rollback | Adopt only if it beats the P1 caption baseline |

## Stopped or deferred

Manual Feishu retry reproduction, ACK injection, Project Gateway replacement, Device Auth,
RPC provenance, broad agent framework adoption, second scheduler, unapproved ComfyUI models
and P4 publishing helpers are not active work.
