# P0 Remaining Actions V22

The 034 maintenance window cannot safely resume until all of these are
available and independently verified in a new fresh preflight:

1. secure injection of `OPENCLAW_GATEWAY_TOKEN` into the maintenance process;
2. a bounded read-only RPC status probe proving current Core ownership and
   exactly one `zhongshu` consumer;
3. reviewed production implementations of account-scoped Core stop/restore
   and Project Gateway start/stop (the current scripts intentionally reject
   execution or run offline only);
4. a tested runtime consumer/connection observer capable of proving the
   required zero- and one-consumer windows.

Do not reuse this authorization window after the environment changes. Begin a
new window with a fresh baseline and explicit authorization.
