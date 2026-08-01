# Single-consumer proof

The recommended production cutover has one Feishu long-connection owner: the project Gateway. The OpenClaw core Feishu Binding is disabled before the project connection starts; the two must never overlap. OpenClaw remains the sole Agent/session/model runtime and does not open a Feishu consumer.

The offline PoC has no network listener and one event dispatcher instance. It asserts duplicate message and callback suppression. Before production validation, instrument active WS count, process identity, event/download/reply/analyzer idempotency keys, and require all counts to show exactly one consumer.
