# P0 Real Qualification Security Review 027

## Evidence handling

- Secrets and tokens: accepted only through an external secret provider; never printed, copied, or written to reports.
- Event identifiers: store one-way hashes or masked correlation values only.
- `chat_id` and `sender_id`: never store raw values; use role labels and hashes.
- Files: use harmless test fixtures only; do not persist file contents in logs or reports.
- Logs: allow timestamp, level, event class, hashed correlation, status and attempt count; reject token, secret, raw identifier and full path fields.
- Configuration: separate test directory and hash-only backup evidence; never read or modify production configuration in 027.

## Security stop conditions

Stop immediately if any output contains a token, secret, raw Feishu identifier, raw file path outside the approved test directory, or attachment content. Preserve only a sanitized error record and begin the reviewed rollback path when in an authorized window.

## Current audit result

The 027 preparation itself performed no credential access, Feishu connection, RPC authentication, Gateway start, Binding stop, or message send. The security design is ready for operator review; runtime security qualification remains `NOT_EXECUTED`.
