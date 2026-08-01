# Full Agent Proxy Validation

Result: `FULL_AGENT_PROXY_UNSUPPORTED_OR_UNPROVEN`.

OpenClaw exposes `api.runtime.agent.runEmbeddedAgent`, a trusted-plugin low-level embedded runner. It does not, from the reviewed public surface, provide a host-managed forwarding operation that reuses the current `video-factory` route exactly. A manual call would need to reconstruct session, workspace, prompt, delivery, reply, and policy semantics; that does not meet the required full-agent equivalence proof.

No proxy was implemented and no model call was made.
