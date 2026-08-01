# P0 Live Media Qualification 012 — Baseline Before

Captured 2026-07-20 (Asia/Shanghai), before recording fresh R2/R2V qualification. This is a read-only baseline; no production configuration, Gateway, Agent, Binding, Cron, model, or tool policy changed.

## Runtime and topology

- `openclaw config validate`: PASS.
- Configuration SHA-256: `d6a97f1025698c08f086c1ee565e1aac1ad30116037e4f135688edbb1171be8c`.
- Router: `xiaomimimo/mimo-v2.5-pro`; fallback remains the same text-only model.
- Media scope: image/audio/video deny rules for the target Feishu group prefix; default allow elsewhere.
- Agents: 17; Bindings: 14; Cron: 4.
- Target group consumer: 1; `video-factory` Binding: 1; internal analyzer Bindings: 0.
- MCP probe: ingest 1 tool/0 diagnostics; analyzers 3 tools/0 diagnostics.

## Event candidates

- Latest PNG receipt: message `om_***9de9`, 17,247 bytes, `image.png`.
- Current bare MP4 receipt: message `om_***27b7`, 52,037 bytes, `p0-video-analysis-test.mp4`.
- IDs are intentionally masked; full values remain only in the original local Channel/session evidence.
- Prior real R2 failure remains preserved as `R2_FAILED:ANALYZER_CALLED_AFTER_INGEST`.

## Qualification boundary

R0 and R1 are retained as PASS. R2 and `R2V_VIDEO_INGRESS_ONLY` are pending parent verification. R3-R5 are NOT_RUN. P0 remains `conditional_not_passed`.

## Git baseline

The path is a Git work tree on `phase/p0-gate-correction`, but it has no commit/HEAD and no remote was reported; workspace files are currently untracked. Publication is therefore not authorized or possible without a reviewed repository/remote boundary.
