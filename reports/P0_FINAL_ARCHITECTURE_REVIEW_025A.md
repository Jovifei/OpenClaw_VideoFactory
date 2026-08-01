# P0 Feishu Gateway Final Architecture Review 025-A

## Final result

`ARCHITECTURE_BLOCKED`

The 024 remediation materially improves the static Channel-layer boundary, but the Project Feishu Gateway does not yet meet the production-migration architecture standard. No consumer cutover is authorized.

The blockers are:

1. A card event creates an analysis request without the required two-message `reply_to_message_id` evidence.
2. The single-consumer lease and verifier are local snapshot utilities, not an atomic runtime fence proving old-Binding shutdown before Project startup.
3. No end-to-end adapter carries the validated Gateway envelope to the audited RPC client with durable idempotency and correlation.

## Audit conditions and evidence

This was a read-only audit. No code or configuration was modified; no Secret was read; no Feishu or live RPC connection, Gateway lifecycle command, commit, or push was used. `PROJECT_STATUS.yaml` remains `P0 / not_started`.

The following offline commands were executed with `PYTHONDONTWRITEBYTECODE=1`:

| Command | Result |
| --- | ---: |
| `python -m unittest discover -s tests -p 'test*feishu*gateway*.py' -v` | 37 passed |
| `python -m unittest discover -s tests -p 'test_openclaw_rpc_client.py' -v` | 9 passed |
| `python -m unittest discover -s tests -p 'test_migration_preflight_scripts.py' -v` | 3 passed |
| `python -m unittest discover -s tests -p 'test_analysis_request.py' -v` | 8 passed |
| `python -m unittest discover -s tests -p 'test_ingest_attachment_core.py' -v` | 45 passed |

Total: **102 offline tests passed**. This proves local contracts and test fixtures, not real Feishu signature verification, Project-RPC authentication, old-Binding shutdown, a live WebSocket count, state restoration, or rollback.

## Decision matrix

| Area | Result | Evidence |
| --- | --- | --- |
| Gateway has no model/Analyzer/GPU/Agent-management code | Pass, static | `policy.py` denies these capabilities; Gateway source no longer imports or calls Analyzer/compute code. |
| RPC privilege escalation | Pass, static | Policy rejects direct model/Analyzer/GPU/tool fields; Agent identity is fixed to `video-factory`. No critical escalation was found. |
| Session isolation | Pass, static | Derived key contains hashed tenant, chat, sender and thread; isolation tests pass. |
| Replay/concurrency | Fail | State and lease writes are not atomic/fenced; retried agent calls lack end-to-end idempotency. |
| Single consumer | Fail | Verifier accepts a supplied snapshot and does not inspect live sockets; the lease is not wired into runtime startup. |
| Migration/rollback | Fail | Checks validate manifests/simulations only; no loss boundary, restore proof, or recovery objective exists. |
| Secret boundary | Partial | Environment/token-provider and ignored runtime paths are good; report redaction and Git-history proof are not enforceable here. |
| Long-term product architecture | Partial | Compute remains outside Gateway, but multi-channel normalization and durable job/GPU orchestration are absent. |

## Controls to retain

- `GATEWAY_CAPABILITIES` permits ingress/identity/request/reply and denies model, Analyzer, GPU, arbitrary filesystem, config modification and Agent creation ([policy.py](../services/feishu_gateway/policy.py:7)).
- Gateway RPC payloads require fixed `video-factory` identity and reject direct model/Analyzer/GPU/tool fields ([policy.py](../services/feishu_gateway/policy.py:20)).
- Schemas require signatures; missing verifier or signature fails closed ([service.py](../services/feishu_gateway/service.py:77)).
- Session identity includes tenant/chat/sender/thread without raw identifiers in the key ([session.py](../services/feishu_gateway/session.py:13)).
- Tickets bind tenant/chat/sender/thread/action, expire after 120 seconds, and are single use after a non-retryable outcome ([service.py](../services/feishu_gateway/service.py:145)).
- The RPC client fixes Agent identity to `video-factory`, uses `deliver=false`, and refuses an invented attachment RPC method ([client.py](../services/feishu_gateway/openclaw_rpc/client.py:124)).

## Findings

### Critical

No critical privilege-escalation issue was found by static review. The reviewed Gateway code does not call a model, Analyzer, GPU, or Agent-management API; the policy does not permit arbitrary model, Analyzer, GPU, tool, or Agent selection.

### High

#### HIGH-025A-01 — Card path bypasses the durable two-message analysis-intent protocol

The durable request creator requires `request_message_id`, target attachment id, `reply_to_message_id`, attachment index, chat, requester and request text ([analysis_request.py](../scripts/analysis_request.py:201)). In contrast, the card schema has no reply target or request-message identity, and `ProjectFeishuGateway.card()` builds a bounded request from a card, receipt and ticket hash ([card_event.schema.json](../schemas/feishu_gateway/card_event.schema.json), [service.py](../services/feishu_gateway/service.py:159), [runtime.py](../services/feishu_gateway/runtime.py:105)).

Impact: a card action becomes a parallel intent protocol. It cannot prove the real reply relationship or run the same textual intent, requester-message, expiry and target validation as the durable `analysis_request.json` flow.

Required: analysis must originate only from a signed later text event with actual `reply_to_message_id`; OpenClaw must create the sole durable request and reject other association mechanisms.

#### HIGH-025A-02 — Single-consumer verifier and lease cannot prove an exclusive real cutover

`verify_single_consumer.py` explicitly consumes a caller-supplied snapshot and never inspects live sockets ([verify_single_consumer.py](../scripts/migration/verify_single_consumer.py:1)). Its lease is a read followed by an in-place JSON write without exclusive creation, inter-process lock, atomic replace, generation/fencing token, or stop authority ([verify_single_consumer.py](../scripts/migration/verify_single_consumer.py:13)). The launcher starts only the offline health runtime and does not acquire or heartbeat the lease ([start_gateway.ps1](../scripts/feishu_gateway/start_gateway.ps1:1)).

Impact: the sequence “old Binding stopped -> Gateway started -> one consumer” is not proven. Two processes can race; a paused old consumer has no fence preventing it resuming after stale takeover.

Required: integrate an operator-authorized atomic/fenced ownership control into old-Binding shutdown and Project startup, then independently observe the real authenticated long-connection owner and event/reply stream.

#### HIGH-025A-03 — No implemented idempotent adapter connects validated Gateway envelopes to the RPC client

The Channel layer invokes injected `rpc(payload)` with its complete validated envelope ([service.py](../services/feishu_gateway/service.py:109)). `OpenClawGatewayClient` instead exposes `send_message(message, session_key)` and serializes only message, fixed Agent id, session key, delivery flag and timeout ([client.py](../services/feishu_gateway/openclaw_rpc/client.py:127)). No adapter maps the text/card envelope, `analysis_request`, message/event id, or ticket correlation to this client.

The client retries the `agent` method after timeout/transport error and gives each attempt a new UUID ([client.py](../services/feishu_gateway/openclaw_rpc/client.py:152)). No stable end-to-end idempotency key reaches OpenClaw.

Impact: the shown client cannot safely carry card analysis context, and an accepted-but-unanswered Agent request can be sent again.

Required: implement one narrow policy-validated adapter that preserves correlation/idempotency. Retry only operations OpenClaw can prove idempotent; record ambiguous delivery for reconciliation.

#### HIGH-025A-04 — Migration, restoration and rollback remain simulations

Preflight and rollback utilities validate operator-supplied JSON/manifests and never query or control OpenClaw ([preflight_check.py](../scripts/migration/preflight_check.py:1), [rollback_verify.py](../scripts/migration/rollback_verify.py:1)). The rollback PowerShell script is simulation-only and cutover experiments toggle local booleans ([rollback_gateway.ps1](../scripts/migration/rollback_gateway.ps1:1), [simulate_cutover.py](../experiments/feishu_gateway_migration/simulate_cutover.py:1)). `GatewayState.save()` is an in-place JSON write without transaction, journal, atomic replacement, retention, or restore validation ([service.py](../services/feishu_gateway/service.py:33)).

Impact: no evidence establishes a message-loss boundary, duplicate reconciliation, state restoration correctness, or rollback RTO/RPO.

Required: add event boundary/drain, transactional state/outbox, hash-verified restore, replay reconciliation, and a measured controlled-channel cutover/rollback rehearsal.

### Medium

#### MEDIUM-025A-05 — General reports and Git history lack enforceable redaction proof

Runtime/token paths are correctly ignored and token providers are injected. Generic `reports/*.md` and `reports/*.json` remain trackable, however, and no redaction gate was found. The current branch has no commits, so historical Git cleanliness cannot be proven.

Required: enforce report/diagnostic redaction before staging and retain only masked correlation identifiers.

#### MEDIUM-025A-06 — Lifecycle health does not attest process identity or consumer owner

The launcher/status pair trust a PID/status file and report basic process health only ([start_gateway.ps1](../scripts/feishu_gateway/start_gateway.ps1:9), [status_gateway.ps1](../scripts/feishu_gateway/status_gateway.ps1:1)). They do not validate process command identity, lease/fence, connection owner, event age, or queue state.

Required: bind readiness and lifecycle actions to process identity plus the fenced consumer owner and safe operational metrics.

#### MEDIUM-025A-07 — Multi-channel/product extension requires a normalized durable work layer

The schemas/session key are Feishu-specific and action routing is a fixed PNG/WAV/MP4 map. This correctly keeps 4070S, video production, automatic topic selection and Analyzer execution outside Gateway, but it supplies no normalized channel/account adapter, durable job queue, GPU scheduler, or extensible Analyzer registry.

Required: keep Gateway compute-free; add normalized channel/account envelopes and durable OpenClaw-owned topic/video/GPU/Analyzer work only in later authorized phases.

### Low

#### LOW-025A-08 — RPC session-creation documentation conflicts with implementation

The RPC report lists session creation as passed, but `create_session()` returns `rpc_method_not_allowed` ([P0_RPC_VERIFICATION_023.md](P0_RPC_VERIFICATION_023.md), [client.py](../services/feishu_gateway/openclaw_rpc/client.py:124)). Operators need an explicit statement that fixed-Agent message delivery creates/uses a session implicitly, if that is the intended contract.

#### LOW-025A-09 — Offline fixture acknowledges an event before downstream completion

`OfflineFeishuGateway.process()` records an event id before message/card processing ([gateway.py](../services/feishu_gateway/gateway.py:37)). If reused as a live adapter, a transient failure could be reported as duplicate on redelivery. The production `ProjectFeishuGateway` does not use this ordering, so this is fixture hygiene rather than a migration blocker.

## Gate to `ARCHITECTURE_READY_FOR_RUNTIME`

All high findings must be resolved, then an explicitly authorized controlled rehearsal must prove, in order:

1. local token-provider injection with loopback `connect`/`health` only;
2. real verifier construction without Feishu traffic;
3. fenced exclusive consumer ownership with independently observed owner;
4. reply-bound analysis admission plus durable idempotency/recovery;
5. reversible, measured test-channel cutover and rollback.

This review grants no authority to read credentials, connect Feishu, create a session, invoke an Agent, change a Binding, or start/restart the Gateway.
