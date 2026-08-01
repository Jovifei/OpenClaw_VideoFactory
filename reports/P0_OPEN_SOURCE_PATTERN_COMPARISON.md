# Pattern comparison

| Source | Adoptable pattern | Not reusable |
|---|---|---|
| official Lark SDK | WS message/card dispatcher and ACK | none of its samples as production policy |
| Hermes | explicit origin/session envelope | complete runtime/session implementation |
| cc-connect | single shared WS owner and dedupe concept | media base64 forwarding, multi-platform fan-out, short in-memory dedupe |
| ComfyUI connector | callback state machine and replay concepts | process-local state and project-specific ingress |

The project retains its existing receipt/ingest/Analyzer implementation rather than importing a third-party media pipeline.
