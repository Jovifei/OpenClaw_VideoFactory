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
