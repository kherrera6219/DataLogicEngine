# Data Flow Diagrams — DataLogicEngine

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-07-04 |
| Status | Active |
| Owner | Platform Architecture |
| Audience | Software engineers, architects, security reviewers, technical evaluators |
| Review cadence | Every 60 days |

## Purpose

Describe how data moves through DataLogicEngine across user interaction, API/security boundaries, DMRF, Truth Engine, DSQP, model/tool execution, storage, memory, trace/export, privacy, and observability.

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
    TRUTH --> DATA
    TRUTH --> PROVIDERS
    TRUTH --> MCP
    TRUTH --> EXPORT
    API --> OPS
    DATA --> OPS
```

---

## DFD-02: Top-level governed request flow

```mermaid
flowchart TD
    A[User prompt/action] --> B[Frontend runtime policy]
    B --> C[API request]
    C --> D[Auth/session/desktop local-auth]
    D --> E[CSRF/CORS/trusted-host/rate-limit checks]
    E --> F[DMRF InjectionDefense]
    F --> G{Allowed?}
    G -- No --> X[Block response + audit/trace]
    G -- Yes --> H[TruthGate]
    H --> I{Gate decision}
    I -- Block --> X
    I -- Allow or warn --> J[TierClassifier]
    J --> K[17-axis Router]
    K --> L[DSQP Personas]
    L --> M[TruthCore Plan]
    M --> N{External execution needed?}
    N -- LLM --> O[LLM Gateway]
    N -- Tool --> P[MCP Connector]
    N -- No --> Q[Local deterministic processing]
    O --> R[Provider response]
    P --> S[Tool result]
    R --> T[Evidence + Convergence]
    S --> T
    Q --> T
    T --> U{Finalize?}
    U -- Refine --> M
    U -- Yes --> V[Persist data/memory/audit]
    V --> W[Trace Explorer + export integrity]
    W --> Y[Response to user]
```

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
    REQ[Governed request] --> INJ[InjectionDefense]
    INJ --> TG[TruthGate]
    TG --> TIER[TierClassifier]
    TIER --> AX[17-axis route]
    AX --> DSQP[DSQP persona construction]
    DSQP --> TC[TruthCore]
    TC --> EV[EvidenceModel]
    TC --> CP[ConvergencePolicy]
    EV --> DEC{Converged?}
    CP --> DEC
    DEC -- No --> TC
    DEC -- Yes --> MEM[TruthMemory / UnifiedMemory]
    MEM --> LINK[TruthLink events]
    LINK --> TRACE[Trace record]
```

---

## DFD-05: Model/provider execution

```mermaid
flowchart TD
    PLAN[TruthCore execution plan] --> NEED{Need model call?}
    NEED -- No --> LOCAL[Local deterministic result]
    NEED -- Yes --> GW[LLM Gateway]
    GW --> CFG[Provider/model config]
    CFG --> KEY[Provider secret lookup]
    KEY --> REQ[Prompt + selected context + metadata]
    REQ --> PROVIDER[Configured AI provider]
    PROVIDER --> RESP[Provider response]
    RESP --> CHECK[Error/latency/usage handling]
    CHECK --> RETURN[Return to TruthCore]

    KEY -. never log raw secrets .-> SAFE[Secret hygiene]
```

Provider calls can transmit selected prompt/context data outside the local machine depending on configuration.

---

## DFD-06: MCP connector/tool execution

```mermaid
flowchart TD
    PLAN[TruthCore / API tool request] --> MCP[MCP registry]
    MCP --> SCOPE[Scope and tenant/user context checks]
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
    API[API / DMRF / Truth Engine] --> SQL[(SQLAlchemy DB\nSQLite/Postgres)]
    API --> REDIS[(Redis\ncache/session/rate-limit)]
    API --> NEO[(Neo4j\ngraph store)]
    API --> CHROMA[(ChromaDB\nvector store)]
    API --> OBJ[(Local Object Store\ndeliverables/audit/exports)]
    API --> USKD[(USKD RAM Graph\nNetworkX)]
    API --> UMEM[(UnifiedMemory\nJSON graph)]
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

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Replaced older Active Defense/QuadPersona/legacy layered diagrams with current DMRF, Truth Engine, DSQP, and 17-axis flow.
3. Added local-first desktop auth, provider execution, MCP connector, data/memory, trace/export, privacy, and support-bundle DFDs.
4. Added data classification and trust-boundary guidance.
