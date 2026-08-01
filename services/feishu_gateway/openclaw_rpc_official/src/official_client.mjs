import { access, readFile, readdir } from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

import { MINIMUM_SCOPES } from "./bridge_contract.mjs";
import {
  DEFAULT_DEVICE_STATE_ROOT,
  createPairingAttemptTransaction,
  deviceStatePaths,
  inspectPrivatePairingState,
  updatePairingAttemptTransaction,
  verifyPrivateDeviceStateRoot,
  writePendingPairingMetadata
} from "./device_store.mjs";
import { projectConnectError, redactIdentifier, sanitizeHello } from "./redaction.mjs";

const CLIENT_ID = "project-feishu-gateway";
const CLIENT_DISPLAY_NAME = "OpenClaw VideoFactory Project Gateway";
const LOOPBACK_URL = "ws://127.0.0.1:18789";

function defaultOpenClawRoot(env = process.env) {
  const appData = env.APPDATA;
  if (typeof appData !== "string" || appData.length === 0) throw new Error("official_openclaw_root_unavailable");
  return join(appData, "npm", "node_modules", "openclaw");
}

function sourceProjection(root, clientModule, version) {
  return {
    package_name: "openclaw",
    package_version: version,
    client_module: `<openclaw-root>/dist/${clientModule}`,
    device_identity_managed_by: "installed_openclaw_client"
  };
}

/** Resolve only the installed official OpenClaw bundle; no package download is attempted. */
export async function resolveOfficialGatewayClientSource({ openclawRoot = defaultOpenClawRoot() } = {}) {
  const root = resolve(openclawRoot);
  const manifest = JSON.parse(await readFile(join(root, "package.json"), "utf8"));
  if (manifest?.name !== "openclaw" || typeof manifest.version !== "string") {
    throw new Error("official_openclaw_manifest_invalid");
  }
  const dist = join(root, "dist");
  const candidates = (await readdir(dist))
    .filter((name) => /^client-[A-Za-z0-9_-]+\.js$/.test(name))
    .sort();
  for (const candidate of candidates) {
    const source = await readFile(join(dist, candidate), "utf8");
    if (source.includes("GatewayClient as t") && source.includes("loadDeviceAuthToken")) {
      return {
        root,
        modulePath: join(dist, candidate),
        projection: sourceProjection(root, candidate, manifest.version)
      };
    }
  }
  throw new Error("official_gateway_client_bundle_unavailable");
}

export async function loadOfficialGatewayClient(options = {}) {
  const source = await resolveOfficialGatewayClientSource(options);
  const module = await import(pathToFileURL(source.modulePath).href);
  if (typeof module.t !== "function" || typeof module.n !== "function") {
    throw new Error("official_gateway_client_exports_unavailable");
  }
  return { GatewayClient: module.t, loadDeviceAuthToken: module.n, source: source.projection };
}

async function resolveOfficialDeviceIdentityLoader({ openclawRoot = defaultOpenClawRoot() } = {}) {
  const root = resolve(openclawRoot);
  const dist = join(root, "dist");
  const candidates = (await readdir(dist))
    .filter((name) => /^device-identity-[A-Za-z0-9_-]+\.js$/.test(name))
    .sort();
  for (const candidate of candidates) {
    const modulePath = join(dist, candidate);
    const source = await readFile(modulePath, "utf8");
    if (!source.includes("loadDeviceIdentityIfPresent")) continue;
    const module = await import(pathToFileURL(modulePath).href);
    if (typeof module.n === "function") return module.n;
  }
  throw new Error("official_device_identity_loader_unavailable");
}

async function loadVerifiedProjectDeviceIdentity({ stateRoot, openclawRoot }) {
  const paths = deviceStatePaths(stateRoot);
  const loadDeviceIdentityIfPresent = await resolveOfficialDeviceIdentityLoader({ openclawRoot });
  return loadDeviceIdentityIfPresent(paths.identity);
}

async function exists(path) {
  try {
    await access(path, fsConstants.F_OK);
    return true;
  } catch {
    return false;
  }
}

function isolatedBridgeEnvironment(stateRoot) {
  // This process is short-lived. Deliberately remove the old shared-token path
  // before the installed client constructs the official device-auth request.
  delete process.env.OPENCLAW_GATEWAY_TOKEN;
  process.env.OPENCLAW_STATE_DIR = stateRoot;
  return {
    OPENCLAW_STATE_DIR: stateRoot,
    OPENCLAW_ALLOW_INSECURE_PRIVATE_WS: "1"
  };
}

function connectionProjection(operation) {
  return {
    operation,
    client_id: CLIENT_ID,
    client_mode: "backend",
    role: "operator",
    scopes: [...MINIMUM_SCOPES],
    explicit_shared_token: false,
    device_identity: true,
    challenge_signature: true
  };
}

function expectedPairingMetadata(error, now) {
  const projected = projectConnectError(error);
  if (projected.details_code !== "PAIRING_REQUIRED" || !projected.pairing_request_id) return null;
  return {
    requestId: projected.pairing_request_id,
    role: "operator",
    scopes: [...MINIMUM_SCOPES],
    createdAt: now().toISOString(),
    expiresAt: projected.pairing_expires_at
  };
}

function safeLocalError(error) {
  const message = error instanceof Error ? error.message : "";
  return /^[a-z0-9_]{1,96}$/i.test(message) ? message : "pairing_preflight_unavailable";
}

/** Read only the Project-owned external state; no identity is created here. */
export async function inspectOfficialPairingPreflight({
  stateRoot = DEFAULT_DEVICE_STATE_ROOT,
  openclawRoot
} = {}) {
  let state;
  try {
    state = await verifyPrivateDeviceStateRoot({ stateRoot });
  } catch (error) {
    return { ready: false, status: safeLocalError(error), independent_device_identity_loaded: false };
  }
  if (!state.exists || !state.directory) {
    return { ready: false, status: "device_state_root_missing", state_acl: state.acl, independent_device_identity_loaded: false };
  }
  if (!state.current_user_and_system) {
    return { ready: false, status: "device_state_acl_invalid", state_acl: state.acl, independent_device_identity_loaded: false };
  }
  let identity;
  let pairing;
  let source;
  try {
    identity = await loadVerifiedProjectDeviceIdentity({ stateRoot, openclawRoot });
    pairing = await inspectPrivatePairingState(stateRoot);
    source = await resolveOfficialGatewayClientSource({ openclawRoot });
  } catch (error) {
    return { ready: false, status: safeLocalError(error), state_acl: state.acl, independent_device_identity_loaded: false };
  }
  if (!identity) {
    return { ready: false, status: "project_device_identity_invalid_or_missing", state_acl: state.acl, independent_device_identity_loaded: false };
  }
  if (pairing.pending_pairing_record_present) {
    return { ready: false, status: "pairing_request_already_pending", state_acl: state.acl, independent_device_identity_loaded: true };
  }
  if (pairing.device_token_file_present) {
    return { ready: false, status: "project_device_token_already_present", state_acl: state.acl, independent_device_identity_loaded: true };
  }
  if (pairing.pairing_transaction_active) {
    return { ready: false, status: "pairing_transaction_already_active", state_acl: state.acl, independent_device_identity_loaded: true };
  }
  return {
    ready: true,
    status: "pairing_preflight_ready",
    state_root: stateRoot,
    state_acl: state.acl,
    independent_device_identity_loaded: true,
    device_id_redacted: redactIdentifier(identity.deviceId),
    protocol_version: source.projection.package_version,
    project_device_token_present: false,
    pending_pairing_present: false,
    pairing_transaction_present: pairing.pairing_transaction_present
  };
}

/**
 * Connect through the installed official client. Pairing mode may create only a
 * new Project identity and one pairing request; health mode refuses to create
 * an identity when no approved Project device state exists.
 */
export async function runOfficialDeviceConnection({
  operation,
  stateRoot,
  openclawRoot,
  timeoutMs = 12_000,
  loadClient = loadOfficialGatewayClient,
  preflightPairing = inspectOfficialPairingPreflight,
  loadProjectIdentity = loadVerifiedProjectDeviceIdentity,
  createTransaction = createPairingAttemptTransaction,
  updateTransaction = updatePairingAttemptTransaction,
  writePending = writePendingPairingMetadata,
  fileExists = exists,
  now = () => new Date()
}) {
  if (operation !== "pairing-request" && operation !== "health") throw new Error("official_operation_forbidden");
  if (operation === "health") {
    const preflight = await preflightPairing({ stateRoot, openclawRoot });
    if (!preflight.independent_device_identity_loaded) {
      return { status: "device_identity_missing", ...connectionProjection(operation), state_acl: preflight.state_acl ?? "unavailable" };
    }
    return { status: "health_operation_requires_approved_device_token", ...connectionProjection(operation), state_acl: preflight.state_acl };
  }

  const preflight = await preflightPairing({ stateRoot, openclawRoot });
  if (!preflight.ready) return { status: "pairing_preflight_failed", ...connectionProjection(operation), preflight };
  const projectIdentity = await loadProjectIdentity({ stateRoot: preflight.state_root, openclawRoot });
  let transaction;
  try {
    transaction = await createTransaction(preflight.state_root, {
      deviceIdRedacted: preflight.device_id_redacted,
      gatewayUrl: LOOPBACK_URL,
      protocolVersion: preflight.protocol_version,
      createdAt: now().toISOString()
    });
  } catch (error) {
    return { status: "pairing_persistence_failed", ...connectionProjection(operation), error_code: safeLocalError(error) };
  }
  let clientPackage;
  try {
    clientPackage = await loadClient({ openclawRoot });
  } catch (error) {
    await updateTransaction(preflight.state_root, transaction.attempt_id, {
      status: "blocked", errorCode: "OFFICIAL_CLIENT_LOAD_FAILED", updatedAt: now().toISOString()
    }).catch(() => {});
    return { status: "connect_failed", ...connectionProjection(operation), error: { top_level_code: "OFFICIAL_CLIENT_LOAD_FAILED" } };
  }
  try {
    await updateTransaction(preflight.state_root, transaction.attempt_id, {
      status: "connect_started", updatedAt: now().toISOString()
    });
  } catch (error) {
    return { status: "pairing_persistence_failed", ...connectionProjection(operation), error_code: safeLocalError(error) };
  }
  const bridgeEnv = isolatedBridgeEnvironment(preflight.state_root);
  const { GatewayClient, source } = clientPackage;
  return await new Promise((resolveResult) => {
    let completed = false;
    let timer;
    let client;
    const complete = async (result) => {
      if (completed) return;
      completed = true;
      if (timer) clearTimeout(timer);
      try {
        await client?.stopAndWait({ timeoutMs: 1_000 });
      } catch {
        // The connect result is authoritative; stopping is best-effort only.
      }
      resolveResult({ ...result, source, state_acl: preflight.state_acl });
    };
    client = new GatewayClient({
      url: LOOPBACK_URL,
      env: bridgeEnv,
      clientName: CLIENT_ID,
      clientDisplayName: CLIENT_DISPLAY_NAME,
      clientVersion: "0.1.0",
      mode: "backend",
      deviceFamily: "server",
      role: "operator",
      scopes: [...MINIMUM_SCOPES],
      caps: [],
      deviceIdentity: projectIdentity,
      requestTimeoutMs: timeoutMs,
      connectChallengeTimeoutMs: timeoutMs,
      hostDeps: {
        logDebug: () => {},
        logError: () => {},
        redactForLog: () => "<redacted>"
      },
      onHelloOk: async (hello) => {
        client.stop();
        const helloProjection = sanitizeHello(hello);
        const paths = deviceStatePaths(preflight.state_root);
        if (await fileExists(paths.deviceAuth)) {
          try {
            await updateTransaction(preflight.state_root, transaction.attempt_id, {
              status: "device_token_issued", updatedAt: now().toISOString()
            });
          } catch (error) {
            await complete({
              status: "pairing_persistence_failed", ...connectionProjection(operation), error_code: safeLocalError(error)
            });
            return;
          }
          await complete({
            status: "pairing_auto_approved",
            ...connectionProjection(operation),
            hello: helloProjection
          });
          return;
        }
        await complete({ status: "pairing_persistence_failed", ...connectionProjection(operation), error_code: "DEVICE_TOKEN_PERSISTENCE_MISSING" });
      },
      onConnectError: async (error) => {
        client.stop();
        const pairing = expectedPairingMetadata(error, now);
        if (pairing) {
          try {
            await updateTransaction(preflight.state_root, transaction.attempt_id, {
              status: "pending_approval",
              pairingRequestId: pairing.requestId,
              expiresAt: pairing.expiresAt,
              updatedAt: now().toISOString(),
              errorCode: "PAIRING_REQUIRED"
            });
            await writePending(preflight.state_root, pairing);
          } catch (persistError) {
            await updateTransaction(preflight.state_root, transaction.attempt_id, {
              status: "persistence_failed", updatedAt: now().toISOString(), errorCode: "PAIRING_PERSISTENCE_FAILED"
            }).catch(() => {});
            await complete({
              status: "pairing_persistence_failed",
              ...connectionProjection(operation),
              error: { ...projectConnectError(error), pairing_request_id: undefined },
              error_code: safeLocalError(persistError)
            });
            return;
          }
        } else {
          await updateTransaction(preflight.state_root, transaction.attempt_id, {
            status: "blocked", updatedAt: now().toISOString(), errorCode: projectConnectError(error).details_code ?? projectConnectError(error).top_level_code
          }).catch(() => {});
        }
        await complete({
          status: pairing ? "pairing_required" : "connect_failed",
          ...connectionProjection(operation),
          error: projectConnectError(error),
          pairing_metadata_saved: Boolean(pairing)
        });
      }
    });
    timer = setTimeout(() => {
      void (async () => {
        client?.stop();
        await updateTransaction(preflight.state_root, transaction.attempt_id, {
          status: "blocked", updatedAt: now().toISOString(), errorCode: "CONNECT_TIMEOUT"
        }).catch(() => {});
        await complete({ status: "connect_timeout", ...connectionProjection(operation) });
      })();
    }, timeoutMs);
    timer.unref?.();
    try {
      client.start();
    } catch (error) {
      client.stop();
      void updateTransaction(preflight.state_root, transaction.attempt_id, {
        status: "blocked", updatedAt: now().toISOString(), errorCode: "CONNECT_START_FAILED"
      }).catch(() => {});
      void complete({ status: "connect_failed", ...connectionProjection(operation), error_code: safeLocalError(error) });
    }
  });
}

export function officialBridgeLayout() {
  return {
    node_bridge: "official_installed_gateway_client",
    python_private_key_access: false,
    python_device_token_access: false,
    permitted_method: "health",
    future_allowlisted_methods: ["session.resolve", "agent.request", "request.status"]
  };
}
