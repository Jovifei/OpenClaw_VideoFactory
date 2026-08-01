import { initializeProjectDeviceIdentity } from "./identity_initializer.mjs";

const result = await initializeProjectDeviceIdentity();
const safe = {
  status: result.status,
  error_code: result.error_code ?? null,
  identity_directory_exists: result.identity_directory_exists ?? false,
  private_key_material_persisted: result.private_key_material_persisted ?? false,
  public_key_material_persisted: result.public_key_material_persisted ?? false,
  identity_metadata_exists: result.identity_metadata_exists ?? false,
  auth_state_exists: result.auth_state_exists ?? false,
  device_id_redacted: result.device_id_redacted ?? null,
  requested_role: result.requested_role ?? null,
  requested_scopes: result.requested_scopes ?? [],
  pairing_status: result.pairing_status ?? null,
  device_token_present: result.device_token_present ?? false,
  pairing_request_present: result.pairing_request_present ?? false,
  state_acl: result.state_acl ?? null,
  initialization_transaction_persisted: result.initialization_transaction_persisted ?? false,
  partial_state_quarantined: result.partial_state_quarantined ?? false,
  network_connections: result.network_connections ?? 0
};
console.log(JSON.stringify(safe));
