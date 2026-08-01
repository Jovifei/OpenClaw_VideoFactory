# P0 Feishu Gateway Architecture Audit 023-A

## Result

`ARCHITECTURE_CONCERNS_FOUND`

This was a read-only, offline architecture audit of the current workspace. No
Gateway was started or restarted; no Feishu, RPC endpoint, credential, secret,
or external service was contacted. The project remains `P0 / not_started`.

**Decision:** the current implementation is **not ready for a production
single-consumer cutover**. Its offline safety primitives are useful, but the
final product boundary must be corrected before any maintenance-window trial.

## Scope and evidence

- Reviewed the four requested implementation/runbook reports; all explicitly
  describe offline-only implementation and an unverified production RPC.
- Reviewed `services/feishu_gateway/`, `schemas/feishu_gateway/`, the relevant
  migration/runtime scripts, and the Feishu/Analyzer tests.
- Executed only offline tests with `PYTHONDONTWRITEBYTECODE=1`:

  - `python -m unittest discover -s tests -p 'test*feishu*gateway*.py' -v` — 37 passed.
  - `python -m unittest discover -s tests -p 'test_analysis_request.py' -v` — 8 passed.
  - `python -m unittest discover -s tests -p 'test_analyzer_mcp.py' -v` — 32 passed.
  - `python -m unittest discover -s tests -p 'test_ingest_attachment_core.py' -v` — 45 passed.

  Total: **122 offline tests passed**. They do not prove a Feishu WebSocket,
  official OpenClaw RPC, real consumer ownership, or a maintenance cutover.

## Architecture assessment

| Area | Assessment | Evidence |
|---|---|---|
| Gateway as ingress layer | Partial | Text is shaped for RPC and media is passed to `ingest`; however, attachment cards subsequently invoke `analyze` in Gateway. |
| OpenClaw as orchestration layer | Fail | The card path bypasses the text/router RPC path and directly invokes the Analyzer after a local `request` callback. |
| Analyzer as compute-only layer | Partial | Analyzer argument surface is restricted and quarantine/hash tests pass; dispatch authority is nevertheless held by Gateway. |
| Gateway model use | Pass (offline code) | No model client is present in the Gateway runtime. |
| Single Feishu consumer | Fail / unproven | Runtime is explicitly offline-only; supplied migration checks consume fake snapshots and state that they never inspect sockets/processes. |
| RPC transport design | Fail for production | Injection is a sound temporary boundary, but the unverified method names/fields are embedded in the client and no official transport contract is proven. |
| Ingress, ticket, SHA and replay controls | Partial | Quarantine, stored-hash verification, one-time tickets and local dedupe have focused tests; signature enforcement and durable concurrency are inadequate. |
| Cutover/runbook | Partial | Sequence and rollback intent are documented, but there is no atomic ownership switch, cursor/state handoff, live verifier, or bounded recovery proof. |
| Long-term extension | Not ready | Current direct Analyzer dispatch and Feishu/group-only identity cannot safely carry GPU scheduling, multiple accounts, or multiple channels. |

## Findings

### Critical

#### CRITICAL-023A-01 — Gateway bypasses OpenClaw and directly dispatches Analyzer

`ProjectFeishuGateway.message()` creates an analysis card for a quarantined
attachment, and `card()` marks the ticket used, locally creates a partial
request payload, then invokes `self.analyze(...)` directly
([service.py](../services/feishu_gateway/service.py:153),
[service.py](../services/feishu_gateway/service.py:171)). The offline PoC test
expressly asserts that cards bypass the router and call Analyzer
([test_feishu_gateway_poc.py](../tests/test_feishu_gateway_poc.py:37)).

This contradicts the durable two-message protocol: an attachment is
ingress-only; a later reply with real `reply_to_message_id` must cause
OpenClaw to create the pending `analysis_request`; only then may the matching
Analyzer execute. That contract is independently tested in
[test_analysis_request.py](../tests/test_analysis_request.py:80). The current
Gateway card request lacks the request message id, reply target, attachment
index, and requester fields required by that flow.

**Impact:** Gateway owns user intent and Analyzer dispatch, bypassing the
intelligent orchestration layer and permitting an architecture-inconsistent
analysis path. It also prevents OpenClaw from centrally applying queueing,
cancellation, recovery, policy and GPU scheduling.

**Required disposition:** remove direct Analyzer dispatch and automatic
analysis-card authority from the production path. Forward only normalized,
signature-verified ingress metadata to OpenClaw; make OpenClaw create and
dispatch a valid `analysis_request` from real reply metadata.

#### CRITICAL-023A-02 — Production event signature validation fails open by default

The schemas make `signature` optional, and
`_require_valid_signature()` returns `True` when no verifier is injected
([message_event.schema.json](../schemas/feishu_gateway/message_event.schema.json),
[service.py](../services/feishu_gateway/service.py:80),
[service.py](../services/feishu_gateway/service.py:111)). The passing signature
test only constructs a Gateway with an injected verifier; it does not prove
the default production construction rejects unsigned events.

**Impact:** wiring a real WebSocket/event adapter without an explicit
fail-closed construction guard would let forged or replayed event objects reach
RPC, ingestion, ticket issuance, or direct analysis.

**Required disposition:** make verified official-Lark signature/timestamp
validation mandatory for every production event type before schema processing;
reject missing verification configuration at startup and test the default
factory, not only an injected test double.

### High

#### HIGH-023A-03 — Group-only session mapping can mix users' conversations

The payload builder and example configuration both use
`feishu:group:{chat_id}` ([runtime.py](../services/feishu_gateway/runtime.py:74),
[feishu_gateway.example.yaml](../config/feishu_gateway.example.yaml)).
`sender_id` is forwarded but is not part of `session_key`; the test asserts this
exact mapping ([test_feishu_gateway_runtime.py](../tests/test_feishu_gateway_runtime.py:25)).

**Impact:** in a group, all users share one OpenClaw session/memory unless the
unknown RPC implementation overrides it. This creates a user-to-user context
and privacy leak risk.

**Required disposition:** define a versioned session policy before RPC
integration. Default to an account/channel/chat/sender namespace for private
state, and require an explicit, tested opt-in for a deliberately shared group
session.

#### HIGH-023A-04 — “One consumer at any time” is simulated, not enforced or observed

The only runtime server accepts `--mode offline` and contains no Feishu
WebSocket/event consumer ([runtime_server.py](../services/feishu_gateway/runtime_server.py:55)).
The migration verifiers explicitly accept supplied snapshots and never inspect
sockets or processes ([verify_consumer_state.py](../scripts/migration/verify_consumer_state.py:1),
[verify_single_consumer.py](../scripts/migration/verify_single_consumer.py:1)).
The cutover/rollback experiments only toggle local booleans.

**Impact:** two live consumers can overlap during migration, or neither can
consume during a gap, while the current evidence format can still say `pass`.
There is also no lease/fencing token, consumer-owner registry, or live
connection identity assertion.

**Required disposition:** create an operator-owned, transport-specific
cutover gate: prove old Binding disconnected, acquire a fenced project-consumer
lease, verify exactly one authenticated long connection with its owner id, and
fail closed on stale/ambiguous observations. Test overlap, gap, reconnect and
rollback against a controlled non-production channel only after authorization.

#### HIGH-023A-05 — RPC “placeholder” embeds an unverified protocol and cannot yet safely absorb the real one

Although the transport is injectable, the contract hard-codes `agent`, a
specific request shape and success status ([runtime.py](../services/feishu_gateway/runtime.py:19)).
The client also calls unverified `health`, `create_session`, and
`attachment_event` methods ([rpc_client.py](../services/feishu_gateway/rpc_client.py:14)).
No official protocol version, authentication handshake, cancellation,
streaming/result correlation, idempotency key, or capability negotiation is
defined.

**Impact:** the future real transport may accept a different semantic model;
the resulting adapter could silently route messages incorrectly or make the
Gateway become a second orchestrator.

**Required disposition:** retain dependency injection but replace the current
method strings with a versioned, officially verified adapter interface. The
adapter must own capability negotiation and map only documented OpenClaw RPC
calls; the domain boundary should expose one normalized `deliver_inbound`
operation with correlation/idempotency semantics.

#### HIGH-023A-06 — Retries and durable state can duplicate work under timeout/concurrency

`OpenClawRpcClient` retries timeout/transport/network outcomes
([rpc_client.py](../services/feishu_gateway/rpc_client.py:29)) without an RPC
idempotency key. `GatewayState.save()` writes the JSON state in place with no
lock, atomic replace, version, TTL, or process fence
([service.py](../services/feishu_gateway/service.py:30)). A timeout deliberately
leaves the event unseen for redelivery
([service.py](../services/feishu_gateway/service.py:123)), which is appropriate
only when the downstream delivery itself is idempotent.

**Impact:** a completed-but-lost response, two processes, or a state-file
crash can execute an Agent/Analyzer twice, lose ticket state, or produce
inconsistent dedupe decisions.

**Required disposition:** use one durable transactional event/outbox store,
an end-to-end idempotency/correlation key, atomic state transitions, bounded
retention, and a documented retry classification/backoff policy. Do not retry
non-idempotent Agent work merely because a response was lost.

#### HIGH-023A-07 — Maintenance procedure does not close message-loss, state-restoration, or rollback-time gaps

The runbook has the correct high-level order (stop old, start project, verify,
smoke, rollback), but it has no inbound cursor/checkpoint, drain/quiesce
protocol, ownership handoff record, accepted duplicate policy, state export /
restore verification, rollback RTO, or replay reconciliation. It also says the
022 launcher is offline-only, so its steps cannot presently enact the
production switch.

**Impact:** the stated sequence cannot prove that no event was missed or
double-processed during the switch, nor that sessions/pending media recover
within an agreed window.

**Required disposition:** make the maintenance runbook executable only after
the above single-consumer control exists. Include event boundary ids and
timestamps, quiescence/drain checks, state backup/restore hash verification,
idempotent replay reconciliation, explicit rollback owner/command, and
measured RTO/RPO acceptance criteria.

### Medium

#### MEDIUM-023A-08 — Secret/log/report boundary is only partially enforced

Positive controls exist: secrets are read from environment only
([runtime.py](../services/feishu_gateway/runtime.py:10)); runtime JSON logs hash
event/chat/sender identifiers ([runtime_server.py](../services/feishu_gateway/runtime_server.py:21));
and `.gitignore` excludes environment files, local config and `runtime/`.
However, generic `reports/*.md` and `reports/*.json` are intentionally
trackable, and there is no report redaction check or test. The repository's
current branch has no commits, so historical Git cleanliness also cannot be
proven by this audit.

**Impact:** a future operator can place ticket, path, chat, RPC error or
credential-bearing diagnostics in a report that is then staged.

**Required disposition:** introduce a CI/pre-commit redaction scan for reports
and diagnostics, test it with representative secret/identifier patterns, and
require only masked correlation ids in runbook evidence.

#### MEDIUM-023A-09 — Error mapping and readiness observability are incomplete and inconsistent

`RpcBridge` retries only timeouts while `OpenClawRpcClient` also retries
transport/network errors; neither uses backoff or jitter. Error mapping omits
rate-limit, overload, conflict/duplicate, cancellation, server failure and
protocol-version classes ([runtime.py](../services/feishu_gateway/runtime.py:38)).
The health server reports process state but not consumer owner, sequence
progress, queue depth, stale-event age, or fenced lease status.

**Impact:** operators cannot distinguish safe retry, permanent rejection,
ambiguous delivery, or consumer split-brain during a cutover.

**Required disposition:** consolidate one RPC policy and add typed error
classes, bounded exponential backoff, correlation ids, consumer identity,
event-lag and handoff metrics to the readiness contract.

#### MEDIUM-023A-10 — Direct synchronous Analyzer call does not support GPU/resource orchestration

The card handler calls `analyze` synchronously after consuming the ticket
([service.py](../services/feishu_gateway/service.py:171)). The Analyzer tests
show CUDA/audio and video work are part of the compute surface
([test_analyzer_mcp.py](../tests/test_analyzer_mcp.py:137)). No job queue,
GPU-lock ownership, cancellation propagation, queue capacity, or per-task
resource policy exists at the Gateway/OpenClaw boundary.

**Impact:** a 4070S workload can block event handling and cannot be centrally
serialized, retried, cancelled, or recovered.

**Required disposition:** OpenClaw must enqueue the analysis job and own its
lifecycle; Analyzer workers must obtain the shared GPU lock and report status
through the job record, never through a synchronous Gateway callback.

#### MEDIUM-023A-11 — Multi-account and multi-channel identities are not modeled

All public schemas and RPC payloads are Feishu-specific and have no account /
tenant, channel, application, or adapter-version namespace. The group-only
session key is therefore also insufficient for account isolation.

**Impact:** adding a second Feishu app/account or a non-Feishu channel risks
identity collisions, incompatible signatures, and hidden routing branches.

**Required disposition:** define a normalized envelope with
`channel`, `account_id`, `tenant_id` where applicable, stable external ids,
adapter version, and per-account credential/consumer ownership. Keep
Douyin publishing as an OpenClaw-managed egress capability rather than a
Gateway concern.

### Low

#### LOW-023A-12 — Ticket and dedupe retention are unbounded

Tickets and seen event hashes are retained indefinitely in the JSON state;
expired tickets are rejected but never pruned. This does not bypass the
one-time/two-minute ticket controls, but it creates long-running state growth
and larger recovery files.

**Required disposition:** add retention/compaction with an audit-safe expiry
record and test recovery across compaction.

#### LOW-023A-13 — Launcher lifecycle identity is weak

The launcher trusts a PID/status file and the stop script can force-stop that
PID after a timeout ([start_gateway.ps1](../scripts/feishu_gateway/start_gateway.ps1:9),
[stop_gateway.ps1](../scripts/feishu_gateway/stop_gateway.ps1:6)). It does not
verify the process command line, runtime fingerprint, or consumer lease.

**Required disposition:** bind lifecycle actions to a process identity and
fenced consumer lease; never infer ownership from a reusable PID alone.

## Controls that should be retained

- Offline-only launcher and `/ready=false` without verified transports.
- Environment-reference configuration and ignored runtime/credential paths.
- SHA-256/quarantine checks and Analyzer rejection of raw inbound paths.
- Hashed identifier logging, one-time 120-second tickets, type/action binding,
  and local duplicate-event tests.
- The separate `analysis_request` test contract: reply target, requester/chat
  match, expiry, stored-hash match, and pending/completed idempotency.

## Required architecture target before a future cutover

```text
Feishu adapter (signature verify, one fenced consumer, normalize ingress)
    -> OpenClaw (session policy, reply-to intent, analysis_request, job/outbox,
                  retries/cancel/recovery, outbound delivery)
        -> Analyzer workers (quarantined copy only, per-job state, GPU lock)
```

The Gateway may validate/normalize ingress and send a normalized envelope to
OpenClaw. It must not decide user analysis intent, invoke models, directly call
Analyzers, own long-running job state, or substitute for the OpenClaw task
orchestrator.

## Acceptance blockers for `ARCHITECTURE_PASS`

1. Direct Analyzer/card dispatch is removed from the production route and a
   real-reply `analysis_request` flow is proven end-to-end in a non-production
   environment.
2. Official Feishu signature/timestamp verification is mandatory and tested
   as the default production factory.
3. An approved official OpenClaw RPC contract is captured; the adapter is
   versioned, correlated, idempotent and transport-replaceable.
4. A documented session policy prevents cross-user/session leakage and has
   group/DM/multi-account tests.
5. A fenced, observable single-consumer cutover with drain, replay and
   rollback/RTO evidence is successfully rehearsed under separate authority.
6. Durable transactional event/job state, typed retry policy, GPU job
   serialization, and report-redaction controls are verified.

## Audit limitations

This report intentionally makes no claim about live Feishu behavior, official
Lark SDK availability, OpenClaw RPC compatibility, credential handling in a
real process, or production migration success. Those require a separately
approved maintenance-window integration and controlled smoke evidence.
