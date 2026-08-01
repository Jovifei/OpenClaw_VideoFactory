# Gateway Runtime Rollback 022

The project runtime can be stopped locally and cleanly using `stop_gateway.ps1`; it waits for local `/shutdown` then forces only the recorded project PID after timeout. It does not modify OpenClaw or Feishu.

Restoring the existing core Feishu Binding remains an operator-controlled, unimplemented action. Consequently, production rollback is not ready and no recovery duration is claimed.
