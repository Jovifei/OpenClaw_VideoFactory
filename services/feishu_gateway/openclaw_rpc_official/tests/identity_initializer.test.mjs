import assert from "node:assert/strict";
import test from "node:test";
import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { mkdtemp } from "node:fs/promises";

import { deviceStatePaths } from "../src/device_store.mjs";
import { initializeProjectDeviceIdentity } from "../src/identity_initializer.mjs";

async function testStateRoot() {
  const temporary = await mkdtemp(join(tmpdir(), "vf-identity-init-"));
  const stateRoot = join(temporary, "private-device");
  return { temporary, stateRoot };
}

const validAcl = async () => ({ current_user_and_system: true, acl: "current_user_and_system" });

test("creates one official-compatible Project identity offline and persists only safe companion metadata", async () => {
  const { stateRoot } = await testStateRoot();
  const result = await initializeProjectDeviceIdentity({
    stateRoot,
    ensureStateRoot: async () => { await mkdir(stateRoot, { recursive: true }); },
    verifyStateRoot: validAcl
  });
  const paths = deviceStatePaths(stateRoot);
  await access(paths.identity);
  await access(paths.projectIdentityMetadata);
  await access(paths.projectAuthState);
  const metadata = JSON.parse(await readFile(paths.projectIdentityMetadata, "utf8"));
  const authState = JSON.parse(await readFile(paths.projectAuthState, "utf8"));
  assert.equal(result.status, "identity_ready");
  assert.equal(result.network_connections, 0);
  assert.match(result.device_id_redacted, /^id-[a-f0-9]{12}$/);
  assert.equal(metadata.pairing_status, "not_requested");
  assert.equal(authState.device_token_present, false);
  assert.equal(authState.pairing_request_id, null);
  assert.equal(JSON.stringify(metadata).includes("privateKey"), false);
});

test("does not overwrite an already valid identity", async () => {
  const { stateRoot } = await testStateRoot();
  const options = {
    stateRoot,
    ensureStateRoot: async () => { await mkdir(stateRoot, { recursive: true }); },
    verifyStateRoot: validAcl
  };
  const first = await initializeProjectDeviceIdentity(options);
  const before = await readFile(deviceStatePaths(stateRoot).identity, "utf8");
  const second = await initializeProjectDeviceIdentity(options);
  const after = await readFile(deviceStatePaths(stateRoot).identity, "utf8");
  assert.equal(first.status, "identity_ready");
  assert.equal(second.status, "already_valid");
  assert.equal(before, after);
});

test("blocks partial identity state before calling the official generator", async () => {
  const { stateRoot } = await testStateRoot();
  const paths = deviceStatePaths(stateRoot);
  await mkdir(join(stateRoot, "identity"), { recursive: true });
  await writeFile(join(stateRoot, "identity", "partial"), "incomplete", "utf8");
  let identityCreated = false;
  const result = await initializeProjectDeviceIdentity({
    stateRoot,
    ensureStateRoot: async () => {},
    verifyStateRoot: validAcl,
    resolveIdentityModule: async () => ({
      loadIfPresent: () => null,
      loadOrCreate: () => { identityCreated = true; },
      packageVersion: "2026.7.1"
    }),
    quarantinePartial: async () => { throw new Error("quarantine_denied"); }
  });
  assert.equal(result.status, "partial_state_blocked");
  assert.equal(identityCreated, false);
  assert.equal(await (async () => { try { await access(join(stateRoot, "identity", "partial")); return true; } catch { return false; } })(), true);
});
