# AI-DIRECTOR-PHASE2-DESKTOP-DETACHED-PROVIDER-QUALIFICATION-005R

## Goal and current state

Phase 2 local implementation is `AI_DIRECTOR_PHASE2_LOCAL_REMEDIATED`; formal P0/P1/P2 remains `not_started/blocked_by_P0/blocked_by_P1`. 005 was blocked because the Codex Desktop app-server respawned and changed `models_cache.json` before hash-bound quarantine. This plan uses a detached hidden PowerShell Worker, one smoke command, and one real acceptance command.

## Hard boundaries

- Keep `Director.create_storyboard`, `generate_video.py --job/--config/--topic/--topic-file`, Storyboard, Timeline, Composition, Pink Pig, TTS, subtitle, FFmpeg and the single existing video pipeline unchanged.
- Only provider cache writes are allowed: exact `C:/Users/Admin/.codex/models_cache.json` and external `E:/Claude_allow/Download/codex-provider-recovery-005r/`.
- Do not change config.toml, auth.json, OAuth, Profile, model selection, OpenClaw, Feishu, Gateway, Binding, Cron, PROJECT_STATUS, or formal gates. No commit/push/merge/reset/clean. Worker never kills Desktop.
- Maximum one smoke and one real acceptance. If either command is attempted, never repeat it in this task.

## Twelve execution gates

1. Read START_HERE_CODEX, PROJECT_STATUS, AGENTS, lessons, 003/004/005 evidence and Obsidian 04/05/06/07. Save branch/HEAD/index/status and the six dirty-file hashes. Run Director/Video/VideoFactory/legacy baselines (47/273/5 and 56 passed, one Windows skip). Create the 005R Change Request and append the task ledger.
2. Add `scripts/lib/ProviderQualification005R.psm1` and `scripts/provider_qualification_005r.ps1`. Expose `Preflight`, `Start -Apply`, and `Verify -RunManifest`. Use fixed Windows PowerShell and Python paths, hidden detached `Start-Process`, atomic external state, process quiescence checks, hash sampling, rollback journal, redacted reports, and no process termination.
3. Add `schemas/ops/provider_qualification_run.schema.json` and `tests/Test-ProviderQualification005R.ps1`. Test state monotonicity, path containment, Desktop-present/no-move, drift/no-move, backup mismatch rollback, one-shot smoke/acceptance, restart refusal, raw-output deletion and forbidden command scans. Run Pester 3.4; failures stop before Worker launch.
4. Add `examples/ai_director_provider_qualification_005r/{README.md,topic.txt,factual_brief.json}`. Topic is `用小粉猪讲清 Modbus RTU：主从通信、数据帧、CRC 和工程排错`; NFKC SHA is `dee7aff68f9b03af3ca1bd78b836c3419df14d2aa49de1bf92dc489564244ec3`; expected job is `director_dee7aff68f9b03af`. Reuse only the existing verified Modbus facts/sources. Refuse if the fresh job directory exists.
5. Run Preflight, then Start -Apply. Worker writes `CLOSE_CODEX_DESKTOP_NOW.txt`; Jovi closes Codex Desktop normally and does not reopen it until `READY_TO_REOPEN.txt` or `BLOCKED.txt` exists. Worker timeout is 30 minutes; no automatic relaunch.
6. Worker waits for the captured Desktop parent and its package app-server children to be absent for ten one-second samples, then requires five one-second identical cache hash/size/mtime samples. Any respawn or drift yields `BLOCKED_DESKTOP_NOT_QUIESCENT` or `BLOCKED_PROVIDER_CACHE_DRIFT` without moving cache.
7. After stable hash, copy the exact cache to external `models_cache.original.json`, verify SHA, move it to `quarantine/models_cache.json`, verify SHA, and preserve both. Recheck config/auth and six dirty hashes. Any error atomically restores the original hash and yields `BLOCKED_PROVIDER_RECOVERY`.
8. Mark `smoke_attempted` before invoking exactly one isolated `codex exec --ephemeral --sandbox read-only --skip-git-repo-check --ignore-user-config --color never --output-schema ... --output-last-message ... -C <empty> -`. Validate Draft Schema, record only exit/size/hash/scene count, delete raw outputs, and require a regenerated healthy cache with zero missing `base_instructions`. Smoke failure rolls back the original cache and yields `REAL_PROVIDER_BLOCKED_SMOKE`.
9. After smoke passes, mark `acceptance_attempted` and invoke exactly once: `generate_video.py --topic-file examples/ai_director_provider_qualification_005r/topic.txt --factual-brief ... --director-provider codex-cli --output-name pink_pig_modbus_ai_provider_005r.mp4`. Do not edit output or retry. Provider failure must leave a sanitized failed report and terminal failed state.
10. Validate all schemas, factual status, Registry-only asset selection, Pink Pig/Composition/subtitle gates, 25–60 second 1080x1920/30fps H264/AAC media, non-silent TTS, FFmpeg decode, ffprobe, frame evidence, then run all Director/Video/VideoFactory/legacy regressions. Any failure is recorded without rerunning Provider.
11. Only after `READY_TO_REOPEN.txt`, Jovi reopens Codex and Luna runs Verify. Spawn three read-only xhigh reviewers: provider/contracts, media/Pink Pig, and Git/environment. Luna reproduces findings, then starts a fresh final reviewer. No reviewer may request a second smoke or acceptance.
12. Generate sanitized `reports/CODEX_DESKTOP_QUIESCENCE_AUDIT_005R.json`, `reports/CODEX_PROVIDER_DETACHED_RUN_005R.json`, and `reports/AI_DIRECTOR_PHASE2_PROVIDER_QUALIFICATION_005R.md`; update tasks/todo, Obsidian 04/07/08, and exact .gitignore exceptions. Only all gates plus final reviewer APPROVED may end with `AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED`; otherwise use the most specific BLOCKED/FAIL status. Stop immediately and do not enter 006, Feishu or formal gates.

## Runtime states and rollback

States are `prepared`, `waiting_for_desktop_exit`, `desktop_quiescent`, `cache_stable`, `cache_quarantined`, `smoke_started`, `smoke_passed`, `acceptance_started`, `acceptance_passed`, `verification_passed`, `complete_pending_review`, `completed`, `failed`, and `blocked`. State writes are atomic with monotonic revisions. `smoke_attempted` and `acceptance_attempted` are write-once. Before smoke success, any boundary error restores the original cache; after smoke success, the healthy regenerated cache remains active and the original backup/quarantine is retained.

## Delivery paths

External runtime is `E:/Claude_allow/Download/codex-provider-recovery-005r/<session>/`; it contains state, heartbeat, hashes, rollback journal and temporary raw outputs only. Repository reports contain no raw prompt/output, credentials, cache content or absolute paths. Obsidian updates go to `04-落地状态与执行计划.md`, `07-AI-Director-Provider真实资格.md`, and new `08-AI-Director-Provider脱离桌面验收.md`.
