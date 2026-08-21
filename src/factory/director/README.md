# Pink Pig AI Director Contract (003)

`Director.create_storyboard(topic)` remains the stable caller-facing
interface. `AIDirector` supplies the local implementation through an injected
`DirectorProvider`.

The provider returns only `DirectorDraft` JSON. The Python layer validates the
draft, injects the real Pink Pig registry/IP fields, creates deterministic
scene IDs and duration intents, validates the existing `Storyboard` schema,
and leaves asset selection and rendering to `video_factory/`.

The production adapter is `CodexCliDirectorProvider`. It invokes Direct Codex
CLI with an ephemeral read-only sandbox, a JSON Schema output constraint, a
bounded timeout, and no model/profile/config mutation. Tests use an offline
fake provider. Provider errors are `FactoryContractError` values with only
safe diagnostic context.

003 accepts manually approved evergreen embedded-engineering topics. It does
not perform source research, AI-hot-topic verification, Feishu delivery,
OpenClaw orchestration, lifecycle persistence, or automated publishing.

## Phase 2 staged extension

The compatible Phase 2 path is `topic -> DirectorScript ->
StoryboardAssembler -> AssetSelector -> existing run_job()`. `ScriptPlanner`
validates 5–9 beats, injects stable IDs/topic digest/style, and allows one
bounded 75–84 quality retry. `StoryboardAssembler` injects registry/IP/
composition fields; `AssetSelector` chooses render-ready Registry assets
deterministically and writes `asset_selection.json`. Provider output never
contains asset IDs, paths, registry versions, scene IDs, or render parameters.

`AIDirector(workflow="phase2")` uses this staged path while default
`workflow="auto"` preserves 003 fake-provider compatibility. A verified brief
with at least two first-party sources is required for `completed`; topic-only
candidates remain `review_required` at `quality_check`. The local
`VideoJobStateMachine` writes atomic snapshots only; it is not a database,
scheduler, retry engine, Feishu integration, or OpenClaw state store.

## Remediation 004

Every Phase 2 planning, storyboard, validation, rendering, and quality
exception is converted to a structured error and leaves a job-local
`video_job_state.json` in `failed` with a monotonic revision. Reused Director
instances clear prior outputs, and current-topic failure reports are sanitized
before persistence. Provider recovery remains a separate task; this package
does not invoke or repair the Codex environment.
