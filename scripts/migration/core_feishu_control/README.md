# Core Feishu account control (033)

These scripts are fail-closed, read-only evaluators. They describe the
production maintenance-window contract but do not invoke OpenClaw, Feishu,
Binding, Gateway, or RPC lifecycle operations. `--execute` is rejected by
design until a separate, explicit maintenance-window authorization is
recorded and reviewed.

The qualified Shadow evidence uses the installed Feishu plugin source, a
process-boundary loopback-only network guard, and a process-boundary fake SDK.
