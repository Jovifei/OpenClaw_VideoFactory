# Project Gateway Startup Contract 031

Status: `OFFLINE_RUNTIME_ONLY_NOT_A_CUTOVER_START_METHOD`

| Required field | Current reviewed implementation |
| --- | --- |
| START_METHOD | `scripts/feishu_gateway/start_gateway.ps1` launches `runtime_server` in the only permitted mode: `offline`. It is not a production Feishu start method. |
| VERIFY_PROCESS | `scripts/feishu_gateway/status_gateway.ps1` checks a local PID file and process existence. No process was running during this audit. |
| HEALTH | The offline server exposes a local health response and status file. Neither was started or queried in 031. |
| READY | Fail-closed: offline mode holds Feishu as `not_initialized` and RPC as `rpc_runtime_verification_blocked`; ready cannot become true. |
| LEASE | No runtime lease writer exists; durable state-lease count was 0. |
| STOP | `scripts/feishu_gateway/stop_gateway.ps1` attempts a local shutdown then can force-stop the local process. It was not run. |
| FORCE_STOP | Present only for the offline PID path; it is not a production rollback mechanism. |
| LOG_LOCATION | Relative project runtime log location: `runtime/logs/gateway.jsonl` |

The repository contains no reviewed Project Feishu transport launcher, production ownership lease, Feishu connection proof, or real RPC-ready process. The offline health runtime is valid for local tests only and cannot satisfy T+1/T+3 cutover criteria.
