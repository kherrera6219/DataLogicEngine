# Universal Knowledge Graph (UKG) System Architecture

## Document metadata

| Field | Value |
|---|---|
| Document version | v3.1.0 |
| Last updated | 2026-07-06 |
| Status | Active |
| Owner | Platform Architecture |
| Review cadence | Every 60 days |

## Purpose

Define the current logical and runtime architecture of DataLogicEngine for engineering, security, operations, and technical-review stakeholders.

This version reflects the current code-backed architecture: local-first runtime modes, DMRF control plane, 17-axis routing, DSQP persona construction, Truth Engine v7.3, multi-store memory, frontend trace review, and release-governed validation.

## Audience

1. Platform engineers
2. Security engineers
3. SRE/operations teams
4. Technical architects
5. QA/release engineers
6. Technical judges and external reviewers

## Related documents

1. `docs/API.md`
2. `docs/DEPLOYMENT.md`
3. `docs/PRODUCTION_READINESS.md`
4. `docs/TESTING.md`
5. `docs/diagrams/04_17_axis_coordinate_model.md`
6. `docs/diagrams/05_truth_engine_architecture.md`
7. `docs/diagrams/09_dmrf_control_plane_deep_dive.md`
8. `docs/diagrams/12_end_to_end_request_lifecycle.md`

## Architecture overview

DataLogicEngine is a local-first AI governance and knowledge-reasoning platform. It is not centered on a single LLM call. The architecture is built around a governed request lifecycle:

```text
User prompt
  -> frontend/API security envelope
  -> DMRF control plane
  -> TruthGate
  -> tier classification
  -> 17-axis routing
  -> DSQP persona construction
  -> TruthCore workflow planning/execution
  -> model/tool execution when required
  -> evidence freshness and convergence policy
  -> memory/audit/artifact persistence
  -> trace review and integrity-protected export
```

The major architecture planes are:

1. **Experience plane** — Next.js/Electron frontend, dashboard, chat, graph, runs/trace explorer, Truth Engine monitor, MCP hub, admin, privacy/disclosures.
2. **API/security plane** — Flask API, sessions, CSRF, CORS, trusted hosts, rate limits, desktop local auth, middleware, operational health.
3. **AI control plane** — DMRF orchestration, injection defense, tiering, 17-axis routing, DSQP, Truth Engine integration, convergence policy, observability.
4. **Truth Engine plane** — TruthGate, TruthCore, TruthMemory, TruthLink.
5. **Data and memory plane** — SQL, Redis, Neo4j, ChromaDB, local object store, USKD NetworkX graph, UnifiedMemory, TruthMemory.
6. **Governance plane** — tests, CI, release gates, trace export integrity, docs/versioning, compliance and audit controls.

## High-level component map

```mermaid
flowchart TD
    User[User / Judge / Operator]
    FE[Next.js + Electron Frontend]
    API[Flask API and Security Envelope]
    DMRF[DMRF Control Plane]
    Truth[Truth Engine v7.3]
    LLM[LLM Gateway / MCP Tools]
    Data[Data and Memory Stores]
    Trace[Trace Explorer and Export Integrity]
    Ops[Testing / CI / Release Governance]

    User --> FE
    FE --> API
    API --> DMRF
    DMRF --> Truth
    Truth --> LLM
    DMRF --> Data
    Truth --> Data
    LLM --> Data
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
| Control plane | `backend/dmrf/` | Governed AI lifecycle orchestration. |
| Truth Engine | `backend/truth_engine/` | Security gate, workflow engine, memory/audit, event bus. |
| Persona engine | `backend/dsqp/` | Deterministic/offline seven-component personas for axes 8-11. |
| Knowledge axes | `core/axes/`, `backend/dmrf/router.py` | 17-axis coordinate routing and FROST mode selection. |
| Model access | `backend/llm_gateway/`, MCP server modules | Cloud model execution (OpenAI gpt-5.5 / Google gemini-3.1-pro-preview), tool execution, connector integration. |
| Relational store | SQLAlchemy with SQLite/PostgreSQL paths | Users, sessions, traces, artifacts, graph rows, audit records. |
| Graph store | Neo4j + USKD NetworkX memory graph | Durable and RAM-resident graph reasoning context. |
| Vector store | ChromaDB PersistentClient | Local embeddings and semantic search. |
| Object store | Local filesystem object store | Deliverables, graphs, eval data, audit logs, trace exports. |
| Cache/queue | Redis where available | Session/cache/rate-limit/streams/queue behavior. |
| Governance | GitHub Actions, pytest, Vitest, Playwright, packaging smoke, release checks | Validation and release safety. |

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
  -> DSQPOrchestrator.construct_all_sync()
  -> TruthCoreDMRFAdapter.workflow_steps()
  -> EvidenceModel.score()
  -> ConvergencePolicy.should_refine()
  -> TruthMemoryDMRFAdapter.persist()
  -> DMRFMLflowTracker.record()
  -> TruthLinkDMRFAdapter.publish()
  -> DMRFObservability.record()
```

Every DMRF step is recorded as a `DMRFStep` and passed through the FROST snapshot bridge. This creates a step-level trace instead of only retaining input/output pairs.

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

The current implementation is deterministic and offline-capable. Future LLM-assisted construction can replace internal answer generation without changing the output contract.

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

TruthCore workflow steps include:

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

Key files:

- `backend/truth_engine/api.py`
- `backend/truth_engine/truth_gate/gateway.py`
- `backend/truth_engine/truth_core/engine.py`
- `backend/truth_engine/truth_memory/manager.py`
- `backend/truth_engine/truth_link/bus.py`

## LLM Gateway architecture

The LLM Gateway (`backend/llm_gateway/`) provides multi-provider AI routing with cross-provider failover, circuit breaker protection, and rate-limit-aware error handling.

### Provider routing

`LLMGateway.process()` resolves eligible providers from the `llm_provider` database table (falling back to environment variables), then attempts requests in order with per-attempt retries. The request lifecycle:

```text
LLMGateway.process()
  -> _get_eligible_providers()   (DB first, env var fallback)
  -> for each provider:
      -> CircuitBreaker.allow_request()?
      -> provider.chat() / provider.complete()
      -> on success: return GatewayResponse(ok=True)
      -> on failure: classify (retryable vs. rate-limit vs. fatal)
      -> retry loop with backoff (only for retryable non-rate-limit errors)
  -> if all providers exhausted: _error_response()
```

### Circuit breaker

The circuit breaker is **class-level** (`LLMGateway._circuit_breakers: dict[str, CircuitBreaker] = {}`), persisting across per-request `LLMGateway()` instantiations within the same process:

- `failure_threshold = 5` — circuit opens after 5 counted failures.
- `recovery_timeout = 60` — circuit resets after 60 seconds.
- Rate-limit (429) responses do **not** increment the failure counter — the provider is healthy, just throttled.

### Rate-limit handling (Sprint 5f — `7c27a64c`)

`_is_rate_limit_error(error)` detects the following in the lowercased error string: `"429"`, `"rate limit"`, `"rate_limit"`, `"quota exceeded"`, `"insufficient_quota"`, `"billing"`.

When a rate-limit is detected:

1. The request is **not** retried (no backoff loop).
2. `cb.record_failure()` is **not** called (circuit state unchanged).
3. `gateway_chat()` in `api.py` returns `HTTP 429` with `{code: "RATE_LIMITED"}` directly, **before** the offline queue check.
4. The frontend (`ChatInterface.tsx`) catches `ApiError` with `status === 429` and displays "The AI provider is currently rate limited."

Previously, rate-limit errors cascaded: 429 → retry 3× → circuit failure counter → circuit opens → all providers skipped → offline queue → 202 "queued for replay". This cascade is now prevented.

### API key encryption

Provider API keys are stored Fernet-encrypted in the `llm_provider` SQL table. The encryption key is derived from `SESSION_SECRET`:

```python
fernet_key = base64.urlsafe_b64encode(hashlib.sha256(SESSION_SECRET.encode()).digest())
```

`SESSION_SECRET` is **stable across restarts** in the packaged Electron app: `loadOrCreatePlainSecretFile()` in `frontend/electron/main.ts` creates `{userData}/secrets/session_secret.secret` (32-byte hex) once on first run and passes the file **path** as `SESSION_SECRET_FILE` to the backend. If decryption fails (e.g., database migrated without the original secret), `LLMProvider.get_api_key()` logs a WARNING with a re-save instruction rather than silently returning `None`.

### Model selection

The stored `LLMProvider.model_id` (set by the user in Settings → API Configuration) is used by default. The frontend (`frontend/lib/api/system_chat.ts`) only includes `provider`/`model` fields when the caller explicitly supplies them, so the backend always reads from DB. Default models are defined in `backend/llm_gateway/model_defaults.py`:

| Provider | Default model |
|---|---|
| OpenAI | `gpt-5.5` |
| Google / Gemini | `gemini-3.1-pro-preview` |

### Cloud model selection

When a request reaches `LLMGateway.process()`, the gateway uses the caller-pinned provider/model, or the user's saved preference (`UserAIPreferences`), or the first active cloud `LLMProvider` record's default model. Every request is served by **one user-selected cloud model**:

| Provider type | Model |
|---|---|
| `openai` | `gpt-5.5` |
| `google` / `gemini` | `gemini-3.1-pro-preview` |

There is no local model tier or complexity-based escalation; an API key + internet connection are required for reasoning. Internal steps that previously used a local model (DSQP answer generation, the defense-supervisor screen) call the selected cloud model via `backend/llm_gateway/active_model.generate_with_active_model()`, and fall back to their deterministic / fail-open path when no key is configured.

### Key files

- `backend/llm_gateway/gateway.py` — `LLMGateway`, `_has_active_cloud_providers`, `_is_rate_limit_error`, `_is_retryable_error`, circuit breaker
- `backend/llm_gateway/api.py` — Flask routes, `gateway_chat()` with 429 early-return
- `backend/llm_gateway/model_defaults.py` — default model IDs per provider
- `models.py` — `LLMProvider.get_api_key()` / `set_api_key()` Fernet encryption

---

## Data, storage, and memory architecture

The platform uses a multi-store architecture with clear separation of responsibilities.

| Store | Role |
|---|---|
| SQLAlchemy database | Durable application state, users, sessions, traces, graph rows, artifacts, audit records. |
| Redis | Cache, sessions, rate limits, queues, TruthLink streams where enabled. |
| Neo4j | Durable graph store for knowledge graph relationships. |
| USKD NetworkX graph | RAM-resident graph for fast reasoning traversal. |
| ChromaDB | Local vector/embedding storage. |
| Local object store | Deliverables, graphs, audit logs, simulation artifacts, eval data, trace exports. |
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
- Windows VM deployment using the same app-owned stack;
- controlled web/cloud deployment where configured.

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

See `docs/API.md` for endpoint-level guidance.

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
- DMRF tier counters and FROST depth metrics;
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

`docs/TESTING.md` records the quality baseline and required release gates.

## Reviewer architecture path

A technical reviewer should inspect these diagrams first:

1. `docs/diagrams/12_end_to_end_request_lifecycle.md`
2. `docs/diagrams/09_dmrf_control_plane_deep_dive.md`
3. `docs/diagrams/05_truth_engine_architecture.md`
4. `docs/diagrams/04_17_axis_coordinate_model.md`
5. `docs/diagrams/10_dsqp_persona_construction_architecture.md`
6. `docs/diagrams/07_data_storage_and_memory_architecture.md`
7. `docs/diagrams/06_local_first_security_model.md`
8. `docs/diagrams/11_frontend_product_surface_and_trace_review_map.md`
9. `docs/diagrams/08_testing_validation_and_release_governance.md`

Then inspect these implementation files:

1. `app.py`
2. `backend/dmrf/orchestrator.py`
3. `backend/dmrf/router.py`
4. `backend/dsqp/dsqp_chain.py`
5. `backend/truth_engine/api.py`
6. `backend/truth_engine/truth_core/engine.py`
7. `backend/truth_engine/truth_gate/gateway.py`
8. `backend/truth_engine/truth_memory/manager.py`
9. `backend/truth_engine/truth_link/bus.py`
10. `backend/storage/connection_manager.py`
11. `backend/storage/uskd_memory_graph.py`
12. `backend/memory/unified_memory_service.py`
13. `frontend/app/layout.tsx`
14. `frontend/components/layout/AppSidebar.tsx`
15. `.github/workflows/ci.yml`

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
