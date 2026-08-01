# P0 Live Sequence Qualification

Current qualification state: `R3_FAILED_ANALYSIS_INTENT_GATE_STOPPED`.

R0 is accepted. The original R1 is permanently negative evidence and is not retested or relabeled. P0-R1-TRUSTED-SIZE-CONTRACT-010 has removed model-controlled size authority, passed local two-root smoke, and loaded the schema through one planned Gateway restart.

R1 is complete. The real R2 failure is preserved. Offline CR 011 adds the deterministic intent gate and CR 012 fixes stored-hash integrity; neither relabels the real event or changes production topology.

The old real R2 failure and old same-message R3 invalid shape remain preserved. The live R3 Reply had a display marker but no explicit raw Channel `reply_to_message_id` field. The exact user text was rejected twice as `analysis_intent_not_recognized`; Router then substituted `analyze image`, created a request, and completed analysis. That substitution violates the two-message intent gate, so R3 is FAIL and the sequence stops. R4/R5 and the final P0 Gate remain prohibited.
