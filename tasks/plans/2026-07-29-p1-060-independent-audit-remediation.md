# P1-060 Independent Audit Remediation

## Goal

Resolve the seven valid findings from the fresh independent read-only review
without contacting Feishu, OpenClaw, Gateway, Chrome network services, or
production controls. The candidate remains offline-only and `PROJECT_STATUS.yaml`
must remain unchanged.

## Evidence boundary

An artifact and SQLite record in the same writable local trust domain cannot
cryptographically prove that a runner process executed. P1-060 must not claim
otherwise. It will downgrade this to explicit self-attested local evidence and
make the final audit fail closed for any outcome that would otherwise call it a
qualified execution proof. A later task may add an independently authorized
external trust root; this task must not invent one.

## 060A — Final-audit CLI write containment

**Change Request:** `P1-060A-FINAL-AUDIT-OUTPUT-CONTAINMENT`.

Limit all three final-audit report outputs to fixed filenames directly beneath
the canonical non-symlink `reports/` directory. Reject absolute, traversal,
symlink, arbitrary filename and special project-file targets before opening any
output. Add targeted tests proving that `PROJECT_STATUS.yaml` and other project
files cannot be output targets.

## 060B — SQLite delivery runtime-state binding

**Change Request:** `P1-060B-DELIVERY-DB-STATE-BINDING`.

Require the SQLite delivery row to have the exact expected `job_id`,
`mode=dry-run`, and `status=recorded`, as well as its existing canonical
manifest equality. Test that a DB-consistent manifest cannot mask a changed
delivery mode or status.

## 060C — Manifest and proof strict schemas

**Change Request:** `P1-060C-DELIVERY-EVIDENCE-SCHEMA`.

Apply exact top-level key whitelists, exact nested artifact fields, safe scalar
types, and recursive no-secret/no-path/no-URL checks to delivery manifest and
execution proof. Existing compatibility booleans remain reject-only guards, not
proof of execution. Add unknown-field and unsafe-value tests.

## 060D — Honest execution provenance classification

**Change Request:** `P1-060D-EXECUTION-PROVENANCE-BOUNDARY`.

Replace `guarded_local_runner` qualification language with explicit
`self_attested_local_runner` evidence. The final audit must report a limited,
non-qualifying state when this is the only provenance; it cannot return the
review-ready status on self-attestation. Preserve existing candidate artifacts;
do not manufacture a key or external signer.

## 060E — Chrome executable containment

**Change Request:** `P1-060E-CHROME-EXECUTABLE-CONTAINMENT`.

Remove the arbitrary `--chrome` override. Resolve only the configured default
local Chrome executable through a canonical allowlist and reject absent,
symlink, UNC, drive-relative and outside-allowlist paths before bundle/browser
work. Tests remain no-render.

## 060F — Remotion bundle containment

**Change Request:** `P1-060F-BUNDLE-OUTPUT-CONTAINMENT`.

Derive bundle output from a canonical non-symlink project-local staging root
and reject any existing/symlinked output. Keep all generated bundle material
inside the approved Remotion root. Add injected-filesystem containment tests;
do not bundle during tests.

## 060G — Failure-output redaction

**Change Request:** `P1-060G-VISUAL-FAILURE-REDACTION`.

Persist and print only stable error codes. Never write or print JavaScript
exception text, paths, input contents, command values or browser diagnostics.
Test failure normalization without rendering.

## Verification and stopping rule

Each increment is serial: create its Change Request, modify only its declared
files, run its focused tests, JSON parse and `git diff --check`. A failed
focused test stops P1-060 at that increment. After all increments, run the
final auditor, full Python, Schema, Pester, Node/TypeScript, npm audit,
bounded MP4 decode, precise secret/large-file scans, then one new bounded
read-only independent review. No P0/P1 Gate or promotion is allowed.
