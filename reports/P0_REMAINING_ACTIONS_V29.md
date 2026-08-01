# Remaining Actions V29

1. Obtain authorization for a **Project-identity-provisioning-only** task. It must create one fresh Project-owned official Ed25519 identity in the existing external state root, verify it read-only, and stop without connecting to the Gateway.
2. After that task proves the identity exists and is consistent, obtain a new, separate authorization for one pairing-request-only connection under 047 constraints.
3. Do not approve, validate a device token, start the Project Gateway, or begin any zhongshu maintenance work until a later explicit authorization.

