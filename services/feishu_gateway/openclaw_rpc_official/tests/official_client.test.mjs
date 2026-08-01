import assert from "node:assert/strict";
import test from "node:test";
import { loadOfficialGatewayClient, runOfficialDeviceConnection } from "../src/official_client.mjs";

test("loads the installed official OpenClaw client without connecting or creating identity", async () => {
  const client = await loadOfficialGatewayClient();
  assert.equal(typeof client.GatewayClient, "function");
  assert.equal(typeof client.loadDeviceAuthToken, "function");
  assert.equal(client.source.package_name, "openclaw");
});

test("pairing request uses a separate device identity and never supplies a shared token", async () => {
  let options;
  const updates = [];
  const pending = [];
  class FakeGatewayClient {
    constructor(value) { this.options = value; options = value; }
    start() {
      queueMicrotask(() => this.options.onConnectError({
        gatewayCode: "UNAUTHORIZED",
        details: { code: "PAIRING_REQUIRED", reason: "not-paired", requestId: "pairing-request-456" }
      }));
    }
    stop() {}
    async stopAndWait() {}
  }
  const result = await runOfficialDeviceConnection({
    operation: "pairing-request",
    preflightPairing: async () => ({
      ready: true,
      state_root: "C:\\private-device",
      state_acl: "current_user_only",
      device_id_redacted: "id-0123456789ab",
      protocol_version: "2026.7.1"
    }),
    loadProjectIdentity: async () => ({ deviceId: "test-device", publicKeyPem: "not-used", privateKeyPem: "not-used" }),
    createTransaction: async () => ({ attempt_id: "11111111-1111-4111-8111-111111111111" }),
    updateTransaction: async (_root, _attemptId, update) => { updates.push(update.status); },
    writePending: async (_root, metadata) => { pending.push(metadata); },
    fileExists: async () => false,
    loadClient: async () => ({ GatewayClient: FakeGatewayClient, source: { package_name: "openclaw", package_version: "2026.7.1" } })
  });
  assert.equal(result.status, "pairing_required");
  assert.equal(result.explicit_shared_token, false);
  assert.equal(options.clientName, "project-feishu-gateway");
  assert.deepEqual(options.scopes, ["operator.read"]);
  assert.equal(Object.hasOwn(options, "token"), false);
  assert.deepEqual(updates, ["connect_started", "pending_approval"]);
  assert.equal(pending.length, 1);
  assert.equal(pending[0].scopes[0], "operator.read");
});

test("missing Project identity blocks before a transaction or Gateway client is created", async () => {
  let transactionCreated = false;
  let clientLoaded = false;
  const result = await runOfficialDeviceConnection({
    operation: "pairing-request",
    preflightPairing: async () => ({
      ready: false,
      status: "project_device_identity_invalid_or_missing",
      independent_device_identity_loaded: false,
      state_acl: "current_user_only"
    }),
    createTransaction: async () => { transactionCreated = true; },
    loadClient: async () => { clientLoaded = true; }
  });
  assert.equal(result.status, "pairing_preflight_failed");
  assert.equal(result.preflight.status, "project_device_identity_invalid_or_missing");
  assert.equal(transactionCreated, false);
  assert.equal(clientLoaded, false);
});
