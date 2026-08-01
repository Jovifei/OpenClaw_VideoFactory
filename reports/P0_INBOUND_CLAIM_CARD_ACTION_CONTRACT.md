# P0 card-action inbound claim contract (016)

## Intended contract

The desired sequence is `card.action.trigger → trusted card event → deterministic claim → no Router/LLM → ticket operation`. A valid claim would require all of: `channel=feishu`, explicit card-action source, operator identity, chat identity, action namespace/action, and a callback token or stable idempotency id. The ticket service would then validate the server-side allowlist, receipt, uploader/operator, chat, TTL, stored hash, and single-use state.

## Current feasibility

The installed core does not expose this sequence to a native plugin on the existing core Binding. It turns the callback into a synthetic text message and dispatches the ordinary Router path. The original callback is not available as a typed `inbound_claim` event, and the generic claim runner is not called for the current route.

## Safety outcome

No implementation is authorized or safe in the current runtime. Do not treat synthetic text, button labels, or model-generated text as card provenance. Do not create a plugin-owned Binding or a second consumer as a workaround. Preserve the existing 015 reports and old R3 failure.
