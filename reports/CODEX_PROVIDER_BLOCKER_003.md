# Codex Provider Blocker 003

## Classification

Environment-level Direct Codex CLI prerequisite failure, isolated from the
Video Factory implementation. No provider recovery action was executed.

## Structured evidence

The isolated failure snapshot under
`dist/director/provider_failures/director_ec229e6efe2c340d/` contains exactly
`director_report.json` and `video_job_state.json`. The report records:

- `code: director_provider_failed`
- `reason: nonzero_exit`
- `exit_code: 1`
- one provider attempt

Both JSON documents validate against their existing schemas. No MP4, timeline,
subtitle, raw prompt, raw output, stdout/stderr, credential, or absolute
provider output is retained in the failure directory.

## Cache structure evidence

The content-free structural probe returned:

```json
{"cache_exists":true,"json_valid":true,"missing_base_instructions_count":9,"model_count":9}
```

Only counts and validity were read. The cache was not printed, edited, moved,
refreshed, or replaced.

## Provider isolation controls

Static source and targeted tests confirm `--ephemeral`, `--sandbox read-only`,
`--skip-git-repo-check`, `--output-schema`, `--output-last-message`,
`shell=False`, a positive timeout (default 180 seconds), and a 256 KiB output
limit. Forbidden write/model/profile/login controls are absent. The provider
review ran 31 targeted tests successfully.

## Project isolation evidence

The project source contains no direct reference to `models_cache.json`,
`base_instructions`, or the user Codex cache path. The failure directory is
separate from the completed fake-provider directory.

## Observation

The failure state is schema-valid but reports `factual_review_status: verified`
while its companion director report requires factual review. This is retained
as a report-integrity observation and is not treated as provider isolation
evidence.

## Current result

Provider isolation is PASS, but real provider acceptance is BLOCKED. This
provider-only report does not qualify the full implementation; the overall
qualification report records `FAIL_IMPLEMENTATION`.
