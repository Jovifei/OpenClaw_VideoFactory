import { runOfficialDeviceConnection } from "./official_client.mjs";
import { redactIdentifier } from "./redaction.mjs";

const result = await runOfficialDeviceConnection({ operation: "pairing-request" });
const safe = {
  ...result,
  error: result.error ? {
    ...result.error,
    pairing_request_id: undefined,
    pairing_request_id_redacted: result.error.pairing_request_id_redacted ?? redactIdentifier(result.error.pairing_request_id)
  } : undefined
};
console.log(JSON.stringify(safe));
