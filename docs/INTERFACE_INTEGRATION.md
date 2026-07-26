# DataLogicEngine interface and client-integration specification

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ENG-003 |
| Title | Interface and client-integration specification |
| Document version | v1.1.0 |
| Product version | 4.3.0 |
| Status | active |
| Audience | API/client engineers, application integrators, security, quality, operators, and professional reviewers |
| Owner | API Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Registered routes, OpenAPI/schema contracts, gateway/MCP implementation, ADRs, and contract tests |
| Confidentiality | Public |
| Last reviewed | 2026-07-25 |
| Next-review trigger | Route, schema, auth, version, streaming, SDK, gateway profile, MCP, or compatibility change |
| Requirements and evidence | Product requirements, generated contracts, route inventory, SDK tests, and Phase 5/8/11 evidence |

## Interface boundary

The versioned DataLogicEngine API Gateway is the primary integration surface for
approved applications, agents, and chatbots. Built-in chat is a reference client
of the same backend-owned governed path. The renderer, SDKs, and clients do not
call model providers or internal data services directly.

The default listener is loopback-only. Same-host clients are supported at the
engineering checkpoint. `private_windows_gateway` remains disabled until the
signed two-machine TLS/firewall qualification passes. Browser/CORS and public-
internet exposure are outside the 4.3.0 contract.

## Version and route policy

- Canonical application endpoints use `/api/v1/*`.
- `/live`, `/ready`, and safe health surfaces have explicit operational contracts.
- Compatibility aliases may remain only when inventoried, tested, non-conflicting,
  and assigned a deprecation/removal policy.
- A breaking request/response, auth, ownership, error, streaming, lifecycle, or
  side-effect change requires a major interface version or an explicitly approved
  compatibility transition.
- Additive optional fields and new endpoints may remain within the current major
  version when old clients preserve defined behavior.
- Responses and trace/export records identify product/interface/schema versions
  where the contract requires them.

Generated OpenAPI and schemas are machine authorities where present; prose
explains boundaries and acceptance but must not contradict generated contracts.

## Authentication and authorization

| Context | Credential/control | Boundary |
|---|---|---|
| Electron desktop | Installation secret, nonce/HMAC, timestamp skew, loopback/Electron policy, Windows owner context | Local desktop only; no renderer secret exposure |
| Owner web session | Flask session, CSRF, trusted host/CORS, authenticated owner checks | Single-owner administrative/user routes |
| Same-host application | Copy-once `ukg_` client key with scopes, limits, expiry, revocation, and client ownership | Gateway routes only; no provider/data-service credentials |
| Private Windows client | DataLogicEngine key plus approved TLS and optional separately recorded mTLS identity | Disabled until CP8-B/CP8-I qualification |
| MCP connector | Owner consent bound to command fingerprint, file root, scopes, and encrypted credentials | Local stdio process; result remains untrusted |

New JSON/API routes use the API-native authentication decorator and return JSON
errors rather than redirects. Owner/admin routes require explicit owner checks;
single-owner mode does not justify omitting authorization. Caller-supplied user,
tenant, provider, policy, trace, store, connector, or tool authority is rejected.

## Governed request contract

Every accepted AI request binds one causal identity through admission, policy,
routing, persona/context construction, provider/tool execution where needed,
evidence/claim validation, convergence, memory/audit, trace, and response.
Supported outcomes include completed, blocked, failed, cancelled, capability-
unavailable, and offline/queued where explicitly allowed.

Responses must report only executed stages and measured values. Null confidence
or quality remains `not measured`. Safe error envelopes contain a stable code/
class, correlation/trace identity when available, retry guidance, and no secret
or private content. Validation, policy, provider, rate/quota, timeout,
cancellation, internal, readiness, and capability errors remain distinguishable.

## Client Gateway profiles

| Profile | Status | Use |
|---|---|---|
| `desktop_loopback` | Implemented | Built-in desktop/reference client |
| `same_host_gateway` | Engineering checkpoint | Named local applications using native API/SDKs |
| `private_windows_gateway` | Disabled/unqualified | Later approved Windows clients over qualified TLS/firewall policy |
| Public/browser gateway | Unsupported | Not part of the product contract |

The owner issues each client one copy-once key and minimum scopes. Durable state
records protected verification material, never the original key. Rotation may
use a bounded overlap; revocation and deletion take effect according to the
audited lifecycle. Client A cannot read or cancel Client B's job or trace.

## Native request modes

- Synchronous: bounded request/response with one causal trace.
- Streaming: native governed server-sent events; only committed/defined events
  are emitted, cancellation is explicit, and buffered delivery is labeled.
- Durable asynchronous: encrypted request/result state, bounded expiry,
  idempotency, poll/result/cancel, and restart-safe ownership.
- Trace read: safe stage metadata within the client boundary; evidence snippets
  require a separate scope.
- OpenAI compatibility: intentionally bounded translation, not full OpenAI API
  parity; unsupported fields/features fail explicitly.

Python and TypeScript SDKs must preserve the native error, streaming,
cancellation, idempotency, and trace contracts. SDK convenience must not create
authority or hide unsupported behavior.

## Rate, budget, retry, and cancellation

PostgreSQL owns durable request/job identity; Redis provides atomic content-free
rate/concurrency, coordination, event, and cancellation functions. A provider
call has a bounded deadline, call/token/spend policy, and one attempt identity.
Retries apply only to approved transient classes, remain within the original
budget/deadline, and do not silently switch providers or duplicate spend.

Cancellation propagates through gateway, governed execution, provider/tool call,
durable job, and trace state where applicable. A cancelled operation must not be
reported completed merely because a late result arrived.

## Knowledge Algorithm interface contract

The current `/api/v1/ka` surface is an authenticated engineering catalog and
partial direct-ID executor. It does not yet satisfy the production product
contract: broad owning-subsystem dispatch is incomplete, full Layer-9/Layer-10
safety execution is not yet qualified, a generic `allow_nonproduction` flag is
not an adequate authorization/
confirmation model, and the SDK/desktop do not share a complete typed
execute/history/trace workflow. Phase 18 closed incomplete after CP18-D failed.
Phase 19 owns correction and keeps the signed rebuild blocked through CP19-L.
CP19-A supplies the verified one-primary-owner and governed-consumer authority
for all 213 KAs through the canonical generated manifest. CP19-B passed after
migrating every existing production caller to the typed canonical result
variants: 18 internal/API/SDK surfaces, 32 typed sites, and zero legacy result
calls across 621 scanned production Python files. The compatibility envelope
remains an external boundary only; missing required values raise or fail closed
and missing confidence is unmeasured/zero. CP19-C now passes with one typed
selector/plan/executor, 213 positive and 213
negative generated fixtures, and a corrected 119-edge zero-cycle dependency
graph. Its effectful nodes produce proposals only; effect application remains
an authoritative-service workflow owned by CP19-I. CP19-D ten-layer integration
inside the canonical governed lifecycle now passes with typed causal L1-L10
state, selector-backed L1 execution, bounded L6-L9 revalidation, and L10-gated
success persistence. CP19-E full correct-ID fail-closed L9/L10 safety is active.

The target versioned interface is generated from the canonical KA manifest and
provides list/search, canonical detail, input/output schema, dependency and
side-effect plan, capability/prerequisite state, governed execute, cancel,
result, history, effect receipt, trace link, and health. Canonical and approved
alias IDs resolve to the same manifest entry; unknown, ambiguous, or retired
aliases fail with a stable public error.

Direct execution derives principal and scope on the server, applies per-KA risk,
policy, confirmation, budget, idempotency, deadline, cancellation, and service-
capability rules, and cannot bypass the canonical controller. High-risk or
effectful operations require their named confirmation contract. Responses
distinguish planned, selected, executed, blocked, unavailable, failed,
cancelled, and applied-effect states and never report a simulated service action
as success. Python and TypeScript SDKs are clients for this contract, not
alternate local KA runtimes.

## MCP integration contract

The supported protocol candidate is MCP `2025-11-25` over local stdio. One exact
absolute command is registered without execution. First start requires owner
consent bound to executable/argument SHA-256 fingerprint, approved file root,
granular scopes, credentials, and expected capabilities. Shell/package runners,
network targets, repository hot-start, subscriptions, sampling, and caller-owned
UKG/KA/graph defaults are absent or rejected.

The backend owns the durable process loop, timeout/cancellation, and Windows Job
Object process-tree termination. Discovery and calls are size/time bounded.
Every result is untrusted, hashed, redacted, secret/prompt-injection checked, and
retained under the approved PostgreSQL/Redis/object lifecycle. Execution history
omits retained content by default.

## Private Windows gateway qualification boundary

The profile may be enabled only for the exact signed release after validating
certificate subject/SAN/chain/purpose/expiry/revocation, private-key ACLs,
approved address/port, restrictive Windows Firewall rule, client identity,
scope/isolation, native/SSE/async/SDK/compatibility, provider/service/network/
disk/restart failures, backup/restore, upgrade/rollback/repair/uninstall,
redaction/no-egress, diagnostics, and two-machine owner approval. Internal
service/supervisor/diagnostic ports remain unreachable.

## Integration acceptance

Contract, route, auth, SDK, gateway, streaming, durable-job, cancellation,
idempotency, compatibility, MCP policy, redaction, and causal trace tests pass at
the engineering checkpoint. Signed-installed same-host/private two-machine
acceptance, TLS/firewall/certificate lifecycle, provider/five-service recovery,
load/soak, backup/restore, UI administration, and independent security/API review
remain release gates. Production/public release is **NO-GO**.

The generated `docs/generated/PRODUCTION_CONTRACT_INDEX.md` is the parity view
for product/API versions, provider/model IDs, internal service candidates, live
route counts, environment keys, and installer artifact naming. Hand-maintained
tables must not override that generated authority.
