# Gateway Runtime Runbook 022

For local/offline verification only:

1. `powershell -ExecutionPolicy Bypass -File .\scripts\feishu_gateway\start_gateway.ps1 -Port 18990`
2. `Invoke-RestMethod http://127.0.0.1:18990/health`
3. `Invoke-RestMethod http://127.0.0.1:18990/ready` (expected false until future verified transports exist).
4. `powershell -ExecutionPolicy Bypass -File .\scripts\feishu_gateway\status_gateway.ps1`
5. `powershell -ExecutionPolicy Bypass -File .\scripts\feishu_gateway\stop_gateway.ps1`

Do not use these commands to run a production cutover without separately approved production-mode integration and the V2 maintenance Runbook approvals.
