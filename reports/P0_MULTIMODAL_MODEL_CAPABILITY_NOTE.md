# P0 multimodal model capability note

This is a record only; no model configuration changed in P0-PREINGEST-MODEL-BARRIER-002.

```text
xiaomimimo/mimo-v2.5
capability: multimodal

xiaomimimo/mimo-v2.5-pro
capability: text_only
```

Current incorrect chain:

```text
selected mimo-v2.5
→ timeout
→ fallback mimo-v2.5-pro
```

Future rule, deferred under `P0-MULTIMODAL-MODEL-ROUTING-001`:

```text
multimodal request
→ multimodal provider only
→ unavailable returns multimodal_model_unavailable
→ never fall back to a text-only model
```
