# P0 remaining actions V27

One narrowly scoped authorization is required: perform a credential-source
maintenance audit/remediation that aligns the OpenClaw CLI control credential
with the running Gateway authentication source, without exposing or writing a
token to project files, configuration, command lines, logs, or reports.

Only after that work proves a health-only Adapter handshake and a structured
`channels.status` owner/count may a separate cutover-authorization decision be
considered. Do not retry service installation or restart from this result.
