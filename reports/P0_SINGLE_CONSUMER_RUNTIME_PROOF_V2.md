# P0 Single Consumer Runtime Proof V2 (024)

Status: `PASS_LOCAL_SIMULATION_ONLY`

`scripts/migration/verify_single_consumer.py` now requires all of the following local observations:

1. exactly one owner: `openclaw_binding` or `project_gateway`;
2. exactly one WebSocket;
3. owner-matched lease record;
4. non-stale heartbeat;
5. no simultaneous Binding and Project Gateway running flags;
6. no duplicate event or reply IDs.

`ConsumerLease` provides a local lock file with owner, heartbeat, stale takeover, and ownership rejection. The test proves Binding ownership blocks Project Gateway, heartbeat refreshes ownership, and a stale lease can be replaced.

The simulated proof returned `pass` for one Project Gateway owner, one socket, a current heartbeat, and unique event/reply IDs. It is not a production observation and does not authorize a cutover. Existing rollback verification remains covered by Python and Pester regression.
