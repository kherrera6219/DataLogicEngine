# End-to-End Request Lifecycle

## Purpose

This is the single judge-facing walkthrough for how DataLogicEngine processes an AI request from user prompt to traceable, exportable evidence.

It connects the major subsystems already mapped in the earlier diagrams:

- Frontend product surface
- API/security envelope
- DMRF control plane
- 17-axis routing
- DSQP persona construction
- Truth Engine
- LLM Gateway
- Storage and memory systems
- Trace explorer
- Export integrity
- Observability and release evidence

The point of this diagram is simple:

> A DataLogicEngine request is not just prompt → model → answer. It is prompt → governed reasoning lifecycle → auditable result.

## Primary Code Paths

- `frontend/app/layout.tsx`
- `frontend/app/chat/`
- `frontend/components/Chat/`
- `frontend/lib/api/chat.ts`
- `frontend/lib/api/trace.ts`
- `app.py`
- `backend/dmrf/orchestrator.py`
- `backend/dmrf/models.py`
- `backend/dmrf/router.py`
- `backend/dsqp/dsqp_orchestrator.py`
- `backend/truth_engine/api.py`
- `backend/truth_engine/truth_gate/gateway.py`
- `backend/truth_engine/truth_core/engine.py`
- `backend/truth_engine/truth_memory/manager.py`
- `backend/truth_engine/truth_link/bus.py`
- `backend/llm_gateway/`
- `backend/storage/`
- `backend/memory/unified_memory_service.py`
- `backend/tracing/`
- `backend/security/export_integrity.py`

## Mermaid Lifecycle Diagram

```mermaid
flowchart TD
    User[User / Judge enters prompt]
    Chat[Frontend Chat UI\n/chat + components/Chat]
    ApiClient[Frontend API Client\nlib/api/chat.ts + base request + CSRF]
    ApiEnvelope[Flask API Envelope\napp.py]

    User --> Chat
    Chat --> ApiClient
    ApiClient --> ApiEnvelope

    subgraph SECURITY[API Security and Runtime Envelope]
        Auth[Auth / Session / Desktop Auto-Login]
        CSRF[CSRF + Origin Checks]
        CORS[CORS Allowlist]
        Hosts[Trusted Host Validation]
        RateLimit[Rate Limiting]
        Middleware[Security Middleware\ninput/request/error controls]
    end

    ApiEnvelope --> Auth
    Auth --> CSRF
    CSRF --> CORS
    CORS --> Hosts
    Hosts --> RateLimit
    RateLimit --> Middleware

    subgraph DMRF[DMRF Control Plane]
        DMRFStart[Create DMRFResult\nrun_id + query digest]
        Inject[InjectionDefense]
        Gate[TruthGate Adapter]
        Tier[TierClassifier]
        Axis[17-Axis Router\nAxisVector]
        DSQP[DSQP Persona Construction\nAxes 8-11]
        Plan[TruthCore Workflow Plan\nTier + Axis17]
        Evidence[EvidenceModel\nFreshness score]
        Converge[ConvergencePolicy\nRefine / Converged]
        Snapshots[FROST Step Snapshots]
    end

    Middleware --> DMRFStart
    DMRFStart --> Inject
    Inject --> Gate
    Gate --> Tier
    Tier --> Axis
    Axis --> DSQP
    DSQP --> Plan
    Plan --> Evidence
    Evidence --> Converge
    DMRFStart -. every step .-> Snapshots
    Inject -. snapshot .-> Snapshots
    Gate -. snapshot .-> Snapshots
    Tier -. snapshot .-> Snapshots
    Axis -. snapshot .-> Snapshots
    DSQP -. snapshot .-> Snapshots
    Plan -. snapshot .-> Snapshots
    Converge -. snapshot .-> Snapshots

    subgraph TRUTH[Truth Engine]
        TruthGate[TruthGate\nsecurity + budget + compliance]
        TruthCore[TruthCore\ntiered workflow execution]
        TruthMemory[TruthMemory\naudit + metrics + artifacts + explainability]
        TruthLink[TruthLink\nevent bus + Redis streams + SSE + DLQ]
    end

    Gate --> TruthGate
    Plan --> TruthCore
    Converge --> TruthMemory
    TruthMemory --> TruthLink

    subgraph MODEL[Model and Tool Execution]
        LLMGateway[LLM Gateway\nprovider selection + policy + telemetry]
        Provider[Model Provider\nOpenAI gpt-5.5 / Google gemini-3.1-pro-preview]
        MCP[MCP / External Tool Connectors]
    end

    TruthCore --> LLMGateway
    LLMGateway --> Provider
    TruthCore --> MCP

    subgraph DATA[Data, Memory, and Evidence Stores]
        SQL[SQL Store\nsessions + traces + artifacts + audit rows]
        Redis[Redis\ncache + session + queue + streams]
        Neo4j[Neo4j Graph Store]
        USKD[USKD NetworkX Memory Graph]
        Vector[ChromaDB Vector Store]
        ObjectStore[Object Store\ndeliverables + graphs + eval_data + audit logs]
        UnifiedMemory[UnifiedMemoryService\nstructured reasoning memory]
    end

    Axis --> Neo4j
    Axis --> USKD
    TruthCore --> Vector
    TruthCore --> UnifiedMemory
    TruthMemory --> SQL
    TruthMemory --> Redis
    TruthMemory --> ObjectStore
    DSQP --> ObjectStore
    TruthLink --> Redis
    Snapshots --> ObjectStore

    subgraph RESPONSE[Response and Review Surfaces]
        Result[DMRFResult / TruthCore Result\nanswer + tier + axis vector + steps + personas + convergence + warnings]
        FrontendResult[Frontend Detailed Response View]
        Runs[Trace Explorer\n/runs + /runs/view]
        Graph[Graph / Knowledge Browser]
        Monitor[Truth Engine Monitor]
    end

    Provider --> Result
    MCP --> Result
    Converge --> Result
    Result --> FrontendResult
    Result --> Runs
    Axis --> Graph
    TruthLink --> Monitor

    subgraph EXPORT[Export and Integrity]
        TraceBundle[Trace / Run Export Bundle]
        SectionHashes[Section Hashes]
        BundleHash[Bundle SHA-256]
        Signature[Optional HMAC-SHA256 Signature]
        Encryption[Optional Fernet Encryption]
        Manifest[Integrity Manifest]
        Auditor[Judge / Auditor Review]
    end

    Runs --> TraceBundle
    TraceBundle --> SectionHashes
    TraceBundle --> BundleHash
    BundleHash --> Manifest
    Signature --> Manifest
    Encryption --> Manifest
    Manifest --> Auditor
```

## Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Judge
    participant FE as Frontend Chat UI
    participant API as Flask API Envelope
    participant DMRF as DMRF Orchestrator
    participant TG as TruthGate
    participant AX as 17-Axis Router
    participant DSQP as DSQP
    participant TC as TruthCore
    participant LLM as LLM Gateway / Provider
    participant MEM as TruthMemory / UnifiedMemory
    participant TL as TruthLink
    participant TRACE as Trace Explorer / Export

    User->>FE: Enter prompt
    FE->>API: Submit request with session/CSRF/runtime context
    API->>API: Auth, CSRF, CORS, trusted host, rate limit, middleware checks
    API->>DMRF: Start governed reasoning lifecycle

    DMRF->>DMRF: Create run_id and DMRFResult
    DMRF->>DMRF: InjectionDefense.detect()
    alt Injection blocked
        DMRF-->>API: ok=false + blocked warning
        API-->>FE: Safe blocked response
        FE-->>User: Show policy/safety response
    else Injection passes
        DMRF->>TG: TruthGate evaluate query/context
        alt TruthGate blocked
            TG-->>DMRF: block_reason + security flags
            DMRF-->>API: ok=false + gate warning
            API-->>FE: Governed block response
        else TruthGate passes
            DMRF->>DMRF: Classify tier
            DMRF->>AX: Route into 17-axis AxisVector
            DMRF->>DSQP: Build persona axes 8-11
            DMRF->>TC: Select TruthCore workflow from tier + Axis17
            TC->>MEM: Recall relevant memory / graph context
            TC->>LLM: Execute model/tool steps when required
            LLM-->>TC: Model/tool output
            TC->>MEM: Record layer/session/artifact/audit data
            DMRF->>DMRF: Score evidence freshness + convergence
            DMRF->>TL: Publish completed event/export bundle
            TL-->>FE: Optional real-time status/SSE event
            DMRF-->>API: DMRFResult / traceable result bundle
            API-->>FE: Answer + trace metadata
            FE-->>User: Display answer and evidence/trace link
            User->>TRACE: Open run / export trace
            TRACE->>TRACE: Build export manifest + hashes/signature/encryption options
            TRACE-->>User: Download/review integrity-protected bundle
        end
    end
```

## Lifecycle Stages

| Stage | Code area | Output |
|---:|---|---|
| 1 | `frontend/app/chat/`, `frontend/components/Chat/` | User prompt and UI context. |
| 2 | `frontend/lib/api/` | API request with CSRF/session handling. |
| 3 | `app.py` | Authenticated, rate-limited, middleware-screened backend request. |
| 4 | `backend/dmrf/orchestrator.py` | `DMRFResult` with run ID and lifecycle state. |
| 5 | `backend/dmrf/injection_defense.py` | Safe/blocked injection-defense result. |
| 6 | `backend/dmrf/truth_integration/gate_adapter.py`, `backend/truth_engine/truth_gate/` | TruthGate evaluation, flags, budget, compliance. |
| 7 | `backend/dmrf/tier_classifier.py` | Five-tier classification. |
| 8 | `backend/dmrf/router.py`, `core/axes/` | 17-axis `AxisVector`. |
| 9 | `backend/dsqp/` | Persona profiles for axes 8-11. |
| 10 | `backend/truth_engine/truth_core/engine.py` | Workflow plan and layer execution. |
| 11 | `backend/llm_gateway/`, `backend/mcp_server/` | Model/tool execution when needed. |
| 12 | `backend/dmrf/evidence_model.py`, `backend/dmrf/convergence_policy.py` | Evidence freshness and convergence/refinement decision. |
| 13 | `backend/truth_engine/truth_memory/`, `backend/memory/` | Audit, artifacts, metrics, explainability, structured memory. |
| 14 | `backend/truth_engine/truth_link/` | Completion/event publication. |
| 15 | `backend/tracing/`, `frontend/app/runs/` | Trace explorer and run detail review. |
| 16 | `backend/security/export_integrity.py` | Integrity-protected export manifest. |

## What Makes This Different From a Wrapper

A simple wrapper usually has this lifecycle:

```text
prompt → model → response
```

DataLogicEngine has this lifecycle:

```text
prompt
  → auth/security/middleware
  → injection defense
  → TruthGate
  → tier classification
  → 17-axis routing
  → DSQP persona construction
  → TruthCore workflow planning
  → evidence freshness scoring
  → convergence policy
  → model/tool execution when required
  → memory/audit/artifact persistence
  → event publication
  → frontend trace review
  → integrity-protected export
```

## Judge Review Path

To verify this lifecycle, inspect:

1. `frontend/app/layout.tsx` and `frontend/app/chat/` — product entry and chat surface.
2. `frontend/lib/api/index.ts`, `frontend/lib/api/chat.ts`, `frontend/lib/api/trace.ts` — frontend request and trace export clients.
3. `app.py` — backend security and API route envelope.
4. `backend/dmrf/orchestrator.py` — the main lifecycle controller.
5. `backend/dmrf/models.py` — result, step, axis vector, and export bundle structures.
6. `backend/truth_engine/truth_gate/gateway.py` — gate/security/budget/compliance behavior.
7. `backend/dmrf/router.py` and `core/axes/` — 17-axis routing.
8. `backend/dsqp/` — persona construction.
9. `backend/truth_engine/truth_core/engine.py` — workflow selection and execution.
10. `backend/storage/`, `backend/memory/`, `backend/truth_engine/truth_memory/` — persistence and memory layers.
11. `backend/truth_engine/truth_link/bus.py` — event publication and streaming.
12. `backend/security/export_integrity.py` — trace export authenticity.
13. `frontend/app/runs/` — user-facing trace review.

## Interpretation

This request lifecycle is the clearest end-to-end explanation of DataLogicEngine. It shows how a user action becomes a governed, routed, reasoned, persisted, observable, and exportable AI event.

For a contest or technical evaluation, this is the diagram to put first when someone asks:

> What does the system actually do?
