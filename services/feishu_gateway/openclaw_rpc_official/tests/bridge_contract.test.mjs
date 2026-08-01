import assert from "node:assert/strict";
import test from "node:test";

import { MINIMUM_SCOPES, validateLocalBridgeRequest } from "../src/bridge_contract.mjs";

test("allows only the documented minimum scope and local method set", () => {
  assert.deepEqual(MINIMUM_SCOPES, ["operator.read"]);
  assert.equal(validateLocalBridgeRequest({ method: "health", params: {} }).method, "health");
  assert.equal(validateLocalBridgeRequest({ method: "agent.request", params: { agentId: "video-factory" } }).method, "agent.request");
});

test("rejects arbitrary agents, tools, models, and management fields", () => {
  assert.throws(() => validateLocalBridgeRequest({ method: "agent.request", params: { agentId: "other" } }), /bridge_agent_forbidden/);
  assert.throws(() => validateLocalBridgeRequest({ method: "health", params: { tool: "shell" } }), /bridge_privileged_field_forbidden/);
  assert.throws(() => validateLocalBridgeRequest({ method: "channels.stop", params: {} }), /bridge_method_forbidden/);
});
