# Codex Provider Recovery Plan 003

This document is a future, separately authorized recovery package. No command
in this qualification executed recovery, login, upgrade, model selection,
cache mutation, OAuth change, or Profile change.

## Preconditions

1. Jovi explicitly authorizes provider recovery as a separate task.
2. Reconfirm branch, HEAD, clean index boundary, and the six preserved dirty
   file hashes.
3. Confirm the intended Codex CLI executable and version without logging in or
   changing configuration.
4. Record a redacted, hash-bound backup of the provider cache only under
   `E:/Claude_allow/Download/codex-provider-recovery-003/`; never copy cache
   contents into Git, reports, Obsidian, or chat.

## Safe recovery sequence

1. Inspect only cache structure and validate the backup hash.
2. Determine the supported, documented source of the missing provider
   instruction fields without guessing or downloading an unapproved model.
3. Apply the smallest provider-environment repair in a separate recovery
   branch/worktree, never in the Video Factory implementation branch.
4. Run one isolated `codex exec --ephemeral --sandbox read-only` smoke test with
   the existing Director schema and a temporary empty working directory.
5. Verify that the smoke test changed neither the repository nor Codex/OAuth/
   Profile configuration.
6. Re-run the Phase 2 final qualification from a fresh job directory. A real
   provider result must remain separate from the prior fake and failed
   snapshots.

## Future command package (NOT EXECUTED in qualification 003)

The following commands are an authorization-gated template. They are shown
for a future Luna run only; no line below was executed for this qualification.

### Path and hash preflight

```powershell
$RecoveryCache = 'C:\Users\Admin\.codex\models_cache.json'
$RecoveryExpected = [System.IO.Path]::GetFullPath($RecoveryCache)
if ($RecoveryCache -ne $RecoveryExpected) { throw 'provider_cache_path_mismatch' }
if (-not (Test-Path -LiteralPath $RecoveryCache -PathType Leaf)) { throw 'provider_cache_missing' }
$RecoveryBackupDir = 'E:\Claude_allow\Download\codex-provider-recovery-003'
New-Item -ItemType Directory -Force -Path $RecoveryBackupDir | Out-Null
$RecoveryHashBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $RecoveryCache).Hash
Copy-Item -LiteralPath $RecoveryCache -Destination (Join-Path $RecoveryBackupDir 'models_cache.json') -Force
$RecoveryBackupHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $RecoveryBackupDir 'models_cache.json')).Hash
if ($RecoveryHashBefore -ne $RecoveryBackupHash) { throw 'provider_cache_backup_hash_mismatch' }
```

### Reversible quarantine and restore

```powershell
$RecoveryQuarantine = Join-Path $RecoveryBackupDir 'quarantine'
New-Item -ItemType Directory -Force -Path $RecoveryQuarantine | Out-Null
Move-Item -LiteralPath $RecoveryCache -Destination (Join-Path $RecoveryQuarantine 'models_cache.json')
# Restore only after an explicitly authorized repair or rollback:
Move-Item -LiteralPath (Join-Path $RecoveryQuarantine 'models_cache.json') -Destination $RecoveryCache
```

The quarantine command must not run unless the exact resolved cache path and
backup hash have been reviewed. If any check fails, restore the original file
and stop; do not delete the quarantine or source file.

### Isolated provider smoke

```powershell
$PinkPigPython = 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe'
$SmokeRoot = Join-Path $RecoveryBackupDir 'smoke-workdir'
New-Item -ItemType Directory -Force -Path $SmokeRoot | Out-Null
& codex exec --ephemeral --sandbox read-only --skip-git-repo-check --color never `
  --output-schema 'E:\project\OpenClaw_VideoFactory\schemas\video\director_draft.schema.json' `
  --output-last-message (Join-Path $SmokeRoot 'draft.json') -C $SmokeRoot - `
  < 'E:\project\OpenClaw_VideoFactory\examples\ai_director_demo\topic.txt'
if ($LASTEXITCODE -ne 0) { throw 'provider_smoke_failed' }
```

The smoke must not add `--model`, `--profile`, `--add-dir`,
`danger-full-access`, `workspace-write`, `resume`, or login/configuration
flags. Inspect only the schema-valid Draft and delete the temporary smoke
response after hashing it; do not retain raw provider output in Git.

### Real acceptance rerun

```powershell
& $PinkPigPython generate_video.py `
  --topic-file 'E:\project\OpenClaw_VideoFactory\examples\ai_director_demo\topic.txt' `
  --factual-brief 'E:\project\OpenClaw_VideoFactory\examples\ai_director_demo\factual_brief.json' `
  --director-provider codex-cli `
  --output-name pink_pig_modbus_ai_demo_requalification.mp4
```

Accept only a fresh job directory with valid Script/Storyboard, verified facts,
completed state, MP4 full decode, and independent ffprobe/render-report parity.
Do not merge its evidence with the prior fake or failure directories.

## Stop conditions

- Missing cache, hash mismatch, unsupported CLI flags, login request, model
  download request, or any write outside the approved recovery directory:
  stop and report BLOCKED.
- Do not repair the current Phase 2 implementation in the provider recovery
  task; lifecycle and pipeline findings require their own implementation task.
- Allow at most one isolated smoke and one real acceptance run. A second
  provider retry is not authorized; on failure restore the verified backup,
  record the exact exit/error code, and stop.
- If the smoke or acceptance changes repository files, OAuth/Profile/config,
  or any forbidden surface, restore only from the reviewed backup and report
  BLOCKED; never continue to a pass claim.

## Acceptance

Recovery is complete only when a fresh real-provider run produces a sanitized
Director report, valid Script/Storyboard, completed job state, verified
factual brief, and a new MP4 whose quality report matches independent ffprobe.
Until then the current qualification remains provider-blocked.
