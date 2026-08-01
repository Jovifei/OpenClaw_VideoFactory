# P0 One-Shot Analysis Intent Smoke (014)

Status: NOT RUN.

No fake production smoke, real command, real attachment, Gateway restart, or production tool registration was performed. The requested user-led smoke must remain gated until a deterministic source for the original Feishu command message id is supplied and the implementation is authorized.

Required future sequence after the blocker is resolved: send `/analyze-next image`, verify `ANALYZE_NEXT_IMAGE_ARMED` with a redacted event trace, upload a new PNG within 120 seconds, verify exactly one matching ingest and one image Analyzer request, and retain the prior R3 failure as immutable negative evidence. Do not use a model rewrite or upload while this report is blocked.
