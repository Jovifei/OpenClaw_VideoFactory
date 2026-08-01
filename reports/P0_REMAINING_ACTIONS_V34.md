# P0 Remaining Actions V34

1. Obtain explicit authorization for a trusted Channel-to-MCP immutable raw
   command provenance mechanism.  Do not infer authorization to modify the
   frozen Binding/Channel path.
2. Implement and independently test that bounded mechanism in a new approved
   change request; prove a Router-rewritten valid command is rejected.
3. Only after that result qualifies, use the prepared runbook for sequential,
   user-controlled R3, then R4, then R5.  Stop at the first failure.
4. Do not run the P0 Gate or change `PROJECT_STATUS.yaml` in this task.
