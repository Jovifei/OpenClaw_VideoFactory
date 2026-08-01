# P0 Gateway Permission Model (024)

Status: `ENFORCED_OFFLINE`

| Capability | Gateway |
| --- | --- |
| receive message | YES |
| receive attachment | YES |
| verify identity/signature | YES |
| create OpenClaw request | YES |
| send reply/card | YES |
| model call | NO |
| Analyzer call | NO |
| GPU task | NO |
| arbitrary filesystem access | NO |
| configuration modify | NO |
| Agent create | NO |

`services/feishu_gateway/policy.py` is the executable matrix. Its validator accepts only `video-factory` requests with the required tenant/chat/sender/thread session context and rejects `analyzer`, `model`, `gpu`, and tool-selection fields. The Matrix test validates all six prohibited capabilities and four representative forbidden RPC fields.
