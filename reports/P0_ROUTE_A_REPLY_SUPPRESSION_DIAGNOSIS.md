# P0 Route A reply-suppression diagnosis

Date: 2026-07-12 (Asia/Shanghai)  
Scope: one target-group text-message smoke investigation only. No configuration, model, Cron, driver, automation, or publishing change was made in this diagnosis.

## Observed result

The fresh target-group text event was received by `zhongshu`, dispatched to the exact `video-factory` group session, completed its MiMo model call successfully, and generated a valid Chinese response. The channel then reported `replies=0`.

The received-event log had plain text `你好`; it did **not** contain Feishu's `<at user_id="...">...</at>` mention representation. The target group is intentionally configured with `requireMention: true`. That fact requires a real mention-picker regression test, but it does **not** by itself explain the failure: the direct session evidence proves the model generated a normal reply. The proven fault boundary is therefore downstream of model completion, in OpenClaw's Feishu reply collection/delivery path.

The currently enabled Feishu plugin is version-drifted relative to the installed OpenClaw core. This is the leading compatibility hypothesis, not a confirmed root cause. Updating it would affect every Feishu account and is outside the existing target-group-only change authority; it must not be done without explicit additional authorization and a backup-plus-rollback plan.

## Evidence

| Command | Exit | Actual result | Evidence path |
|---|---:|---|---|
| `openclaw logs --plain --local-time --limit 160 --max-bytes 250000 --timeout 30000` | 0 | At 17:21:40 a plain text event was received by `zhongshu`, dispatched to `agent:video-factory:feishu:group:oc_***1555`; at 17:21:57 it completed with `replies=0`. | `reports/command_logs/112d_route_a_fresh_session_openclaw_logs.txt` |
| `openclaw sessions --agent video-factory --active 60 --limit 10 --json` | 0 | The target group session is healthy, not aborted, and reports `xiaomimimo/mimo-v2.5`; it emitted 41 output tokens. The raw transient capture was removed because it contained non-redacted identifiers. | Terminal evidence only; sanitized finding recorded here. |
| `openclaw sessions tail --agent video-factory --session-key <redacted> --tail 40` | 0 | The new run reached `model.completed` and `session.ended success` at 17:21:57. | Terminal evidence only; sanitized finding recorded here. |
| UTF-8 read of the matching session JSONL | 0 | The model's final text was `你好呀！有什么可以帮你的吗？😊`; the input did not include a mention entity. | Terminal evidence only; no raw session or message ID copied into reports. |

## Required next smoke action

The user must select the **中书省** bot from Feishu's mention picker and send one standalone message: `@中书省 你好`. The verifier must see both the `<at ...>` representation in the incoming event and a nonzero reply count or visible bot response before marking text inbound smoke as passed. If a real mention still ends in `replies=0`, retain the evidence, stop the smoke sequence, and request explicit authority for a global Feishu-plugin compatibility update.

## Risk and rollback

Risk is limited to a pending test: a non-mentioned message may be deliberately suppressed in this allowlisted, mention-required group, and an unresolved adapter issue may also prevent outbound replies. No configuration was changed. Rollback is not applicable. Do not weaken `requireMention` merely to make this test pass.
