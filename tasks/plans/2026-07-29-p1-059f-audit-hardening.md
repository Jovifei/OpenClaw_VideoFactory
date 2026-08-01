# P1-059F Audit Hardening

## Goal

Close the three independent-review gaps in the offline P1 candidate audit:

1. protect `render_manifest.json` with the same SQLite SHA contract as the
   artifacts whose fields it controls;
2. replace declaration-only delivery flags with a locally guardable and
   independently verifiable dry-run execution proof;
3. make visual-review input and output containment canonical, symlink-safe and
   manifest-only.

The work remains repository-only. It must not perform real Feishu delivery,
OpenClaw/Gateway lifecycle, P0/P1 Gates, phase-state changes, browser/model
download, commit, push or tag.

## F0 — Baseline

1. Record the status hash, Project Gateway listener count, selected candidate
   Job IDs, current artifact DB presence for `render_manifest.json`, and the
   059E independent-review findings.
2. Preserve all existing Jobs and reports. No cleanup or candidate rerender.
3. Before any candidate-evidence write, resolve the five Job IDs solely from
   `reports/P1_POLISH_CANDIDATE_058.json`; a handoff or historical report is
   never an execution source of truth.

## F1 — Render-manifest integrity

**Change Request:** `P1-059F-RENDER-MANIFEST-INTEGRITY`.

Modify only:

- `scripts/p1_final_audit.py`;
- `tests/test_p1_final_audit.py`.

Add `render_manifest.json` to the existing required DB-hashed artifact list.
The pipeline already writes and records it; do not change SQLite schema,
pipeline behavior or delivery payloads.

Tests must prove: missing DB row fails, file tampering fails before semantic
inspection, index contains the artifact, and a DB-consistent wrong encoder
still reaches `encoder_mismatch`.

Run focused Python tests, the live final auditor (read-only over Jobs), JSON
parse and increment `git diff --check`. Stop if any fails.

## F2 — Dry-run execution proof

**Change Request:** `P1-059F-DRY-RUN-EXECUTION-PROOF`.

Modify or create only:

- `src/factory/delivery.py`;
- `src/factory/db.py` only for a read-only delivery lookup if needed;
- `scripts/p1_dry_run_delivery_runner.py`;
- `scripts/p1_final_audit.py`;
- their focused Python tests.

The runner accepts only a valid Job ID and uses fixed project-local state and
package roots. Before delivery code executes it installs a Python audit hook
that denies DNS/socket and subprocess/os-system events. It exposes no target,
endpoint, recipient, credential, command or environment-forwarding argument.

The runner writes an atomic, redacted `dry_run_execution_proof.json` only after
the local delivery operation completes under the guard. The proof must record
safe scalar counts, manifest SHA, runner-source SHA and deterministic delivery
key; never PID, paths, command line, environment, user text or exceptions.

The proof, delivery manifest and SQLite delivery row must agree. The proof and
any updated redacted metrics must have DB artifact hashes. The final auditor
must reject missing/tampered proof, manifest/DB mismatch, unsafe proof fields,
guard counters above zero, target-like fields or runner source drift. Legacy
`network_called` and `lark_cli_called` may remain for compatibility but cannot
be acceptance evidence.

Tests must exercise guard event classification without network I/O, proof
idempotency, file/DB/proof tampering, forbidden runner arguments, and static
absence of delivery transport imports/calls. No test may make a real network
or lark-cli call.

After focused tests pass, run the runner once for each existing selected Job
to generate guarded local proofs; it must not change videos, source media or
delivery targets.

## F3 — Visual-review containment

**Change Request:** `P1-059F-VISUAL-REVIEW-CONTAINMENT`.

Modify only:

- `remotion/scripts/render-review-stills.mjs`;
- `remotion/scripts/test-review-stills.mjs`.

Disable legacy `--input` fail-closed. Accept only one `--inputs-manifest`, one
project-relative `--output=reports/p1_review_<id>`, and optional local Chrome
path. Reject unknown, repeated and value-less arguments before bundle/browser
work.

Use `lstat` plus `realpath` to require a non-symlink manifest below `reports/`
and four non-symlink inputs below `jobs/p1_candidate/`; compare canonical paths
against the canonical project root and use canonical duplicates. Require the
canonical `reports/` parent to be non-symlink and derive output/staging below
it. Existing output or a symlink fails without following it.

Tests use an injected filesystem seam for stable symlink/outside-canonical
coverage, plus legal manifest, command parsing, frame mapping and contact-grid
regressions. Do not render stills during the unit test.

## F4 — Requalification

1. Run the final auditor after F1/F2 proof creation and verify five exact
   roles, DB hashes, dry-run proof and media contracts.
2. Run focused Python and Node tests, then full Python discovery, Schema,
   `pip check`, explicitly enumerated Pester, Remotion typecheck, npm audit,
   review-still test, artifact media/decode, exact-scope secret/large-file scan
   and `git diff --check` in that order. Stop at the first failing family.
3. Perform a new independent read-only review limited to the hardened audit,
   runner and visual-review files. It cannot be test evidence.
4. Only if all pass, update status reports and the two existing Obsidian notes
   to `P1_OFFLINE_REVIEW_PACKAGE_READY`; otherwise retain a precise blocked
   state. Never enter a P0/P1 Gate.
