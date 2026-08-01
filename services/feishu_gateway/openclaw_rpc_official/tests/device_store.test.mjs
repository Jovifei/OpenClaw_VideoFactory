import assert from "node:assert/strict";
import test from "node:test";
import { mkdtemp, readFile } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";

import {
  createPairingAttemptTransaction,
  deviceStatePaths,
  ensurePrivateDeviceStateRoot,
  inspectPrivatePairingState,
  restrictToCurrentWindowsUser,
  updatePairingAttemptTransaction,
  writePendingPairingMetadata
} from "../src/device_store.mjs";

test("keeps pairing metadata outside the project and applies the supplied ACL guard", async () => {
  const temporary = await mkdtemp(join(tmpdir(), "vf-device-store-"));
  const stateRoot = join(temporary, "private-device");
  const calls = [];
  const state = await ensurePrivateDeviceStateRoot({
    stateRoot,
    projectRoot: join(temporary, "project"),
    restrictAcl: async (target) => {
      calls.push(target);
      return { applied: true, reason: "current_user_only" };
    }
  });
  const pending = await writePendingPairingMetadata(state.stateRoot, {
    requestId: "request-123",
    role: "operator",
    scopes: ["operator.read"],
    createdAt: "2026-07-26T00:00:00.000Z"
  });
  const stored = await readFile(pending, "utf8");
  assert.equal(calls.length, 1);
  assert.equal(stored.includes("deviceToken"), false);
  assert.equal(stored.includes("privateKey"), false);
});

test("rejects a device state directory inside the project", async () => {
  const temporary = await mkdtemp(join(tmpdir(), "vf-device-store-"));
  await assert.rejects(
    ensurePrivateDeviceStateRoot({ stateRoot: join(temporary, "project", "device"), projectRoot: join(temporary, "project") }),
    /device_state_must_be_outside_project/
  );
});

test("uses the current Windows process SID rather than a mutable username variable", async () => {
  const calls = [];
  await restrictToCurrentWindowsUser("C:\\device-state", {
    platform: "win32",
    resolveSid: async () => "S-1-5-21-100-200-300-400",
    run: async (command, args) => {
      calls.push({ command, args });
      return { stdout: "" };
    }
  });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].command, "powershell.exe");
  assert.equal(calls[0].args.join(" ").includes("S-1-5-21-100-200-300-400"), true);
  assert.equal(calls[0].args.join(" ").includes("S-1-5-18"), true);
  assert.equal(calls[0].args.join(" ").includes("DirectorySecurity"), true);
});

test("persists a pre-connection pairing transaction atomically outside the project", async () => {
  const temporary = await mkdtemp(join(tmpdir(), "vf-pairing-transaction-"));
  const stateRoot = join(temporary, "private-device");
  const state = await ensurePrivateDeviceStateRoot({
    stateRoot,
    projectRoot: join(temporary, "project"),
    restrictAcl: async () => ({ applied: true, reason: "current_user_only" })
  });
  const transaction = await createPairingAttemptTransaction(state.stateRoot, {
    attemptId: "11111111-1111-4111-8111-111111111111",
    deviceIdRedacted: "id-0123456789ab",
    gatewayUrl: "ws://127.0.0.1:18789",
    protocolVersion: "2026.7.1",
    createdAt: "2026-07-26T00:00:00.000Z"
  });
  assert.equal(transaction.status, "prepared_not_connected");
  await updatePairingAttemptTransaction(state.stateRoot, transaction.attempt_id, {
    status: "connect_started",
    updatedAt: "2026-07-26T00:00:01.000Z"
  });
  const paths = deviceStatePaths(state.stateRoot);
  const stored = await readFile(paths.pairingTransaction, "utf8");
  const inspection = await inspectPrivatePairingState(state.stateRoot);
  assert.equal(stored.includes("privateKey"), false);
  assert.equal(inspection.pairing_transaction_active, true);
  assert.equal(inspection.pairing_transaction_status, "connect_started");
});
