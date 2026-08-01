# P0 Core Binding Media Baseline 050

Date: 2026-07-27  
Scope: existing `zhongshu -> OpenClaw Core Feishu Binding -> video-factory`
route.  This is a baseline classification, not a new live qualification.

| Gate | Status | Evidence boundary |
|---|---|---|
| R0 text | PASS | prior real Core-route evidence |
| R1 TXT secure ingress | PASS | prior real Core-route evidence |
| R2 PNG secure ingress | PASS | `P0_LIVE_MEDIA_R2_QUALIFICATION_012.md` |
| R3 image analysis | NOT_PASSED | `P0_R3_TWO_MESSAGE_EVENT_20260720.md`; no ticket-route event occurred |
| R4 audio analysis | NOT_RUN | no real ticket-route event occurred |
| R5 video analysis | NOT_RUN | no real ticket-route event occurred |
| Project Gateway route | DEFERRED | `DEFERRED_TO_P1_CHANNEL_HARDENING` |
| P0 | conditional_not_passed | `PROJECT_STATUS.yaml` remains unchanged |

Bare MP4 quarantine ingress is historical PASS only; it is not R5.  The
independent 050 regression is offline/synthetic evidence, so it cannot promote
R3-R5 or prove that the already-running Core process has rediscovered the MCP
tool surface.

The preserved route invariants are historical evidence: 17 Agents, 14
Bindings, 4 Cron jobs, and one target-group consumer.  No live inventory was
requested or executed in this baseline.
