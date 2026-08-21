# AI Director Phase 2 Final Qualification 003

## Scope and authority

This is a read-only final qualification of the existing local Phase 2
implementation. It did not modify OpenClaw, Feishu, Gateway, Binding, OAuth,
Cron, `PROJECT_STATUS.yaml`, Codex cache/config/Profile/model state, or the
six pre-existing dirty user files. No commit, push, merge, reset, cleanup, or
real-provider retry was performed.

## Local implementation evidence

- `tests/director`: **32 passed**.
- `tests/video`: **273 passed**.
- `video_factory/tests`: **5 passed**.
- Legacy `generate_video.py --job tests/video/fixtures/job_offline.yaml`:
  exit 0.
- Legacy `generate_video.py --config examples/pink_pig_demo/config.yaml`:
  exit 0.
- Python compileall for `src`, `video_factory`, and `generate_video.py`:
  exit 0.
- Lifecycle/schema focused tests: **37 passed**.

## Fake-provider media evidence

The completed fake-provider snapshot is
`dist/director/director_ec229e6efe2c340d/` and contains the expected topic,
research, source, script, score, storyboard, asset selection, job, state,
timeline, subtitle, render report, quality report, and MP4 artifacts.

Independent ffprobe and full FFmpeg decode pass:

- 38.4 seconds
- 1080x1920
- 30/1 FPS
- H.264 video
- AAC audio at 24000 Hz
- five selected assets, five distinct Registry IDs
- subtitle present and subtitle region begins at y=1120
- report asset order matches `asset_selection.json`
- state `completed`, factual status `verified`, quality `completed`

The topic-only snapshot independently remains `quality_check` /
`review_required` / `review_required`, so generation is not mislabeled as
fact-verified publication.

## Contract and architecture review

PASS findings:

- Stable `Director.create_storyboard(topic)` interface.
- Closed DirectorScript semantics; provider cannot select paths or Registry
  asset IDs.
- Deterministic Storyboard assembly and Registry-only AssetSelector injection.
- Existing compiler, Composition, Pink Pig quality gate, subtitle/audio,
  renderer, and `run_job()` are used by the Phase 2 topic path.
- Provider sandbox, timeout, output cap, sanitization, and failure isolation
  controls.

FAIL findings requiring a later implementation task:

1. `generate_video.run_topic()` catches only `FactoryContractError` around
   job validation/rendering. `run_job()` can raise `ValueError`, `RuntimeError`,
   or renderer/audio errors. Such a failure can leave the Phase 2 snapshot at
   `rendering` (or `storyboard_ready` for validation outside the try block)
   instead of writing a readable `failed` snapshot.
2. Reusing an `AIDirector` instance after a prior success can leave stale
   `last_report` data when a later phase-2 attempt fails before replacing it;
   the failure path may write that stale report.
3. Strict repository-wide single-pipeline review finds the pre-existing,
   callable `src/factory/pipeline.py` / `src/factory/render.py` CandidateTts /
   captions path alongside `generate_video.py` + `video_factory/pipeline`.
   The new Director package does not invoke it, but the implementation report's
   blanket “no second pipeline” statement is too broad under the plan's strict
   gate. This is a baseline architecture debt, not a mutation made by this
   read-only audit.

These findings are not repaired in this task because the task is qualification
and provider isolation only.

## Real provider result

The isolated Direct Codex CLI attempt failed with sanitized
`director_provider_failed`, nonzero exit, and exit code 1. A content-free cache
probe found 9 valid cache model entries and 9 missing `base_instructions`
fields. Project source does not read or write that cache. Provider recovery is
documented separately and was not executed.

## Git and forbidden-surface audit

Branch/HEAD, index, merge/rebase state, six-file preservation, ignored runtime
artifact boundary, and no-new-forbidden-surface mutation all pass. The
worktree is intentionally dirty because it contains the uncommitted Phase 2
subject implementation plus six pre-existing user changes; it is not a
submission or merge proof.

Literal Git evidence:

- branch: `codex/ai-director-video-factory-phase2-001`
- HEAD: `76180a59ea662bdf168d88baaeb777d3e8eb59ef`
- remote: `origin` is the GitHub repository configured for this workspace;
  the Phase 2 branch has no remote ref and was not pushed.
- index: empty; merge/rebase/cherry-pick/revert markers absent.
- detailed boundary record: `reports/PHASE2_GIT_AUDIT_003.md`.

## Independent reviews

- Git/remote specialist: PASS for branch, HEAD, index, preserved dirty files,
  and no new forbidden-surface mutation.
- Contract/architecture specialist: PASS for public interfaces, schemas,
  Registry-only asset injection, Composition/Pink Pig gates, and `run_job()`
  reuse; FAIL for strict alternate-pipeline scope and lifecycle error paths.
- Provider/security specialist: PASS for read-only flags, timeout/output cap,
  sanitization, failure-directory separation, and 31 targeted tests; real
  provider remains blocked.
- Fresh final reviewer: APPROVED after report-only corrections for explicit
  trackability, recovery command template, readiness wording, provider-status
  scope, and required report sections.

## Provider recovery handoff

No provider recovery was executed. The future, authorization-gated command
package is [CODEX_PROVIDER_RECOVERY_PLAN_003.md](CODEX_PROVIDER_RECOVERY_PLAN_003.md).
It includes path/hash preflight, reversible quarantine/restore, one isolated
smoke, one real acceptance run, and a no-second-retry stop rule.

## Remaining debt

- Non-contract render/validation exceptions need failed-state persistence.
- Director reuse must clear or isolate `last_report` before a new attempt.
- The pre-existing `src/factory` CandidateTts/Remotion path requires a product
  decision under the strict repository-wide single-pipeline rule.
- Direct Codex CLI prerequisite remains blocked; no second provider exists.
- Topic-only output still requires factual review; AI-hot topics need date and
  source contracts.
- No database-backed lifecycle, cancellation, recovery, or long-term retry
  engine; no VideoClaw orchestration; Feishu/automation not started.
- Style quality remains non-pixel-based and some SVG-only poses may fallback.
- Formal P0/P1/P2 status remains unchanged.

## Final disposition

The local fake-provider implementation and media gates pass, but the strict
contract findings and the real provider prerequisite prevent qualification.
The correct status is:

```text
FAIL_IMPLEMENTATION
```

Provider-specific substatus (isolation only; not an overall qualification):

```text
REAL_PROVIDER_BLOCKED
```

No Phase 2 readiness marker is asserted. Formal P0/P1/P2 status remains
unchanged. The next action is a separately authorized implementation repair
for lifecycle failure snapshots and a decision on the pre-existing alternate
candidate pipeline; provider recovery is a separate, later authorization.
