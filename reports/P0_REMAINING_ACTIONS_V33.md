# P0 Remaining Actions V33

1. Perform only the user-driven R3 image sequence in
   `P0_REAL_MEDIA_SEQUENCE_R3_R5_050.md`.
2. If R3 passes, proceed to R4; if R4 passes, proceed to R5.  Stop immediately
   at the first failure.
3. Keep 046-049 and every Project-Gateway/device route deferred to
   `P1_CHANNEL_HARDENING`; do not retry, delete, or use them as R0-R5 evidence.
4. Do not run a P0 acceptance gate or update `PROJECT_STATUS.yaml` under this
   task.

