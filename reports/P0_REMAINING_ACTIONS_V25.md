# P0 remaining actions V25

1. Obtain authorization only for a read-only Gateway service-control-path audit.
2. Determine the safe-restart rejection class without reading or changing any
   credential, configuration, Binding, Agent, Cron, OAuth, or model state.
3. Request a new lifecycle authorization only if that audit proves a specific,
   reversible control remedy.

Do not retry the restart under the 043B authorization. The old Gateway remains
healthy and no recovery start is warranted.
