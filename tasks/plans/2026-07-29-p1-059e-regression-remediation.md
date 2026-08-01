# P1-059E Regression Remediation

## Goal

Remove the two reproducible, offline-only blockers found by 059E without
changing the P0/P1 phase, production runtime, OpenClaw installation, Feishu,
Gateway, credentials, candidate Jobs or generated master videos.

The only allowed result is a new attempt at the existing 059E full regression.
This work does not qualify P1, does not run a P0/P1 Gate, and does not replace
the required real R3 retest.

## Constraints

- Keep `PROJECT_STATUS.yaml` byte-for-byte unchanged.
- Do not start, stop, restart or configure OpenClaw, a Gateway, Binding,
  Agent, Cron, Feishu or browser session.
- Do not install dependencies, download browsers, or use `--no-sandbox`.
- Do not delete candidate artifacts, reports or prior failure evidence.
- No commit, push, tag, broad staging or cleanup.
- Every source increment has its own Change Request and targeted proof.

## R0 — Baseline and minimal reproduction

1. Record SHA-256 values for the two candidate source files and their tests,
   the current `PROJECT_STATUS.yaml` hash, and the existing 059E result.
2. Run only the Core contract module in the same discovery form and record its
   result.
3. Run a bounded, ordered predecessor subset only when needed to determine
   whether test process state reproduces the Core failure; do not run the full
   suite in this increment.
4. Keep existing 059E failure evidence immutable.

Stop if the reproduction indicates a changed OpenClaw installation or a
production process; neither may be repaired in this task.

## R1 — Core contract test isolation

**Change Request:** `P1-059E-CORE-TEST-ISOLATION-REMEDIATION`.

1. Change only `tests/test_core_feishu_control_contract_032.py`.
2. Replace the module-import-time `APPDATA` derived path with a small
   call-time resolver. It uses `APPDATA` when supplied and otherwise derives
   only the current user's Windows roaming-app-data default from `Path.home()`.
3. Preserve every installed-source assertion and fail closed if that one
   current-user location cannot see the expected directory. Do not add a
   configurable path fallback, copy source bundles, mock a bundle, or weaken
   string assertions.
4. Add focused regression coverage for both `APPDATA` and the current-user
   fallback, including the missing-`APPDATA` child-process case.
5. Verify the modified module with direct unittest and discovery invocation;
   parse any updated report JSON and run `git diff --check` for the increment.

If its targeted tests fail, restore only this increment from its pre-change
mirror, retain a safe failure report and stop before R2.

## R2 — Mascot contact-sheet local renderer compatibility

**Change Request:** `P1-059E-MASCOT-CONTACT-SHEET-REMEDIATION`.

1. Change only `src/factory/mascot.py` and
   `tests/test_p1_candidate_media.py`.
2. Preserve deterministic local SVG input, temporary user data directory,
   local-file-only policy and the PNG output contract.
3. Add an explicit process timeout and a safe non-network headless rendering
   compatibility configuration that does not attach to, close or modify an
   existing user Chrome profile. Do not use `--no-sandbox`.
4. Capture only a bounded last diagnostic line on failure; do not emit local
   file URLs or environment data.
5. Add a targeted test for the command contract and maintain the existing PNG
   size/output test.
6. Run the mascot media test module, then validate the output header and
   dimensions with local file inspection.

If the targeted contact-sheet test fails, restore only this increment from its
pre-change mirror, retain a safe failure report and stop. Do not introduce an
unverified renderer or browser download.

## R3 — Re-entry decision for 059E

1. Confirm both increments are green, project Gateway listener count remains
   zero, and `PROJECT_STATUS.yaml` hash is unchanged.
2. Update the 059E status/report only with the new narrow results; do not
   overwrite the original full-suite failure record.
3. Request or use existing authorization to rerun the original 059E full
   verification exactly once. If Python remains red, stop before all later
   checks and classify the new failure accurately.

## Acceptance

- Core contract source assertions remain real installed-source checks and pass
  reliably under their targeted discovery execution.
- The mascot contact sheet is a non-empty valid PNG produced locally from the
  eight existing SVGs without interacting with the user Chrome profile.
- No new dependency, production operation, phase/state change or network
  action occurs.
- A full 059E retry happens only after R1 and R2 pass.
