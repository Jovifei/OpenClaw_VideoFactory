# P0 remaining actions V11

1. Stop 016 at `INBOUND_CLAIM_DID_NOT_BLOCK_ROUTER`.
2. Do not create the native plugin under the current route; it would not be invoked before the Router.
3. Do not send the fake card probe or invoke any Analyzer.
4. Preserve the 015 card reports and the old R3 failure.
5. A future continuation requires a supported, explicitly authorized pre-Router interception seam that preserves trusted Feishu card source/operator/chat/action/token metadata without adding a consumer, changing core source, or creating a second Binding. If that cannot be provided, the current single-group card-action design remains blocked.
6. R4/R5 and the final P0 Gate remain gated by the prior R3 failure and are not part of this round.

Offline regression result for this round: PASS for the existing suites only (Python 122/122; Pester 15/15, 46/46, 36/36; V2.8 4/4 and 88/88; MCP diagnostics 0). No card-action acceptance claim follows from those suites.
