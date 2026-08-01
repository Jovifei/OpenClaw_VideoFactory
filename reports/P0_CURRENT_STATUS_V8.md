# P0 Current Status V8

Fresh real evidence still qualifies the repaired R2 PNG ingress and the separate bare MP4 ingress-only check. The old R2 Analyzer-after-ingest failure and the old R3 invalid same-message shape remain preserved. The new live R3 attempt failed at the intent gate and the sequence is stopped; R4/R5, final Gate, and Git publication are prohibited.

- R2 replacement: PASS (`om_***9de9`), one ingest, zero Analyzer calls, full PNG hash/size/receipt/quarantine evidence.
- MP4 ingress-only: PASS (`om_***27b7`), one ingest, zero video Analyzer calls, full MP4 hash/size/receipt/quarantine evidence; not R5.
- Topology/config: 17 Agents, 14 Bindings, 4 Cron, one target-group consumer, unchanged config SHA.
- Git: unborn branch with no remote; publication blocked.

P0-013 offline two-message analysis is ready: attachment ingress is caption-free, a later Feishu Reply creates a separate `analysis_request`, and Analyzer MCP enforces it. Offline evidence is 122/122 Python, 15/15 new Pester, 46/46 router, 36/36 inbound, 4/4 V2.8 wrapper, and 88/88 V2.8 schema checks.

The public MCP surface is 2 ingest tools (`ingest_attachment`, `create_analysis_request`) and 3 Analyzer tools, with Analyzer dispatch restricted to four safe fields. Production config SHA is unchanged and Gateway was not restarted.

R3 failure evidence: `reports/P0_R3_TWO_MESSAGE_EVENT_20260720.json`. The exact Chinese Reply text was rejected twice as `analysis_intent_not_recognized`; changing it to English `analyze image` later allowed a completed `xiaomimimo/mimo-v2.5` analysis, but that is not a valid R3 pass. No code/config/Gateway change occurred.
