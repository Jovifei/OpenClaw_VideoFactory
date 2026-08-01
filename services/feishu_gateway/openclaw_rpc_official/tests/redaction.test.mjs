import assert from "node:assert/strict";
import test from "node:test";

import { projectConnectError, redactIdentifier } from "../src/redaction.mjs";

test("redacts pairing request identifiers and discards raw messages", () => {
  const result = projectConnectError({
    gatewayCode: "UNAUTHORIZED",
    message: "sensitive message must not leave the bridge",
    details: {
      code: "PAIRING_REQUIRED",
      reason: "not-paired",
      requestId: "pairing-request-123",
      expiresAt: "2026-07-26T01:00:00.000Z",
      recommendedNextStep: "review_auth_configuration",
      canRetryWithDeviceToken: false
    }
  });
  assert.equal(result.details_code, "PAIRING_REQUIRED");
  assert.equal(result.pairing_request_id, "pairing-request-123");
  assert.match(result.pairing_request_id_redacted, /^id-[a-f0-9]{12}$/);
  assert.equal(JSON.stringify(result).includes("sensitive message"), false);
  assert.notEqual(result.pairing_request_id_redacted, redactIdentifier("another-request"));
  assert.equal(result.pairing_expires_at, "2026-07-26T01:00:00.000Z");
});

test("drops unknown server error fields", () => {
  const result = projectConnectError({ gatewayCode: "UNAUTHORIZED", details: { code: "UNKNOWN", message: "raw" } });
  assert.equal(result.details_code, null);
  assert.equal(Object.hasOwn(result, "message"), false);
});
