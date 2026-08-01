import { execFile as execFileCallback } from "node:child_process";
import { promisify } from "node:util";
import { access, mkdir, open, readFile, rename, stat, unlink } from "node:fs/promises";
import { isAbsolute, relative, resolve, join } from "node:path";
import { homedir } from "node:os";
import { randomUUID } from "node:crypto";

const execFile = promisify(execFileCallback);
const SYSTEM_SID = "S-1-5-18";

export const DEFAULT_DEVICE_STATE_ROOT = join(homedir(), ".openclaw-video-factory", "device");

function assertExternalStateRoot(stateRoot, projectRoot = process.cwd()) {
  if (typeof stateRoot !== "string" || !isAbsolute(stateRoot)) throw new Error("device_state_root_must_be_absolute");
  const resolvedRoot = resolve(stateRoot);
  const relation = relative(resolve(projectRoot), resolvedRoot);
  if (relation === "" || (!relation.startsWith("..") && !isAbsolute(relation))) {
    throw new Error("device_state_must_be_outside_project");
  }
  return resolvedRoot;
}

function powerShellLiteral(value) {
  return `'${String(value).replaceAll("'", "''")}'`;
}

export async function resolveCurrentWindowsUserSid({ run = execFile } = {}) {
  const { stdout } = await run(
    "powershell.exe",
    ["-NoProfile", "-NonInteractive", "-Command", "[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value"],
    { windowsHide: true }
  );
  const sid = typeof stdout === "string" ? stdout.trim() : "";
  if (!/^S-\d+(?:-\d+)+$/i.test(sid)) throw new Error("device_state_owner_unavailable");
  return sid;
}

export async function restrictToCurrentWindowsUser(stateRoot, {
  platform = process.platform,
  resolveSid = resolveCurrentWindowsUserSid,
  run = execFile
} = {}) {
  if (platform !== "win32") return { applied: false, reason: "non_windows" };
  const sid = await resolveSid({ run });
  const aclCommand = `$user=New-Object System.Security.Principal.SecurityIdentifier(${powerShellLiteral(sid)});$system=New-Object System.Security.Principal.SecurityIdentifier(${powerShellLiteral(SYSTEM_SID)});$security=New-Object System.Security.AccessControl.DirectorySecurity;$security.SetAccessRuleProtection($true,$false);$rights=[System.Security.AccessControl.FileSystemRights]::FullControl;$inheritance=[System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [System.Security.AccessControl.InheritanceFlags]::ObjectInherit;$propagation=[System.Security.AccessControl.PropagationFlags]::None;$allow=[System.Security.AccessControl.AccessControlType]::Allow;$security.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($user,$rights,$inheritance,$propagation,$allow)));$security.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($system,$rights,$inheritance,$propagation,$allow)));[System.IO.Directory]::SetAccessControl(${powerShellLiteral(stateRoot)},$security)`;
  await run("powershell.exe", ["-NoProfile", "-NonInteractive", "-Command", aclCommand], {
    windowsHide: true
  });
  return { applied: true, reason: "current_user_and_system" };
}

export async function ensurePrivateDeviceStateRoot({
  stateRoot = DEFAULT_DEVICE_STATE_ROOT,
  projectRoot = process.cwd(),
  restrictAcl = restrictToCurrentWindowsUser
} = {}) {
  const resolvedRoot = assertExternalStateRoot(stateRoot, projectRoot);
  await mkdir(resolvedRoot, { recursive: true, mode: 0o700 });
  const acl = await restrictAcl(resolvedRoot);
  return { stateRoot: resolvedRoot, acl };
}

/** Read-only ACL verification for an already-provisioned external state root. */
export async function verifyPrivateDeviceStateRoot({
  stateRoot = DEFAULT_DEVICE_STATE_ROOT,
  projectRoot = process.cwd(),
  resolveSid = resolveCurrentWindowsUserSid,
  run = execFile
} = {}) {
  const resolvedRoot = assertExternalStateRoot(stateRoot, projectRoot);
  let info;
  try {
    info = await stat(resolvedRoot);
  } catch {
    return { exists: false, directory: false, acl: "unavailable", current_user_only: false };
  }
  if (!info.isDirectory()) return { exists: true, directory: false, acl: "unavailable", current_user_only: false };
  if (process.platform !== "win32") return { exists: true, directory: true, acl: "unsupported", current_user_only: false };
  const sid = await resolveSid({ run });
  const command = `$acl=Get-Acl -LiteralPath ${powerShellLiteral(resolvedRoot)};$sid=${powerShellLiteral(sid)};$system=${powerShellLiteral(SYSTEM_SID)};$rules=@($acl.Access|ForEach-Object{try{$_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value}catch{''}});$allowed=@($sid,$system);[pscustomobject]@{protected=[bool]$acl.AreAccessRulesProtected;allowed_principals_only=(@($rules|Where-Object{$_ -and $_ -notin $allowed}).Count -eq 0);current_sid_rule_count=@($rules|Where-Object{$_ -eq $sid}).Count;system_rule_count=@($rules|Where-Object{$_ -eq $system}).Count;rule_count=@($rules).Count}|ConvertTo-Json -Compress`;
  const { stdout } = await run("powershell.exe", ["-NoProfile", "-NonInteractive", "-Command", command], { windowsHide: true });
  let acl;
  try { acl = JSON.parse(String(stdout)); } catch { throw new Error("device_state_acl_projection_invalid"); }
  const currentUserAndSystem = acl.protected === true && acl.allowed_principals_only === true && acl.current_sid_rule_count === 1 && acl.system_rule_count === 1 && acl.rule_count === 2;
  return {
    exists: true,
    directory: true,
    acl: currentUserAndSystem ? "current_user_and_system" : "not_current_user_and_system",
    current_user_and_system: currentUserAndSystem
  };
}

export function deviceStatePaths(stateRoot) {
  const root = resolve(stateRoot);
  return {
    root,
    identity: join(root, "identity", "device.json"),
    deviceAuth: join(root, "identity", "device-auth.json"),
    pendingPairing: join(root, "pending-pairing.json"),
    pairingTransaction: join(root, "pairing-attempt.json"),
    identityInitializationTransaction: join(root, "identity-initialization-transaction.json"),
    projectIdentityMetadata: join(root, "project-device-identity-metadata.json"),
    projectAuthState: join(root, "project-device-auth-state.json")
  };
}

function validPairingRequestId(value) {
  return typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(value);
}

const ACTIVE_TRANSACTION_STATUSES = new Set([
  "prepared_not_connected",
  "connect_started",
  "pending_approval",
  "device_token_issued",
  "persistence_failed"
]);

function validAttemptId(value) {
  return typeof value === "string" && /^[0-9a-f-]{36}$/i.test(value);
}

function normalizeScopes(value) {
  return Array.isArray(value) && value.length === 1 && value[0] === "operator.read"
    ? ["operator.read"]
    : ["operator.read"];
}

async function exists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function readJsonIfExists(path) {
  try {
    return JSON.parse(await readFile(path, "utf8"));
  } catch (error) {
    if (error?.code === "ENOENT") return null;
    throw new Error("private_pairing_record_invalid");
  }
}

/** Write one private record atomically and synchronously flush the file contents. */
export async function writePrivateAtomicJson(path, value) {
  const temporary = `${path}.${randomUUID()}.tmp`;
  let handle;
  try {
    handle = await open(temporary, "wx", 0o600);
    await handle.writeFile(`${JSON.stringify(value)}\n`, "utf8");
    await handle.sync();
    await handle.close();
    handle = undefined;
    await rename(temporary, path);
  } catch (error) {
    try { await handle?.close(); } catch {}
    try { await unlink(temporary); } catch {}
    throw error;
  }
  return path;
}

/** Return a safe boolean-only projection; never return request IDs or device material. */
export async function inspectPrivatePairingState(stateRoot) {
  const paths = deviceStatePaths(stateRoot);
  const transaction = await readJsonIfExists(paths.pairingTransaction);
  const status = typeof transaction?.status === "string" ? transaction.status : null;
  return {
    pending_pairing_record_present: await exists(paths.pendingPairing),
    device_token_file_present: await exists(paths.deviceAuth),
    pairing_transaction_present: transaction !== null,
    pairing_transaction_active: Boolean(status && ACTIVE_TRANSACTION_STATUSES.has(status)),
    pairing_transaction_status: status
  };
}

/**
 * Create the durable pre-connection record. If this succeeds, a crash still
 * distinguishes "not connected" from later persisted connection states.
 */
export async function createPairingAttemptTransaction(stateRoot, {
  attemptId = randomUUID(),
  deviceIdRedacted,
  displayName = "OpenClaw VideoFactory Project Gateway",
  role = "operator",
  scopes = ["operator.read"],
  gatewayUrl,
  protocolVersion,
  createdAt = new Date().toISOString()
} = {}) {
  const paths = deviceStatePaths(stateRoot);
  const current = await inspectPrivatePairingState(stateRoot);
  if (current.pending_pairing_record_present) throw new Error("pairing_request_already_pending");
  if (current.device_token_file_present) throw new Error("project_device_token_already_present");
  if (current.pairing_transaction_active) throw new Error("pairing_transaction_already_active");
  if (!validAttemptId(attemptId)) throw new Error("pairing_attempt_id_invalid");
  if (typeof deviceIdRedacted !== "string" || !/^id-[a-f0-9]{12}$/.test(deviceIdRedacted)) {
    throw new Error("pairing_device_id_invalid");
  }
  if (role !== "operator" || JSON.stringify(normalizeScopes(scopes)) !== JSON.stringify(scopes)) {
    throw new Error("pairing_role_or_scope_invalid");
  }
  if (typeof gatewayUrl !== "string" || !/^ws:\/\/127\.0\.0\.1:18789$/.test(gatewayUrl)) {
    throw new Error("pairing_gateway_url_invalid");
  }
  if (typeof protocolVersion !== "string" || !/^\d{4}\.\d+\.\d+$/.test(protocolVersion)) {
    throw new Error("pairing_protocol_version_invalid");
  }
  const transaction = {
    version: 1,
    attempt_id: attemptId,
    device_id_redacted: deviceIdRedacted,
    display_name: displayName,
    requested_role: role,
    requested_scopes: ["operator.read"],
    gateway_url: gatewayUrl,
    protocol_version: protocolVersion,
    created_at: createdAt,
    status: "prepared_not_connected",
    pairing_request_id: null,
    pairing_request_id_persisted: false,
    error_code: null
  };
  await writePrivateAtomicJson(paths.pairingTransaction, transaction);
  return { attempt_id: attemptId, status: transaction.status };
}

/** Advance the one pairing transaction without returning its private request ID. */
export async function updatePairingAttemptTransaction(stateRoot, attemptId, update) {
  const paths = deviceStatePaths(stateRoot);
  const transaction = await readJsonIfExists(paths.pairingTransaction);
  if (!transaction || transaction.version !== 1 || transaction.attempt_id !== attemptId) {
    throw new Error("pairing_transaction_missing_or_mismatched");
  }
  const allowedStatuses = new Set([
    "connect_started", "pending_approval", "device_token_issued", "blocked", "persistence_failed"
  ]);
  if (!allowedStatuses.has(update?.status)) throw new Error("pairing_transaction_status_invalid");
  if (update.status === "pending_approval" && !validPairingRequestId(update.pairingRequestId)) {
    throw new Error("pairing_request_id_invalid");
  }
  const next = {
    ...transaction,
    status: update.status,
    updated_at: typeof update.updatedAt === "string" ? update.updatedAt : new Date().toISOString(),
    error_code: typeof update.errorCode === "string" && /^[A-Z0-9_]{1,64}$/.test(update.errorCode)
      ? update.errorCode
      : null,
    pairing_request_id: update.status === "pending_approval" ? update.pairingRequestId : transaction.pairing_request_id,
    pairing_request_id_persisted: update.status === "pending_approval" ? true : transaction.pairing_request_id_persisted,
    expires_at: typeof update.expiresAt === "string" ? update.expiresAt : transaction.expires_at ?? null,
    device_token_persisted: update.status === "device_token_issued" ? true : Boolean(transaction.device_token_persisted)
  };
  await writePrivateAtomicJson(paths.pairingTransaction, next);
  return {
    attempt_id: transaction.attempt_id,
    status: next.status,
    pairing_request_id_persisted: next.pairing_request_id_persisted,
    device_token_persisted: next.device_token_persisted
  };
}

/** Persist pairing metadata only; the official client owns private key and token files. */
export async function writePendingPairingMetadata(stateRoot, metadata) {
  if (!validPairingRequestId(metadata?.requestId)) throw new Error("pairing_request_id_invalid");
  const paths = deviceStatePaths(stateRoot);
  const payload = {
    version: 1,
    requestId: metadata.requestId,
    role: metadata.role === "operator" ? "operator" : "operator",
    scopes: normalizeScopes(metadata.scopes),
    displayName: "OpenClaw VideoFactory Project Gateway",
    createdAt: typeof metadata.createdAt === "string" ? metadata.createdAt : new Date().toISOString(),
    expiresAt: typeof metadata.expiresAt === "string" ? metadata.expiresAt : null
  };
  await writePrivateAtomicJson(paths.pendingPairing, payload);
  return paths.pendingPairing;
}
