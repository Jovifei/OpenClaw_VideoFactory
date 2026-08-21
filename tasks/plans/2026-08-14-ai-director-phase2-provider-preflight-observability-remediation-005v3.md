# AI-DIRECTOR-PHASE2-PREFLIGHT-OBSERVABILITY-REMEDIATION-005V3

This plan is a local-only remediation for the sanitized `unexpected_error`
returned by the single 005V2 read-only Preflight. It authorizes no Provider,
Worker, Desktop, cache mutation, smoke, acceptance, MP4, or phase promotion.

The implementation will add a fixed gate/substep/reason error contract,
TestDrive fault injection, and a diagnostic-only profile. A new diagnostic
Preflight may be run only after local tests and independent reviews pass and
Jovi grants a separate one-command authorization.

Terminal local success: `AI_DIRECTOR_PHASE2_PREFLIGHT_OBSERVABILITY_REMEDIATED`.
Terminal diagnostic results are either
`PREFLIGHT_DIAGNOSTIC_BLOCKED:<gate>:<reason>` or
`READY_FOR_005V4_REAL_PROVIDER_QUALIFICATION_PLANNING`.
