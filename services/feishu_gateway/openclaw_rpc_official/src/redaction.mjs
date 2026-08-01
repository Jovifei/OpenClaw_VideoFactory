import { createHash } from "node:crypto";

const SAFE_DETAIL_CODES = new Set([
  "PAIRING_REQUIRED",
  "AUTH_SCOPE_MISMATCH",
  "AUTH_DEVICE_TOKEN_MISMATCH",
  "DEVICE_IDENTITY_REQUIRED",
  "DEVICE_AUTH_INVALID",
  "DEVICE_AUTH_DEVICE_ID_MISMATCH",
  "DEVICE_AUTH_SIGNATURE_EXPIRED",
  "DEVICE_AUTH_NONCE_REQUIRED",
  "DEVICE_AUTH_NONCE_MISMATCH",
  "DEVICE_AUTH_SIGNATURE_INVALID",
  "DEVICE_AUTH_PUBLIC_KEY_INVALID",
  "AUTH_TOKEN_MISMATCH",
  "PROTOCOL_MISMATCH"
]);
const SAFE_PAIRING_REASONS = new Set(["not-paired", "role-upgrade", "scope-upgrade", "metadata-upgrade"]);
const SAFE_NEXT_STEPS = new Set([
  "retry_with_device_token",
  "update_auth_configuration",
  "update_auth_credentials",
  "wait_then_retry",
  "review_auth_configuration"
]);

export function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function redactIdentifier(value) {
  if (typeof value !== "string" || value.length === 0) return null;
  return `id-${createHash("sha256").update(value, "utf8").digest("hex").slice(0, 12)}`;
}

function safeCode(value) {
  return typeof value === "string" && SAFE_DETAIL_CODES.has(value) ? value : null;
}

function safeReason(value) {
  return typeof value === "string" && SAFE_PAIRING_REASONS.has(value) ? value : null;
}

function safeNextStep(value) {
  return typeof value === "string" && SAFE_NEXT_STEPS.has(value) ? value : null;
}

function safeIsoTimestamp(value) {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/.test(value)
    ? value
    : null;
}

/** Return only protocol fields that are safe to persist or report. */
export function projectConnectError(error) {
  const details = isRecord(error?.details) ? error.details : {};
  const gatewayCode = typeof error?.gatewayCode === "string" && /^[A-Z0-9_]{1,64}$/.test(error.gatewayCode)
    ? error.gatewayCode
    : "UNAVAILABLE";
  const requestId = typeof details.requestId === "string" && /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(details.requestId)
    ? details.requestId
    : null;
  return {
    top_level_code: gatewayCode,
    details_code: safeCode(details.code),
    details_reason: safeReason(details.reason),
    can_retry_with_device_token: typeof details.canRetryWithDeviceToken === "boolean"
      ? details.canRetryWithDeviceToken
      : null,
    recommended_next_step: safeNextStep(details.recommendedNextStep),
    pairing_request_id: requestId,
    pairing_request_id_redacted: redactIdentifier(requestId),
    pairing_expires_at: safeIsoTimestamp(details.expiresAt)
  };
}

export function sanitizeHello(hello) {
  const auth = isRecord(hello?.auth) ? hello.auth : {};
  const scopes = Array.isArray(auth.scopes)
    ? auth.scopes.filter((scope) => typeof scope === "string" && scope.length <= 64)
    : [];
  return {
    role: typeof auth.role === "string" ? auth.role : null,
    scopes,
    device_token_present: typeof auth.deviceToken === "string" && auth.deviceToken.length > 0
  };
}
