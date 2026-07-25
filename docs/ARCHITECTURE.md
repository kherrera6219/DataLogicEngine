# Universal Knowledge Graph (UKG) System Architecture

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ENG-001 |
| Title | System architecture description |
| Document version | v4.7.0 |
| Product version | 4.3.0 |
| Status | active |
| Audience | Architecture, engineering, security, operations, quality, and professional reviewers |
| Owner | Architecture |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Approved product boundary, implemented runtime, ADRs, and qualification evidence |
| Confidentiality | Public |
| Last reviewed | 2026-07-25 |
| Next-review trigger | Runtime boundary, service, interface, data-flow, or deployment-architecture change |
| Requirements and evidence | Root plan, source tree, ADRs, diagrams, and production-readiness reports |

## Purpose

Define the current logical and runtime architecture of DataLogicEngine for engineering, security, operations, and technical-review stakeholders.

This version reflects the current code-backed architecture: an isolated
application factory and owned runtime, the Phase 5 `governed.v1` execution
contract, one backend-owned causal orchestrator, app-owned data services,
frontend trace review, Phase 6 typed evidence-quality decisions, Phase 7 bounded
provider execution/privacy accounting, and release-governed validation.

## Audience

1. Platform engineers
2. Security engineers
3. SRE/operations teams
4. Technical architects
5. QA/release engineers
6. Technical judges and external reviewers

## Related documents

1. `docs/INTERFACE_INTEGRATION.md`
2. `docs/ADMINISTRATOR_OPERATIONS_GUIDE.md`
3. `docs/VERIFICATION_VALIDATION_REPORT.md`
4. `docs/VERIFICATION_VALIDATION_REPORT.md`
5. `docs/KA_TRUTHCORE_VALIDATION_DOSSIER.md`
6. `docs/KA_TRUTHCORE_VALIDATION_DOSSIER.md`
7. `docs/ARCHITECTURE.md`
8. `docs/ARCHITECTURE.md`

## Architecture overview

### Phase 6 evidence-quality engineering checkpoint

All approved answer-producing surfaces now enter one transport-neutral
`GovernedRequest` and one backend-owned `GovernedExecutionOrchestrator`.
Transport routes own authentication and server-derived principal context; the
orchestrator owns admission, cancellation, DMRF/TruthGate, bounded retrieval,
deterministic DSQP, TruthCore/KA preflight, prompt construction, bounded provider
execution, validation, and transactional trace persistence.

`LLMGateway.execute()` remains the canonical gateway entry. `process()` is a thin
compatibility adapter. The public TruthCore entry is also an adapter, and SDK
0.6 is a service client rather than a second reasoning implementation.
Direct answer-mode simulation returns `SIMULATION_DURABLE_JOB_REQUIRED` after
admission and points to the separate durable simulation API. ADR-0007 selects
the backend multi-agent engine as the sole user-triggered authority; core/FROST
and legacy engines are reference-only and are absent from production entry
points.

The Phase 6 contract adds typed `SourceRecord`, trace-bound `EvidenceRecord`,
stable claim offsets, persisted claim/evidence relationships, citations,
validators, `ConfidenceMeasurement`, and `ConvergenceDecision`. Retrieval
relevance is never reused as source quality. Missing source quality/freshness or
unmeasured validators keep the versioned evidence-support result null. Enhanced
mode performs at most one refinement cycle, then finalizes, abstains, or blocks.

TruthCore's production preflight publishes `truthcore-preflight.v1` state and
failure transitions and can execute only production-enabled KA catalog entries.
Experimental and placeholder KAs are disabled in governed production traces.
Legacy hash-vector DRL output is not a production convergence signal.

### Phase 18 Knowledge Algorithm target architecture

The Phase 6 production-enabled filter remains a safety control, but the
2026-07-25 review proved the KA subsystem is not complete. The current 125-entry
executable registry, 277-row metadata catalog, 114-row SDK/design catalog,
unregistered Layer-9 suite, multiple engines/loaders, partial selector, and
sample SDK handlers are conflicting authorities. The signed rebuild is paused
while Phase 18 resolves them without capability loss.

The target architecture has one versioned KA manifest and one controller. The
manifest owns canonical identity and aliases, purpose, schemas, version,
layer/persona/subsystem, dependencies, selector triggers, determinism/seed,
evidence and service requirements, risk, confirmation, budgets, side-effect
class, implementation, limitation, test, and documentation references. API,
desktop, SDK, trace, and generated catalogs consume that manifest rather than
joining historical metadata by numeric ID.

The controller receives server-owned governed context and selects only
applicable KAs using intent, domain, risk, tier/layer/persona, evidence state,
policy, budget, dependency DAG, and live service capability. Pure KAs return
typed results or state-change proposals. Effectful KAs use approved app-owned
service ports after authorization, confirmation, idempotency, and transaction
checks and return authoritative receipts. The orchestrator remains the single
writer. Planned, selected, dependency, executed, skipped-with-reason, blocked,
failed, cancelled, unavailable, and applied-effect states are trace-distinct.

Layer 9, Layer 10, TruthCore/refinement, DMRF, DSQP/personas, retrieval/graph/
memory, ingestion, simulation, MCP, providers, gateway, and operations reuse the
same controller. Compatibility adapters may preserve older callers, but no
private engine, SDK handler map, unmanaged Celery queue, or direct provider/
store path is a production authority. Every canonical KA has a real owning
call path and its own named functional test before the source exit gate permits
the rebuild.

### Phase 10 durable simulation architecture

`dle-simulation.v1` owns versioned scenarios, participants, corpus references,
plans, budgets, expected artifacts, and results. Quick, standard, and deep plans
declare exact 4/5/7 provider-call ceilings. The simulation adapter exposes only
`generate_simulation_turn`; it cannot call the full governed pipeline and
enforces call/token/tool/cost/deadline/cancellation/pause limits.

PostgreSQL is authoritative for sessions, steps, events, provider attempts,
evidence, checkpoints, artifact records, controls, and terminal state. Redis is
content-free coordination and progress only. Required transcript/result objects
use the `simulation-artifacts` authority. Approved live measured summaries may
be indexed in Chroma and relationships in Neo4j; deterministic fixed-seed
qualification results are not promoted as measured knowledge.

Every completed provider turn has a durable usage record and verified checkpoint
before the next turn. Restart resumes only from verified state and fails safely
after an ambiguous uncheckpointed provider call. Numeric confidence exists only
when cited evidence and explicit validators support it; otherwise the API and UI
report Not measured.

### Phase 11 governed MCP connector architecture

ADR-0008 selects MCP `2025-11-25` over local stdio as the only external
connector transport candidate. The authenticated REST/JSON-RPC layer is an
app control plane, not a public MCP HTTP transport. Registration validates one
absolute executable, arguments, working folder, file roots, environment/
credential references, granular scopes, and limits without starting it. Owner
consent binds an exact SHA-256 fingerprint and scope subset; any definition
change invalidates authority.

The backend owns a durable asyncio loop and Windows Job Object with kill-on-
close and a memory ceiling. Named execution IDs support timeout and explicit
cancellation. PostgreSQL owns connector definition, consent, discovery,
lifecycle, and execution records; Redis mirrors content-free live state; large
governed results use the required `mcp-results` object bucket. Connector output
is untrusted, bounded, hashed, redacted, and checked for prompt-injection signals
before any later governed workflow can treat it as evidence.

Streamable HTTP, WebSocket, network-capable connectors, caller-selected
subscriptions, sampling, repository hot-start, and default UKG/KA/graph tools are
absent. Production process start is qualification-gated. Installed OS file
isolation, lifecycle/Electron acceptance, and backup/restore remain open; a
Windows Job Object is not represented as a filesystem sandbox.

### Phase 3 internal data-plane checkpoint

The application now has one app-owned rootless Podman delivery profile for the
five required data-plane capabilities. `PodmanDataPlaneManager` derives
installation-specific container/network/volume/secret names and loopback ports,
verifies immutable image identity and app labels, applies rootless/read-only/
capability/resource controls, and exposes lifecycle/probe state through the
Phase 2 supervisor. Production construction fails closed when its candidate lock
is not authorized or when PostgreSQL, Redis, Neo4j, ChromaDB, or the object
contract is unavailable.

The 2026-07-13 live engineering run passed real operations, restart durability,
truthful identity/status, and cleanup for the complete profile. This is not a
clean installed-production qualification. Exact runtime packaging, independent
review, coordinated recovery, and final installed-system gates remain open.

ADR-0010 defines the capability requirement **app-owned S3-compatible object
store** and selects SeaweedFS 4.40-dle.1 for rebuilt installed qualification.
The service remains production-disabled until the retained installed and
independent release gates pass.

DataLogicEngine is a local-first AI governance and knowledge-reasoning platform. It is not centered on a single LLM call. The architecture is built around a governed request lifecycle:

```text
authenticated request
  -> governed.v1 admission/cancellation
  -> DMRF defense, TruthGate, tier, and 17-axis route
  -> bounded source-identified retrieval
  -> deterministic DSQP + TruthCore/KA preflight
  -> one approved provider prompt and bounded execution
  -> output/claim/citation/policy validation
  -> transactional run/stage/evidence/claim persistence
  -> stable trace ID and explicit result/failure
```

The major architecture planes are:

1. **Experience plane** — Next.js/Electron frontend, dashboard, chat, graph, runs/trace explorer, Truth Engine monitor, MCP hub, admin, privacy/disclosures.
2. **Runtime ownership plane** — app factory, installation identity, runtime lock,
   startup phases, service supervisor, readiness/capabilities, admission drain,
   and Windows lifecycle coordination.
3. **API/security plane** — Flask API, sessions, CSRF, CORS, trusted hosts, rate limits, desktop local auth, middleware, operational health.
4. **AI control plane** — the `governed.v1` contract and canonical orchestrator,
   DMRF defense/tiering/axes, bounded retrieval, deterministic DSQP,
   TruthCore/KA preflight, prompt construction, validation, and trace truth.
5. **Truth Engine plane** — TruthGate and the canonical TruthCore adapter;
   legacy private workflow helpers do not own a public answer path.
6. **Data and memory plane** — PostgreSQL, Redis, Neo4j, ChromaDB, app-owned S3
   object storage, USKD NetworkX working graph, UnifiedMemory, and TruthMemory.
7. **Governance plane** — tests, CI, release gates, trace export integrity, docs/versioning, compliance and audit controls.

## High-level component map

```mermaid
flowchart TD
    User[User / Judge / Operator]
    FE[Next.js + Electron Frontend]
    API[Flask API and Security Envelope]
    Governed[governed.v1 Orchestrator]
    DMRF[DMRF / TruthGate / Routing]
    Truth[TruthCore / KA Preflight]
    LLM[LLM Gateway / MCP Tools]
    Data[Data and Memory Stores]
    Trace[Trace Explorer and Export Integrity]
    Ops[Testing / CI / Release Governance]

    User --> FE
    FE --> API
    API --> Governed
    Governed --> DMRF
    DMRF --> Truth
    Truth --> Governed
    Governed --> LLM
    Governed --> Data
    Data --> Trace
    DMRF --> Trace
    Truth --> Trace
    Ops --> API
    Ops --> FE
    Ops --> Data

    subgraph Frontend
        Dashboard[/dashboard]
        Chat[/chat]
        Runs[/runs]
        Graph[/graph + /knowledge]
        Monitor[/truth-engine]
        MCP[/mcp]
        Admin[/admin]
    end

    FE --> Dashboard
    FE --> Chat
    FE --> Runs
    FE --> Graph
    FE --> Monitor
    FE --> MCP
    FE --> Admin

    subgraph DMRFSteps[DMRF Execution]
        Inject[InjectionDefense]
        Gate[TruthGate Adapter]
        Tier[TierClassifier]
        Axis[17-Axis Router]
        DSQP[DSQP Personas]
        Plan[TruthCore Plan]
        Conv[Evidence + Convergence]
        Frost[FROST Snapshots]
    end

    DMRF --> Inject --> Gate --> Tier --> Axis --> DSQP --> Plan --> Conv
    DMRF -. every step .-> Frost

    subgraph TruthModules[Truth Engine Modules]
        TruthGate[TruthGate]
        TruthCore[TruthCore]
        TruthMemory[TruthMemory]
        TruthLink[TruthLink]
    end

    Truth --> TruthGate
    Truth --> TruthCore
    Truth --> TruthMemory
    Truth --> TruthLink

    subgraph Stores[Storage]
        SQL[SQLAlchemy / PostgreSQL or SQLite]
        Redis[Redis]
        Neo4j[Neo4j]
        Chroma[ChromaDB]
        ObjectStore[Local Object Store]
        USKD[USKD NetworkX Graph]
        UnifiedMemory[UnifiedMemoryService]
    end

    Data --> SQL
    Data --> Redis
    Data --> Neo4j
    Data --> Chroma
    Data --> ObjectStore
    Data --> USKD
    Data --> UnifiedMemory
```

## Core runtime stack

| Layer | Current implementation | Role |
|---|---|---|
| Frontend | Next.js App Router, React, TypeScript, Tailwind, Shadcn/Radix, Electron optional shell | Product UI, trace review, graph views, chat, admin, MCP, disclosures. |
| Backend | Flask 3.x, Python 3.11+, blueprints, SQLAlchemy | API gateway, security envelope, route registry, service orchestration. |
| Runtime ownership | `backend/runtime/` plus `create_app()` | Per-application state, startup phases, installation/runtime lock, service supervision, readiness, drain, and shutdown. |
| Control plane | `backend/dmrf/` | Governed AI lifecycle orchestration. |
| Truth Engine | `backend/truth_engine/` | Security gate, workflow engine, memory/audit, event bus. |
| Persona engine | `backend/dsqp/` | Deterministic/offline seven-component personas for axes 8-11. |
| Knowledge axes | `core/axes/`, `backend/dmrf/router.py` | 17-axis coordinate routing and FROST mode selection. |
| Model access | `backend/llm_gateway/`, MCP server modules | Cloud model execution (OpenAI gpt-5.5 / Google gemini-3.1-pro-preview), tool execution, connector integration. |
| Relational store | PostgreSQL production authority; SQLite bootstrap/development/repair only | Users, sessions, traces, artifacts, graph rows, audit records. |
| Graph store | Neo4j + USKD NetworkX memory graph | Durable and RAM-resident graph reasoning context. |
| Vector store | ChromaDB PersistentClient | Local embeddings and semantic search. |
| Object store | app-owned S3-compatible object store production authority; filesystem bootstrap/development/repair only | Deliverables, graphs, eval data, audit logs, trace exports. |
| Cache/queue | Required Redis production service | Session/cache/rate-limit/streams/queue behavior. |
| Governance | GitHub Actions, pytest, Vitest, Playwright, packaging smoke, release checks | Validation and release safety. |

## Application factory and runtime ownership

`app.py` exports `create_app()` as the authoritative construction path. Importing
the module does not construct a Flask application or start stores, threads,
event loops, network clients, managed services, logging handlers, or key
initialization. A deprecated lazy `app` proxy remains only for compatibility;
`main.py`, `wsgi.py`, `scripts/run_ukg_server.py`, and Electron-launched backend
execution construct and shut down an explicit application.

Every application instance owns these objects through `app.extensions`:

1. `ApplicationRuntime` and per-app request metrics;
2. one `ServiceSupervisor` and one `DatabaseLifecycleManager` adapter;
3. Socket.IO, SQLAlchemy engines, audit/encryption services, MCP state, and
   optional audio/video/document/simulation integrations;
4. connection, graph, vector, object, USKD, and unified-memory stores.

Startup order is deterministic:

```text
configuration
  -> paths and ACL
  -> installation identity and runtime lock
  -> service supervisor
  -> service identity/version verification
  -> migrations
  -> stores
  -> routes and workers
  -> readiness
```

Production startup fails closed when SQLite is selected, automatic schema
creation is requested, the runtime root belongs to another Windows user, an
incompatible installation version is found, a required service is absent or
unhealthy, or a listener has an unverified identity. Development/testing may use
explicit local fallbacks, but those modes do not satisfy production readiness.

Service state is one of `not_installed`, `stopped`, `starting`, `migrating`,
`ready`, `degraded`, `failed`, `stopping`, or `blocked`. `/live` answers process
liveness, `/ready` answers core readiness with safe blockers, and authenticated
`/api/v1/system/capabilities` publishes per-service state. Mutations are rejected
while the runtime is starting, draining, migrating, backing up, restoring,
updating, or stopping.

Electron waits for `/ready` before opening the main shell. It sends signed
suspend, resume, time-change, logoff, and shutdown events and uses bounded
graceful cleanup. The API gateway listener is a distinct supervised capability
and remains disabled/loopback-only until Phase 8.

## 2026-06-08 architecture baseline

The current architecture baseline is defined by these code-backed subsystems:

1. **DMRF control plane** — `backend/dmrf/orchestrator.py` coordinates injection defense, TruthGate, tiering, 17-axis routing, DSQP, TruthCore planning, evidence/convergence, memory, tracking, TruthLink, and observability.
2. **17-axis model** — `core/axes/` and `backend/dmrf/router.py` convert user context into an `AxisVector` with active axes, confidence, FROST depth, and Truth Engine mode.
3. **Axis 17 FROST mode selector** — `core/axes/axis17_frost_mode.py` maps reasoning tier to FROST layer depth and TruthCore mode.
4. **DSQP persona construction** — `backend/dsqp/` creates deterministic seven-part personas for axes 8-11 and persists deliverables to object storage when available.
5. **Truth Engine v7.3** — `backend/truth_engine/` exposes TruthGate, TruthCore, TruthMemory, and TruthLink through API and DMRF adapters.
6. **Multi-store memory** — Neo4j/SQL graph, USKD NetworkX graph, ChromaDB vectors, UnifiedMemory structured graph, TruthMemory audit memory, and local object store all serve distinct roles.
7. **Local-first runtime** — desktop/local/hybrid behavior uses loopback auth, per-install secret, nonce/HMAC signatures, DPAPI helper, and app-owned storage services.
8. **Frontend review surface** — `/chat`, `/runs`, `/graph`, `/knowledge`, `/truth-engine`, `/mcp`, `/admin`, and disclosure pages expose system operation to users and reviewers.
9. **Testing/release governance** — CI validates backend, frontend, contract, parity, security, packaging, environment, lockfile, Docker, and release governance gates.
10. **Cloud AI model** — `backend/llm_gateway/`: every request is served by the user-selected cloud model (OpenAI `gpt-5.5` or Google `gemini-3.1-pro-preview`), resolved from `UserAIPreferences` / configured `LLMProvider` records. There is no local model tier or escalation engine; an API key + internet are required for reasoning.

## DMRF control plane

DMRF is the operational brain of the AI architecture.

Runtime order:

```text
DMRFResult creation
  -> InjectionDefense.detect()
  -> TruthGateDMRFAdapter.evaluate()
  -> DMRFTierClassifier.classify()
  -> DMRFRouter.route()
  -> await DSQPOrchestrator.construct_all()
  -> TruthCoreDMRFAdapter.workflow_steps()
  -> EvidenceModel.score()
  -> ConvergencePolicy.should_refine() [legacy DMRF telemetry only]
  -> TruthMemoryDMRFAdapter.persist()
  -> DMRFMLflowTracker.record()
  -> TruthLinkDMRFAdapter.publish()
  -> DMRFObservability.record()
```

Every DMRF step is recorded as a `DMRFStep` and passed through the FROST snapshot bridge. This creates a step-level trace instead of only retaining input/output pairs.

The DMRF `ConvergencePolicy` result is retained as routing telemetry; it does
not decide whether an answer is finalized. The canonical `governed.v1`
orchestrator binds claims to persisted evidence and uses
`backend/governed_execution/quality.py` (`dle-confidence.v1`) for the bounded
`refine`, `finalize`, `abstain`, or `block` decision. Missing measurements stay
`null/not_measured`, and refinement is limited to one additional provider call.

In the packaged desktop runtime, enhanced chat enables DMRF by default. DMRF constructs axes 8-11 concurrently, and the SDK overlay reuses that persona chain rather than issuing a second DSQP construction pass. The gateway merges DMRF and SDK records into one run ID before persisting the final trace.

Key files:

- `backend/dmrf/orchestrator.py`
- `backend/dmrf/models.py`
- `backend/dmrf/injection_defense.py`
- `backend/dmrf/tier_classifier.py`
- `backend/dmrf/router.py`
- `backend/dmrf/evidence_model.py`
- `backend/dmrf/convergence_policy.py`
- `backend/dmrf/frost_bridge.py`
- `backend/dmrf/truth_integration/`

## 17-axis knowledge framework

The 17-axis model converts natural-language requests into explicit routing coordinates.

Axis groups:

1. Axes 1-7 — knowledge context: domain, sector, semantic bridges, branch, nodes, regulatory aggregation, compliance mesh.
2. Axes 8-11 — expert personas: knowledge, sector, regulatory, compliance.
3. Axes 12-13 — location/jurisdiction and time/version context.
4. Axes 14-16 — lifecycle, risk/threat, ethics/trust/criticality.
5. Axis 17 — FROST mode selector: tier to FROST depth and TruthCore mode.

Axis 17 currently maps:

| Tier | FROST depth | TruthCore mode |
|---|---:|---|
| `trivial` | 2 | `direct` |
| `moderate` | 4 | `standard` |
| `high_stakes` | 7 | `regulatory_strict` |
| `extreme` | 10 | `full_refinement` |
| `autonomous` | 10 | `governed_agentic` |

Key files:

- `core/axes/axis_system.py`
- `core/axes/axis17_frost_mode.py`
- `core/axes/axis15_risk_threat.py`
- `core/axes/axis16_ethics_trust.py`
- `backend/dmrf/router.py`

## DSQP persona architecture

DSQP constructs persona axes 8-11 as structured profiles rather than simple role prompts.

Each DSQP persona contains seven components:

1. `job_role`
2. `education`
3. `certifications`
4. `skills`
5. `training`
6. `career_path`
7. `related_jobs`

The canonical Phase 5 path constructs DSQP context deterministically. A future
LLM-assisted mode would require explicit consent, provider-call accounting, and
proof that its output causally affects the final decision.

Key files:

- `backend/dsqp/dsqp_chain.py`
- `backend/dsqp/dsqp_orchestrator.py`
- `backend/dsqp/dsqp_validator.py`
- `backend/dsqp/dsqp_registry.py`
- `backend/dsqp/templates/`

## Truth Engine architecture

Truth Engine is a four-module subsystem:

| Module | Role |
|---|---|
| TruthGate | Request gate for security, budget, priority, compliance, and trust checks. |
| TruthCore | Tiered reasoning/session engine with workflow steps. |
| TruthMemory | Audit, cache, metrics, artifact, explainability, and MLflow-style tracking layer. |
| TruthLink | Event bus with priority queue, optional Redis streams, SSE, and dead-letter handling. |

The private legacy TruthCore helper retains workflow-step implementations for
internal tests and Phase 6 migration:

```text
intent_parsing
hybrid_retrieval
deep_research
pov_expansion
multi_persona_reasoning
quant_validation
agi_planning
trust_validation
meta_reasoning
final_safety_gate
memory_patch
```

These steps are not independently claimed as executed by the public answer path.
The canonical orchestrator selects the bounded workflow and records only the
TruthCore/KAs that actually run.

Key files:

- `backend/truth_engine/api.py`
- `backend/truth_engine/truth_gate/gateway.py`
- `backend/truth_engine/truth_core/engine.py`
- `backend/truth_engine/truth_memory/manager.py`
- `backend/truth_engine/truth_link/bus.py`

## LLM Gateway architecture

The LLM Gateway (`backend/llm_gateway/`) is the provider boundary inside the
canonical orchestrator. `LLMGateway.execute()` accepts `GovernedRequest` and
owns the single orchestrator entry; `process()` only converts older gateway
callers/results. Provider selection returns exactly one supported provider/model.
Deadline, cancellation, typed failure/retry, circuit, call/token/spend,
egress-ledger, and replay policy stay inside the request-wide governed bound.

The external Client Gateway is an admission and transport layer above that same
orchestrator, not a second provider path. `dle-gateway.v1` supports named client
principals, explicit scopes, server-owned virtual models, strict schemas, sync,
live governed SSE, durable jobs, trace summaries, and a bounded OpenAI shape.
Loopback is the default. The private Windows profile fails startup until its
certificate/firewall/two-machine qualification is accepted.

```text
Approved client + ukg_ key
  -> strict dle-gateway.v1 contract
  -> PostgreSQL client/virtual-model/idempotency/job policy
  -> atomic Redis minute/day/concurrency admission + job lease/cancel state
  -> one GovernedRequest with immutable external-client principal
  -> GovernedExecutionOrchestrator
  -> retrieval / KAs / TruthCore / validation / trace
  -> bounded LLMGateway provider execution when the virtual model permits
  -> governed result, validated-output SSE, or durable encrypted result
```

Client keys contain only protected verification material and are returned once.
Provider keys remain a separate outbound Provider Connections boundary. Large
retained job results are encrypted, hash-verified, and materialized into the
app-owned `gateway-results` S3 bucket; clients never receive object-store
credentials or direct object URLs.

### Knowledge lifecycle authority

Electron picker capabilities are consumed before the backend acquires a source
into bounded app-owned staging. PostgreSQL is authoritative for ingestion jobs,
files, chunks, attempts, hashes, checkpoints, and source revisions. Redis carries
content-free queue/lease/state/progress data. Neo4j and Chroma are rebuildable
revisioned materializations. The app-owned `knowledge-sources` S3 bucket is
authoritative for the required hashed original and normalized artifacts.

A corpus revision is complete only when PostgreSQL, Neo4j, Chroma, and both
required objects agree. Governed retrieval validates those authorities plus
permission, retention, defense, embedding, and deletion state before context is
eligible. ADR-0006 keeps working memory distinct from validated trust and limits
promotion to validated governed outcomes.

### Provider routing

The orchestrator constructs one policy/persona/evidence/KA-aware prompt before
invoking the provider boundary. The provider-only lifecycle is:

```text
GovernedExecutionOrchestrator
  -> construct approved provider messages
  -> LLMGateway bounded provider method
  -> _get_eligible_providers()   (DB first, supported env fallback)
  -> select exactly one OpenAI or Google provider/model
  -> enforce request/session/day/month call, token, and known-spend budgets
  -> CircuitBreaker.can_execute()?
  -> backend async provider.complete()
  -> persist content-free attempt/egress ledger record
  -> on success: return only after ledger persistence
  -> on failure: typed retry/replay/status policy inside remaining deadline
  -> on terminal failure: finalize governed trace and typed error
```

### Circuit breaker

The circuit breaker is **class-level** (`LLMGateway._circuit_breakers: dict[str, CircuitBreaker] = {}`), persisting across per-request `LLMGateway()` instantiations within the same process:

- `failure_threshold = 5` — circuit opens after 5 counted failures.
- `recovery_timeout = 60` — circuit resets after 60 seconds.
- Rate-limit/quota/billing/auth/model/policy failures do not represent a network
  outage. Only network, provider-outage, timeout, and unknown transport failures
  affect circuit state.

### Typed failure and replay handling

Provider exceptions and responses normalize to invalid key, unauthorized model,
invalid model, quota exhausted, billing suspended, rate limited, network,
provider outage, timeout, policy block, malformed response, cancellation,
persistence, internal, or unknown. Retry occurs only for a typed idempotent
transient failure, consumes the same provider-call budget, honors bounded
`Retry-After` when available, and never switches silently to the other provider.

Only `network`, `provider_outage`, and `timeout` are replayable. The Windows
production offline queue requires DPAPI, bounds items/bytes/expiry, deduplicates
by request identity, and re-runs current policy and budget checks at replay.

### API key encryption

New provider API keys are DPAPI-protected in the `llm_provider` SQL table on
Windows. Desktop production fails closed if DPAPI is unavailable. Legacy Fernet
values remain readable for migration and nonproduction/test fallback; keys are
never serialized through provider, status, ledger, trace, or export responses.

### Model selection

The stored `LLMProvider.model_id` (set by the user in Settings → API
Configuration) is used by default. The frontend includes `provider`/`model` only
when explicitly selected. Defaults are generated from
`config/provider_manifest.v1.json` through
`backend/llm_gateway/provider_manifest.py`:

| Provider | Default model |
|---|---|
| OpenAI | `gpt-5.5` |
| Google / Gemini | `gemini-3.1-pro-preview` |

### Cloud model selection

When a governed request reaches the provider boundary, it uses the caller-pinned
provider/model when policy permits, the owner's saved preference/default, or one
deterministically selected supported active provider. A request receives exactly
one provider/model selection and no cross-provider failover:

| Provider type | Model |
|---|---|
| `openai` | `gpt-5.5` |
| `google` / `gemini` | `gemini-3.1-pro-preview` |

There is no local model tier or complexity-based escalation. A provider-backed
answer requires an owner-configured key and network access; `local_review` must
not fabricate one. Canonical DSQP is deterministic and does not make a hidden
provider call.

### Key files

- `backend/governed_execution/` — canonical contracts, orchestration, retrieval,
  prompt construction, validation, and trace persistence
- `backend/llm_gateway/gateway.py` — `execute()` adapter/orchestrator entry,
  bounded provider handling, eligibility, error classification, circuit breaker,
  and usage persistence
- `backend/llm_gateway/providers/` — backend-owned async OpenAI/Google adapters
- `backend/llm_gateway/provider_budget.py` — server-owned budget policy
- `backend/llm_gateway/provider_errors.py` — typed retry/replay/failure policy
- `backend/llm_gateway/api.py` — gateway, cancellation, queue, status, and ledger routes
- `backend/llm_gateway/external_contract.py` — profiles, scopes, and virtual models
- `backend/llm_gateway/admission_limiter.py` — atomic Redis admission/concurrency
- `backend/llm_gateway/jobs.py` and `job_coordination.py` — bounded durable jobs
- `config/provider_manifest.v1.json` — provider/model capability authority
- `models.py` — provider credentials, client keys, virtual models, idempotency,
  jobs, traces, audit, and usage authorities

---

## Data, storage, and memory architecture

The platform uses a multi-store architecture with clear separation of responsibilities.

| Store | Role |
|---|---|
| SQLAlchemy database | Durable application state, users, sessions, traces, graph rows, artifacts, audit records. |
| Redis | Required production cache, sessions, atomic client limits/concurrency, gateway job coordination/cancellation state, queues, and TruthLink streams. |
| Neo4j | Durable graph store for knowledge graph relationships. |
| USKD NetworkX graph | RAM-resident graph for fast reasoning traversal. |
| ChromaDB | Local vector/embedding storage. |
| app-owned S3-compatible object store | Required production S3-compatible artifacts, exports, evidence, retained large gateway results, and backups. |
| Local object store | Bootstrap/development/repair role only; not the production app-owned S3-compatible object store substitute. |
| UnifiedMemoryService | Structured reasoning memory graph persisted to JSON. |
| TruthMemory | Audit/explainability memory for Truth Engine and DMRF sessions. |

Current storage mode is local/app-owned by default. `backend/storage/connection_manager.py` treats `local`, `vm`, and `auto` as supported modes and deprecates external cloud database mode in favor of internal app-owned storage services.

Key files:

- `backend/storage/connection_manager.py`
- `backend/storage/object_store.py`
- `backend/storage/vector_store.py`
- `backend/storage/graph_store.py`
- `backend/storage/uskd_memory_graph.py`
- `backend/memory/unified_memory_service.py`
- `backend/truth_engine/truth_memory/manager.py`

## Frontend product architecture

The frontend is a Next.js App Router application with an optional Electron desktop shell.

Primary product surfaces:

1. `/dashboard` — system overview.
2. `/chat` — Enterprise AI interface.
3. `/runs` and `/runs/view` — Trace Explorer and run detail review.
4. `/graph` and `/knowledge` — graph and knowledge-node inspection.
5. `/truth-engine` — Truth Engine monitor.
6. `/mcp` — MCP connector hub.
7. `/projects` — project management.
8. `/admin` — governance, compliance, provider, and audit views (single authenticated owner).
9. `/settings`, `/settings/privacy`, `/legal/privacy`, `/about/cloud-services`, `/about/ai-limitations` — configuration and transparency surfaces.

Root provider stack:

```text
FeatureFlagProvider
  ClientErrorBootstrap
  ThemeProvider
    SWRConfig
      AuthProvider
        AppInitializer
          ToastProvider
            ApiErrorBoundary
              AppSidebar
              CloudDisclosureBanner
              NavBar
              main content
              DesktopStatus
```

Key files:

- `frontend/app/layout.tsx`
- `frontend/components/layout/AppSidebar.tsx`
- `frontend/contexts/AuthContext.tsx`
- `frontend/lib/api/`
- `frontend/electron/`

## Local-first and desktop architecture

The local-first architecture supports:

1. Electron desktop runtime.
2. Flask backend on loopback.
3. Next.js frontend or exported Electron frontend.
4. App-owned internal databases and stores.
5. Desktop local auth using per-install secret, nonce challenge, HMAC signatures, and timestamp skew checks.
6. Windows DPAPI helper for local protected data.
7. Local trace export hashing/signing/encryption options.
8. Windows backend rebuild, installer integrity, packaging smoke, installer-mode smoke, and NSIS governance checks.

Supported deployment patterns:

- desktop deployment;
- Windows VM deployment using the same app-owned stack.

Public web/cloud SaaS is excluded from the active completion program. A private
Windows gateway profile remains disabled until Phase 8 qualification.

Key files:

- `backend/security/desktop_local_auth.py`
- `backend/security/dpapi_store.py`
- `backend/security/encryption_manager.py`
- `backend/security/export_integrity.py`
- `frontend/lib/runtime/policy.ts`
- `scripts/windows/`

Implementation note: the current `EncryptionManager` writes new field-level encrypted payloads with AES-256-GCM and records `AES-256-GCM` in the key registry. Legacy `Fernet-AES-128-CBC` entries remain decryptable for backward compatibility. DPAPI uses Windows platform crypto through `win32crypt`.

## API and route architecture

Canonical APIs live under `/api/v1/*`. Legacy aliases remain only for transition coverage and emit deprecation headers.

Major API families:

1. `/api/v1/auth/*`
2. `/api/v1/gateway/*`
3. `/api/v1/truth/*`
4. `/api/v1/trace/*`
5. `/api/v1/ka/*`
6. `/api/v1/mcp/*`
7. `/api/v1/compliance/*`
8. `/api/v1/privacy/*`
9. `/api/v1/gdpr/*`
10. `/api/v1/retention/*`
11. `/api/v1/storage/*`
12. `/api/v1/simulations/*`
13. `/api/v1/ingestion/*`
14. `/api/v1/{pillars,sectors,domains,knowledge,nodes,edges}`

See `docs/INTERFACE_INTEGRATION.md` for endpoint-level guidance.

## Security architecture

Security controls include:

1. session hardening;
2. CSRF and origin checks;
3. CORS allowlist;
4. trusted-host validation;
5. rate limiting;
6. desktop loopback authentication;
7. DPAPI local protection helper;
8. field-level encryption manager;
9. export integrity hashing/signing/encryption;
10. TruthGate input sanitization, budget checks, and compliance markers;
11. injection defense in DMRF;
12. desktop local-auth gating in the frontend (single OS-level user);
13. contract-tested JSON error behavior for canonical API routes.

## Observability and traceability

Observability surfaces include:

- correlation IDs;
- `/metrics` Prometheus output;
- exact governed stages with start/end time, measured duration, status, and
  stable trace ID;
- DMRF tier, axes, DSQP, TruthCore, KA, policy, provider, evidence, and claim
  records only when those activities execute;
- Truth Engine status/stats endpoints;
- Trace Explorer;
- TruthMemory audit and explainability data;
- TruthLink events and SSE;
- CI-generated reports;
- runtime precheck and readiness reports.

Trace exports can include section hashes, bundle hash, optional HMAC signatures, optional encryption, and manifest metadata.

## Testing and release governance

The current validation architecture includes:

1. Python/pytest unit and integration tests.
2. API contract tests.
3. Local-mode parity tests.
4. Security regression tests.
5. Truth Engine, KA, axes, compliance, simulation, and Windows tests.
6. Frontend Vitest, Playwright E2E, visual regression, accessibility sweep, lint, typecheck, and build.
7. Windows packaging smoke tests.
8. NSIS governance checks.
9. Environment parity and lockfile governance.
10. Docker image build verification.
11. Release checklist and branch protection policies.

`docs/VERIFICATION_VALIDATION_REPORT.md` records the quality baseline and required release gates.

## Reviewer architecture path

A technical reviewer should inspect these diagrams first:

1. `docs/ARCHITECTURE.md`
2. `docs/ARCHITECTURE.md`
3. `docs/KA_TRUTHCORE_VALIDATION_DOSSIER.md`
4. `docs/KA_TRUTHCORE_VALIDATION_DOSSIER.md`
5. `docs/KA_TRUTHCORE_VALIDATION_DOSSIER.md`
6. `docs/DATA_ARCHITECTURE.md`
7. `docs/SECURITY_ARCHITECTURE.md`
8. `docs/PRODUCT_REQUIREMENTS.md`
9. `docs/VERIFICATION_VALIDATION_REPORT.md`

Then inspect these implementation files:

1. `app.py`
2. `backend/governed_execution/contracts.py`
3. `backend/governed_execution/orchestrator.py`
4. `backend/governed_execution/retrieval.py`
5. `backend/governed_execution/prompt.py`
6. `backend/governed_execution/validation.py`
7. `backend/governed_execution/trace_persistence.py`
8. `backend/llm_gateway/gateway.py`
9. `backend/dmrf/router.py`
10. `backend/truth_engine/truth_core/engine.py`
11. `backend/storage/connection_manager.py`
12. `frontend/components/Chat/LiveTracePanel.tsx`
13. `.github/workflows/ci.yml`

## Change notes for v4.4.0

1. Added ADR-0007's sole simulation authority, exact plan budgets, non-recursive
   adapter, durable store responsibilities, verified restart, and confidence
   truth boundary.

## Change notes for v4.2.0

1. Replaced legacy multi-provider/Fernet routing detail with the Phase 7
   generated manifest, one selected provider, backend async adapters, typed
   failure/replay, DPAPI-first secrets, and usage/budget architecture.
2. Recorded that successful output is released only after durable content-free
   attempt persistence and current SSE remains buffered.

## Change notes for v4.0.0

1. Recorded `governed.v1`, the single backend-owned orchestrator, the thin SDK
   and compatibility adapters, exact trace semantics, and simulation boundary.
2. Separated Phase 5 causal execution proof from the Phase 6 evidence,
   confidence, convergence, and KA-validity program.

## Change notes for v3.3.0

1. Recorded the qualified five-service Podman engineering profile, supervisor-
   owned fail-closed adapters, and retained installed-production gates.
2. Replaced the product-specific object-store target with the capability
   requirement and selected SeaweedFS 4.40-dle.1 under ADR-0010 while retaining
   production authorization false.

## Change notes for v3.2.0

1. Replaced the implicit global-startup description with the implemented
   application factory, app-owned runtime, nine startup phases, service-state
   model, installation lock, readiness, drain, and Windows lifecycle contract.
2. Clarified that production refuses SQLite/automatic schema fallback and that
   concrete five-service delivery remains the Phase 3 boundary.

## Change notes for v3.1.0

1. Reviewed the architecture source of truth during the production top-level documentation pass; the current DMRF, Truth Engine, local-first data, and cloud BYOK model remains authoritative.
2. Updated metadata so the architecture reference reflects the July 2026 production documentation pass.

## Change notes for v2.7.0

1. Added dedicated LLM Gateway architecture section: multi-provider routing, class-level circuit breaker, rate-limit protection (Sprint 5f — commit `7c27a64c`), Fernet API key encryption, and model selection from DB.
2. Updated document version to v2.7.0 and last-updated date to 2026-06-08.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Reframed architecture around the current DMRF control plane rather than older generic middleware language.
3. Added current 17-axis, Axis 17/FROST, and DSQP persona architecture.
4. Updated Truth Engine description to the current TruthGate, TruthCore, TruthMemory, and TruthLink modules.
5. Added multi-store memory architecture covering SQL, Redis, Neo4j, USKD, ChromaDB, object store, UnifiedMemory, and TruthMemory.
6. Added frontend product surface and trace-review architecture.
7. Added local-first/desktop architecture and updated field-encryption notes for AES-256-GCM with legacy Fernet decrypt compatibility.
8. Added security, observability, testing, and reviewer verification paths tied to implementation files and the new diagram set.
