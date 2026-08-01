import { createHash, randomUUID } from "node:crypto";
import { access, lstat, mkdir, open, readFile, readdir, rename, rm, unlink } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

import {
  DEFAULT_DEVICE_STATE_ROOT,
  deviceStatePaths,
  ensurePrivateDeviceStateRoot,
  restrictToCurrentWindowsUser,
  verifyPrivateDeviceStateRoot,
  writePrivateAtomicJson
} from "./device_store.mjs";
import { loadOfficialGatewayClient, resolveOfficialGatewayClientSource } from "./official_client.mjs";
import { redactIdentifier } from "./redaction.mjs";

const DISPLAY_NAME = "Project Feishu Gateway";
const REQUESTED_ROLE = "operator";
const REQUESTED_SCOPES = Object.freeze(["operator.read"]);

function safeLocalError(error) {
  const message = error instanceof Error ? error.message : "";
  return /^[a-z0-9_]{1,96}$/i.test(message) ? message : "identity_initialization_unavailable";
}

async function pathExists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function resolveOfficialIdentityModule({ openclawRoot } = {}) {
  const source = await resolveOfficialGatewayClientSource({ openclawRoot });
  const candidates = (await readdir(join(source.root, "dist")))
    .filter((name) => /^device-identity-[A-Za-z0-9_-]+\.js$/.test(name))
    .sort();
  for (const candidate of candidates) {
    const modulePath = join(source.root, "dist", candidate);
    const code = await readFile(modulePath, "utf8");
    if (!code.includes("loadOrCreateDeviceIdentity") || !code.includes("loadDeviceIdentityIfPresent")) continue;
    const module = await import(pathToFileURL(modulePath).href);
    if (typeof module.r === "function" && typeof module.n === "function" && typeof module.s === "function" &&
      typeof module.c === "function" && typeof module.t === "function" && typeof module.o === "function") {
      return {
        loadOrCreate: module.r,
        loadIfPresent: module.n,
        sign: module.s,
        verify: module.c,
        deriveDeviceId: module.t,
        publicKeyRaw: module.o,
        packageVersion: source.projection.package_version
      };
    }
  }
  throw new Error("official_device_identity_generator_unavailable");
}

async function syncPrivateFile(path) {
  // Windows requires a write-capable handle for FlushFileBuffers/fsync.
  const handle = await open(path, "r+");
  try {
    await handle.sync();
  } finally {
    await handle.close();
  }
}

async function inspectIdentityDirectory(paths) {
  const identityDirectory = dirname(paths.identity);
  try {
    const info = await lstat(identityDirectory);
    if (info.isSymbolicLink() || !info.isDirectory()) return { kind: "unsafe" };
    const entries = await readdir(identityDirectory);
    return { kind: entries.length === 0 ? "empty" : "artifacts", entryCount: entries.length, identityDirectory };
  } catch (error) {
    if (error?.code === "ENOENT") return { kind: "absent", identityDirectory };
    throw error;
  }
}

async function hashFilesForManifest(directory, relative = "") {
  const entries = await readdir(directory, { withFileTypes: true });
  const manifest = [];
  for (const entry of entries) {
    const nextRelative = relative ? `${relative}/${entry.name}` : entry.name;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      manifest.push(...await hashFilesForManifest(path, nextRelative));
    } else if (entry.isFile()) {
      const content = await readFile(path);
      manifest.push({ name: nextRelative, sha256: createHash("sha256").update(content).digest("hex") });
    } else {
      throw new Error("identity_partial_state_contains_unsupported_entry");
    }
  }
  return manifest;
}

async function quarantinePartialIdentity({ stateRoot, identityDirectory, now, restrictAcl = restrictToCurrentWindowsUser }) {
  const stamp = now().toISOString().replace(/[-:.]/g, "").replace("Z", "Z");
  const quarantineRoot = join(dirname(stateRoot), "quarantine", stamp);
  await mkdir(quarantineRoot, { recursive: true, mode: 0o700 });
  await restrictAcl(quarantineRoot);
  const destination = join(quarantineRoot, "identity");
  await rename(identityDirectory, destination);
  const manifest = {
    version: 1,
    status: "quarantined_partial_project_identity",
    created_at: now().toISOString(),
    files: await hashFilesForManifest(destination)
  };
  await writePrivateAtomicJson(join(quarantineRoot, "manifest.json"), manifest);
  return { quarantined: true, fileCount: manifest.files.length };
}

function metadataFor(identity, protocolVersion, createdAt) {
  return {
    version: 1,
    identity_schema_version: 1,
    device_id: identity.deviceId,
    display_name: DISPLAY_NAME,
    public_key_format: "spki-pem-ed25519",
    created_at: createdAt,
    protocol_version: protocolVersion,
    role_requested: REQUESTED_ROLE,
    scopes_requested: [...REQUESTED_SCOPES],
    pairing_status: "not_requested"
  };
}

function authStateFor(createdAt) {
  return {
    version: 1,
    pairing_request_id: null,
    device_token_present: false,
    pairing_status: "not_requested",
    created_at: createdAt
  };
}

function initializationProjection({ status, stateAcl, identity, metadataExists, authStateExists, protocolVersion, transactionPersisted, quarantine = false }) {
  return {
    status,
    identity_directory_exists: true,
    private_key_material_persisted: true,
    public_key_material_persisted: true,
    identity_metadata_exists: metadataExists,
    auth_state_exists: authStateExists,
    device_id_redacted: redactIdentifier(identity.deviceId),
    protocol_version: protocolVersion,
    requested_role: REQUESTED_ROLE,
    requested_scopes: [...REQUESTED_SCOPES],
    pairing_status: "not_requested",
    device_token_present: false,
    pairing_request_present: false,
    state_acl: stateAcl,
    initialization_transaction_persisted: transactionPersisted,
    partial_state_quarantined: quarantine,
    network_connections: 0
  };
}

async function validateOfflineIdentity({ identity, official, paths, openclawRoot }) {
  const reloaded = official.loadIfPresent(paths.identity);
  if (!reloaded || reloaded.deviceId !== identity.deviceId) throw new Error("identity_reload_validation_failed");
  if (official.deriveDeviceId(reloaded.publicKeyPem) !== reloaded.deviceId) throw new Error("identity_device_id_validation_failed");
  const nonce = `offline-initialization-${randomUUID()}`;
  const signature = official.sign(reloaded.privateKeyPem, nonce);
  if (!official.verify(reloaded.publicKeyPem, nonce, signature)) throw new Error("identity_signature_validation_failed");
  if (official.verify(reloaded.publicKeyPem, `${nonce}-modified`, signature)) throw new Error("identity_modified_nonce_accepted");
  if (!official.publicKeyRaw(reloaded.publicKeyPem)) throw new Error("identity_public_key_encoding_invalid");
  const { GatewayClient } = await loadOfficialGatewayClient({ openclawRoot });
  const client = new GatewayClient({
    url: "ws://127.0.0.1:18789",
    clientName: "project-feishu-gateway",
    clientDisplayName: DISPLAY_NAME,
    mode: "backend",
    role: REQUESTED_ROLE,
    scopes: [...REQUESTED_SCOPES],
    caps: [],
    deviceIdentity: reloaded,
    hostDeps: { logDebug: () => {}, logError: () => {}, redactForLog: () => "<redacted>" }
  });
  if (client.getConnectionMetadata().hasDeviceIdentity !== true) throw new Error("identity_official_client_rejected");
  return reloaded;
}

async function cleanupGeneratedArtifacts(paths) {
  await rm(dirname(paths.identity), { recursive: true, force: true }).catch(() => {});
  await unlink(paths.projectIdentityMetadata).catch(() => {});
  await unlink(paths.projectAuthState).catch(() => {});
}

/**
 * Explicit, offline-only initializer. It never constructs a WebSocket or calls
 * GatewayClient.start; the installed official generator owns the compatible
 * device.json serialization.
 */
export async function initializeProjectDeviceIdentity({
  stateRoot = DEFAULT_DEVICE_STATE_ROOT,
  openclawRoot,
  now = () => new Date(),
  ensureStateRoot,
  verifyStateRoot = verifyPrivateDeviceStateRoot,
  resolveIdentityModule = resolveOfficialIdentityModule,
  quarantinePartial = quarantinePartialIdentity
} = {}) {
  const paths = deviceStatePaths(resolve(stateRoot));
  const ensure = ensureStateRoot ?? (async () => await ensurePrivateDeviceStateRoot({ stateRoot: paths.root }));
  try {
    await ensure();
  } catch (error) {
    return { status: "initialization_failed", error_code: safeLocalError(error), network_connections: 0 };
  }
  let acl;
  try {
    acl = await verifyStateRoot({ stateRoot: paths.root });
  } catch (error) {
    return { status: "initialization_failed", error_code: safeLocalError(error), network_connections: 0 };
  }
  if (!acl.current_user_and_system) {
    return { status: "initialization_failed", error_code: "device_state_acl_invalid", network_connections: 0 };
  }
  if (await pathExists(paths.deviceAuth) || await pathExists(paths.pendingPairing) || await pathExists(paths.pairingTransaction)) {
    return { status: "partial_state_blocked", error_code: "existing_pairing_or_token_state", network_connections: 0 };
  }
  let official;
  try {
    official = await resolveIdentityModule({ openclawRoot });
  } catch (error) {
    return { status: "format_blocked", error_code: safeLocalError(error), network_connections: 0 };
  }
  const existing = official.loadIfPresent(paths.identity);
  if (existing) {
    let validated;
    try {
      validated = await validateOfflineIdentity({ identity: existing, official, paths, openclawRoot });
    } catch (error) {
      return { status: "partial_state_blocked", error_code: safeLocalError(error), network_connections: 0 };
    }
    return initializationProjection({
      status: "already_valid",
      stateAcl: acl.acl,
      identity: validated,
      metadataExists: await pathExists(paths.projectIdentityMetadata),
      authStateExists: await pathExists(paths.projectAuthState),
      protocolVersion: official.packageVersion,
      transactionPersisted: await pathExists(paths.identityInitializationTransaction)
    });
  }
  if (await pathExists(paths.projectIdentityMetadata) || await pathExists(paths.projectAuthState) || await pathExists(paths.identityInitializationTransaction)) {
    return { status: "partial_state_blocked", error_code: "existing_identity_metadata_without_valid_identity", network_connections: 0 };
  }
  let directory;
  try {
    directory = await inspectIdentityDirectory(paths);
  } catch (error) {
    return { status: "partial_state_blocked", error_code: safeLocalError(error), network_connections: 0 };
  }
  let quarantined = false;
  if (directory.kind === "unsafe") return { status: "partial_state_blocked", error_code: "identity_directory_unsafe", network_connections: 0 };
  if (directory.kind === "artifacts") {
    try {
      await quarantinePartial({ stateRoot: paths.root, identityDirectory: directory.identityDirectory, now });
      quarantined = true;
    } catch (error) {
      return { status: "partial_state_blocked", error_code: safeLocalError(error), network_connections: 0 };
    }
  }
  const createdAt = now().toISOString();
  const attemptId = randomUUID();
  const transaction = {
    version: 1,
    attempt_id: attemptId,
    target_directory: "identity",
    created_at: createdAt,
    generator_version: "official_openclaw_device_identity",
    protocol_version: official.packageVersion,
    status: "preparing"
  };
  try {
    await writePrivateAtomicJson(paths.identityInitializationTransaction, transaction);
  } catch (error) {
    return { status: "initialization_failed", error_code: safeLocalError(error), network_connections: 0 };
  }
  try {
    const identity = official.loadOrCreate(paths.identity);
    await syncPrivateFile(paths.identity);
    const reloaded = await validateOfflineIdentity({ identity, official, paths, openclawRoot });
    const metadata = metadataFor(reloaded, official.packageVersion, createdAt);
    const authState = authStateFor(createdAt);
    await writePrivateAtomicJson(paths.projectIdentityMetadata, metadata);
    await writePrivateAtomicJson(paths.projectAuthState, authState);
    const metadataReloaded = JSON.parse(await readFile(paths.projectIdentityMetadata, "utf8"));
    const authStateReloaded = JSON.parse(await readFile(paths.projectAuthState, "utf8"));
    if (metadataReloaded.device_id !== reloaded.deviceId || metadataReloaded.pairing_status !== "not_requested" ||
      authStateReloaded.pairing_request_id !== null || authStateReloaded.device_token_present !== false) {
      throw new Error("identity_metadata_validation_failed");
    }
    await writePrivateAtomicJson(paths.identityInitializationTransaction, {
      ...transaction,
      status: "ready",
      completed_at: now().toISOString(),
      device_id_redacted: redactIdentifier(reloaded.deviceId)
    });
    return initializationProjection({
      status: "identity_ready",
      stateAcl: acl.acl,
      identity: reloaded,
      metadataExists: true,
      authStateExists: true,
      protocolVersion: official.packageVersion,
      transactionPersisted: true,
      quarantine: quarantined
    });
  } catch (error) {
    await cleanupGeneratedArtifacts(paths);
    await writePrivateAtomicJson(paths.identityInitializationTransaction, {
      ...transaction,
      status: "initialization_failed",
      failed_at: now().toISOString(),
      error_code: safeLocalError(error)
    }).catch(() => {});
    return { status: "initialization_failed", error_code: safeLocalError(error), network_connections: 0 };
  }
}
