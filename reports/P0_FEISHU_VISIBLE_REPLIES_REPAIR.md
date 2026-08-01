# P0 Feishu visible-replies repair

Date: 2026-07-12 (Asia/Shanghai)  
Authorization: Jovi explicitly requested repair after the target group repeatedly produced no Feishu reply.  
Scope: P0 only. No P1 work, model download, driver change, Cron registration, Jianying automation, or Douyin publishing occurred.

## Confirmed root cause

`messages.groupChat.visibleReplies` was `message_tool`. OpenClaw maps that group-chat mode to message-tool-only delivery, which suppresses ordinary model final text from automatic channel delivery. That exactly matched the observed target-group session: a successful `xiaomimimo/mimo-v2.5` final response plus Feishu `dispatch complete (queuedFinal=false, replies=0)`.

Source evidence was inspected read-only:

- `C:\Users\Admin\AppData\Roaming\npm\node_modules\openclaw\dist\source-reply-delivery-mode-WUrUYZQd.js:52-89` maps `message_tool` to automatic-source-delivery suppression.
- `C:\Users\Admin\.openclaw\npm\projects\openclaw-feishu-dc69f44688\node_modules\@openclaw\feishu\dist\monitor.account-Cl-QnhPV.js:1878-1883` disables the no-visible-reply fallback for message-tool-only delivery; line 2997 records the final reply count.

## Applied minimal repair

| Command | Exit | Actual result | Evidence |
|---|---:|---|---|
| `openclaw config get messages.groupChat.visibleReplies` | 0 | Returned `message_tool`. | Terminal evidence; no sensitive output. |
| Copy current config to `~/.openclaw/backups/openclaw.json.p0-visible-replies-20260712-211707.bak`; SHA-256 | 0 | Backup created; SHA-256 `9CAC5C561E7C0918899FEF8BE08BA6907E1ACB29F82FB3CFAB17EF7F91693A0A`. | External backup, not copied into the repository. |
| `openclaw config patch --file reports/patches/p0_group_visible_replies_automatic.json5 --dry-run --json` | 0 | One operation; schema and SecretRef resolvability checks passed. | `reports/patches/p0_group_visible_replies_automatic.json5` |
| `openclaw config patch --file reports/patches/p0_group_visible_replies_automatic.json5` | 0 | Applied one config update. | Same patch file. |
| `openclaw config validate` and `openclaw config get messages.groupChat.visibleReplies` | 0 | Config valid; value is now `automatic`. | Terminal evidence; no sensitive output. |
| `openclaw gateway restart --safe --json` | 0 | Gateway stopped safely with no active work. This host's scheduled-task service did not automatically relaunch. | Terminal evidence. |
| `openclaw gateway start`; `openclaw gateway probe`; `openclaw channels status --probe` | 0 | Gateway accepted admin read probe; all 13 configured Feishu accounts including `zhongshu` are `running, works`. | Terminal evidence; target peer remains `oc_***1555`. |

## Plugin attempt and rollback

The initially suspected Feishu plugin drift was investigated under Jovi's authorization.

- `openclaw plugins update feishu --dry-run` exited 1 before writing because the recorded npm range was unsupported by that command.
- An exact compatible plugin `@openclaw/feishu@2026.6.10` was installed after a backup, but its Gateway restart left the service unavailable. It was immediately rolled back using the supported installer to `@openclaw/feishu@2026.6.6`.
- The current Gateway is healthy with Feishu `2026.6.6`; source analysis proved the plugin version was not the root cause. No configuration secret was copied to reports.

## Residual risk and rollback

Risk: `visibleReplies` is a group-chat-wide OpenClaw delivery policy, so existing bots with normal model finals may now reply automatically instead of requiring an explicit message tool call. This was necessary to repair the confirmed shared delivery setting and was explicitly authorized by Jovi. Existing account bindings, target-group allowlist, mention requirement, sender allowlist, models, and Cron entries were not changed.

Rollback: restore the timestamped external config backup above, run `openclaw config validate`, then `openclaw gateway start` if this Windows scheduled-task service does not auto-relaunch after safe restart. The narrow logical rollback is to set only `messages.groupChat.visibleReplies` back to `message_tool` using the same validated patch workflow.

## Pending acceptance proof

Text delivery remains pending until a new real Feishu mention-picker message produces a visible bot reply and a nonzero final-reply count. Do not mark P0 passed before that proof and the remaining file/video/Codex/lark smoke items complete.
