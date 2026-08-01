# MiMo multimodal routing plan — deferred

Status: `deferred_until_preingest_barrier_passes`; no model configuration has been changed.

Future requirement only, not applied in this task:

- `xiaomimimo/mimo-v2.5` is the multimodal candidate.
- `xiaomimimo/mimo-v2.5-pro` is text-only.
- A multimodal request must select only multimodal candidates.
- A `mimo-v2.5` timeout must not fall back to `mimo-v2.5-pro`.
- If no multimodal candidate is available, return `multimodal_model_unavailable`.

## Capability labels and selection invariant

| Candidate | Capability label | Eligible for multimodal request |
| --- | --- | --- |
| `xiaomimimo/mimo-v2.5` | `multimodal` | yes |
| `xiaomimimo/mimo-v2.5-pro` | `text_only` | no |

Selection is capability-filtered before invocation. The text-only candidate must never be selected as fallback for a multimodal request. A timeout, unavailable route, or failure of every eligible multimodal candidate resolves to the deterministic error `multimodal_model_unavailable`; it must not silently downgrade to text-only execution.

This is an architecture requirement only. It neither enables attachment model calls nor changes models, fallbacks, Runtime, OAuth, plugins, or OpenClaw configuration.

Before any future change, inspect the live schema to identify the exact capability and fallback fields, back up the configuration, apply the smallest model-routing-only semantic diff, verify a multimodal failure path, and restore the backup if validation fails. No model, fallback, Runtime, OAuth, or plugin configuration was changed in this task.
