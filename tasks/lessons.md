# Lessons

## 2026-07-28 — Backend completion is not a user-visible result

- Do not classify a media flow as product-qualified merely because the Ticket, request, analyzer, and result artifact completed.
- Verify that the originating Feishu group receives a readable, sanitized analysis summary. A generic completion notice is a partial pass and blocks the next media phase.

## 2026-07-30 — Treat per-media visible results as a separate contract

- A successful Analyzer artifact cannot justify the next media phase when the
  public projection still returns a generic completion notice. Audit every
  media kind before its first real qualification and remediate its own
  server-owned presentation before asking Jovi to upload a test fixture.
- A user-visible fresh Core ingress reply is runtime evidence for that event,
  but it does not make credentialed CLI observability available. Keep these
  evidence layers distinct and never paste or reuse a Ticket outside its
  original Feishu group.

## 2026-07-24 — Maintenance authorization still requires executable proof

- After Jovi grants a maintenance scope, execute every safe in-scope preparation and read-only verification instead of stopping at documentation.
- Authorization never converts an unknown consumer owner, missing secret injection, or non-executable control contract into evidence. Stop before T0 only at a concrete fail-closed gate and name the exact missing proof.
- A fake RPC token or Shadow lifecycle proves an interface, not production authentication or ownership.

## 2026-07-20 — Feishu attachment intent is a two-message protocol

Feishu cannot reliably send an attachment and its analysis caption as one message. Treat the attachment event as ingress-only and accept analysis intent only from a later text Reply with Channel-provided `reply_to_message_id`; never infer association from time, filename, or bot summaries.

## 2026-07-20 — Keep media safety eligibility separate from user intent

- `analysis_allowed=true` means only that a quarantined copy is safe to inspect; it must never trigger an Analyzer without an explicit, normalized, type-matching `attachment_action` and `analysis_requested=true`.
- PowerShell receipts may contain uppercase SHA-256 while Python emits lowercase. Analyzer integrity checks must canonicalize full 64-character hashes, use `stored_sha256` for the stored copy, and separately require source/stored equality.

## 2026-07-16 — Do not let a privileged test stall an otherwise testable repair

- When Windows denies test-only file symlink creation, preserve the security requirement and replace only the test mechanism with an unprivileged junction or function-seam test.
- A queued follow-up is not completed work. Report the exact blocker, finish the active task, then explicitly advance the queue in the user-approved order.
- Before merging documentation during an active repair, verify the repair has stopped changing files; otherwise postpone the merge instead of creating ambiguous evidence.

## 2026-07-14 — Keep code execution separate from the production runtime gate

- Do not bind Codex CLI login, OpenClaw OAuth profiles, the optional Codex Plugin, and the `video-factory` primary Runtime into one P0 requirement.
- P0 validates the OpenClaw infrastructure chain. OpenClaw Default Runtime is valid, and `/codex status`, `/codex models`, and Codex Plugin OAuth are not P0 acceptance criteria.
- Validate Codex development capability with isolated `codex exec --ephemeral` read and workspace-write smokes. Do not repair or mutate OpenClaw Codex OAuth when direct Codex CLI is the approved executor.
- Treat `deferred_optional_not_blocking` as an explicit architectural state, not a hidden failure or an invitation to continue diagnosis.
- When the user corrects a gate architecture, update the gate, acceptance docs, backlog, and active plan together before resuming implementation.

## 2026-08-01 — Desktop Codex update does not imply CLI update

- On Windows, verify `Get-Command codex -All` and `codex --version`; the
  desktop application's Store package and the npm CLI shim can be different
  installations with different release ages.
- Do not assume the desktop application's embedded `codex.exe` is callable
  from an ordinary PowerShell process: WindowsApps ACLs may deny direct
  execution. Record the path split before proposing an upgrade.
- A temporary older-model override cannot satisfy a configured-model P0 CLI
  smoke and is prohibited when model selection is architecturally locked.

## 2026-07-14 — User-authorized automatic execution

- Distinguish a user authorization for automatic P0 command execution from an OAuth reauthentication authorization. Do not infer one from the other.
- When Jovi authorizes automatic execution, scope the policy to the affected agent and preserve phase gates, peer/sender allowlists, attachment non-execution, and publishing prohibitions unless he explicitly expands them.
- Verify the effective host-intersected policy after every change; a configured `mode=auto` may still produce an on-miss approval prompt.

## 2026-07-12 — Child-claude timeout handling

- A blank child launcher result after timeout is not evidence that the child produced no output or made no progress.
- Before classifying a timeout, inspect the launcher diagnostics and structured fields (`Success`, `TimedOut`, `Result`, `Stderr`, `RawStderr`, and `DiagnosticsPath`).
- Do not delegate an audit of more than five files to Child Claude. The parent agent must perform broader inventory and review directly.
- For a bounded child read-only task, set the explicit working directory and path boundary, do not provide secrets, and preserve diagnostics in the P0 report.
- A child that remains alive until the 90-second launcher boundary with no acceptable final JSON is a `completion timeout`, not a launch failure, isolation failure, or proof of no progress. A 30-second watchdog with no output is only `running`.
- Do not retry a broad or poorly bounded audit. For a correctly bounded package (at most five named files, compact output, and at most three turns), retry only in a fresh session; after three consecutive failed attempts, the parent takes over.

## 2026-07-18 — Child-claude classification correction

- Do not describe a 90-second Child Claude termination as a generic "failure" without the structured classification. Report `completion timeout` when `launchError` is empty, the child remains alive through watchdog checks, and no valid final JSON arrives before the deadline.
- Use a no-tool smoke to prove the launcher/profile chain separately from a bounded read-only package. Do not infer a tool, scope, or isolation problem from a broad task's completion timeout.

## 2026-07-12 — Feishu routing assumptions

- Do not assume a VideoFactory-specific Feishu app is required before checking OpenClaw's exact peer-routing support.
- When an existing account is authorized for reuse, prefer a new exact group peer binding over an account-wide rebinding; verify precedence, target-group ownership, and existing bindings before applying.
- Treat account-level access-control fields as potentially shared state. Do not narrow or replace them unless the live schema proves a peer-scoped alternative or the user explicitly accepts the impact.
- Do not infer a group's sender open_id from `commands.ownerAllowFrom`. Confirm it from a real rejected/accepted Feishu inbound log before writing a per-group sender allowlist.
- An exact peer binding governs only messages received by its selected account. If another bot account is also a member of the group, explicitly disable that group for the other account or remove that bot before claiming single-consumer routing.

## 2026-07-12 — Runtime model proof

- A model listed as available by `openclaw models list` is not proof that the active embedded runtime can resolve it. Do not switch a routed agent's primary model without a real message-response proof.
- Keep the OpenClaw agent model separate from the Codex Supervisor command surface. When a user specifies the existing agent model, preserve that model and verify `/codex` commands independently.
- Never record, use, or echo a credential pasted into chat. Treat it as exposed and advise rotation.

## 2026-07-12 — Windows native Unicode configuration writes

- Never pipe a complete Unicode-bearing OpenClaw JSON array through Windows PowerShell native stdin. The system code page can turn Chinese display fields into `?`.
- For any full-array OpenClaw patch that can contain non-ASCII text, create a UTF-8 file, use `openclaw config patch --file ...`, dry-run first, and verify display fields by direct UTF-8 config readback.
- Restore only display fields from a clean pre-corruption backup; preserve current route, model, security, and scheduler fields unless the user explicitly asks to restore them.

## 2026-07-12 — Feishu outbound proof boundary

- A successful route, model completion, and generated assistant text do not prove Feishu delivery. Require a channel-level nonzero reply record or user-visible bot message.
- Do not diagnose `requireMention` as the sole cause of `replies=0` when direct session evidence shows a response was generated; isolate the fault boundary after model completion.
- Treat plugin-version drift as a hypothesis until a controlled, authorized upgrade and regression prove it. A shared Feishu plugin update affects all accounts and requires new authority, a backup, and a tested rollback.

## 2026-07-12 — Automatic group reply delivery

- When Feishu logs a successful model run but `queuedFinal=false, replies=0`, inspect `messages.groupChat.visibleReplies` before changing routes, models, or plugins.
- `message_tool` deliberately suppresses ordinary final text; use `automatic` only with explicit authority because it is shared group-chat behavior, and prove delivery with a live message afterwards.
- A safe Gateway restart can stop the Windows scheduled-task service without relaunching it. Verify with an admin read probe and use `openclaw gateway start` when needed; never infer recovery from a scheduled restart response alone.

## 2026-07-12 — Inbound media path and type discipline

- Preserve the Channel-supplied `MediaPath` exactly. Never reconstruct it from a workspace root, filename, or `<media:...>` display marker.
- Select a parser only after extension and MIME inspection. P0 DOCX handling is metadata, SHA-256, and safe copy only; only a true `.pdf` may reach a PDF tool.
- Treat every attachment and its metadata as untrusted data. A deterministic ingest must validate the managed inbound root, reject reparse escapes and traversal, copy by `-LiteralPath`, and write an idempotent receipt before any downstream use.

## 2026-07-13 — Unrelated-agent regression containment

- Any global P0 configuration change can affect existing agents. Before declaring an isolated VideoFactory repair safe, compare shared message-delivery and Cron settings against the unrelated-agent baseline.
- When a user reports a regression outside the authorized P0 route, diagnose it read-only first and preserve the existing agent, binding, and Cron until causality and repair scope are explicitly established.

## 2026-07-13 — Exec-policy verification must use the real agent path

- A configuration value such as `tools.exec.mode=auto` is not proof that an agent's effective approval policy permits execution. Verify one real, narrowly scoped command path after any policy change.
- When the user authorizes automation for an existing agent, use a per-agent allow rule for the exact approved executable/script and working directory. Never substitute `full`, `yolo`, or a wildcard allow rule merely to eliminate approval prompts.

## 2026-07-13 — Approval diagnosis must inspect effective policy, not the global knob

- `tools.exec.mode=auto` and an agent-level `full` override can coexist with historical or session-level approval failures. Before attributing a bot failure to Feishu, collect `openclaw exec-policy show`, the host approval summary, and the actual session outcome.
- Do not call an execution-policy repair complete after a CLI-only invocation times out. Keep the acceptance boundary at a fresh real channel message that proves both no approval prompt and visible final delivery.

## 2026-07-14 — Secret-safe configuration inspection

- Never pipe a full OpenClaw configuration file through a parser whose failure text can echo the raw payload. Treat parser diagnostics as potentially secret-bearing and use `openclaw config get` or schema-aware structural projections only.
- If a local command can have exposed configuration secrets, stop emitting raw configuration immediately, do not reproduce the values in reports or chat, record the exposure boundary without values, and advise the operator to rotate affected credentials.

## 2026-07-14 — Codex CLI smoke isolation

- Never infer a read-only Codex CLI smoke from defaults. Pass `--sandbox read-only` explicitly and compare a full workspace manifest, Git porcelain status, and binary diff before and after the command.
- Before upgrading a CLI, prove its resolved path and installation manager. If more than one independent installation path exists, stop instead of deleting, relinking, or guessing precedence.
- Keep Codex CLI capability separate from OpenClaw Plugin OAuth and Runtime state. A direct CLI upgrade or smoke never authorizes login, profile, auth-order, model, Runtime, or OpenClaw configuration changes.
- When Jovi confirms that an operator-only step is complete and explicitly says to continue, resume the already approved downstream verification sequence; do not require a redundant authorization checkpoint.
- A user-issued maintenance freeze overrides an earlier resume. Until the exact resume phrase is received, reuse the last verified CLI facts and do not poll versions, invoke Codex, request software closure, or retry blocked smoke/gate steps.
# 2026-07-20 — P0-ONE-SHOT-ANALYSIS-INTENT-014

- A deterministic command must be bound to the original Channel event, including its real message id; raw text or a model rewrite is not sufficient evidence for a one-shot attachment intent.
- OpenClaw command/skill dispatch can preserve command text while omitting the source message id. Check the runtime type/schema before implementing a pending-intent feature; stop with `DETERMINISTIC_COMMAND_SOURCE_UNAVAILABLE` when the binding is absent.
- Offline Reply/Analyzer tests and prior live ingress passes do not authorize or prove the new one-shot route. Preserve the earlier R3 FAIL and keep later live steps gated.

# 2026-07-21 — P0-FEISHU-CARD-ANALYSIS-ACTION-015

- Feishu card capability has two separate facts: the OpenClaw core can send cards and register `card.action.trigger`, but its built-in Feishu handler can still route actions into synthetic commands and the Router. Card support is not proof of a deterministic project callback.
- Verify whether the generic plugin interactive registry is actually wired for the target channel before treating its type declarations as an integration point; in this runtime it is used by Discord/Telegram paths, not the Feishu monitor.
- When the target account uses WebSocket mode, local OpenClaw config cannot prove the Feishu developer-console callback subscription. Preserve the single existing message consumer and require redacted admin verification before live card smoke.

# 2026-07-21 — credential-output containment

- Never run a generic parser or diagnostic against a complete credential-bearing OpenClaw configuration when its failure path can echo the original payload. Use narrow `openclaw config get` projections or an in-memory scanner that emits only type, path, line, and one-way fingerprint.
- Treat interactive tool and terminal transcripts as possible credential stores. Scan project artifacts and app-managed session archives separately; do not delete or rewrite app-managed evidence without an explicit retention decision.

# 2026-07-21 — Channel-boundary decision after core metadata loss

- Once evidence proves a core Channel Binding normalizes away trusted event metadata before project controls, stop iterating post-Binding prompts, commands, Reply inference, or claims. Evaluate only a replacement Channel owner or a project-owned Channel gateway using isolated raw-event evidence.

# 2026-07-22 — RPC health-output containment

- Treat `openclaw gateway call health --json` as credential-adjacent: project only the Boolean probe result and endpoint class, never echo or persist its raw response.

# 2026-07-26 - Project Gateway authentication path correction

- Once the installed OpenClaw protocol proves Project access is device-auth based, stop retrying shared `OPENCLAW_GATEWAY_TOKEN`, service installation, or Gateway restart. Build a separate Project device identity, sign the challenge through the installed official client, request pairing once, and keep the device token outside the repository.
- A healthy service registration and CLI health probe do not prove the Project client can authenticate. Treat them as lifecycle evidence only; the Project readiness boundary is an official-client device handshake with explicit approved role and scopes.

# 2026-07-29 — Offline audit evidence and output containment

- Never let an audit CLI accept arbitrary output paths: a read-only audit can
  still overwrite phase or policy files through report arguments. Bind outputs
  to canonical, non-symlinked report locations.
- A JSON proof, artifact hash and SQLite row in the same writable trust domain
  are self-attestation only. Do not label them as independent execution proof
  without a separately protected trust root.
- Error text, browser paths and local command values are sensitive diagnostics.
  Persist and display stable error codes only in candidate evidence.
- Do not describe an increment as complete merely because its pre-existing
  regression suite passes. Mark it complete only after every newly required
  adversarial test and its declared independent review have run.

# 2026-07-30 — Persisted receipt schema parity

- Do not treat a helper's return payload as the persisted receipt schema. Before
  adding a receipt-field eligibility check, inspect a real quarantined receipt
  and add a contract test for its field names and normalized values.

# 2026-07-30 — Analyzer artifact presentation parity

- Formatter-only tests are insufficient. For every new Analyzer output, load
  the exact serialized `_write_result` artifact through its public presentation
  loader before declaring the user-visible result path complete.

# 2026-08-01 — Audio transcript artifact parity

- `transcribe_audio` writes `transcript.json` with top-level transcript fields;
  do not infer a nested `result` shape from another Analyzer. A completed local
  transcript can coexist with an empty user reply when the presentation loader
  is wrong. The project venv import probe is separate evidence and does not
  explain a completed artifact from another runtime.

# 2026-08-02 — External agent concurrency must be proven separately

- A healthy Feishu Channel can still appear broken when one agent launches duplicate long-running subprocesses. Diagnose Channel receipt, dispatch, process concurrency, and queue-cap eviction separately before changing Gateway configuration.
- For external agent workspaces, add an OS-level single-run lock and a bounded real-time budget; prompt rules alone are not a concurrency control.

# 2026-08-04 — Use available Feishu CLI test paths before asking Jovi to test

- Do not treat a real user-originated inbound test as a reason to stop before checking the installed `lark-cli` profiles and identity modes.
- Under Jovi's authorization, run the allowed target's dry-run, bot-identity send, idempotency retry, and read-only outcome checks autonomously; use `--as user` only when an authorized user token is actually available.
- Keep sender identity explicit: a bot-originated message can prove CLI egress and any observed Router behavior, but it cannot be mislabeled as user-originated ingress or P0 single-consumer/deduplication proof.

# 2026-08-04 — P0-089: Verify platform controls before making an external-evidence prerequisite

- Do not invent a developer-console action from an abstract test requirement. Before asking Jovi for an external replay, verify the official platform's actual retry, logging, and replay controls.
- For Feishu event delivery, distinguish unsupported manual replay from supported automatic retry: v2 events use `event_id` for idempotency, and retry is platform-triggered after failed/late acknowledgement.
- When a gate's evidence collection method is infeasible, preserve the gate's safety objective, retire the false collection path, and design a bounded real test before changing either the Gate or production routing.

# 2026-08-04 — P0-091: Keep the project outcome ahead of an infeasible subtest

- Do not repeatedly retest a supporting evidence mechanism after its authorized run has shown that the required observable is unavailable. Stop and classify whether the blocker is runtime, platform capability, or acceptance-contract design.
- Report official phase status separately from offline candidate capability. A qualified offline MP4 pipeline is valuable implementation progress, but it is not P1 or production until the live boundaries and formal Gate pass.
- Re-plan from the product dependency chain after every terminal evidence failure: P0 admissibility, P1 deterministic delivery, P2 daily automation, then optional GPU/reference/Jianying work. Do not let one unproductive P0 probe dominate the work queue.

# 2026-08-09 — Phase1.5 composition correction

- A knowledge-video renderer must treat content, subtitle, brand, and signature regions as a single contract. A passing MP4 is not enough when captions can cover the illustration.
- The Pink Pig upstream repository is a style/persona/composition source, not a picture directory. Use Registry-owned local knowledge illustrations and keep the upstream reference in provenance.
- Registry branding overlays must be excluded from the legacy directory-scanning scene manifest; otherwise adding a signature asset silently changes the legacy scene count.
- Composition subtitle style is authoritative over old job overrides. Normalize final-video pixel values to the libass virtual canvas and inspect at least one extracted frame before claiming layout correctness.

# 2026-08-09 — Phase 2 provider evidence boundary

- Keep fake-provider, schema, media, and real-provider evidence in separate
  categories. A deterministic local MP4 cannot be promoted to AI Director
  READY when the single real provider acceptance returns nonzero.
- When a provider fails before producing a report, overwrite the job's
  `director_report.json` with a sanitized structured failure report; never
  leave a previous successful provider report as if it described the failed
  attempt.

# 2026-08-10 — Phase 2 remediation lifecycle and retirement boundary

- Every Phase 2 stage must normalize non-contract exceptions to
  `video_job_execution_failed` and atomically persist a sanitized `failed`
  snapshot; an ordinary Python exception must never leave a job in
  `rendering` or `storyboard_ready`.
- A stable-topic job directory must be reset before a retry, and a reused
  Director must clear `last_report`, script, score, and asset-selection
  outputs before planning. Current topic digest and error code are required
  before accepting a failure report.
- Retiring a legacy media chain means removing its callable source modules,
  not merely returning a no-op response. Keep only database/state/inventory/
  cancellation controls and make retired CLI commands fail closed with
  `code/message/context` and exit 2.
- `factual_review_required` is a boolean contract: verified factual briefs
  set state and Director reports to `false`; topic-only candidates remain
  review-required. Error paths must redact Windows drive-letter paths such as
  `C:/...` as well as slash/backslash variants.
- A detached Provider runtime must be fully reviewed and source-hash frozen before launch. Worker generations may recover only at explicit lease/checkpoint boundaries; once a smoke or acceptance command is claimed, its one-shot outcome must never be guessed or rerun.
- A Provider retry must use a new task ID, external run namespace, fixture/job ID, reports, and Change Request. Never restart or overwrite a terminal blocked run to manufacture continuity.

# 2026-08-11 — Detached qualification handoff boundary

- A Desktop close/reopen is an explicit human interlock for a detached-worker
  qualification, not a normal video-generation step. Do not ask Jovi to close
  or reopen the app until the Worker contract, source freeze, and prelaunch
  reviewer have all passed; explain that the close proves Worker survival and
  the reopen is only for read-only Verify and independent review.
- If the manual interlock is not completed before the bounded wait expires,
  record the run as `BLOCKED_DETACHED_WORKER_DIED` or the more specific
  quiescence blocker and do not start another Worker under the same task.
- Restarting Codex Desktop after a detached Worker has died does not reset the
  qualification ledger. Preserve the blocked run and require a new task ID,
  namespace, fixture, source freeze, and explicit one-Worker authorization
  before another real-provider attempt.

# 2026-08-12 - 005T detached provider execution gate

- A restarted Desktop is only an environmental prerequisite. It is not proof
  that a detached Worker survived, that the cache is quiescent, or that a real
  Provider command ran. Keep the 005T Worker, smoke, and acceptance counters
  zero until the bound handoff marker and independent approvals exist.
- Profiles without an authorized rehearsal must reject `Rehearse` before any
  preflight reads cache/config/auth. Production qualification still requires
  the single bounded Worker path and the exact run-bound human close marker.
- Source-freeze digests must use the exact production canonicalization,
  including the Profile's literal relative path separators; a manually
  normalized equivalent path can fail prelaunch binding before any Worker.
- A successful Preflight does not imply Worker readiness. Preserve the first
  pre-ready Worker exit as terminal `BLOCKED_DETACHED_WORKER_DIED` evidence and
  never retry smoke or acceptance in that qualification namespace.

# 2026-08-12 - 005U worker reservation state contract

- `worker_started` is a reservation checkpoint: generation, tokens and lease are bound, but the child PID may still be zero. Require a positive PID only from `supervisor_ready` onward, and never emit readiness markers before PID persistence.
- Keep the historical 005S multi-generation recovery PID-zero debt separate; do not expand a one-generation 005U repair or reuse that recovery path for 005V.

# 2026-08-12 - 005U fault-injection review correction

- A passing state/schema suite is not sufficient evidence for a launch-order fix. Every newly added process guard must have TestDrive fault injection for throw, null/PID-zero, persistence/CAS failure, token cleanup, marker suppression, and the structured blocked snapshot before the final reviewer may approve the remediation.

# 2026-08-13 - Marker evidence must exercise production ownership

- A failure assertion against an arbitrary file that production never writes is
  vacuous. Marker-suppression tests must use the exact production leaf names and
  the same production-used seam, plus a positive control that proves the seam
  can create every marker with its expected content and order.
- Static transaction review is not production integration proof. Keep the
  Supervisor and Worker entrypoints wired to dependency-injected seams that the
  TestDrive fault matrix invokes directly; do not maintain a second inline
  readiness path.

# 2026-08-13 - Browser-backed legacy baseline must fail closed at the host boundary

- A Chrome contact-sheet crash (`STATUS_BREAKPOINT`) is neither a Python contract
  pass nor evidence to relax browser sandbox flags. Preserve the existing
  `--no-sandbox` prohibition and classify the run as an environment baseline
  blocker until a clean, approved host execution proves the same legacy suite.
- Redirecting `TEMP`/`TMP` can remove one filesystem-denial hypothesis, but it
  does not justify treating a persistent browser crash as a product-code defect
  or continuing a one-shot Provider qualification.

# 2026-08-13 - 005W legacy Chrome host baseline

- A clean, attributable external host run is valid evidence only when current
  source/test hashes, Chrome binary hash, isolated profile/temp root, and exact
  one-shot counts are recorded together.
- The contact-sheet target test may clean its PNG through TemporaryDirectory;
  report the test internal PNG/1360x780 assertions and explicitly say when no
  PNG is retained. Never invent an artifact hash.
- Passing the legacy host baseline only reopens a fresh 005V local
  source-freeze/prelaunch review. It does not authorize Provider, Worker,
  smoke, acceptance, MP4, 006, Feishu, Cron, or formal phase promotion.
- Keep 005T immutable hashes and 005V BASELINE_BLOCKED zero counters in every
  host-baseline Change Request so a later reviewer can prove the boundary
  without inspecting raw logs.

# 2026-08-14 - 005V3 Preflight observability

- A generic sanitized `unexpected_error` is safe against leakage but is not an
  auditable diagnostic. Preflight failures must carry only fixed gate,
  substep, reason, and optional exit-code enums; the original exception and
  command context must never enter the envelope.
- A consumed one-shot bridge remains terminal evidence. A diagnostic profile
  needs a new task ID, external namespace, counter, and authorization gate;
  it must not revive or reinterpret the prior bridge.
- Local observability remediation ends before Preflight execution. A passing
  TestDrive/Python suite does not authorize cache/config/auth reads, Desktop
  interaction, Worker start, smoke, acceptance, MP4 generation, or 006.
## 2026-08-13 - 005V local gate re-entry

- A prose Change Request prohibition is not a runtime gate. Operational modes
  must load the canonical CR and fail closed on its execution status.
- Historical evidence must bind to an exact run ID, not merely a session-shaped
  string; source freeze must include every runtime byte that can affect output.
- A recursive cleanup is not safe merely because its parent was checked:
  validate containment and reparse state at every node during deletion.

## 2026-08-14 - 005V2 one-shot Preflight observability

- A one-shot read-only Preflight must emit a stable, auditable sub-gate reason;
  converting every unexpected exception to `unexpected_error` is safe for
  secrecy but insufficient for diagnosis. Record the command as consumed,
  preserve the sanitized envelope, and require a new authorization for any
  diagnostic or retry plan.
- A failed Preflight that creates no external run root, active lock, job, marker,
  Worker, smoke, acceptance or MP4 is a terminal preflight blocker, not evidence
  that the Provider is healthy and not permission to advance to 006.

# 2026-08-14 - Product delivery order must not inherit internal historical labels

- Do not let historical P0/P1/P2 implementation labels redefine the user-facing
  product sequence. Before planning work, write the direct user input, required
  output, excluded integrations, and phase boundary in the canonical phase map.
- A local reference-video theme-analysis path is not advanced reference-video
  recreation. Keep the former conservative and original in Phase 1; treat any
  near-copy of pacing, shot order, visual packaging, or identifiable expression
  as a Phase 4 authorization and originality-review question.
- “AI TTS” and “GPU acceleration” are capability descriptions, not permission
  to invoke remote Providers or download models. State the local baseline and
  require a separate approved scope for external services or optional hardware
  integrations.

# 2026-08-15 - Execute the current product phase, not the longest historical blocker

- After a product-phase realignment, re-read the canonical phase map before
  continuing a historical Provider-remediation chain. A terminal Provider
  diagnostic can remain preserved while independent local-video work advances.
- The first useful Phase 1 proof is a real, locally narrated MP4 plus a human
  review package and idempotent local job record. Passing that slice is progress,
  not permission to mark the whole phase ready or enter Feishu/Cron.

# 2026-08-22 - Human review must inspect copy before audiovisual readiness

- A locally valid MP4 with a passed quality package can still fail the real
  review when the planner emits generic narration or duplicate punctuation.
- For a fixed topic, bind the five beats to the verified factual claims and
  assert the rendered `script.json`/`subtitle.srt` content before discussing a
  different voice provider.
- Preserve accepted Registry visuals, create a new candidate Job after a copy
  correction, and keep Jianying/remote AI-TTS behind a separate authorization;
  local SAPI proves the pipeline but does not prove voice suitability.

# 2026-08-22 - Jianying drafts need duration and export gates

- The Jianying Skill can create a valid v11.3-compatible draft with native SAMI
  narration even when automatic export is not safe for the installed version.
- Always compare visual duration with the complete voice timeline before handing
  over a draft; fail closed or add an explicit tail-frame pad instead of letting
  narration run past the picture.
- Keep the deterministic MP4 primary, create a new draft name, and require Jovi
  to listen and export manually; never use UI automation as hidden proof.

# 2026-08-22 - Validate visual semantics before editing in Jianying

- A valid Jianying draft can still be semantically wrong when the upstream
  Registry binds a topic's narration to another topic's reusable cards.
- Inspect the rendered asset manifest and at least one contact sheet before
  blaming the editor; add topic-specific selection tags and a negative test
  that rejects cross-topic assets.
- Regenerate a new draft from the corrected visual input. Preserve old drafts
  for audit, keep export manual, and report the mismatch as a pipeline asset
  selection defect rather than an editor defect.

# 2026-08-22 - Personal IP must be explicit, original, and optional

- Never infer that a style/prompt repository or a project-created PNG/SVG is
  Jovi's Pink Pig personal IP. The original asset pack and a verifiable receipt
  are required before any mascot composition is allowed.
- Pink Pig is opt-in per video. The safe default is no mascot; a missing or
  unverifiable original-asset adapter must fail closed rather than invent a
  substitute.
- The editor was not the root cause of the latest mismatch. Validate the
  upstream brief and selected visual semantics first, then send the corrected
  visual input to the fixed `jianying-editor-skill` backend. Keep export and
  publication manual.

# 2026-08-23 - Theme, canvas, and subtitle authority belong to the chain

- Do not use Pink Pig pink as a global technical-video background. Resolve a
  theme palette from the topic/style tokens; Pink Pig remains explicit and
  user-original-only.
- Default to 1920×1080 when the Registry assets and reference examples are
  landscape. Preserve portrait only as an explicit brief choice.
- A Jianying draft must receive a visual-only input. If the input already has
  burned-in subtitles, adding Jianying's native Subtitles track creates a
  misleading duplicate; enforce one subtitle authority in the draft.
- Verify both media-level audio and draft-level VoiceOver state. A non-silent
  AAC stream plus `mute:false` is an automated gate, not proof that Jovi has
  heard the voice; manual listening remains required.
- Keep new runtime, draft, and report roots on E: and fail closed on C:. Use
  one editor backend per job and document external candidates without enabling
  them beside Jianying.

# 2026-08-23 - Public reference URLs require verification before clean-room reconstruction

- A reference URL is not evidence that the video was actually inspected. Open the real page, resolve the media, record its hash/ffprobe/audio observations, and preserve the source outside the repository before making any claim about its structure.
- “先复刻” must be interpreted as reconstructing the information logic and visual grammar when ownership is not established; never copy the source audio, full transcript, frames, logo, creator identity, or recognizable shot expression into an original brief or render chain.
- If the approved offline ASR snapshot is absent, mark semantic audio transcription unavailable and report codec/level/timing observations only; do not invent a transcript.
- HyperFrames and other external candidates may inform layout or motion tokens, but the project keeps one deterministic renderer and one Jianying editor backend per job. HeyGen remains separately authorized work, not a default Phase 1 call.

# 2026-08-23 - Voice-first timing prevents Remotion/Jianying drift

- Equal-duration visual beats are unsafe when local TTS durations vary. Measure
  the exact voice assets first and persist one timing manifest with microsecond
  starts/ends and hashes.
- Remotion scene boundaries, Jianying VoiceOver clips, and native subtitles must
  consume that same manifest; regenerate a new draft when the manifest changes.
- A healthy AAC stream or an unmuted Jianying track is only an automated gate.
  Manual listening is still required, and the project must remain fail-closed on
  timing mismatch beyond one video frame.
# 2026-08-23 - Post-render layout gate is mandatory

- A technically valid MP4 can still be unusable when a title, axis label, or caption crosses the canvas edge. Every video job must run a post-render gate that checks canvas, safe-area boxes, representative frames, black/frozen samples, audio presence, and complete decode before handing the visual to Jianying.
- Theme colors must come from topic/style tokens. Pink Pig branding is opt-in and must never become the default technical-video background.
- Keep one subtitle authority: Remotion visual output is subtitle-free when Jianying native subtitles are enabled.
- A voice-first manifest can still leave a long silent tail when the visual target is longer than the narration. Measure total voice coverage before finalizing; either extend the original narration or shorten the visual, then regenerate the draft and preview.
- Frame inspection must check semantic placement as well as overflow. In the RC Bode chart, the phase labels were inside the canvas but initially mapped to the wrong vertical positions; the v5 render corrected the chart before Jianying packaging.
