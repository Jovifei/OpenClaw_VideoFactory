# Phase 1 I2C semantic editorial and diagram increment

CR: `reports/change_requests/PHASE1-I2C-SEMANTIC-EDITORIAL-013.json`.

1. Add source-owned editorial binding metadata to the I2C research fixture and schema.
2. Implement deterministic candidate review that accepts only complete source-bound
   concepts or explicitly safe framing; preserve the 85 threshold and one-rewrite budget.
3. Extend scene-plan contracts with a bounded I2C diagram specification and compile it
   only from verified fact IDs.
4. Add one deterministic I2C bus/open-drain/timing renderer in the existing
   `TechnicalExplainer` composition; preserve generic behavior for other topics.
5. Add Python, Node and Remotion negative/positive tests, run focused and bounded
   regressions, then produce one fresh I2C audible candidate for manual review.

Stop on any unsupported claim, missing source binding, cross-language contract drift,
or render/post-render failure. Do not run Formal Gate or Phase Promotion in this increment.
