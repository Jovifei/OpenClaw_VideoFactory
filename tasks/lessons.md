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
