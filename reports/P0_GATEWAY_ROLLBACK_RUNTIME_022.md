# Gateway Rollback Runtime 022

`scripts/migration/rollback_gateway.ps1` is simulation-only in P0. It records the required order: stop project Gateway, confirm exit, restore old Binding through an operator-approved procedure, then validate text and attachment paths. It cannot change a Binding or restart the core Gateway.

Real rollback remains blocked until command-level old-Binding restoration and a recovery-time objective are approved.
