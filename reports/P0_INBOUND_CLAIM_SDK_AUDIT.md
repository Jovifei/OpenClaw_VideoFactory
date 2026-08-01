# P0 inbound_claim SDK audit (016)

## Result

`INBOUND_CLAIM_DID_NOT_BLOCK_ROUTER`.

Secondary independent blocker: `INBOUND_CLAIM_METADATA_INSUFFICIENT`.

This is a read-only audit of the installed OpenClaw 2026.7.1 runtime. No plugin, code, configuration, Binding, consumer, Gateway, model, Agent, or Cron was changed.

## What the SDK supports

- Native plugins have a supported `definePluginEntry` entry contract (`plugin-entry-R9cUrV0y.d.ts:125-166`).
- `OpenClawPluginApi.on` accepts `inbound_claim` with optional `priority` and `timeoutMs` (`types-DaHgOqFX.d.ts:12298-12300`).
- The hook result is `{ handled: boolean, reply?: ReplyPayload }` (`hook-types-DQ9eTy2x.d.ts:551-555`), so a claimed event could short-circuit a dispatch if it reaches the hook.

## Why the current route cannot use it

The generic hook runner has `runInboundClaim` (`hook-runner-global-Cucx8m-W.js:689-696`), but the installed dispatch contains no generic call to it. The only inbound-claim call is `runInboundClaimForPluginOutcome` at `dispatch-V82RCNJs.js:1501-1508`, inside the `pluginOwnedBinding` branch. That branch is guarded by `pluginOwnedBindingRecord` and `isPluginOwnedSessionBindingRecord` at `dispatch-V82RCNJs.js:1301-1307`.

The target group currently uses the existing core route Binding for `video-factory`; it is not a plugin-owned conversation Binding. Therefore a native plugin registered with `api.on("inbound_claim", ...)` would not be called before this Router/Agent path. A plugin cannot truthfully claim or block the current route without a Binding/core-routing change, both prohibited in 016.

## Why card metadata is not sufficient anyway

The Feishu monitor parser does receive callback fields (`operator`, `token`, `action.tag/value`, `open_message_id`, and `chat_id`) at `monitor.account-BE_Pfm_n.js:5634-5668`. The built-in handler then creates a synthetic text event at `monitor.account-BE_Pfm_n.js:3411-3429` with a generated `card-action-<token>` message id, sender identity, chat id, text message type, and command text. The original callback source, action tag/value, named token, and open chat id are not preserved as typed hook fields.

The canonical mapper exposes only the fields listed in `message-hook-mappers-BK8VuspZ.js:143-226`; its metadata contains ordinary routing/media fields and has no `raw_message`, `card.action.trigger`, or raw action object. The inbound-claim types likewise do not provide a raw callback field (`hook-types-DQ9eTy2x.d.ts:144-235`). A string such as `/card button {"vf_action":"..."}` would not satisfy the required trust boundary.

## Gate decision

The first blocking layer for the current production route is the missing pre-Router claim invocation: `INBOUND_CLAIM_DID_NOT_BLOCK_ROUTER`. Even if that invocation were added through a permitted route, the current synthetic event would fail the required trusted card source/action metadata gate: `INBOUND_CLAIM_METADATA_INSUFFICIENT`.

The fake card probe and plugin prototype were not created because the feasibility gate failed. R3/R4/R5 were not advanced.
