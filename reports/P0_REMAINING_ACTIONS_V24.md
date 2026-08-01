# P0 remaining actions V24

1. Start a new maintenance process only after it has inherited the existing
   secure environment token. Do not disclose or change the token.
2. Obtain a new, bounded authorization for the single safe restart and
   health-only validation retry.
3. Re-run 043 preflight. If the maintenance-process token remains absent, stop
   again; do not restart, alter the user environment, or use a token value from
   another source.

No zhongshu cutover, R0-R5, P0 Gate, Project Gateway launch, or real Feishu
traffic is authorized by this result.
