# Data Flow Diagrams — DataLogicEngine

## Document metadata

| Field | Value |
|---|---|
| Document version | v3.1.0 |
| Last updated | 2026-07-13 |
| Status | Active |
| Owner | Platform Architecture |
| Audience | Software engineers, architects, security reviewers, technical evaluators |
| Review cadence | Every 60 days |

## Purpose

Describe how data moves through the Phase 5 `governed.v1` contract, one causal
orchestrator, provider boundary, transactional trace, storage, privacy, and
observability surfaces.

These diagrams are source-of-truth data-flow references for the current architecture. Archived whitepapers may contain older exploratory diagrams and should not override this document.

## Related documents

1. `docs/ARCHITECTURE.md`
2. `docs/ARCHITECTURE_MAP.md`
3. `docs/WORKFLOW.md`
4. `docs/DATABASE_SCHEMA.md`
5. `docs/SECURITY.md`
6. `docs/PRIVACY_POLICY.md`
7. `docs/diagrams/12_end_to_end_request_lifecycle.md`
8. `docs/diagrams/07_data_storage_and_memory_architecture.md`

---

## Data classification reference

| Class | Examples | Handling guidance |
|---|---|---|
| User content | prompts, uploaded files, notes, project data | local-first by default; may be sent to providers/connectors only when configured/required. |
| Identity/session data | username, email, session, desktop auth metadata | protect with auth/session controls and avoid leaking to traces/logs. |
| Provider secrets | API keys, tokens, connector credentials | store through configured secret paths; never log raw values. |
| AI trace data | stages, evidence, claims, personas, policy decisions | audit/review value; may include sensitive context; protect export paths. |
| Operational telemetry | metrics, latency, errors, health, readiness | sanitize where needed; use for reliability and release evidence. |
| Export bundles | trace/data exports, manifests, hashes, signatures | integrity protected; user/admin controls govern sharing. |

---

## DFD-01: System context

```mermaid
flowchart LR
    USER([User / Analyst])
    ADMIN([Admin / Operator])
    DESKTOP[Windows Desktop\nElectron]
    BROWSER[Browser UI\nNext.js]
    API[Flask API\nSecurity Envelope]
    DMRF[DMRF Control Plane]
    TRUTH[Truth Engine\nTruthGate / TruthCore / TruthMemory / TruthLink]
    DATA[(Local / App-Owned Stores\nSQL / Redis / Neo4j / Chroma / Object / Memory)]
    PROVIDERS[AI Providers\nOpenAI / Google Gemini]
    MCP[MCP Connectors / External Tools]
    EXPORT[Trace Export / Privacy Export]
    OPS[Metrics / Logs / Support Bundles]

    USER --> DESKTOP
    USER --> BROWSER
    ADMIN --> BROWSER
    DESKTOP --> API
    BROWSER --> API
    API --> DMRF
    DMRF --> TRUTH
    TRUTH --> PROVIDERS
    TRUTH --> MCP
    DMRF --> DATA
    DATA --> EXPORT
    API --> OPS
    DATA --> OPS
```

---

## DFD-02: Top-level governed request flow

```mermaid
flowchart TD
    A[Authenticated prompt/action] --> B[GovernedRequest governed.v1]
    B --> C[Admission and cancellation]
    C --> D{Simulation?}
    D -- Yes --> X[Phase 10 unavailable result]
    D -- No --> E[DMRF defense, TruthGate, tier, axes]
    E --> F{Allowed?}
    F -- No --> Y[Policy-blocked result]
    F -- Yes --> G[Bounded source-identified retrieval]
    G --> H[Deterministic DSQP]
    H --> I[TruthCore and required KA preflight]
    I --> J[One policy/evidence/persona/KA prompt]
    J --> K[Bounded provider execution]
    K --> L[Output, claim, citation, policy validation]
    L --> M[Transactional run and trace persistence]
    X --> M
    Y --> M
    M --> N[GovernedResult and stable trace ID]
```

Every mode uses the same trace ID from request admission through persisted run,
stage, evidence, claim, KA, persona, policy, API, and UI state. The SDK consumes
the service result and does not add or reconstruct execution stages.

---

## DFD-03: Desktop local-auth and runtime policy

```mermaid
flowchart TD
    E[Electron desktop runtime] --> P[Runtime policy]
    P --> L{Local/hybrid mode?}
    L -- Yes --> R[Loopback request]
    R --> S[Install secret lookup]
    S --> N[Nonce challenge]
    N --> H[HMAC signature]
    H --> T[Timestamp skew validation]
    T --> C[Constant-time comparison]
    C --> A{Accepted?}
    A -- Yes --> API[API request proceeds]
    A -- No --> DENY[Reject request]
    L -- No --> WEB[Web/session auth required]

    S --> DPAPI[DPAPI helper where available]
```

Desktop local-auth data must not be treated as a public cloud/web trust boundary.

---

## DFD-04: DMRF and Truth Engine internal flow

```mermaid
flowchart TD
    REQ[GovernedRequest] --> INJ[InjectionDefense]
    INJ --> TG[TruthGate]
    TG --> TIER[TierClassifier]
    TIER --> AX[17-axis route]
    AX --> RET[Bounded retrieval]
    RET --> DSQP[Deterministic DSQP context]
    DSQP --> TC[TruthCore selection and KA preflight]
    TC --> PROMPT[Approved provider prompt]
    PROMPT --> VALIDATE[Output/claim/citation validation]
    VALIDATE --> TRACE[Transactional trace persistence]
```

---

## DFD-05: Model/provider execution

```mermaid
flowchart TD
    PLAN[Canonical orchestrator] --> NEED{Provider answer allowed/needed?}
    NEED -- No --> LOCAL[Local review or explicit failure]
    NEED -- Yes --> PROMPT[Construct approved prompt]
    PROMPT --> GW[LLM Gateway provider boundary]
    GW --> CFG[Provider/model config]
    CFG --> KEY[Provider secret lookup]
    KEY --> REQ[Prompt + selected context + metadata]
    REQ --> PROVIDER[Configured AI provider]
    PROVIDER --> RESP[Provider response]
    RESP --> CHECK[Error/latency/usage handling]
    CHECK --> RETURN[Return to canonical validator]

    KEY -. never log raw secrets .-> SAFE[Secret hygiene]
```

Provider calls can transmit selected prompt/context data outside the local machine depending on configuration.

---

## DFD-06: MCP connector/tool execution

```mermaid
flowchart TD
    PLAN[TruthCore / API tool request] --> MCP[MCP registry]
    MCP --> SCOPE[Scope and authenticated-principal/local-profile checks]
    SCOPE --> VALIDATE[Request contract validation]
    VALIDATE --> OUTBOUND[Outbound/tool call]
    OUTBOUND --> EXT[External service]
    EXT --> RESULT[Tool result]
    RESULT --> CONTRACT[Response contract validation]
    CONTRACT --> TRACE[Trace/audit/metrics]
    TRACE --> RETURN[Return to workflow]

    SCOPE -->|Denied| DENY[Policy denial + audit]
```

Connector data handling depends on connector scopes, external service policy, and user/admin configuration.

---

## DFD-07: Data, memory, and artifact flow

```mermaid
flowchart LR
    API[Governed orchestrator and application APIs] --> SQL[(PostgreSQL\nrelational authority)]
    API --> REDIS[(Redis\ncache/session/rate-limit)]
    API --> NEO[(Neo4j\ngraph store)]
    API --> CHROMA[(ChromaDB\nvector store)]
    API --> OBJ[(App-owned S3 contract\ndeliverables/audit/exports)]
    API --> USKD[(USKD RAM Graph\nNetworkX)]
    API --> UMEM[(Bounded working memory\nmaterialized state)]
    API --> TMEM[(TruthMemory\naudit/explainability)]

    OBJ --> EXPORT[Export bundle / manifest]
    TMEM --> TRACE[Trace Explorer]
    UMEM --> TRACE
```

Local-first storage does not mean air-gapped operation. Providers/connectors/export flows can move selected data externally.

---

## DFD-08: Trace and export integrity flow

```mermaid
flowchart TD
    RUN[Run / trace data] --> SECTIONS[Trace sections\nevidence / claims / policy / personas]
    SECTIONS --> HASH[Section hashes]
    HASH --> BUNDLE[Bundle hash]
    BUNDLE --> MANIFEST[Export manifest]
    MANIFEST --> OPTSIG{HMAC enabled?}
    OPTSIG -- Yes --> SIG[HMAC signature]
    OPTSIG -- No --> NOSIG[Unsigned manifest]
    MANIFEST --> OPTENC{Encryption enabled?}
    OPTENC -- Yes --> ENC[Encrypted payload envelope]
    OPTENC -- No --> PLAIN[Plain export payload]
    SIG --> OUT[User/admin export]
    NOSIG --> OUT
    ENC --> OUT
    PLAIN --> OUT
```

Exported files may leave the application boundary after download and should be handled according to privacy/security policy.

---

## DFD-09: Privacy export/delete flow

```mermaid
flowchart TD
    USER[Owner privacy action] --> AUTH[Auth/session/single-owner check]
    AUTH --> ACTION{Export or delete?}
    ACTION -- Export --> COLLECT[Collect eligible user data]
    COLLECT --> REDACT[Redact/sanitize where configured]
    REDACT --> PACKAGE[Package JSON/export bundle]
    PACKAGE --> MANIFEST[Hash/manifest]
    MANIFEST --> DOWNLOAD[User download]

    ACTION -- Delete --> SCOPE[Resolve deletion scope]
    SCOPE --> APPLY[Delete/anonymize eligible data]
    APPLY --> AUDIT[Audit deletion event]
    AUDIT --> CONFIRM[Confirmation]
```

Deletion behavior may be constrained by backup, audit, legal, security, or deployment retention policy.

---

## DFD-10: Observability and support bundle flow

```mermaid
flowchart TD
    APP[Application runtime] --> METRICS[/metrics]
    APP --> LOGS[Runtime logs]
    APP --> ERRORS[Error records / crash IDs]
    APP --> TRACE[Trace/audit records]
    METRICS --> OPS[Operator review]
    LOGS --> SUPPORT[Support bundle generator]
    ERRORS --> SUPPORT
    TRACE --> SUPPORT
    SUPPORT --> SANITIZE[Sanitize/redact]
    SANITIZE --> BUNDLE[Support bundle artifact]
```

Support bundles must avoid raw secrets and should be treated as sensitive operational artifacts.

---

## Primary trust boundaries

1. Client/browser/Electron renderer boundary.
2. Desktop local-auth boundary.
3. API/security envelope boundary.
4. Provider/model boundary.
5. MCP connector/external tool boundary.
6. Local data-store boundary.
7. Trace/export boundary.
8. Operational logs/support bundle boundary.

## DFD-09: Client Gateway admission and durable result flow

```mermaid
flowchart LR
    CLIENT[Approved application with ukg key] --> CONTRACT[Strict dle-gateway.v1 contract]
    CONTRACT --> PG[(PostgreSQL client policy idempotency jobs virtual models)]
    CONTRACT --> REDIS[(Redis atomic limits concurrency job lease cancel state)]
    PG --> GOV[Canonical governed orchestrator]
    REDIS --> GOV
    GOV --> SYNC[Sync governed result]
    GOV --> SSE[Live stages then validated output]
    GOV --> JOB[Encrypted durable job result]
    JOB --> SMALL[(PostgreSQL encrypted small result)]
    JOB --> LARGE[(MinIO gateway-results encrypted large result)]
    LARGE --> VERIFY[Hash verification before authorized release]
    GOV --> TRACE[Client-owned redacted trace summary]
```

Provider keys and all internal service credentials remain outside the client
boundary. Private network ingress remains disabled pending qualification.

## Change notes for v3.1.0

1. Added the Client Gateway contract, PostgreSQL/Redis/MinIO responsibility,
   validated-output SSE, durable result, and owned trace flow.

## Change notes for v3.0.0

1. Replaced plan-only refinement/convergence flow with the implemented
   `governed.v1` causal lifecycle and transactional trace boundary.
2. Corrected the SDK, simulation, confidence, and production-store data flows.

## Change notes for v2.7.0

1. Replaced stale tenant/user MCP scope wording with authenticated-principal/local-profile checks.
2. Updated metadata for the production top-level documentation review.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Replaced older Active Defense/QuadPersona/legacy layered diagrams with current DMRF, Truth Engine, DSQP, and 17-axis flow.
3. Added local-first desktop auth, provider execution, MCP connector, data/memory, trace/export, privacy, and support-bundle DFDs.
4. Added data classification and trust-boundary guidance.
