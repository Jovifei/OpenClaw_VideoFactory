# P0 Evidence Index V6

Operating state: `conditional_not_passed` (P0 Gate not run). 008 round: `READY_FOR_REAL_CHANNEL_SEQUENCE` (all no-user work complete).

| Area | Evidence | State |
| --- | --- | --- |
| 007 independent review | `P0_REAL_CHANNEL_BASELINE_BEFORE.json/.md` | 20/20 passed; SHA `3001ec3b...` == 007 final; no drift |
| Change request | `change_requests/P0-REAL-CHANNEL-QUALIFICATION-008.json` | authorized; no production change |
| Haiku A-F | `child_claude/REAL_CHANNEL_{CONFIG,OBSERVABILITY,ROUTER_SECURITY,ANALYZER,TEST_MATRIX}_REVIEW.md` | 5/6 completed; F (P0 Gate) pending, covered by main-agent prereview |
| Observability | `P0_REAL_CHANNEL_EVENT_TRACE.json/.md`, `scripts/observability/trace_event.py` | validated on agent-turn event (pre_ingest=0, router_images=0, raw_path=false, model=pro) |
| Fixtures | `P0_REAL_CHANNEL_FIXTURE_PREPARATION.md`, `tests/fixtures/feishu_delivery/{p0-audio-test.wav,p0-video-analysis-test.mp4,fixture_manifest.json}` | audio 5.77s + video 5.0s, offline TTS + ffmpeg, no cloud |
| Local analyzer validation | `P0_LOCAL_ANALYZER_RUNTIME_VALIDATION.json/.md`, `scripts/local_analyzer_validation/validate_analyzers.py` | audio (faster-whisper CUDA) + video (ffprobe+frames+whisper) + image (mimo-v2.5) PASS |
| Idempotency | `P0_REAL_CHANNEL_IDEMPOTENCY.md` | 17/17 tests + observability demo (N retries -> 1 receipt) |
| Negative tests | `P0_REAL_CHANNEL_NEGATIVE_TESTS.md` | MIME/signature/path/oversize/unauthorized/reparse/prompt-injection covered |
| lark-cli dry-run | `P0_LARK_EGRESS_DRY_RUN_EVIDENCE_V2.json/.md`, `scripts/capture_lark_dry_run.py` | 4/4 exit 0, no actual send |
| P0 Gate prereview | `P0_GATE_PREREVIEW.json/.md`, `P0_GATE_REMAINING_BLOCKERS.md`, `scripts/p0_gate_prereview.py` | BLOCKED (11 passed/2 cond/2 def/11 blocked); actual Gate NOT run; P0_READY NOT created |
| Post-migration audit | `P0_POST_MIGRATION_AUDIT.json/.md` | no production change; only project files added |
| Haiku summary | `P0_HAIKU_REAL_CHANNEL_REVIEW_SUMMARY.md` | A-E done; F pending (covered) |
| Master qualification | `P0_REAL_CHANNEL_QUALIFICATION.json/.md` | 22 required items |
| Status V6 | `P0_CURRENT_STATUS_V6.md/.json` | conditional_not_passed; READY_FOR_REAL_CHANNEL_SEQUENCE |
| Tests (unchanged) | `Test-SingleGroupMediaRouter.ps1` 45/45, `Test-IngestInboundMedia.ps1` 32/32, `test_ingest_attachment_core.py` 17/17 | 94/94 |
| 007 evidence (prior round) | `P0_SINGLE_GROUP_ROUTER_IMPLEMENTATION.*`, `P0_INGEST_ATTACHMENT_TOOL.*`, `P0_INTERNAL_MEDIA_AGENTS.*`, `P0_GPU_MEDIA_LOCK_CONTRACT.md`, `P0_MULTI_ATTACHMENT_CONTRACT.md`, `P0_ROUTER_TOOL_POLICY.*` | 007 production state, intact |
| Old routes (not retried) | `P0_PLUGIN_OWNED_BINDING_MIGRATION.md`, `P0_FULL_AGENT_PROXY_VALIDATION.md`, `P0_PREINGEST_ARCHITECTURE_OPTIONS.md`, `P0_CHANNEL_MIDDLEWARE_FEASIBILITY.md` | design blocked; 007/008 used scope-deny + tool-policy |

## Secrets policy

All apiKeys, appSecrets, gateway token, real target-group id, file_keys, full user ids are masked/hashed in every report. Real identifiers live only in the live config and MCP server env.

## Protected state retained

No P0 Gate, P0_READY, PROJECT_STATUS update, commit, tag, push, P1, model install/download, real Feishu outbound, OAuth/Binding/Cron change, core source change, new dependency.
