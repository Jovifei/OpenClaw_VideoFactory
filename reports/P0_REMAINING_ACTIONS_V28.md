# Remaining Actions V28

1. Obtain fresh authorization for one Project Gateway pairing-request-only connection after the repaired ACL baseline.
2. Have the Gateway operator approve the resulting redacted Project device request for `operator.read` only.
3. Run device-token health-only verification. Do not create a business Session or start the Project Gateway.
4. Only after that result is `PROJECT_GATEWAY_DEVICE_AUTH_READY` and `RPC_PREFLIGHT_READY`, request a separate maintenance-window authorization for any zhongshu cutover work.

