# P0 package-gate repair

## Trigger

`scripts/00_package_check.ps1` was run after its prescribed local bootstrap and exited `2`. All package checks except `no apparent secrets` passed. The recorded hits were only pip source files beneath the generated project-local `.venv` directory.

## Root cause

`scripts/90_acceptance_gate.py` recursively scanned every text file in the project root. It did not exclude `.venv`, even though P0 requires `scripts/00_bootstrap_python.ps1 -Apply` to create that directory before this check. Pip contains identifiers such as `api_key`, which match the intentionally conservative secret pattern but are neither project configuration nor user credentials.

## Minimal repair

The gate now excludes only generated interpreter/VCS cache directories: `.venv`, `.git`, and `__pycache__`. It still scans all project-authored source, configuration, skills, and `reports/`; `external` and archived content retain their previous handling. No secret pattern was relaxed and no report was changed to force a pass.

## Evidence and rollback

- Failing output: `reports/command_logs/08_package_check.txt`
- Failure detail: `reports/gate_package.json`
- Bootstrap evidence: `reports/command_logs/07_python312_bootstrap_apply.txt`
- Rollback: restore the prior `scripts/90_acceptance_gate.py` content and the matching prior SHA line in `SHA256SUMS.txt`; the original false-positive behavior will return.

## Risk

Secrets accidentally written inside generated `.venv` or `.git` are no longer surfaced by this package-source gate. This is acceptable for this gate because neither directory is project-authored configuration, both are excluded from version control, and user-controlled reports remain scanned. Do not store credentials in either directory.

## Related P0 probe repair

The initial machine preflight also showed that its `$Args` parameter collided with PowerShell's automatic `$args` variable. It therefore invoked several tools with no arguments, including an interactive Python process. `scripts/01_machine_preflight.ps1` and `scripts/02_capture_openclaw_state.ps1` now bind `-Args` to an explicit `CommandArgs` parameter and splat that value. This changes only argument delivery; it does not add installation, configuration, or network-mutating behavior.

## Bounded probe repair

With arguments repaired, `openclaw skills check` was confirmed to exceed the outer 60-second preflight limit. The machine preflight now runs every probe as a direct, captured child process with a three-second limit and records an exit code of `-2` plus `TIMED OUT` when a command does not finish. This replaces a high-overhead PowerShell-job attempt that could itself exceed the outer preflight budget. The timeout starts no configuration wizard and does not modify OpenClaw state.

The machine inventory now records only the OpenClaw binary version. Gateway, config validation, doctor, skills, channels, cron, schema, and security audit are P0-02 responsibilities and will be captured separately with their own bounded collector. This eliminates duplicate, blocking calls without omitting the required evidence.

The direct collector now refreshes the completed process before reading its exit code. The preflight already exits deterministically: `0` when no generated blockers exist and `2` when it records blockers. This removes the prior false GPU blocker caused by a null `Process.ExitCode` and prevents an unrelated prior native command from deciding the result.

## Bounded OpenClaw state capture

P0-02 now captures every requested OpenClaw command with the same process-level three-second bound, stores each command and exit code in its individual state file, and redacts common secret forms before persistence. The collector returns `0` once all state files are written; a captured nonzero or `TIMED OUT` result is evidence for the configuration plan and P0 gate, never a pass.

## Windows runtime-gate repair

The P0 gate originally asked Python to execute `openclaw`, `codex`, and `lark-cli` directly. On this Windows host the commands resolve to PowerShell `.ps1` shims, which Python cannot execute as child processes. The gate now resolves their adjacent `.cmd` shims only on Windows before running the same argument list. It does not change the pass criteria; it makes the runtime checks reflect the installed tools rather than a shell-wrapper artifact.

## Windows encoding compatibility repair

Windows PowerShell 5.1 writes `Set-Content -Encoding UTF8` with a BOM. Its own P0 machine preflight therefore produced valid JSON that `scripts/90_acceptance_gate.py` rejected when it read only strict `utf-8`. The gate now reads JSON and YAML with `utf-8-sig`, accepting both Windows BOM-bearing and standard UTF-8 files while keeping the same JSON/YAML parsers and validation behavior.

## Evidence-file extension repair

`openclaw skills check --agent video-factory --json` was captured with its command and exit-code footer in a file named `reports/command_logs/62_skills_check_video_factory.json`. The file is deliberately a human-readable command log, not a standalone JSON document, so the recursive package parser correctly rejected its extra footer. Its name was changed to `62_skills_check_video_factory.txt` without changing its content. The gate again parses every actual `.json` file, rather than excluding command logs from validation.

## Doctor collection timeout repair

The P0 gate used a uniform 60-second limit. A direct, redacted `openclaw doctor` run completed with exit 0 in 57.2 seconds, while a prior gate run hit the 60-second boundary under load. Only the gate's `doctor` invocation now has a 90-second limit; all other runtime commands retain 60 seconds. This preserves real doctor warnings and removes a timing-only false failure. Evidence: `reports/command_logs/71_openclaw_doctor_extended.txt`. Rollback: restore the previous one-line result comprehension and matching SHA checksum.

## Route A command-log extension repair

Five Route A command logs began with a human-readable `COMMAND:` header followed by JSON output, but their filenames ended in `.json`. The strict parser correctly rejected them. They were renamed to `.txt` without content changes: `76_route_a_live_schema.txt`, `78_route_a_config_schema_lookup.txt`, `78a_route_a_config_schema_lookup_retry.txt`, `80_route_a_remaining_schema_lookups.txt`, and `89_route_a_codex_model_schema_lookup.txt`. This preserves strict validation of actual JSON evidence files.
