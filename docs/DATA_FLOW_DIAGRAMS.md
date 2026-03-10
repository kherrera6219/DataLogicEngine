# Data Flow Diagrams — DataLogicEngine

**Document Control**

| Field | Value |
|-------|-------|
| Owner | Platform Architecture |
| Last Updated | March 2026 |
| Status | Active |
| Audience | Software engineers, architects, technical reviewers |
| Review Cadence | Every 60 days |

---

## Table of Contents

1. [Overview](#overview)
2. [DFD-01: System Context (Level 0)](#dfd-01-system-context-level-0)
3. [DFD-02: Top-Level Data Flows (Level 1)](#dfd-02-top-level-data-flows-level-1)
4. [DFD-03: Chat Message — End-to-End Flow (Level 2)](#dfd-03-chat-message--end-to-end-flow-level-2)
5. [DFD-04: LLM Gateway and Provider Routing](#dfd-04-llm-gateway-and-provider-routing)
6. [DFD-05: Security Data Flow](#dfd-05-security-data-flow)
7. [DFD-06: MCP Connector Execution Flow](#dfd-06-mcp-connector-execution-flow)
8. [DFD-07: Knowledge Graph Write Flow](#dfd-07-knowledge-graph-write-flow)
9. [DFD-08: Audit and Observability Flow](#dfd-08-audit-and-observability-flow)
10. [DFD-09: Secret Resolution Flow (Startup)](#dfd-09-secret-resolution-flow-startup)
11. [Data Classification Reference](#data-classification-reference)

---

## Overview

These data flow diagrams describe how data moves through DataLogicEngine at multiple levels of abstraction. They follow the Yourdon-DeMarco DFD notation adapted for Mermaid rendering:

- **Rectangles** — External entities (users, external systems)
- **Rounded boxes** — Processes (internal transformation steps)
- **Cylinders / DB icons** — Data stores
- **Arrows** — Data flows with labels

---

## DFD-01: System Context (Level 0)

This diagram shows DataLogicEngine as a single system with its external entities.

```mermaid
graph LR
    U([Human User\nBrowser / Desktop])
    ADMIN([Administrator\nBrowser])
    OIDC([Azure AD / OIDC\nIdentity Provider])
    AI_PROVIDER([AI Providers\nOpenAI · Anthropic · Gemini · Grok])
    MCP_EXT([External Systems\nJira · Salesforce · Custom APIs])
    SENTRY([Sentry\nCrash Reporting])
    SIEM([SIEM\nSecurity Event Stream])

    U -->|"Chat messages, queries,\nproject actions"| DLE[DataLogicEngine]
    ADMIN -->|"User management,\nconfiguration, audit review"| DLE
    DLE -->|"AI responses, run traces,\ngraph visualizations"| U
    DLE -->|"Admin dashboard, audit logs,\nsystem health"| ADMIN

    DLE <-->|"SSO token exchange"| OIDC
    DLE -->|"LLM inference requests"| AI_PROVIDER
    AI_PROVIDER -->|"Completions, embeddings"| DLE
    DLE <-->|"Tool calls, data fetch"| MCP_EXT
    DLE -->|"Exception reports"| SENTRY
    DLE -->|"Security events (Syslog)"| SIEM
```

---

## DFD-02: Top-Level Data Flows (Level 1)

This diagram decomposes the system into its six major processing subsystems.

```mermaid
graph TD
    U([User])
    ADMIN([Admin])

    subgraph DataLogicEngine
        GW[1.0\nAPI Gateway\nFlask 3.1]
        SEC[2.0\nSecurity Layer\nRBAC · MFA · Active Defense]
        KE[3.0\nKnowledge Engine\n17-Axis · KAs · Graph]
        TE[4.0\nTruth Engine\n5-Tier Reasoning]
        LLMGW[5.0\nLLM Gateway\nProvider Routing]
        MCP[6.0\nMCP Server\nExternal Connectors]
    end

    DB[(PostgreSQL\nPrimary Store)]
    REDIS[(Redis\nCache · Sessions · Queue)]
    NEO4J[(Neo4j\nGraph DB)]
    CHROMA[(ChromaDB\nVector Store)]

    U -->|"HTTP/WSS Request"| GW
    ADMIN -->|"Admin HTTP Request"| GW

    GW -->|"Authenticated request"| SEC
    SEC -->|"Authorized request\n+ user context"| KE
    KE -->|"Enriched query\n+ knowledge coords"| TE
    TE -->|"Structured prompt\n+ tier config"| LLMGW
    TE -->|"Tool call request"| MCP

    LLMGW -->|"Inference request"| AI_PROVIDER([AI Providers])
    AI_PROVIDER -->|"Completion"| LLMGW

    MCP -->|"Scoped API call"| EXT_SYS([External Systems])
    EXT_SYS -->|"Tool result"| MCP

    LLMGW -->|"Final answer"| TE
    MCP -->|"Tool result"| TE
    TE -->|"Verified response"| KE
    KE -->|"Response + trace"| GW
    GW -->|"HTTP Response"| U

    KE <-->|"Read/write nodes"| DB
    KE <-->|"Graph queries"| NEO4J
    KE <-->|"Vector search"| CHROMA
    SEC <-->|"Session data"| REDIS
    TE <-->|"Audit events"| DB
    GW <-->|"Rate limit counters"| REDIS
```

---

## DFD-03: Chat Message — End-to-End Flow (Level 2)

This is the most important flow. It traces a single chat message from the user through all processing layers and back.

```mermaid
graph TD
    START([User submits\nchat message])

    subgraph "Layer 1 — API Gateway (app.py)"
        MW1[Correlation ID\ninjection]
        MW2[Rate limit\ncheck]
        MW3[CSRF token\nvalidation]
        MW4[Security headers\napplication]
    end

    subgraph "Layer 2 — Security Gate (backend/security/)"
        AUTH[Session /\nJWT validation]
        RBAC_CHK[RBAC permission\ncheck\nMCP_EXECUTE or UKG_READ]
        MFA_CHK{MFA\nrequired?}
        ACTIVE_DEF[Active Defense\nSupervisor LLM\nassesses intent]
        VERDICT{Threat\nscore < 0.7?}
        HONEYPOT[Route to\nhoneypot sandbox]
    end

    subgraph "Layer 3 — Knowledge Engine (core/)"
        COORD[Resolve 17-axis\nknowledge coordinate]
        KA_SELECT[Select applicable\nKnowledge Algorithms]
        GRAPH_ENR[Enrich with\ngraph context\nNeo4j / Postgres]
        VECTOR_RTR[Vector retrieval\nChromaDB RAG]
    end

    subgraph "Layer 4 — Truth Engine (backend/truth_engine/)"
        TIER_SELECT[Tier classifier\ntrivial/moderate/high_stakes\nextreme/autonomous]
        REFINEMENT[Refinement\norchestrator\n10 possible steps]
        PERSONA[QuadPersona\nfour-perspective\nreasoning]
        TRUST_GATE[TruthGate\nbudget + compliance\nvalidation]
        META[Meta-reasoning\ncontroller]
        SAFETY[Final safety\ngate]
    end

    subgraph "Layer 5 — LLM Gateway (backend/llm_gateway/)"
        PROFILE[Model profile\nselection]
        CIRCUIT{Circuit\nbreaker\nopen?}
        PROVIDER_CALL[Primary provider\nAPI call]
        FAILOVER[Failover to\nnext provider]
        LATENCY[Record latency\np50/p95/p99]
    end

    subgraph "Layer 6 — Connectors (backend/mcp_server/)"
        MCP_SCOPE[Scope\nenforcement]
        MCP_CALL[Tool execution]
        MCP_VALIDATE[Result\ncontract validation]
        MCP_METRICS[Record connector\nlatency metrics]
    end

    subgraph "Layer 8 — Observability"
        AUDIT[Write audit\nhash-chain entry]
        TRACE[Write run\ntrace record]
        METRICS[Emit Prometheus\nmetrics]
    end

    RESP([Return response\nto user])

    START --> MW1 --> MW2 --> MW3 --> MW4
    MW4 --> AUTH
    AUTH -->|"Valid session"| RBAC_CHK
    AUTH -->|"Invalid"| E401[401 Unauthorized]

    RBAC_CHK -->|"Permitted"| MFA_CHK
    RBAC_CHK -->|"Denied"| E403[403 Forbidden]

    MFA_CHK -->|"Required + verified"| ACTIVE_DEF
    MFA_CHK -->|"Not required"| ACTIVE_DEF
    MFA_CHK -->|"Required + missing"| E403

    ACTIVE_DEF --> VERDICT
    VERDICT -->|"Safe"| COORD
    VERDICT -->|"Threat detected"| HONEYPOT
    HONEYPOT -->|"Sandboxed\ndecoy response"| RESP

    COORD --> KA_SELECT --> GRAPH_ENR --> VECTOR_RTR
    VECTOR_RTR --> TIER_SELECT

    TIER_SELECT -->|"trivial"| SAFETY
    TIER_SELECT -->|"moderate"| PERSONA
    TIER_SELECT -->|"high_stakes+"| REFINEMENT

    REFINEMENT --> PERSONA --> TRUST_GATE --> META --> SAFETY
    PERSONA --> TRUST_GATE

    SAFETY -->|"Approved"| PROFILE
    SAFETY -->|"Blocked"| E422[Safety block\nerror response]

    PROFILE --> CIRCUIT
    CIRCUIT -->|"Closed"| PROVIDER_CALL
    CIRCUIT -->|"Open"| FAILOVER
    PROVIDER_CALL -->|"Success"| LATENCY
    PROVIDER_CALL -->|"Error"| FAILOVER
    FAILOVER --> PROVIDER_CALL
    LATENCY --> MCP_SCOPE

    MCP_SCOPE -->|"Scopes valid"| MCP_CALL
    MCP_SCOPE -->|"No tool call needed"| AUDIT
    MCP_CALL --> MCP_VALIDATE --> MCP_METRICS --> AUDIT

    AUDIT --> TRACE --> METRICS --> RESP
```

---

## DFD-04: LLM Gateway and Provider Routing

```mermaid
graph TD
    REQ[Gateway Request\nGatewayRequest dataclass]

    subgraph "backend/llm_gateway/gateway.py"
        PROFILE_SEL{Task profile?}
        CODE_P[code → Codestral]
        ANALYSIS_P[analysis → Claude 3.5 Sonnet]
        LONG_P[long_context → Gemini 1.5 Pro]
        REASON_P[reasoning → Grok 4 Fast]
        DEFAULT_P[default → GPT-4o]

        UKG_PIPE{run_ukg_pipeline\n= true?}
        UKG[UKG SDK Pipeline\nCoordinateResolver17\nKAExecutor\nUKGOverlay]

        GOV[AIGovernanceEngine\ntoken limits · content policy]

        CIRCUIT{Circuit breaker\nstate?}
        P1[Primary provider\nAPI call]
        P2[Secondary provider\nfailover]
        P3[Tertiary provider\nfailover]
        ERR[All providers failed\nreturn structured error]

        USAGE[Log LLMProviderUsage\nto database]
        LATENCY_M[Record latency metrics\nbackend/llm_gateway/latency_metrics.py]
    end

    DB_PROV[(LLMProvider\nDB table\nencrypted API keys)]
    DB_USAGE[(LLMProviderUsage\nDB table)]

    REQ --> PROFILE_SEL
    PROFILE_SEL --> CODE_P & ANALYSIS_P & LONG_P & REASON_P & DEFAULT_P

    CODE_P & ANALYSIS_P & LONG_P & REASON_P & DEFAULT_P --> UKG_PIPE
    UKG_PIPE -->|"Yes"| UKG --> GOV
    UKG_PIPE -->|"No"| GOV

    DB_PROV -->|"Encrypted key\ndecrypted at call time"| GOV

    GOV --> CIRCUIT
    CIRCUIT -->|"Closed (healthy)"| P1
    CIRCUIT -->|"Open (tripped)"| P2
    P1 -->|"Success"| USAGE
    P1 -->|"Error/timeout"| P2
    P2 -->|"Success"| USAGE
    P2 -->|"Error"| P3
    P3 -->|"Success"| USAGE
    P3 -->|"Error"| ERR

    USAGE --> DB_USAGE
    USAGE --> LATENCY_M
```

---

## DFD-05: Security Data Flow

```mermaid
graph TD
    REQ([Incoming HTTP Request])

    subgraph "Middleware Stack (app.py)"
        CID[Inject Correlation ID\nX-Correlation-ID header]
        RL[Rate Limiter\nFlask-Limiter · per-IP · per-user]
        CSRF_MW[CSRF Middleware\nFlask-WTF token check]
        SSRF_MW[SSRF Guard\nbackend/api_gateway/\nAllowlist enforcement]
        SEC_HDRS[Security Headers\nHSTS · CSP · X-Frame-Options\nX-Content-Type-Options]
    end

    subgraph "Authentication (backend/auth/)"
        SESSION_CHK{Valid session\nor JWT?}
        OIDC_FLOW[OIDC / Azure AD\ntoken validation]
        LOCAL_AUTH[Local session\ncookie validation]
        DESKTOP_AUTH[Desktop no-login\nSID mapping]
    end

    subgraph "Authorization (backend/security/rbac.py)"
        PERM_CHK{Has required\nPermission?}
        ROLE_LOOKUP[Look up user role\nand permissions]
        AUDIT_ACCESS[Write access\ndecision to audit log]
    end

    subgraph "Active Defense (backend/security/active_defense.py)"
        SUPERVISOR[Supervisor LLM\nassesses intent]
        THREAT_SCORE{threat_score\n< 0.7?}
        HONEYPOT_R[HoneypotRouter\nsandboxed response]
        INJECTION[PromptInjectionShield\npreprocessor sanitization]
    end

    subgraph "Tenant Isolation (backend/security/tenant_rls.py)"
        RLS[Set Postgres\nSESSION tenant_id\nbefore every query]
    end

    subgraph "Data Stores"
        AUDIT_DB[(AuditLog\nhash-chained)]
        SEC_EVENTS[(SecurityEvent\ntable)]
        REDIS_SESS[(Redis\nsession store)]
        PII_DB[(Encrypted PII\nPostgres columns)]
    end

    SIEM([SIEM\nSyslog export])

    REQ --> CID --> RL
    RL -->|"Under limit"| CSRF_MW
    RL -->|"Over limit"| E429[429 Too Many Requests]

    CSRF_MW -->|"Valid"| SSRF_MW --> SEC_HDRS --> SESSION_CHK

    SESSION_CHK -->|"Web/JWT"| LOCAL_AUTH
    SESSION_CHK -->|"OIDC"| OIDC_FLOW
    SESSION_CHK -->|"Desktop"| DESKTOP_AUTH
    SESSION_CHK -->|"None"| E401[401 Unauthorized]

    LOCAL_AUTH & OIDC_FLOW & DESKTOP_AUTH --> ROLE_LOOKUP
    ROLE_LOOKUP --> PERM_CHK
    PERM_CHK -->|"Denied"| E403[403 Forbidden]
    PERM_CHK -->|"Granted"| AUDIT_ACCESS
    AUDIT_ACCESS --> INJECTION
    AUDIT_ACCESS --> AUDIT_DB

    INJECTION --> SUPERVISOR --> THREAT_SCORE
    THREAT_SCORE -->|"Safe"| RLS
    THREAT_SCORE -->|"Threat"| HONEYPOT_R
    HONEYPOT_R --> SEC_EVENTS

    RLS -->|"Tenant context set"| APP_LOGIC[Application Logic\nall queries auto-filtered\nby tenant_id]
    APP_LOGIC --> PII_DB

    SEC_EVENTS --> SIEM
    AUDIT_DB --> SIEM

    REDIS_SESS <-->|"Session read/write"| SESSION_CHK
```

---

## DFD-06: MCP Connector Execution Flow

```mermaid
graph TD
    TE_REQ([Truth Engine\ntool call request])

    subgraph "backend/mcp_server/"
        ROUTER[MCP Router\nrouter.py\nRoute to connector]
        SCOPE_ENF[Scope Enforcer\nscope_enforcement.py\nVerify OAuth scopes]
        OAUTH[OAuth Manager\noauth_manager.py\nGet/refresh token]
        REGISTRY[Tool Registry\nregistry.py\nResolve tool function]
        CONTRACT[Contract Validator\ncontract_validation.py\nValidate input schema]
        EXEC[Tool Execution\nrun the function]
        RESULT_VAL[Result Validator\ncontract_validation.py\nValidate output schema]
        METRICS[Connector Metrics\nconnector_metrics.py\nRecord p50/p95/p99]
    end

    DB_CONN[(MCPConnector\nDB table\ncredentials encrypted)]
    DB_TOKEN[(MCPOAuthToken\nDB table)]
    EXT_API([External System\nJira · Salesforce · Custom])

    TE_REQ --> ROUTER
    ROUTER --> DB_CONN
    DB_CONN -->|"Connector config"| SCOPE_ENF

    SCOPE_ENF -->|"Scopes insufficient"| E403[403 Scope denied]
    SCOPE_ENF -->|"Scopes OK"| OAUTH

    OAUTH --> DB_TOKEN
    DB_TOKEN -->|"Valid token"| REGISTRY
    DB_TOKEN -->|"Expired token"| REFRESH[Token refresh\n→ EXT_API /oauth/token]
    REFRESH --> DB_TOKEN

    REGISTRY --> CONTRACT
    CONTRACT -->|"Schema invalid"| E422[422 Contract violation]
    CONTRACT -->|"Schema valid"| EXEC

    EXEC -->|"API call"| EXT_API
    EXT_API -->|"Response"| RESULT_VAL
    RESULT_VAL -->|"Result invalid"| E502[502 Contract violation\non response]
    RESULT_VAL -->|"Result valid"| METRICS

    METRICS -->|"Tool result"| TE_REQ
```

---

## DFD-07: Knowledge Graph Write Flow

```mermaid
graph TD
    SRC([Source\nUser upload · API · Crawler])

    subgraph "Input Validation"
        SCHEMA_VAL[Schema validation\nPydantic / Marshmallow]
        DEDUP[Deduplication check\nhash-based]
    end

    subgraph "17-Axis Coordinate Resolution (core/coordinate_system.py)"
        COORD_PARSE[Parse input\nto AxisCoordinate objects]
        COORD_VALIDATE[Validate axis numbers\n1-17 range check]
        COORD_BUILD[Build UnifiedCoordinate\n17-dimensional address]
        NODE_ID[Generate node_id\nSHA-256 of coordinate string]
    end

    subgraph "Knowledge Algorithm Processing (core/algorithms/)"
        KA_SCAN[Scan applicable KAs\nfor this coordinate]
        KA_EXEC[Execute relevant KAs\ne.g., KA-004 sanitize\nKA-010 bias detect]
    end

    subgraph "Graph Storage"
        PG_WRITE[Write KnowledgeNode\nto PostgreSQL\nwith tenant_id RLS]
        NEO_WRITE[Write node + edges\nto Neo4j\ngraph relationships]
        VECTOR_WRITE[Embed content\nwrite to ChromaDB\nRAG retrieval index]
    end

    subgraph "Audit"
        AUDIT_WRITE[Write AuditLog entry\nhash-chained]
        TRACE_WRITE[Write to RunTrace\nif within a run]
    end

    RESP([Return\nnode_id + coordinate])

    SRC --> SCHEMA_VAL
    SCHEMA_VAL -->|"Invalid"| E422[422 Validation Error]
    SCHEMA_VAL -->|"Valid"| DEDUP

    DEDUP -->|"Duplicate"| E409[409 Conflict]
    DEDUP -->|"New"| COORD_PARSE

    COORD_PARSE --> COORD_VALIDATE
    COORD_VALIDATE -->|"Invalid axis"| E400[400 Bad Request]
    COORD_VALIDATE -->|"Valid"| COORD_BUILD

    COORD_BUILD --> NODE_ID --> KA_SCAN --> KA_EXEC

    KA_EXEC --> PG_WRITE
    KA_EXEC --> NEO_WRITE
    KA_EXEC --> VECTOR_WRITE

    PG_WRITE & NEO_WRITE & VECTOR_WRITE --> AUDIT_WRITE
    AUDIT_WRITE --> TRACE_WRITE --> RESP
```

---

## DFD-08: Audit and Observability Flow

```mermaid
graph TD
    subgraph "Event Sources"
        API_REQ[API Request\nevent]
        SEC_EVENT[Security\nevent]
        AI_CALL[AI provider\ncall]
        MCP_CALL[Connector\ncall]
        SYS_EVENT[System\nevent]
    end

    subgraph "Audit Logger (backend/security/audit_logger.py)"
        HASH_CHAIN[Hash-chain\ncomputation\nSHA-256 of prev + event]
        AUDIT_WRITE[Write AuditLog\nto PostgreSQL]
        SYSLOG_EMIT[Emit to Syslog\nfor SIEM ingestion]
    end

    subgraph "Metrics Pipeline (Prometheus)"
        AI_LAT[AI latency metrics\nbackend/llm_gateway/latency_metrics.py\np50/p95/p99 per provider]
        MCP_LAT[Connector latency\nbackend/mcp_server/connector_metrics.py]
        SLO_TRACK[SLO tracker\nbackend/observability/latency_slo.py]
        RLS_METRICS[RLS metrics\nbackend/security/tenant_rls.py]
        CRASH_METRICS[Crash reporting metrics\nbackend/observability/crash_reporting.py]
    end

    subgraph "Distributed Tracing (backend/tracing/)"
        CORR_ID[Correlation ID\npropagation]
        RUN_TRACE[RunTrace record\nper execution run]
        TRACE_EXPORT[Signed trace export\nencrypted envelopes]
    end

    subgraph "Crash Reporting"
        SENTRY[Sentry SDK\ncapture_exception_with_fallback]
        FALLBACK_ID[Fallback crash ID\nif Sentry unavailable]
    end

    subgraph "Data Stores"
        AUDIT_DB[(AuditLog\ntable)]
        TRACE_DB[(RunTrace\ntable)]
        PROM[(Prometheus\nmetrics endpoint\n/metrics)]
    end

    SIEM([External SIEM\nSyslog])
    SENTRY_SVC([Sentry.io])

    API_REQ & SEC_EVENT & AI_CALL & MCP_CALL & SYS_EVENT --> HASH_CHAIN
    HASH_CHAIN --> AUDIT_WRITE --> AUDIT_DB
    AUDIT_WRITE --> SYSLOG_EMIT --> SIEM

    AI_CALL --> AI_LAT --> SLO_TRACK
    MCP_CALL --> MCP_LAT --> SLO_TRACK
    SLO_TRACK & RLS_METRICS & CRASH_METRICS --> PROM

    API_REQ --> CORR_ID --> RUN_TRACE --> TRACE_DB
    TRACE_DB -->|"On export request"| TRACE_EXPORT

    SYS_EVENT -->|"Exception"| SENTRY --> SENTRY_SVC
    SENTRY -->|"Fallback"| FALLBACK_ID
```

---

## DFD-09: Secret Resolution Flow (Startup)

This flow runs at application startup before any request is served. It shows how `SESSION_SECRET` (and other secrets) are resolved through the vault-aware pipeline.

```mermaid
graph TD
    START([Application startup\napp.py])

    subgraph "backend/security/secret_resolver.py"
        CHK1{SESSION_SECRET_FILE\nenv var set?}
        READ_FILE[Read secret\nfrom file path]

        CHK2{SESSION_SECRET_DPAPI_B64\nenv var set?}
        DPAPI[Decrypt via\nWindows DPAPI]

        CHK3{DLE_SECRET_STORE_JSON\nenv var set?}
        JSON_STORE[Read from\nJSON secret store]

        CHK4{SESSION_SECRET\nenv var set?}
        PLAIN[Use plaintext\nenv var]

        PROD_CHK{PRODUCTION_VAULT_SECRETS\n_REQUIRED = true?}
        PROD_ERR[Abort startup\nERROR: no vault-backed secret]

        RESOLVED[Secret resolved\nmark source]
    end

    subgraph "Production Validation (app.py)"
        SEC_VALIDATE[validate_production_security\ncheck for default credentials\nweak passwords · plaintext secrets]
        WARN[Log security\nwarnings / errors]
    end

    FLASK_CONFIG[Configure Flask\nSECRET_KEY = resolved secret\nSession cookie hardening]

    READY([Application ready\nto serve requests])

    START --> CHK1
    CHK1 -->|"Yes"| READ_FILE --> RESOLVED
    CHK1 -->|"No"| CHK2
    CHK2 -->|"Yes"| DPAPI --> RESOLVED
    CHK2 -->|"No"| CHK3
    CHK3 -->|"Yes"| JSON_STORE --> RESOLVED
    CHK3 -->|"No"| CHK4
    CHK4 -->|"Yes"| PLAIN

    PLAIN --> PROD_CHK
    PROD_CHK -->|"Yes (production mode)"| PROD_ERR
    PROD_CHK -->|"No (dev mode)"| RESOLVED

    RESOLVED --> SEC_VALIDATE --> WARN --> FLASK_CONFIG --> READY
```

---

## Data Classification Reference

| Data Category | Examples | Storage | Encryption |
|---------------|----------|---------|-----------|
| **PII — Tier 1** | User email addresses | PostgreSQL (`users._email`) | AES-256 field encryption (EncryptionManager) |
| **PII — Tier 2** | Usernames, API key metadata | PostgreSQL | Hashed (password_hash) or plaintext column |
| **Secrets** | API keys, OAuth tokens, MFA secrets | PostgreSQL (encrypted columns) | AES-256 field encryption |
| **Session data** | Active session tokens | Redis | Redis TLS in transit; HTTPONLY/SECURE cookies |
| **Knowledge graph** | Nodes, edges, coordinates | PostgreSQL + Neo4j | At-rest encryption (disk-level) |
| **Vectors / embeddings** | RAG document chunks | ChromaDB | At-rest encryption (disk-level) |
| **Audit trail** | Access events, security events | PostgreSQL (`audit_logs`) | Hash-chained; immutable |
| **Run traces** | Execution steps, LLM outputs | PostgreSQL (`run_traces`) | Signed envelopes on export |
| **Binary assets** | Documents, exports | MinIO (S3) | Server-side encryption |
| **Metrics** | Latency counters, SLO gauges | Prometheus (in-memory) | None — no PII in metrics |
| **Crash reports** | Exception tracebacks | Sentry (external) | Sanitized before export |
