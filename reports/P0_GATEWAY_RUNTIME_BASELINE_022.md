# Gateway Runtime Baseline 022

Before 022, `services/feishu_gateway` contained injectable PoC orchestration only: no process entry point, PID, HTTP health surface, runtime status, or structured log sink. Configuration was environment-only through `GatewaySettings`; the official SDK had been isolated in an experiment only. Python is 3.14.2. Runtime logs/status had no production location or lifecycle owner.

022 adds a project-local, default-offline runtime under `runtime/` (Git-ignored), a sample-only configuration contract, and PowerShell lifecycle scripts. It does not start a Feishu client or authenticate to OpenClaw.
