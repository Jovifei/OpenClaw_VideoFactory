# AI Director Phase 2 Final Qualification 003 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Independently qualify the existing Phase 2 implementation, isolate the real Codex CLI provider blocker from project evidence, and produce a safe recovery plan without changing the Director or provider environment.

**Architecture:** Luna is the sole coordinator and report writer. Three read-only subagents audit Git/boundaries, contracts/architecture, and provider/security evidence in parallel while Luna executes the authoritative tests sequentially; a fresh final-review subagent then checks the assembled reports. The audit never repairs Codex cache, invokes the real provider, changes project implementation, or promotes a formal phase.

**Tech Stack:** Windows PowerShell, Python pytest, JSON Schema, Git/GitHub read-only queries, FFmpeg/ffprobe, Markdown reports, Obsidian UTF-8 notes.

---

## 0. Fixed scope, starting facts, and terminal states

Current expected baseline:

- Repository: E:\project\OpenClaw_VideoFactory
- Branch: codex/ai-director-video-factory-phase2-001
- HEAD: 76180a59ea662bdf168d88baaeb777d3e8eb59ef
- Phase 2 local tests last observed: director 32 passed, video 273 passed, legacy 5 passed
- Fake-provider evidence: dist/director/director_ec229e6efe2c340d/output.mp4
- Isolated real-provider failure: dist/director/provider_failures/director_ec229e6efe2c340d/
- Formal PROJECT_STATUS.yaml: unchanged P0 not_started; P1/P2 blocked
- Current implementation report: reports/AI_DIRECTOR_PHASE2_IMPLEMENTATION.md

This is a qualification task, not a feature task. It must not modify:

- generate_video.py
- src/factory/director/
- src/factory/assets/
- video_factory/
- schemas/
- tests/
- PROJECT_STATUS.yaml
- OpenClaw, Feishu, Gateway, Binding, OAuth, Cron, model, Profile, or runtime configuration
- C:\Users\Admin\.codex\config.toml
- C:\Users\Admin\.codex\models_cache.json

It must not run:

- codex exec
- codex login
- model/profile selection
- reset, clean, checkout, commit, push, merge, rebase, or tag
- a formal P0/P1/P2 Gate

The only permitted writes are:

- reports/change_requests/AI-DIRECTOR-PHASE2-FINAL-QUALIFICATION-003.json
- reports/PHASE2_GIT_AUDIT_003.md
- reports/CODEX_PROVIDER_BLOCKER_003.md
- reports/CODEX_PROVIDER_RECOVERY_PLAN_003.md
- reports/PHASE2_FINAL_QUALIFICATION_003.md
- tasks/todo.md, append-only
- .gitignore, exact report exceptions only
- E:/AI_Tools/Obsidian/Data/notes-personal/codex_memory/03-项目记忆/OpenClaw_VideoFactory/05-AI-Director与素材智能.md, append-only

Terminal result must be exactly one of:

- READY_FOR_REAL_PROVIDER_TEST: every local gate passes and no current provider-environment blocker is observable.
- PASS_LOCAL_PROVIDER_BLOCKED: every local gate passes, but the isolated provider-environment blocker still exists.
- FAIL_IMPLEMENTATION: a local contract, test, media, security, or boundary gate fails reproducibly.

AI_DIRECTOR_PHASE2_READY is forbidden in this task because no real provider run is authorized.

## 1. File responsibility map

Files to create:

- reports/change_requests/AI-DIRECTOR-PHASE2-FINAL-QUALIFICATION-003.json
  - Records the read-only audit authority and exact write surface.
- reports/PHASE2_GIT_AUDIT_003.md
  - Records branch topology, dirty/index state, remote refs, ignored artifacts, large-file scan, and boundary hashes.
- reports/CODEX_PROVIDER_BLOCKER_003.md
  - Records the sanitized provider failure and proves it is isolated from the Video Factory implementation.
- reports/CODEX_PROVIDER_RECOVERY_PLAN_003.md
  - Defines a separately authorized, reversible future recovery procedure; none of its mutation commands run now.
- reports/PHASE2_FINAL_QUALIFICATION_003.md
  - Reconciles main-agent evidence and independent subagent reviews into one terminal result.

Files to modify:

- tasks/todo.md
  - Append the qualification checklist and final review block.
- .gitignore
  - Append exact tracking exceptions for the five qualification artifacts only if git check-ignore proves they are ignored.
- 05-AI-Director与素材智能.md
  - Append final qualification status and links without rewriting existing history.

Read-only implementation surfaces:

- generate_video.py
- src/factory/director/director_contract.py
- src/factory/director/ai_director.py
- src/factory/director/script_planner.py
- src/factory/director/storyboard_assembler.py
- src/factory/director/asset_selector.py
- src/factory/director/provider.py
- video_factory/pipeline/job_state.py
- video_factory/pipeline/validation.py
- video_factory/pipeline/storyboard.py
- video_factory/pipeline/renderer.py
- video_factory/pipeline/render_report.py
- video_factory/pipeline/subtitle.py
- video_factory/pipeline/pink_pig_quality.py
- schemas/video/
- tests/director/
- tests/video/
- video_factory/tests/

## Task 1: Freeze authority and current worktree

**Files:**

- Read: START_HERE_CODEX.md
- Read: PROJECT_STATUS.yaml
- Read: AGENTS.md
- Read: tasks/lessons.md
- Read: reports/AI_DIRECTOR_PHASE2_IMPLEMENTATION.md
- Create: reports/change_requests/AI-DIRECTOR-PHASE2-FINAL-QUALIFICATION-003.json
- Modify: tasks/todo.md

- [ ] **Step 1: Read the required control documents completely**

Run:

~~~powershell
Set-Location E:\project\OpenClaw_VideoFactory
Get-Content -Raw -Encoding UTF8 START_HERE_CODEX.md
Get-Content -Raw -Encoding UTF8 PROJECT_STATUS.yaml
Get-Content -Raw -Encoding UTF8 AGENTS.md
Get-Content -Raw -Encoding UTF8 tasks/lessons.md
Get-Content -Raw -Encoding UTF8 reports/AI_DIRECTOR_PHASE2_IMPLEMENTATION.md
~~~

Expected: every file is readable; PROJECT_STATUS.yaml remains P0 not_started and P1/P2 blocked.

- [ ] **Step 2: Verify the branch, HEAD, merge state, and index**

Run:

~~~powershell
git branch --show-current
git rev-parse HEAD
git status --porcelain=v2 --branch
git diff --cached --quiet
$QualificationIndexExit = $LASTEXITCODE
Test-Path .git\MERGE_HEAD
Test-Path .git\rebase-merge
Test-Path .git\rebase-apply
Write-Output "index_exit=$QualificationIndexExit"
~~~

Expected:

- branch is codex/ai-director-video-factory-phase2-001
- HEAD is 76180a59ea662bdf168d88baaeb777d3e8eb59ef
- index_exit is 0
- all three merge/rebase checks are False

If any expectation differs, write the actual condition to the final report as FAIL_IMPLEMENTATION and stop before running tests.

- [ ] **Step 3: Capture hashes for the six pre-existing dirty files**

Run:

~~~powershell
$QualificationDirtyFiles = @(
  'PROJECT_STATUS.yaml',
  'reports/P0_ACCEPTANCE_MATRIX_V2.yaml',
  'scripts/analysis_request.py',
  'scripts/analyzer_mcp.py',
  'scripts/mcp_ingest_attachment.py',
  'scripts/media_action_ticket.py'
)
$QualificationDirtyFiles | ForEach-Object {
  $QualificationHash = Get-FileHash -Algorithm SHA256 -LiteralPath $_
  [pscustomobject]@{
    path = $_
    sha256 = $QualificationHash.Hash.ToLowerInvariant()
  }
} | ConvertTo-Json -Depth 3
~~~

Expected: six path/hash records. Keep the literal hashes in Luna's working notes and compare them again in Task 10. Do not write those user-file contents into a report.

- [ ] **Step 4: Create the bounded Change Request**

Use apply_patch to create exactly:

~~~json
{
  "id": "AI-DIRECTOR-PHASE2-FINAL-QUALIFICATION-003",
  "task": "Phase 2 Final Audit and Provider Isolation",
  "repository_root": "E:/project/OpenClaw_VideoFactory",
  "expected_branch": "codex/ai-director-video-factory-phase2-001",
  "expected_head": "76180a59ea662bdf168d88baaeb777d3e8eb59ef",
  "mode": "read_only_qualification",
  "allowed_writes": [
    "reports/change_requests/AI-DIRECTOR-PHASE2-FINAL-QUALIFICATION-003.json",
    "reports/PHASE2_GIT_AUDIT_003.md",
    "reports/CODEX_PROVIDER_BLOCKER_003.md",
    "reports/CODEX_PROVIDER_RECOVERY_PLAN_003.md",
    "reports/PHASE2_FINAL_QUALIFICATION_003.md",
    "tasks/todo.md",
    ".gitignore",
    "E:/AI_Tools/Obsidian/Data/notes-personal/codex_memory/03-项目记忆/OpenClaw_VideoFactory/05-AI-Director与素材智能.md"
  ],
  "read_only_surfaces": [
    "generate_video.py",
    "src/factory/director/",
    "video_factory/",
    "schemas/",
    "tests/",
    "dist/director/",
    "C:/Users/Admin/.codex/models_cache.json"
  ],
  "forbidden_surfaces": [
    "PROJECT_STATUS.yaml",
    "OpenClaw",
    "Feishu",
    "Gateway",
    "Binding",
    "OAuth",
    "Cron",
    "Codex config",
    "Codex models cache",
    "Codex model or Profile",
    "formal P0/P1/P2 Gate"
  ],
  "forbidden_commands": [
    "codex exec",
    "codex login",
    "git reset",
    "git clean",
    "git checkout",
    "git commit",
    "git push",
    "git merge",
    "git rebase"
  ],
  "preexisting_unrelated_dirty_files": [
    "PROJECT_STATUS.yaml",
    "reports/P0_ACCEPTANCE_MATRIX_V2.yaml",
    "scripts/analysis_request.py",
    "scripts/analyzer_mcp.py",
    "scripts/mcp_ingest_attachment.py",
    "scripts/media_action_ticket.py"
  ],
  "does_not_imply_phase_pass": true,
  "does_not_authorize_provider_recovery": true,
  "does_not_authorize_commit_or_push": true
}
~~~

- [ ] **Step 5: Append the execution checklist**

Append, without replacing earlier history:

~~~markdown
## AI-DIRECTOR-PHASE2-FINAL-QUALIFICATION-003 — IN PROGRESS

- [ ] Freeze branch, HEAD, index, dirty-file hashes, and phase boundary.
- [ ] Complete Git/local/remote artifact audit.
- [ ] Complete Director contract and single-pipeline audit.
- [ ] Re-run 32+/273+/5 test gates and both legacy CLI modes.
- [ ] Independently verify MP4, ffprobe, render report, subtitles, assets, and state snapshots.
- [ ] Isolate and document the real Codex CLI provider blocker without running or repairing it.
- [ ] Produce the separately authorized provider recovery plan.
- [ ] Reconcile three specialist reviews and one fresh final review.
- [ ] Update qualification reports and Obsidian, recheck forbidden hashes, and stop.
~~~

Audit gate: Change Request parses as JSON, todo history is preserved, and no implementation file changed during Task 1.

## Task 2: Launch simultaneous read-only specialist audits

**Files:**

- Read-only: entire repository and existing evidence
- No subagent may create or modify files

Luna remains the only writer. Subagent observations are advisory until Luna reproduces them.

- [ ] **Step 1: Spawn Git and boundary reviewer**

Use a fresh subagent named qualification_git_review with this exact task:

~~~text
Work read-only in E:\project\OpenClaw_VideoFactory.
Audit AI-DIRECTOR-PHASE2-FINAL-QUALIFICATION-003 only.
Read START_HERE_CODEX.md, PROJECT_STATUS.yaml, AGENTS.md, the new Change Request, and the Phase 2 implementation report.
Inspect branch, HEAD, index, worktree, local and remote branch topology, ignored dist/cache/model artifacts, tracked large binaries, and the six pre-existing dirty files.
Do not edit files, run tests, invoke codex exec, access credentials, commit, push, reset, clean, merge, or rebase.
Return:
1. PASS/FAIL for branch and index boundary.
2. Exact unexpected tracked or staged paths.
3. Whether dist, cache, model, MP4, WAV, and MP3 files are tracked.
4. Remote branch observations.
5. A final reviewer verdict and command list.
~~~

- [ ] **Step 2: Spawn contracts and architecture reviewer**

Use a fresh subagent named qualification_contract_review with this exact task:

~~~text
Work read-only in E:\project\OpenClaw_VideoFactory.
Audit the existing Phase 2 chain:
Topic -> ScriptPlanner -> DirectorScript -> StoryboardAssembler -> AssetSelector -> existing compile_storyboard -> existing run_job -> render report and quality gate.
Verify Director.create_storyboard(topic) compatibility, VideoJob State 1.0 and 2.0, Registry-only asset selection, Pink Pig quality gate, Composition/subtitle boundaries, and that no second renderer/audio/subtitle/FFmpeg pipeline exists.
Read schemas and tests but do not edit or run write-producing commands.
Do not invoke codex exec.
Return:
1. Interface map with exact files and symbols.
2. PASS/FAIL per contract.
3. Any duplicated pipeline or provider-to-asset/path injection.
4. Exact file and line for each finding.
5. Final verdict.
~~~

- [ ] **Step 3: Spawn provider and security reviewer**

Use a fresh subagent named qualification_provider_review with this exact task:

~~~text
Work read-only in E:\project\OpenClaw_VideoFactory.
Audit only existing provider failure evidence and provider adapter safety.
Read the isolated provider failure report/state, src/factory/director/provider.py, relevant tests, and the implementation report.
Do not run codex exec. Do not modify or print Codex cache/config/profile/OAuth/model contents.
Confirm the structured failure, read-only sandbox flags, timeout/output bounds, absence of raw prompt/output/credentials/absolute paths, and separation from the completed fake-provider job directory.
Return:
1. PASS/FAIL per isolation property.
2. Sanitized blocker classification.
3. Whether the evidence supports project-code failure or environment failure.
4. Any unsafe retained data paths.
5. Final verdict.
~~~

- [ ] **Step 4: Confirm the concurrency boundary**

Expected:

- all three subagents are read-only
- no subagent runs pytest, FFmpeg, or a rendering command
- Luna alone runs authoritative verification commands
- subagent results are not accepted as command evidence without Luna reproduction

If any subagent writes to the workspace, stop, record the exact path, and classify the audit FAIL_IMPLEMENTATION unless Luna can prove the write was limited to an allowed report and fully restore the audit boundary without touching user work.

## Task 3: Perform the Git and remote audit

**Files:**

- Create: reports/PHASE2_GIT_AUDIT_003.md
- Read: .gitignore
- Read: reports/change_requests/AI-DIRECTOR-VIDEO-FACTORY-PHASE2-001.json

- [ ] **Step 1: Capture local branch topology**

Run:

~~~powershell
git remote -v
git branch -vv
git log -5 --oneline --decorate
git status --short --untracked-files=all
git diff --name-status
git diff --cached --name-status
~~~

Expected:

- current branch remains codex/ai-director-video-factory-phase2-001
- index output is empty
- no commit, push, reset, clean, merge, or rebase occurred

- [ ] **Step 2: Query remote refs without fetching or changing local refs**

Run:

~~~powershell
git ls-remote --heads origin main codex/pink-pig-phase1-5-composition codex/pink-pig-ai-director-003 codex/ai-director-video-factory-phase2-001
~~~

Interpretation:

- record only refs actually returned
- do not infer that a missing remote branch is deleted or merged
- do not run git fetch
- current expected observation is that Phase 1.5 is published while the Phase 2 working branch is local and uncommitted

- [ ] **Step 3: Check ignored and tracked generated artifacts**

Run:

~~~powershell
git ls-files dist
git ls-files | Select-String -Pattern '\.(mp4|wav|mp3|bin|safetensors|ckpt|onnx|pt|pth)$'
git status --short --untracked-files=all | Select-String -Pattern '(^|/|\\)(dist|cache|models?)(/|\\)|\.(mp4|wav|mp3)$'
git check-ignore -v -- dist/director/director_ec229e6efe2c340d/output.mp4
$QualificationRepoRoot = [System.IO.Path]::GetFullPath((git rev-parse --show-toplevel).Trim())
$QualificationCachePath = [System.IO.Path]::GetFullPath('C:\Users\Admin\.codex\models_cache.json')
if ($QualificationCachePath.StartsWith($QualificationRepoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw 'codex_cache_unexpectedly_inside_repository'
}
Write-Output 'codex_cache_outside_repository=true'
~~~

Expected:

- git ls-files dist returns no tracked files
- no model/cache/media binary is staged
- the external Codex cache is outside repository tracking

- [ ] **Step 4: Scan tracked file sizes without opening contents**

Run:

~~~powershell
git ls-files | ForEach-Object {
  if (Test-Path -LiteralPath $_ -PathType Leaf) {
    $QualificationItem = Get-Item -LiteralPath $_
    if ($QualificationItem.Length -gt 10485760) {
      [pscustomobject]@{
        path = $_
        bytes = $QualificationItem.Length
      }
    }
  }
} | Format-Table -AutoSize
~~~

Expected: no unexpected tracked file above 10 MiB. Any model/cache/media binary is a FAIL unless it is an already approved repository asset with documented provenance.

- [ ] **Step 5: Write PHASE2_GIT_AUDIT_003.md**

The report must contain these exact sections:

~~~markdown
# Phase 2 Git Audit 003

## Scope
Read-only Git, artifact, ignore, and remote-ref audit.

## Branch and HEAD
Record the literal branch and full commit SHA observed.

## Index and worktree
List staged paths, Phase 2 paths, and the six pre-existing unrelated dirty paths separately.

## Remote refs
Record only literal refs returned by git ls-remote.

## Generated and large artifacts
Record tracked dist count, tracked media/model/cache count, and files above 10 MiB.

## Ignore behavior
Record git check-ignore results for the fake MP4 and the qualification reports.

## Boundary conclusion
Write PASS or FAIL with concrete reasons.
~~~

Audit gate: report claims match the commands, no secret-bearing content is copied, and the Git/index state is unchanged.

## Task 4: Audit the Phase 2 contract and single-pipeline architecture

**Files:**

- Read: generate_video.py
- Read: src/factory/director/
- Read: video_factory/pipeline/
- Read: schemas/video/
- Read: tests/director/
- Read: tests/video/

- [ ] **Step 1: Locate the public interfaces**

Run:

~~~powershell
rg -n "class Director|def create_storyboard|class AIDirector|class ScriptPlanner|def create_script|class StoryboardAssembler|def from_script|class AssetSelector|def select_assets|class VideoJobStateMachine|def transition|def run_topic|def run_job" generate_video.py src/factory/director video_factory/pipeline
~~~

Expected symbols:

- Director.create_storyboard
- AIDirector.create_storyboard
- ScriptPlanner.create_script
- StoryboardAssembler.from_script
- AssetSelector.select_assets
- VideoJobStateMachine.transition
- generate_video.run_topic
- generate_video.run_job

- [ ] **Step 2: Verify the Schema catalog and error contracts**

Run:

~~~powershell
rg -n '"director_script"|"director_factual_brief"|"asset_selection_report"|"director_quality_report"|"video_job_state"' video_factory/pipeline/validation.py schemas/video/README.md
rg -n "director_.*invalid|video_job_state_invalid|code.*message.*context" src/factory/director video_factory/pipeline tests/director tests/video
~~~

Expected:

- every Phase 2 schema is registered in validation.py
- validation errors remain FactoryContractError values
- structured failures expose code, message, and context

- [ ] **Step 3: Verify provider output cannot choose assets or paths**

Run:

~~~powershell
rg -n '"asset_id"|registry_version|output_ref|work_dir|ffmpeg|asset_path' schemas/video/director_script.schema.json src/factory/director/script_planner.py src/factory/director/storyboard_assembler.py src/factory/director/asset_selector.py
~~~

Expected:

- DirectorScript Schema does not permit asset_id, paths, Registry version, work directory, or FFmpeg settings
- StoryboardAssembler injects deterministic identifiers and composition fields
- AssetSelector injects Registry-backed asset IDs

- [ ] **Step 4: Verify the existing pipeline is reused exactly once**

Run:

~~~powershell
rg -n "run_job\(" generate_video.py
rg -n "subprocess|ffmpeg|ffprobe|render_video|build_srt|plan_audio" src/factory/director
rg -n "compile_storyboard|validate_pink_pig_quality|SubtitleLayoutEngine|build_render_report" generate_video.py video_factory/pipeline
~~~

Expected:

- run_topic calls existing run_job once
- src/factory/director contains no renderer, FFmpeg, audio, or subtitle execution chain
- compiler, quality, subtitle, audio, render report, and renderer remain under the existing Video Factory

- [ ] **Step 5: Verify lifecycle compatibility**

Run:

~~~powershell
$QualificationPython = 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe'
& $QualificationPython -m pytest tests/director/test_job_state_machine.py tests/director/test_phase2_contract_schemas.py tests/video/test_video_job_state.py -q
~~~

Expected: all selected tests pass, including VideoJob State 1.0 compatibility and 2.0 ordered transitions.

Audit gate: any second pipeline, provider-selected asset path, broken public signature, or lifecycle regression is FAIL_IMPLEMENTATION. Do not repair it in this task.

## Task 5: Run authoritative tests and legacy CLI regression

**Files:**

- Test: tests/director/
- Test: tests/video/
- Test: video_factory/tests/
- Read/write generated evidence: dist/

- [ ] **Step 1: Run all Director tests**

Run:

~~~powershell
$QualificationPython = 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe'
& $QualificationPython -m pytest tests/director -q
$QualificationDirectorExit = $LASTEXITCODE
Write-Output "director_exit=$QualificationDirectorExit"
~~~

Expected: exit 0 and at least 32 passed.

- [ ] **Step 2: Stop immediately if Director tests fail**

If director_exit is nonzero:

- record the exact failing test names and stable error codes
- do not change code or tests
- do not run later test groups
- final result is FAIL_IMPLEMENTATION

- [ ] **Step 3: Run all video tests**

Run:

~~~powershell
& $QualificationPython -m pytest tests/video -q
$QualificationVideoExit = $LASTEXITCODE
Write-Output "video_exit=$QualificationVideoExit"
~~~

Expected: exit 0 and at least 273 passed.

- [ ] **Step 4: Stop immediately if video tests fail**

Use the same stop discipline as Step 2. Do not attempt a guessed repair.

- [ ] **Step 5: Run legacy tests**

Run:

~~~powershell
& $QualificationPython -m pytest video_factory/tests -q
$QualificationLegacyExit = $LASTEXITCODE
Write-Output "legacy_exit=$QualificationLegacyExit"
~~~

Expected: exit 0 and 5 passed.

- [ ] **Step 6: Run the two legacy CLI modes**

Run sequentially:

~~~powershell
& $QualificationPython generate_video.py --job tests/video/fixtures/job_offline.yaml
$QualificationJobExit = $LASTEXITCODE
& $QualificationPython generate_video.py --config examples/pink_pig_demo/config.yaml
$QualificationConfigExit = $LASTEXITCODE
Write-Output "job_exit=$QualificationJobExit"
Write-Output "config_exit=$QualificationConfigExit"
~~~

Expected: job_exit 0 and config_exit 0.

- [ ] **Step 7: Verify source compilation**

Run:

~~~powershell
& $QualificationPython -m py_compile generate_video.py video_factory/pipeline/job_state.py video_factory/pipeline/validation.py
Get-ChildItem src/factory/director -Filter *.py | ForEach-Object {
  & $QualificationPython -m py_compile $_.FullName
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
~~~

Expected: exit 0 with no syntax errors.

Audit gate: all four command groups pass. Child-agent claims never replace these main-agent results.

## Task 6: Verify fake-provider media and report parity

**Files:**

- Read: dist/director/director_ec229e6efe2c340d/
- Read: dist/director/director_06b00f079b94d3e8/
- Read: video_factory/configs/compositions/knowledge_illustration.json
- Read: src/factory/assets/pink_pig/registry.json

- [ ] **Step 1: Verify the completed fake-provider snapshot is internally coherent**

Run:

~~~powershell
$QualificationVerifiedDir = 'E:\project\OpenClaw_VideoFactory\dist\director\director_ec229e6efe2c340d'
$QualificationRequired = @(
  'topic.txt',
  'research.md',
  'sources.json',
  'style_tokens.json',
  'script.json',
  'director_score.json',
  'storyboard.json',
  'asset_selection.json',
  'director_report.json',
  'video_job.yaml',
  'video_job_state.json',
  'storyboard.resolved.json',
  'timeline.json',
  'subtitle.srt',
  'render_report.json',
  'director_quality_report.json',
  'director_quality_report.md',
  'output.mp4'
)
$QualificationRequired | ForEach-Object {
  [pscustomobject]@{
    artifact = $_
    exists = Test-Path -LiteralPath (Join-Path $QualificationVerifiedDir $_)
  }
} | Format-Table -AutoSize
~~~

Expected: every artifact exists.

- [ ] **Step 2: Run independent ffprobe**

Run:

~~~powershell
ffprobe -v error -show_entries format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate -of json "$QualificationVerifiedDir\output.mp4"
~~~

Expected:

- video codec h264
- width 1080
- height 1920
- frame rate 30/1
- audio codec aac
- audio sample rate 24000
- duration between 25 and 60 seconds

- [ ] **Step 3: Run complete decode**

Run:

~~~powershell
ffmpeg -v error -i "$QualificationVerifiedDir\output.mp4" -f null -
$QualificationDecodeExit = $LASTEXITCODE
Write-Output "decode_exit=$QualificationDecodeExit"
~~~

Expected: decode_exit 0 and no decode errors.

- [ ] **Step 4: Compare ffprobe, render report, asset selection, and state**

Run:

~~~powershell
$QualificationCheck = @'
import json
import subprocess
from pathlib import Path

job = Path(r"E:\project\OpenClaw_VideoFactory\dist\director\director_ec229e6efe2c340d")
probe = json.loads(subprocess.check_output([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate",
    "-of", "json", str(job / "output.mp4")
], text=True, encoding="utf-8"))
report = json.loads((job / "render_report.json").read_text(encoding="utf-8"))
state = json.loads((job / "video_job_state.json").read_text(encoding="utf-8"))
quality = json.loads((job / "director_quality_report.json").read_text(encoding="utf-8"))
selection = json.loads((job / "asset_selection.json").read_text(encoding="utf-8"))
video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
selected = [item["selected_asset_id"] for item in selection["selections"]]
assert video["codec_name"] == report["codec"] == "h264"
assert int(video["width"]) == report["resolution"]["width"] == 1080
assert int(video["height"]) == report["resolution"]["height"] == 1920
assert video["r_frame_rate"] == "30/1" and report["fps"] == 30.0
assert audio["codec_name"] == report["audio"]["codec"] == "aac"
assert int(audio["sample_rate"]) == report["audio"]["sample_rate"] == 24000
assert abs(float(probe["format"]["duration"]) - float(report["duration"])) <= 0.05
assert state["state"] == "completed"
assert state["factual_review_status"] == "verified"
assert quality["status"] == "completed"
assert len(set(selected)) >= 4
assert selected == report["asset_ids"]
assert report["subtitle"]["present"] is True
assert report["subtitle_region"]["y"] >= 1120
print(json.dumps({
    "status": "pass",
    "duration": report["duration"],
    "asset_count": len(selected),
    "distinct_assets": len(set(selected)),
    "state": state["state"],
    "quality": quality["status"]
}, ensure_ascii=False))
'@
& $QualificationPython -c $QualificationCheck
~~~

Expected: one JSON object with status pass, duration 38.4, asset_count 5, distinct_assets 5, state completed, and quality completed.

- [ ] **Step 5: Verify the topic-only snapshot**

Run:

~~~powershell
$QualificationTopicOnly = Get-Content -Raw -Encoding UTF8 'dist/director/director_06b00f079b94d3e8/video_job_state.json' | ConvertFrom-Json
$QualificationTopicOnlyQuality = Get-Content -Raw -Encoding UTF8 'dist/director/director_06b00f079b94d3e8/director_quality_report.json' | ConvertFrom-Json
Write-Output "state=$($QualificationTopicOnly.state)"
Write-Output "quality=$($QualificationTopicOnlyQuality.status)"
Write-Output "factual=$($QualificationTopicOnly.factual_review_status)"
~~~

Expected:

- state quality_check
- quality review_required
- factual review_required

Audit gate: no fake-provider artifact may be described as a real-provider result.

## Task 7: Isolate and document the real-provider blocker

**Files:**

- Read: dist/director/provider_failures/director_ec229e6efe2c340d/director_report.json
- Read: dist/director/provider_failures/director_ec229e6efe2c340d/video_job_state.json
- Read: src/factory/director/provider.py
- Create: reports/CODEX_PROVIDER_BLOCKER_003.md

- [ ] **Step 1: Verify the failure snapshot is separate from the completed job**

Run:

~~~powershell
$QualificationFailureDir = 'E:\project\OpenClaw_VideoFactory\dist\director\provider_failures\director_ec229e6efe2c340d'
Get-ChildItem -LiteralPath $QualificationFailureDir -File | Select-Object Name,Length
Get-Content -Raw -Encoding UTF8 "$QualificationFailureDir\director_report.json"
Get-Content -Raw -Encoding UTF8 "$QualificationFailureDir\video_job_state.json"
~~~

Expected:

- exactly the sanitized failure report and failure state are required evidence
- error code director_provider_failed
- reason nonzero_exit
- exit_code 1
- no MP4, timeline, subtitle, raw prompt, raw output, or credentials in the failure directory

- [ ] **Step 2: Verify provider adapter isolation controls**

Run:

~~~powershell
rg -n -- "--ephemeral|read-only|--skip-git-repo-check|--output-schema|--output-last-message|shell=False|timeout_seconds|max_output" src/factory/director/provider.py tests/video/test_director_provider.py tests/director
rg -n "danger-full-access|workspace-write|--model|--profile|--add-dir|resume|codex login" src/factory/director
~~~

Expected:

- required safe flags and limits are present
- forbidden flags/actions are absent from production provider invocation

- [ ] **Step 3: Perform a structural, content-free cache probe**

This step reads structure only and prints no model names, instructions, tokens, paths from the JSON, or other values.

Run:

~~~powershell
$QualificationCacheProbe = @'
import json
from pathlib import Path

path = Path(r"C:\Users\Admin\.codex\models_cache.json")
result = {
    "cache_exists": path.is_file(),
    "json_valid": False,
    "model_count": 0,
    "missing_base_instructions_count": 0,
}
if path.is_file():
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        models = value.get("models", []) if isinstance(value, dict) else []
        if not isinstance(models, list):
            models = []
        result["json_valid"] = isinstance(value, dict)
        result["model_count"] = len(models)
        result["missing_base_instructions_count"] = sum(
            1 for item in models
            if isinstance(item, dict) and "base_instructions" not in item
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        pass
print(json.dumps(result, sort_keys=True))
'@
& $QualificationPython -c $QualificationCacheProbe
~~~

Interpretation:

- if missing_base_instructions_count is greater than zero, the recorded environment blocker is independently supported
- if the structure differs or cannot be parsed, write provider_cache_structure_inconclusive; do not open or print the cache
- do not edit, rename, delete, refresh, or replace the cache

- [ ] **Step 4: Prove the project does not depend on the cache file directly**

Run:

~~~powershell
rg -n "models_cache\.json|base_instructions|C:\\Users\\Admin\\.codex" generate_video.py src/factory/director video_factory schemas tests
~~~

Expected: no project production code reference to the user cache path or base_instructions field.

- [ ] **Step 5: Write CODEX_PROVIDER_BLOCKER_003.md**

The report must contain:

~~~markdown
# Codex Provider Blocker 003

## Classification
Environment-level Direct Codex CLI prerequisite failure, isolated from the Video Factory implementation.

## Structured evidence
Record director_provider_failed, nonzero_exit, and exit code 1 from the isolated failure report.

## Cache structure evidence
Record only cache existence, JSON validity, model count, and missing base_instructions count.

## Project isolation evidence
Record that project source does not read or write the Codex cache and that provider safety flags remain enforced.

## Security boundary
No raw cache content, prompt, response, stdout, stderr, credential, OAuth material, model name, or absolute provider output is retained.

## Current result
PASS_LOCAL_PROVIDER_BLOCKED if all local gates pass; otherwise FAIL_IMPLEMENTATION.
~~~

Audit gate: no codex exec invocation and no Codex environment mutation occurred.

## Task 8: Write the separately authorized provider recovery plan

**Files:**

- Create: reports/CODEX_PROVIDER_RECOVERY_PLAN_003.md

No command in this task is executed. The report describes a future authorization package.

- [ ] **Step 1: Define the future recovery boundary**

The recovery plan must state:

- it is a separate task requiring Jovi's explicit authorization
- it may back up and rename only C:\Users\Admin\.codex\models_cache.json
- it may write the backup only under E:\Claude_allow\Download\codex-provider-recovery-003\
- it may not modify config.toml, OAuth, login state, Profile, selected model, OpenClaw, Feishu, Gateway, Binding, or Cron
- it may not hand-edit cache JSON
- it permits exactly one isolated CLI smoke and, after that passes, exactly one real Video Factory acceptance run

- [ ] **Step 2: Include the exact future backup and path-verification commands**

Put these commands in the recovery plan, labeled NOT EXECUTED:

~~~powershell
$RecoveryCache = [System.IO.Path]::GetFullPath('C:\Users\Admin\.codex\models_cache.json')
$RecoveryExpected = [System.IO.Path]::GetFullPath('C:\Users\Admin\.codex\models_cache.json')
if ($RecoveryCache -ne $RecoveryExpected) { throw 'provider_cache_path_mismatch' }
if (-not (Test-Path -LiteralPath $RecoveryCache -PathType Leaf)) { throw 'provider_cache_missing' }
$RecoveryBackupDir = 'E:\Claude_allow\Download\codex-provider-recovery-003'
New-Item -ItemType Directory -Path $RecoveryBackupDir -Force | Out-Null
$RecoveryHashBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $RecoveryCache).Hash.ToLowerInvariant()
Copy-Item -LiteralPath $RecoveryCache -Destination "$RecoveryBackupDir\models_cache.before.json" -Force
$RecoveryBackupHash = (Get-FileHash -Algorithm SHA256 -LiteralPath "$RecoveryBackupDir\models_cache.before.json").Hash.ToLowerInvariant()
if ($RecoveryHashBefore -ne $RecoveryBackupHash) { throw 'provider_cache_backup_hash_mismatch' }
~~~

- [ ] **Step 3: Include the reversible cache-isolation commands**

Put these commands in the recovery plan, labeled NOT EXECUTED:

~~~powershell
$RecoveryQuarantine = "$RecoveryBackupDir\models_cache.quarantined.json"
Move-Item -LiteralPath $RecoveryCache -Destination $RecoveryQuarantine
if (Test-Path -LiteralPath $RecoveryCache) { throw 'provider_cache_isolation_failed' }
if (-not (Test-Path -LiteralPath $RecoveryQuarantine)) { throw 'provider_cache_quarantine_missing' }
~~~

The plan must say that the original remains recoverable at the quarantine path and is never deleted.

- [ ] **Step 4: Include the future isolated CLI smoke**

Put this command in the recovery plan, labeled NOT EXECUTED:

~~~powershell
$RecoverySandbox = 'E:\Claude_allow\Download\codex-provider-recovery-003\sandbox'
New-Item -ItemType Directory -Path $RecoverySandbox -Force | Out-Null
'Return {"status":"ok"} only.' | codex.cmd exec --ephemeral --sandbox read-only --skip-git-repo-check --ignore-user-config --color never -C $RecoverySandbox -
~~~

Success criteria:

- exit code 0
- no workspace writes
- no login, model, Profile, OAuth, or configuration change
- newly created cache, if any, parses and every model record has base_instructions

Failure action:

- do not retry
- restore the quarantined cache using Move-Item only after confirming no new cache would be overwritten
- record the actual failure

- [ ] **Step 5: Include the future real Director acceptance command**

This command is allowed only after the isolated smoke passes and is labeled NOT EXECUTED:

~~~powershell
$RecoveryPython = 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe'
& $RecoveryPython generate_video.py --topic-file examples/ai_director_demo/topic.txt --factual-brief examples/ai_director_demo/factual_brief.json --director-provider codex-cli --output-name pink_pig_modbus_ai_demo.mp4
~~~

Success criteria:

- CLI exit 0
- director_report provider is codex-cli and error is null
- 5–9 scenes
- assets all come from Registry
- VideoJob state completed
- real MP4 is 1080x1920, 30 fps, H.264, AAC, 25–60 seconds
- complete FFmpeg decode passes
- render report matches independent ffprobe
- no raw prompt/output, credential, cache content, or absolute path retained

- [ ] **Step 6: Include rollback and stop conditions**

The future plan must require:

- restore the backed-up cache if the official CLI does not regenerate a valid cache
- never delete either cache copy until success is independently audited
- no second smoke or full provider retry without a new decision
- no AI Director code changes as a response to a cache failure
- no READY marker until the real full-chain acceptance passes

Audit gate: CODEX_PROVIDER_RECOVERY_PLAN_003.md is executable but none of its mutation or provider commands ran during qualification.

## Task 9: Reconcile specialist findings and run a fresh final review

**Files:**

- Read: the three specialist responses
- Read: the four draft reports
- No subagent writes

- [ ] **Step 1: Collect all three specialist responses**

For each response, Luna records:

- task name
- files reviewed
- commands used
- PASS/FAIL findings
- exact file/line for findings
- whether the subagent changed any file

- [ ] **Step 2: Reproduce every adverse finding**

Rules:

- use the smallest read-only command that confirms or rejects the finding
- if reproduced, include it in the appropriate report
- if rejected, record the contradictory evidence and why
- do not edit implementation
- if a local defect is reproduced, final result is FAIL_IMPLEMENTATION

- [ ] **Step 3: Ask the provider reviewer to audit the fresh media evidence**

Send this follow-up:

~~~text
The main agent has completed authoritative tests and media checks.
Read only the current completed fake-provider job, topic-only state, isolated provider failure directory, and the draft qualification reports.
Do not run tests, FFmpeg, codex exec, or write files.
Confirm that:
1. completed fake and failed real-provider snapshots are not mixed;
2. topic-only remains quality_check/review_required;
3. report claims match the current JSON files;
4. no real-provider success is claimed.
Return PASS/FAIL with exact evidence paths.
~~~

- [ ] **Step 4: Spawn a fresh final reviewer**

Use a new subagent named qualification_final_reviewer:

~~~text
Perform an independent, read-only final review of AI-DIRECTOR-PHASE2-FINAL-QUALIFICATION-003 in E:\project\OpenClaw_VideoFactory.
Read the Change Request, Phase 2 implementation report, PHASE2_GIT_AUDIT_003.md, CODEX_PROVIDER_BLOCKER_003.md, CODEX_PROVIDER_RECOVERY_PLAN_003.md, current Git status, current job JSON artifacts, and current test evidence reported by the main agent.
Do not modify files, run codex exec, repair cache, or change Git.
Check internal consistency, overclaims, missing evidence, forbidden-surface changes, and whether the proposed terminal result follows this mapping:
- READY_FOR_REAL_PROVIDER_TEST only when local gates pass and no provider environment blocker remains.
- PASS_LOCAL_PROVIDER_BLOCKED when local gates pass and the environment blocker remains.
- FAIL_IMPLEMENTATION when a local gate fails.
Return APPROVE or CHANGES_REQUIRED with exact reasons.
~~~

- [ ] **Step 5: Resolve final review**

- APPROVE: proceed to Task 10
- CHANGES_REQUIRED caused by report inconsistency: correct only the allowed reports, then ask the same reviewer for one follow-up review
- CHANGES_REQUIRED caused by source/test/media defect: do not fix; final result FAIL_IMPLEMENTATION
- reviewer unavailable: report independent_final_review_not_performed and do not claim READY_FOR_REAL_PROVIDER_TEST

## Task 10: Write final qualification report and synchronize records

**Files:**

- Create: reports/PHASE2_FINAL_QUALIFICATION_003.md
- Modify: .gitignore
- Modify: tasks/todo.md
- Modify: 05-AI-Director与素材智能.md

- [ ] **Step 1: Select the terminal result deterministically**

Use this order:

1. Any reproducible local test, contract, media, boundary, or security failure -> FAIL_IMPLEMENTATION.
2. All local gates pass and the cache/provider blocker remains -> PASS_LOCAL_PROVIDER_BLOCKED.
3. All local gates pass and no current provider blocker remains -> READY_FOR_REAL_PROVIDER_TEST.

Given the current known cache evidence and the prohibition on recovery, the expected result is PASS_LOCAL_PROVIDER_BLOCKED. Record another result only when this run's evidence proves it.

- [ ] **Step 2: Write PHASE2_FINAL_QUALIFICATION_003.md**

Use these exact sections:

~~~markdown
# AI Director Phase 2 Final Qualification 003

## 1. Scope and non-goals
State that this was read-only qualification plus recovery-plan design.

## 2. Branch, HEAD, index, and remote evidence
Reference PHASE2_GIT_AUDIT_003.md and record literal results.

## 3. Contract and single-pipeline audit
Record interfaces, schemas, lifecycle compatibility, Registry selection, and run_job reuse.

## 4. Authoritative tests
Record exact commands, exit codes, and passed counts.

## 5. Media and report evidence
Record ffprobe, decode, state, quality, subtitle region, and asset parity.

## 6. Provider isolation
Reference CODEX_PROVIDER_BLOCKER_003.md and distinguish project evidence from environment evidence.

## 7. Independent reviews
Record the three specialist results and final reviewer decision.

## 8. Forbidden-surface audit
Record unchanged hashes and absence of Codex/OpenClaw/Feishu/Gateway/OAuth/Cron/Gate mutations.

## 9. Recovery handoff
Reference CODEX_PROVIDER_RECOVERY_PLAN_003.md and state that it was not executed.

## 10. Remaining debt
Retain real-provider acceptance, provider recovery authorization, formal Gate, orchestration, Feishu, and automation debt.

## Final result
Write exactly one allowed terminal result.
~~~

The report must not contain AI_DIRECTOR_PHASE2_READY.

- [ ] **Step 3: Append exact .gitignore exceptions if required**

First run:

~~~powershell
git check-ignore -q -- reports/PHASE2_FINAL_QUALIFICATION_003.md
$QualificationFinalIgnored = $LASTEXITCODE
git check-ignore -q -- reports/PHASE2_GIT_AUDIT_003.md
$QualificationGitIgnored = $LASTEXITCODE
git check-ignore -q -- reports/CODEX_PROVIDER_BLOCKER_003.md
$QualificationBlockerIgnored = $LASTEXITCODE
git check-ignore -q -- reports/CODEX_PROVIDER_RECOVERY_PLAN_003.md
$QualificationRecoveryIgnored = $LASTEXITCODE
~~~

If any exit code is 0, append without deleting or reordering existing rules:

~~~gitignore
!reports/PHASE2_FINAL_QUALIFICATION_003.md
!reports/PHASE2_GIT_AUDIT_003.md
!reports/CODEX_PROVIDER_BLOCKER_003.md
!reports/CODEX_PROVIDER_RECOVERY_PLAN_003.md
!reports/change_requests/AI-DIRECTOR-PHASE2-FINAL-QUALIFICATION-003.json
~~~

- [ ] **Step 4: Append the Obsidian qualification checkpoint**

Append to:

E:/AI_Tools/Obsidian/Data/notes-personal/codex_memory/03-项目记忆/OpenClaw_VideoFactory/05-AI-Director与素材智能.md

The new section must include:

- task name AI-DIRECTOR-PHASE2-FINAL-QUALIFICATION-003
- actual branch and HEAD
- actual 32+/273+/5 test counts
- media result
- final reviewer result
- terminal qualification result
- provider blocker classification
- recovery report link
- formal PROJECT_STATUS unchanged
- next action is provider recovery authorization, not AI Director feature expansion or Feishu

- [ ] **Step 5: Recheck the six dirty-file hashes**

Repeat Task 1 Step 3 and compare all six literal hashes.

Expected: all six unchanged. Any mismatch is a boundary failure unless the file was independently changed by Jovi during execution; if so, record external_concurrent_change and do not attribute it to qualification.

- [ ] **Step 6: Run final mechanical checks**

Run:

~~~powershell
git diff --check
git status --short --untracked-files=all
git diff --cached --name-only
git check-ignore -q -- reports/PHASE2_FINAL_QUALIFICATION_003.md
$QualificationFinalTrackable = $LASTEXITCODE
git check-ignore -q -- reports/PHASE2_GIT_AUDIT_003.md
$QualificationGitTrackable = $LASTEXITCODE
git check-ignore -q -- reports/CODEX_PROVIDER_BLOCKER_003.md
$QualificationBlockerTrackable = $LASTEXITCODE
git check-ignore -q -- reports/CODEX_PROVIDER_RECOVERY_PLAN_003.md
$QualificationRecoveryTrackable = $LASTEXITCODE
Write-Output "final_trackable=$QualificationFinalTrackable"
Write-Output "git_trackable=$QualificationGitTrackable"
Write-Output "blocker_trackable=$QualificationBlockerTrackable"
Write-Output "recovery_trackable=$QualificationRecoveryTrackable"
~~~

Expected:

- git diff --check exits 0
- index remains empty
- all four trackable values are 1
- only allowed audit records changed during this task

- [ ] **Step 7: Close tasks/todo.md and stop**

Mark each qualification checklist item complete only if its actual gate ran. Append:

~~~markdown
### Review — AI-DIRECTOR-PHASE2-FINAL-QUALIFICATION-003

- Local qualification result: record the actual terminal result.
- Director/video/legacy counts: record literal results.
- Independent review: record APPROVE or CHANGES_REQUIRED.
- Provider recovery: plan only; not executed.
- Formal P0/P1/P2 status: unchanged.
- No commit, push, provider invocation, cache/config/OAuth/Profile/model mutation, OpenClaw, Feishu, Gateway, Binding, Cron, or new AI Director feature work occurred.
~~~

Stop immediately. Do not execute CODEX_PROVIDER_RECOVERY_PLAN_003.md and do not begin Feishu, VideoClaw, orchestration, automation, or formal Gate work.

## Self-review checklist for the plan author

- [x] Spec coverage: Git audit, local qualification, provider isolation, recovery design, independent subagents, final report, and stop conditions all have named tasks.
- [x] Placeholder scan: no deferred implementation step or unspecified test remains.
- [x] Type consistency: DirectorScript, Storyboard, AssetSelectionReport, DirectorQualityReport, VideoJob State, and report filenames are consistent across tasks.
- [x] Boundary consistency: implementation and provider environment remain read-only; only reports, todo, exact ignore exceptions, and one Obsidian page are writable.
- [x] Evidence consistency: Luna executes authoritative commands; subagents review independently and never substitute for test or media evidence.
