# P0 Child Claude Revalidation

Status: `launcher_and_bounded_readonly_package_succeeded`.

## Corrected classification of A-D

The four prior A-D architecture reviews were not launch failures and did not prove an isolation rejection. Each child started, remained alive through three 30-second watchdog checks, emitted no accepted final JSON, and was terminated at the 90-second completion boundary. Their correct classification is `completion timeout`.

Those packages were broad architecture audits and therefore unsuitable for the bounded-child contract. They remain diagnostic-only; the parent source review remains the evidence for the OpenClaw architecture conclusion.

## Fresh validation

| Package | Scope | Result |
| --- | --- | --- |
| No-tool smoke | Exact `CHILD_SMOKE_OK` reply | `Success=true`, `TimedOut=false`, `Turns=1`, completed in 11.4 seconds |
| Bounded review | Four named project reports, read-only | `Success=true`, `TimedOut=false`, completed in 26.7 seconds; correctly returned `completion timeout`, no launch/isolation proof, and confirmed that the middleware conclusion does not depend on A-D |

The launcher source passes the requested `--max-turns 3` to Claude. The bounded review returned `num_turns=5`; the launcher documentation describes the cap as tool-call turns, while the returned total has no individual tool-call trace. This count is therefore not proof that the cap was bypassed.

## Rule going forward

Use Child Claude only for a bounded package with no more than five parent-named files, compact acceptance criteria, and an independently reviewable result. Keep broad architecture and repository audits with the parent. A bounded package that reaches the 90-second deadline may be retried in a fresh session up to the three-attempt cap; then the parent takes over.
