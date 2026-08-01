# P1-OFFLINE-CANDIDATE-FINAL-AUDIT-059

## 1. Task contract

### Goal

Turn the existing `P1_POLISH_CANDIDATE_READY_OFFLINE` outputs into one
internally consistent, hash-verified, visually reviewable handoff package.

This is the next executable step toward final delivery. It does **not** promote
P0 or P1 and does not replace the required real Feishu R3 retest.

### Current evidence

- Formal phase: `PROJECT_STATUS.yaml` remains at P0.
- Real runtime status: `R3_RESULT_REPLY_FIXED` and
  `READY_FOR_REAL_R3_RETEST`.
- Offline candidate status: `P1_POLISH_CANDIDATE_READY_OFFLINE`.
- Five final candidate Jobs are recorded in
  `reports/P1_POLISH_CANDIDATE_058.json`.
- The five Jobs have MP4, WAV, SRT, cover, quality and dry-run delivery
  artifacts and are marked `PENDING_REVIEW`.

### Live blockers

- The original Feishu group has not completed the fresh R3 result retest.
- The first visual baseline has not been approved by Jovi.
- Real P1 delivery and the formal P1 Gate remain blocked by P0.

### Allowed scope

- Repository-only Python, Node/Remotion, tests and reports.
- Rendering review stills from already generated candidate inputs.
- Read-only ffprobe/decode and SQLite/artifact inspection.
- Updating the two named OpenClaw VideoFactory Obsidian review notes after the
  repository evidence passes.

### Prohibitions

- No real Feishu message, upload, attachment, card or delivery.
- No OpenClaw, Gateway, Binding, Agent, Cron, OAuth or model change.
- No Project Gateway start and no Core Feishu lifecycle action.
- No master-video rerender, dependency upgrade, model/browser download or
  ComfyUI action.
- No `P1_READY.json`, `P1_TEST_RESULTS.json`, phase promotion or
  `PROJECT_STATUS.yaml` modification.
- No commit, push, tag, reset, clean, broad staging or deletion of existing
  Jobs/evidence.

## 2. Authoritative candidate set

The implementation must load the candidate set from
`reports/P1_POLISH_CANDIDATE_058.json`; production code must not hardcode Job
IDs. The current expected set, used only as a pre-execution cross-check, is:

| Role | Fixture/template | Current Job |
| --- | --- | --- |
| NVENC evidence | FIX-001 / protocol-frame | `job-b99e42aadbe2ae655226471a` |
| CPU evidence | FIX-001 / protocol-frame | `job-0b8f1a65ee84dad9f98a8855` |
| Engineering case | FIX-002 / engineering-case | `job-ac751a1eac2bd82bf85aec43` |
| Flow diagram | FIX-003 / flow-diagram | `job-0823a41bec7c6bd696c7bc00` |
| Code sample | SAMPLE-CODE-001 / code-explainer | `job-72554171701c3f6843de6e04` |

If the selection report does not resolve exactly these five semantic roles,
stop with:

`P1_OFFLINE_AUDIT_BLOCKED:candidate_selection`

Do not silently choose a newer directory by timestamp.

## 3. Ordered implementation increments

Each increment requires its own approved Change Request under
`reports/change_requests/` before source changes. Execute strictly in order.

### 059A — Baseline freeze

**Purpose and preconditions**

- Establish the immutable before-state.
- Confirm the five selected Jobs exist and Project Gateway process count is
  zero.

**Create**

- `reports/change_requests/P1-OFFLINE-FINAL-AUDIT-059A.json`
- `reports/P1_FINAL_AUDIT_BASELINE_059.json`

**Baseline fields**

- UTC/local timestamp and repository root;
- Git HEAD/status without staging or cleaning;
- SHA-256 of `PROJECT_STATUS.yaml`;
- selected Job IDs and semantic roles;
- per-Job state and required-file presence;
- Python, Node, npm, FFmpeg and ffprobe versions;
- Project Gateway process count;
- explicit confirmation that no external connection was opened.

Do not store environment dumps, credentials, user text, Ticket values or
private OpenClaw configuration.

**Verification**

```powershell
Get-Content -Encoding UTF8 PROJECT_STATUS.yaml
git status --short
.venv\Scripts\python.exe -m pip check
node --version
npm --version
ffmpeg -version
ffprobe -version
```

**Failure behavior**

No rollback is needed because this increment writes reports only. Missing Job,
active Project Gateway or an unreadable status file stops the task before
source edits:

`P1_OFFLINE_AUDIT_BLOCKED:baseline`

### 059B — Final artifact auditor

**Purpose**

Replace hardcoded/stale candidate reporting with a selection-driven,
fail-closed auditor.

**Create or modify**

- Create `scripts/p1_final_audit.py`.
- Create `tests/test_p1_final_audit.py`.
- Modify `scripts/p1_candidate_report.py` into a compatibility wrapper that
  uses the same selection-driven audit path; remove its old 057 Job list.
- Create `reports/change_requests/P1-OFFLINE-FINAL-AUDIT-059B.json`.

**Public command**

```powershell
.venv\Scripts\python.exe scripts\p1_final_audit.py `
  --selection reports\P1_POLISH_CANDIDATE_058.json `
  --output-json reports\P1_FINAL_AUDIT_059.json `
  --output-markdown reports\P1_FINAL_AUDIT_059.md
```

The command is read-only with respect to `jobs/` and `state/`.

**Required checks**

1. Resolve five semantic roles from the selection report.
2. Require every selected Job to be `PENDING_REVIEW`.
3. Require the expected Fixture/template pair and one NVENC plus one libx264
   FIX-001 result.
4. Require:
   `job.json`, `script.json`, `storyboard.json`, `render_input.json`,
   `voice.wav`, `captions.json`, `captions.srt`, `final_master.mp4`,
   `feishu_preview.mp4`, `cover.png`, `quality_report.json`,
   `publish_info.md`, `delivery_manifest.json`, `run_metrics.json`.
5. Recompute actual SHA-256 and compare it with SQLite artifact records and
   delivery-manifest entries where each contract supplies a hash.
6. Reject absolute paths, URL paths, `..` traversal, files outside the Job
   root and unresolved manifest references.
7. Verify delivery schema v2, `mode=dry-run`, idempotency key stability and
   absence of a real target/network action.
8. Verify quality checks are passed, media is decodable, video is
   1080x1920/30 FPS, duration matches the resolved contract, an audio stream
   exists and preview size is within the candidate limit.
9. Verify metrics contain no script/narration text, credential-shaped fields,
   environment dumps or private absolute paths.
10. Verify forbidden promotion artifacts are absent.

**Generated evidence**

- `reports/P1_FINAL_AUDIT_059.md`
- `reports/P1_FINAL_AUDIT_059.json`
- `reports/P1_FINAL_ARTIFACT_INDEX_059.json`

The artifact index records Job role, repository-relative path, size and
recomputed SHA-256. It must not contain absolute private paths.

**Tests**

Use temporary synthetic Job roots and cover:

- valid five-Job selection;
- missing artifact;
- actual/DB hash mismatch;
- actual/manifest hash mismatch;
- stale or duplicate semantic role;
- wrong encoder assignment;
- absolute path, traversal and URL rejection;
- real-delivery target or network mode rejection;
- secret/unsafe metrics rejection;
- forbidden `P1_READY.json` rejection;
- report output redaction.

**Failure/rollback**

- Never repair, regenerate or delete a failing artifact.
- Preserve the failing audit JSON with a safe error code.
- Revert only 059B source files to their pre-increment copies if its own tests
  fail; preserve the failure report.

Terminal failure:

`P1_OFFLINE_AUDIT_BLOCKED:artifact_integrity`

### 059C — Final visual review set

**Purpose**

Regenerate review stills from each final Job's actual render input and correct
the contact-sheet layout.

**Create or modify**

- Modify `remotion/scripts/render-review-stills.mjs`.
- Create `remotion/scripts/test-review-stills.mjs`.
- Create `reports/change_requests/P1-OFFLINE-FINAL-AUDIT-059C.json`.
- Generate only under `reports/p1_review_059/` and ignored Remotion temporary
  output.

**Interface**

Add a backward-compatible input:

```text
--inputs-manifest <repository-relative-json>
```

Manifest schema:

```json
{
  "schema_version": "1.0",
  "templates": {
    "protocol-frame": "jobs/p1_candidate/<job>/render_input.json",
    "engineering-case": "jobs/p1_candidate/<job>/render_input.json",
    "flow-diagram": "jobs/p1_candidate/<job>/render_input.json",
    "code-explainer": "jobs/p1_candidate/<job>/render_input.json"
  }
}
```

Rules:

- exactly four known template keys;
- repository-relative paths only;
- inputs must remain below `jobs/p1_candidate/`;
- reject URL, absolute path, traversal, missing file, duplicate resolved file
  or a template mismatch inside the input;
- protocol-frame uses the final NVENC FIX-001 input; CPU remains encoding
  evidence and is not a second visual column.

**Outputs**

- five frames per template: 0%, 25%, 50%, 75%, final;
- contact sheet with four template columns and five timeline rows;
- `review_manifest.json` with input references, frame numbers, output SHA and
  generation status;
- provisional comparison/diff evidence.

The new baseline status is always:

`provisional_pending_jovi`

Pixelmatch cannot approve brand correctness. Existing 058 stills are marked
stale after the final template changes; they remain retained as historical
evidence.

**Tests**

- exact mapping from four inputs to four compositions;
- grid coordinates: columns=templates, rows=timeline points;
- 0/25/50/75/final frame bounds;
- all unsafe path cases;
- duplicate/mismatched input rejection;
- deterministic rerun SHA;
- pixelmatch unchanged, below-threshold and above-threshold cases;
- no automatic baseline approval.

**Failure/rollback**

Delete no existing review files. Write into a new temporary 059 directory and
atomically rename only after all 20 stills and the manifest succeed. On
failure, retain the temporary failure log and stop:

`P1_OFFLINE_AUDIT_BLOCKED:visual_review_generation`

### 059D — Status reconciliation and operator handoff

**Purpose**

Make the current formal gate, offline capability and next user action
unambiguous.

**Create or modify**

- Create `reports/P1_STATUS_DRIFT_059.md`.
- Create `reports/P1_REMAINING_ACTIONS_059.md`.
- Create `reports/P1_FINAL_REVIEW_PACKAGE_059.md`.
- Replace duplicated content in `reports/NEXT_USER_ACTION.md` with one
  canonical action.
- Add a current 059 section at the top of `tasks/todo.md`; do not change old
  historical checkboxes.
- Create `reports/change_requests/P1-OFFLINE-FINAL-AUDIT-059D.json`.

**Required wording**

- Formal truth: P0 remains current and P1 remains blocked by P0.
- Capability truth: the offline P1 candidate exists and has passed only the
  checks recorded by 059.
- Unique real action: fresh original-group R3 retest.
- No report may state or imply P1 qualification, real delivery or production
  readiness.

**Obsidian update**

After all repository reports validate, update only:

- `codex_memory/03-项目记忆/OpenClaw_VideoFactory/待验证的项目/2026-07-30-P1完善候选验证清单.md`
- `codex_memory/03-项目记忆/OpenClaw_VideoFactory/待完善/2026-07-30-P1完善候选完成记录.md`

The operator executing this step must use the connected Obsidian project
record or obtain a write grant limited to those two exact files. Do not write
elsewhere in the vault.

The notes must include clickable paths for:

- five final MP4s;
- five WAV/SRT/cover sets;
- contact sheet and visual review manifest;
- NVENC/CPU evidence;
- cancellation/recovery/idempotency evidence;
- final audit and quality reports.

Every checklist row uses exactly one classification:

- 已自动验证;
- 已实现待 Jovi 审核;
- 等待真实 R3;
- 因正式阶段门禁延期;
- 上游能力阻塞.

**Failure/rollback**

If Obsidian write access is unavailable, repository reports still remain
valid, but final task status is:

`P1_OFFLINE_AUDIT_BLOCKED:obsidian_handoff`

Do not create a substitute vault or copy.

### 059E — Full verification and independent read-only review

**Purpose**

Prove the final source and report state after all 059 changes.

**Create**

- `reports/change_requests/P1-OFFLINE-FINAL-AUDIT-059E.json`
- `reports/P1_FINAL_TEST_RESULTS_059.json`
- `reports/P1_FINAL_SECURITY_SCAN_059.md`
- `reports/P1_CURRENT_STATUS_059.md`

**Required commands**

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
.venv\Scripts\python.exe scripts\v28_schema_tests.py
.venv\Scripts\python.exe -m pip check

Set-Location remotion
npm run typecheck
npm audit --omit=dev
node scripts\test-review-stills.mjs
Set-Location ..

git diff --check
```

Pester 3.4 does not support directory discovery as acceptable evidence.
Enumerate every current `tests/Test-*.ps1` file, sort by name, invoke each
explicitly with `Invoke-Pester -Script <file> -PassThru`, sum passed/failed,
and fail if any script or assertion fails.

Also:

- parse every new JSON report;
- ffprobe and bounded-decode all five final master/preview MP4s;
- verify the 20 stills and contact sheet are non-empty;
- scan changed source/reports for credential candidates without printing raw
  matches;
- scan tracked/source additions for unexpected large files;
- rerun the final auditor;
- confirm Project Gateway count remains zero;
- confirm `PROJECT_STATUS.yaml` hash equals the 059A baseline;
- confirm no external or production action occurred.

**Independent review**

One read-only reviewer may inspect only:

- `scripts/p1_final_audit.py`;
- `tests/test_p1_final_audit.py`;
- `remotion/scripts/render-review-stills.mjs`;
- `remotion/scripts/test-review-stills.mjs`;
- `reports/P1_FINAL_AUDIT_059.json`.

The reviewer must not modify files or treat its opinion as test evidence. It
must try to falsify selection integrity, hash verification, path containment,
dry-run isolation and visual mapping.

**Stop conditions**

Any unexpected source change, test failure, external process, Secret candidate,
hash drift or report inconsistency stops the task. Do not weaken a check,
regenerate a master or proceed to P0/P1 gates.

## 4. Acceptance result

All of the following are required:

- selection-driven audit passes for exactly five semantic roles;
- actual file hashes reconcile with authoritative records;
- five masters and previews pass media checks;
- final visual set contains 20 correctly mapped stills and one contact sheet;
- full Python, explicit Pester, Schema, TypeScript, dependency and security
  checks pass;
- Obsidian review notes point to the actual final artifacts;
- Project Gateway remains zero;
- `PROJECT_STATUS.yaml` is unchanged;
- no production or real Feishu action occurred.

Only then report:

```text
P1_OFFLINE_REVIEW_PACKAGE_READY
WAITING_FOR_JOVI_REVIEW_AND_REAL_R3
```

Otherwise report only:

```text
P1_OFFLINE_AUDIT_BLOCKED:<accurate_layer>
```

## 5. Next phase boundary

After 059, do not start P2. The next real operation is the existing fresh R3
test in the original Feishu group. R4, R5, P0 Gate, formal P1 qualification and
P2 implementation each require their own ordered evidence and authorization.

