# Sequence Diagrams — DataLogicEngine

**Document Control**

| Field | Value |
|-------|-------|
| Owner | Platform Architecture |
| Last Updated | March 2026 |
| Status | Active |
| Audience | Software engineers, architects, QA, API integrators |
| Review Cadence | Every 60 days |
| Notation | UML sequence diagram syntax rendered in Mermaid |

---

## Table of Contents

1. [SD-01: Web Login with MFA](#sd-01-web-login-with-mfa)
2. [SD-02: Desktop Auto-Login (Electron)](#sd-02-desktop-auto-login-electron)
3. [SD-03: Chat Message — Full Round Trip](#sd-03-chat-message--full-round-trip)
4. [SD-04: LLM Provider Call with Circuit Breaker Failover](#sd-04-llm-provider-call-with-circuit-breaker-failover)
5. [SD-05: MCP Tool Call Execution](#sd-05-mcp-tool-call-execution)
6. [SD-06: Knowledge Node Write](#sd-06-knowledge-node-write)
7. [SD-07: RBAC Permission Check](#sd-07-rbac-permission-check)
8. [SD-08: Active Defense Assessment](#sd-08-active-defense-assessment)
9. [SD-09: Run Trace Export (Signed)](#sd-09-run-trace-export-signed)
10. [SD-10: OIDC / Azure AD Authentication](#sd-10-oidc--azure-ad-authentication)

---

## SD-01: Web Login with MFA

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant Flask as Flask API<br/>(app.py)
    participant AuthRoutes as Auth Routes<br/>(routes/auth_routes.py)
    participant UserModel as User Model<br/>(models.py)
    participant MFA as MFA Manager<br/>(backend/security/mfa.py)
    participant Redis as Redis<br/>(session store)
    participant AuditLog as Audit Logger<br/>(backend/security/audit_logger.py)

    User->>Browser: Navigate to /login
    Browser->>Flask: GET /login
    Flask->>Browser: Login page HTML

    User->>Browser: Enter username + password
    Browser->>Flask: POST /auth/login {username, password}

    Flask->>Flask: Apply middleware:<br/>Correlation ID, CSRF check,<br/>Rate limit check

    Flask->>AuthRoutes: Route to login handler
    AuthRoutes->>UserModel: User.query.filter_by(username=username)
    UserModel-->>AuthRoutes: User record

    AuthRoutes->>UserModel: user.is_account_locked()
    alt Account locked
        UserModel-->>AuthRoutes: locked_until > now()
        AuthRoutes-->>Flask: 423 Locked
        Flask-->>Browser: Account locked message
    end

    AuthRoutes->>UserModel: user.check_password(password)
    alt Password invalid
        UserModel-->>AuthRoutes: False
        AuthRoutes->>UserModel: Increment failed_login_attempts
        AuthRoutes-->>Flask: 401 Invalid credentials
        Flask-->>Browser: Error message
    end

    alt MFA enabled
        AuthRoutes-->>Browser: Redirect to /auth/mfa-challenge
        User->>Browser: Enter TOTP code
        Browser->>Flask: POST /auth/mfa-verify {totp_code}
        Flask->>MFA: verify_totp(user.mfa_secret, totp_code)
        alt TOTP invalid
            MFA-->>Flask: False
            Flask-->>Browser: 401 Invalid MFA code
        end
        MFA-->>Flask: True
    end

    AuthRoutes->>UserModel: Reset failed_login_attempts<br/>Update last_successful_login
    AuthRoutes->>Redis: Create encrypted session<br/>session[user_id] = user.id
    Redis-->>AuthRoutes: Session token
    AuthRoutes->>AuditLog: Write login_success event<br/>(hash-chained)
    AuditLog-->>AuthRoutes: ok

    AuthRoutes-->>Flask: Set-Cookie: session=<token>; HttpOnly; Secure
    Flask-->>Browser: 302 Redirect to /dashboard
    Browser->>Flask: GET /dashboard (with session cookie)
    Flask-->>Browser: Dashboard page
```

---

## SD-02: Desktop Auto-Login (Electron)

```mermaid
sequenceDiagram
    participant Electron as Electron Shell<br/>(frontend/electron/)
    participant Main as main.py<br/>(startup entry)
    participant Flask as Flask API<br/>(app.py)
    participant DesktopAuth as Desktop Auth<br/>(backend/security/desktop_local_auth.py)
    participant UserModel as User Model<br/>(models.py)
    participant SafeStorage as safeStorage<br/>(OS-protected key store)
    participant Redis as Redis<br/>(session store)

    Electron->>Main: Application launched
    Main->>Flask: Start Flask server (port 5000)
    Flask->>Flask: Load .env + resolve SESSION_SECRET<br/>via secret_resolver.py

    Electron->>Flask: GET /auth/desktop-init
    Flask->>DesktopAuth: Initiate desktop auth flow

    DesktopAuth->>SafeStorage: Read Windows SID<br/>from OS context
    SafeStorage-->>DesktopAuth: Windows SID string

    DesktopAuth->>UserModel: User.query.filter_by(sid=windows_sid)
    alt SID found (returning user)
        UserModel-->>DesktopAuth: Existing user record
    else SID not found (first run)
        DesktopAuth->>UserModel: Create User(sid=sid, role='owner',<br/>username=hostname, no_login=True)
        UserModel-->>DesktopAuth: New user record
    end

    DesktopAuth->>Redis: Create session for user
    Redis-->>DesktopAuth: Session token

    DesktopAuth-->>Flask: Set-Cookie: session=<token>
    Flask-->>Electron: 200 OK + session cookie

    Electron->>Flask: GET /dashboard (with session cookie)
    Flask-->>Electron: Dashboard HTML
    Electron->>Electron: Render WebView with dashboard
```

---

## SD-03: Chat Message — Full Round Trip

```mermaid
sequenceDiagram
    actor User
    participant UI as Chat UI<br/>(frontend/app/chat)
    participant APIClient as API Client<br/>(frontend/lib/)
    participant Flask as Flask API
    participant ActiveDef as Active Defense<br/>(backend/security/active_defense.py)
    participant Knowledge as Knowledge Engine<br/>(core/)
    participant TruthEngine as Truth Engine<br/>(backend/truth_engine/)
    participant LLMGateway as LLM Gateway<br/>(backend/llm_gateway/)
    participant Provider as AI Provider<br/>(OpenAI/Anthropic/etc)
    participant DB as PostgreSQL
    participant AuditLog as Audit Logger

    User->>UI: Type message + press Send
    UI->>APIClient: POST /api/chat/message<br/>{session_id, content, model}

    APIClient->>Flask: HTTP POST with session cookie

    Flask->>Flask: Middleware: Correlation ID +<br/>Rate limit + CSRF + Security headers

    Note over Flask: RBAC check: MCP_EXECUTE or UKG_READ

    Flask->>DB: Save ChatMessage(role=user)
    DB-->>Flask: message_id

    Flask->>ActiveDef: assess_incoming(content, history, user_role)
    ActiveDef->>LLMGateway: Supervisor LLM call<br/>(separate API key, mode=json)
    LLMGateway-->>ActiveDef: SecurityVerdict{threat_score, is_safe}

    alt Threat detected (score >= 0.7)
        ActiveDef-->>Flask: BLOCKED
        Flask-->>APIClient: Safety block response (decoy)
        APIClient-->>UI: Display block message
    end

    Flask->>Knowledge: Resolve 17-axis coordinate<br/>for this query
    Knowledge->>DB: Query knowledge graph<br/>(with tenant_id RLS)
    DB-->>Knowledge: Relevant nodes + edges
    Knowledge->>Knowledge: Run applicable KAs<br/>(KA-004 sanitize, etc.)
    Knowledge-->>Flask: Enriched context + coordinate

    Flask->>TruthEngine: Process(query, context, coordinate)
    TruthEngine->>TruthEngine: Select processing tier<br/>(trivial/moderate/high_stakes/extreme/autonomous)

    loop Refinement steps (1-10 depending on tier)
        TruthEngine->>TruthEngine: Execute step<br/>(intent_parsing, hybrid_retrieval,<br/>multi_persona_reasoning, etc.)
    end

    TruthEngine->>LLMGateway: Route LLM request<br/>(selected model + profile)
    LLMGateway->>Provider: Inference request
    Provider-->>LLMGateway: Completion response
    LLMGateway-->>TruthEngine: Response + latency recorded

    TruthEngine->>TruthEngine: Final safety gate check
    TruthEngine-->>Flask: Verified response + run_id

    Flask->>DB: Save ChatMessage(role=assistant)<br/>Update LLMProviderUsage<br/>Write RunTrace record
    Flask->>AuditLog: Write hash-chained audit entry
    AuditLog-->>Flask: ok

    Flask-->>APIClient: 200 OK {response, run_id, coordinates}
    APIClient-->>UI: Render response
    UI-->>User: Display AI response + trace button
```

---

## SD-04: LLM Provider Call with Circuit Breaker Failover

```mermaid
sequenceDiagram
    participant TruthEngine as Truth Engine
    participant Gateway as LLM Gateway<br/>(backend/llm_gateway/gateway.py)
    participant CB as Circuit Breaker
    participant Primary as Primary Provider<br/>(e.g., GPT-4o)
    participant Secondary as Secondary Provider<br/>(e.g., Claude 3.5)
    participant Tertiary as Tertiary Provider<br/>(e.g., Gemini)
    participant DB as PostgreSQL<br/>(LLMProvider table)
    participant Metrics as Latency Metrics<br/>(latency_metrics.py)

    TruthEngine->>Gateway: GatewayRequest{messages, profile, tier}

    Gateway->>DB: Load provider configs<br/>Decrypt API keys (AES-256)
    DB-->>Gateway: Provider list with decrypted keys

    Gateway->>Gateway: Select model by profile<br/>(code→Codestral, analysis→Claude, etc.)

    Gateway->>CB: Check primary provider circuit state
    alt Primary circuit CLOSED (healthy)
        CB-->>Gateway: CLOSED — proceed
        Gateway->>Primary: POST /v1/chat/completions
        alt Success
            Primary-->>Gateway: 200 OK {completion}
            Gateway->>Metrics: Record latency (p50/p95/p99)
            Gateway->>DB: Insert LLMProviderUsage record
            Gateway-->>TruthEngine: Response
        else Failure (5xx / timeout)
            Primary-->>Gateway: Error
            Gateway->>CB: Increment error counter
            Note over CB: If count > threshold → OPEN circuit
        end
    end

    alt Primary circuit OPEN (tripped)
        CB-->>Gateway: OPEN — skip primary
        Gateway->>CB: Check secondary provider circuit state
        alt Secondary CLOSED
            Gateway->>Secondary: POST /messages (Anthropic API)
            alt Success
                Secondary-->>Gateway: 200 OK {completion}
                Gateway->>Metrics: Record latency
                Gateway-->>TruthEngine: Response (failover)
            else Failure
                Secondary-->>Gateway: Error
            end
        end
        alt Secondary also OPEN
            Gateway->>Tertiary: POST to Gemini API
            alt Success
                Tertiary-->>Gateway: Response
                Gateway-->>TruthEngine: Response (second failover)
            else All failed
                Gateway-->>TruthEngine: Error{all_providers_unavailable}
            end
        end
    end
```

---

## SD-05: MCP Tool Call Execution

```mermaid
sequenceDiagram
    participant TruthEngine as Truth Engine
    participant Router as MCP Router<br/>(backend/mcp_server/router.py)
    participant ScopeEnf as Scope Enforcer<br/>(scope_enforcement.py)
    participant OAuthMgr as OAuth Manager<br/>(oauth_manager.py)
    participant Registry as Tool Registry<br/>(registry.py)
    participant Validator as Contract Validator<br/>(contract_validation.py)
    participant ExternalAPI as External System<br/>(Jira / Salesforce)
    participant DB as PostgreSQL<br/>(MCPConnector + MCPOAuthToken)
    participant ConnMetrics as Connector Metrics<br/>(connector_metrics.py)

    TruthEngine->>Router: Execute tool: {tool_name, input, connector_id}

    Router->>DB: Load MCPConnector by id + tenant_id
    DB-->>Router: Connector config (credentials encrypted)

    Router->>ScopeEnf: enforce_scopes(tool_name, context)
    ScopeEnf->>Registry: Get required_scopes for tool
    Registry-->>ScopeEnf: required_scopes list
    ScopeEnf->>DB: Load MCPOAuthToken for connector
    DB-->>ScopeEnf: Token{scopes, expires_at}

    alt Insufficient scopes
        ScopeEnf-->>Router: ScopeViolationError
        Router-->>TruthEngine: 403 {error: insufficient_scope}
    end

    alt Token expires in < 5 minutes
        ScopeEnf->>OAuthMgr: refresh_token(connector_id)
        OAuthMgr->>ExternalAPI: POST /oauth/token {refresh_token}
        ExternalAPI-->>OAuthMgr: New access_token + refresh_token
        OAuthMgr->>DB: Update MCPOAuthToken
        DB-->>OAuthMgr: ok
    end

    ScopeEnf-->>Router: Context validated

    Router->>Registry: Get tool function by name
    Registry-->>Router: Tool callable

    Router->>Validator: validate_tool_arguments(tool_name, input)
    alt Invalid arguments
        Validator-->>Router: ContractViolationError
        Router-->>TruthEngine: 422 {error: schema_violation}
    end

    Router->>ExternalAPI: Execute tool call<br/>(e.g., GET /rest/api/3/issue/{id})
    ExternalAPI-->>Router: Tool result

    Router->>Validator: validate_tool_result(tool_name, result)
    alt Invalid result
        Validator-->>Router: ContractViolationError
        Router-->>TruthEngine: 502 {error: response_contract_violation}
    end

    Router->>ConnMetrics: Record execution latency<br/>(connector, tool, duration_ms)
    ConnMetrics-->>Router: ok

    Router-->>TruthEngine: Tool result payload
```

---

## SD-06: Knowledge Node Write

```mermaid
sequenceDiagram
    actor Client as Client (User / API)
    participant Flask as Flask API
    participant KARoutes as KA Routes<br/>(routes/ka_routes.py)
    participant CoordSys as Coordinate System<br/>(core/coordinate_system.py)
    participant KAExec as KA Executor<br/>(core/knowledge_algorithm/)
    participant PG as PostgreSQL<br/>(KnowledgeNode table)
    participant Neo4j as Neo4j<br/>(Graph DB)
    participant Chroma as ChromaDB<br/>(Vector Store)
    participant LLMGateway as LLM Gateway<br/>(embeddings)
    participant AuditLog as Audit Logger

    Client->>Flask: POST /api/knowledge/nodes {axis_values, content, metadata}
    Flask->>Flask: Middleware + RBAC check (UKG_WRITE)

    Flask->>KARoutes: Route to node creation handler
    KARoutes->>KARoutes: Schema validation (Pydantic)
    alt Invalid schema
        KARoutes-->>Flask: 422 Validation Error
    end

    KARoutes->>CoordSys: Parse axis values → AxisCoordinate objects
    CoordSys->>CoordSys: Validate axis numbers (1-17)
    CoordSys->>CoordSys: Build UnifiedCoordinate (17-dimensional)
    CoordSys->>CoordSys: Generate node_id (SHA-256 of coord string)
    CoordSys-->>KARoutes: UnifiedCoordinate + node_id

    KARoutes->>KAExec: Run pre-write KAs:<br/>KA-004 (sanitize) → KA-010 (bias) → KA-034 (adversarial)
    alt KA gate failed
        KAExec-->>KARoutes: KAViolationError
        KARoutes-->>Flask: 422 KA violation
    end
    KAExec-->>KARoutes: Sanitized content

    KARoutes->>LLMGateway: Generate embedding vector<br/>for content (run_ukg_pipeline=False)
    LLMGateway-->>KARoutes: Embedding vector (float[])

    KARoutes->>PG: INSERT KnowledgeNode<br/>{node_id, coordinate, content, tenant_id}
    PG-->>KARoutes: Record saved

    KARoutes->>Neo4j: Create node + relationship edges<br/>based on axis crosswalks
    Neo4j-->>KARoutes: Graph updated

    KARoutes->>Chroma: Upsert document<br/>{id: node_id, embedding: vector, metadata}
    Chroma-->>KARoutes: Indexed

    KARoutes->>AuditLog: Write knowledge_node_created<br/>(hash-chained, includes node_id + coordinate)
    AuditLog-->>KARoutes: ok

    KARoutes-->>Flask: 201 Created {node_id, coordinate_string}
    Flask-->>Client: 201 Created response
```

---

## SD-07: RBAC Permission Check

```mermaid
sequenceDiagram
    participant Request as HTTP Request
    participant Decorator as @require_permission decorator<br/>(backend/security/rbac.py)
    participant RBAC as RBACManager
    participant UserCtx as Flask current_user<br/>(flask_login)
    participant AuditLog as Audit Logger

    Request->>Decorator: Route function called

    Decorator->>UserCtx: is_authenticated?
    alt Not authenticated
        UserCtx-->>Decorator: False
        Decorator-->>Request: 401 Unauthorized<br/>{error: authentication_required}
    end

    Decorator->>UserCtx: Get user.role
    UserCtx-->>Decorator: role string (e.g., "analyst")

    Decorator->>RBAC: roles[user.role]
    alt Role not found
        RBAC-->>Decorator: None
        Decorator-->>Request: 403 Forbidden<br/>{error: unknown_role}
    end

    RBAC-->>Decorator: Role{permissions: Set[Permission]}

    Decorator->>RBAC: role.has_permission(required_permission)
    alt Permission denied
        RBAC-->>Decorator: False
        Decorator->>AuditLog: Write permission_denied event<br/>{user_id, permission, endpoint, ip}
        AuditLog-->>Decorator: ok
        Decorator-->>Request: 403 Forbidden<br/>{error: insufficient_permissions,<br/>required: permission.value}
    end

    RBAC-->>Decorator: True (permission granted)
    Note over Decorator: For sensitive permissions,<br/>write permission_granted audit event
    Decorator->>Request: Continue to route handler function
```

---

## SD-08: Active Defense Assessment

```mermaid
sequenceDiagram
    participant Flask as Flask API
    participant ActiveDef as ActiveDefenseService<br/>(backend/security/active_defense.py)
    participant Shield as PromptInjectionShield<br/>(backend/security/prompt_injection_shield.py)
    participant Gateway as LLM Gateway<br/>(Supervisor LLM — separate API key)
    participant SupervisorLLM as Supervisor LLM<br/>(AI Provider)
    participant Honeypot as HoneypotRouter<br/>(backend/security/honeypot.py)
    participant SecEvents as SecurityEvent table<br/>(PostgreSQL)

    Flask->>ActiveDef: assess_incoming(user_input, history_summary, user_role)

    ActiveDef->>Shield: Pre-screen for injection patterns
    Shield->>Shield: Pattern matching:<br/>ignore instructions · DAN · role overrides<br/>base64 payloads · jailbreak lexicon
    Shield-->>ActiveDef: Annotated input<br/>(flags prepended if detected)

    ActiveDef->>Gateway: GatewayRequest{<br/>  messages: [supervisor_prompt + annotated_input],<br/>  mode: "json",<br/>  meta: {tier: "security_defense", system_call: True},<br/>  run_ukg_pipeline: False<br/>}

    alt Supervisor LLM reachable
        Gateway->>SupervisorLLM: POST /completions<br/>(using DEFENSE_LLM_API_KEY)
        SupervisorLLM-->>Gateway: JSON response<br/>{threat_score, threat_type, reason, recommended_action}
        Gateway-->>ActiveDef: SecurityVerdict

        alt threat_score < 0.7 (safe)
            ActiveDef-->>Flask: SAFE — proceed to Knowledge Engine
        else threat_score >= 0.7 (threat detected)
            ActiveDef->>SecEvents: INSERT SecurityEvent<br/>{user_id, threat_type, threat_score, input_hash}
            SecEvents-->>ActiveDef: ok
            ActiveDef->>Honeypot: Route to honeypot
            Honeypot-->>ActiveDef: Convincing decoy response
            ActiveDef-->>Flask: BLOCKED — return decoy response
        end
    else Supervisor LLM unreachable (FAIL-SAFE)
        Gateway-->>ActiveDef: Error / timeout
        Note over ActiveDef: FAIL-CLOSED RULE:<br/>When supervisor is unavailable,<br/>DEFAULT TO BLOCK
        ActiveDef->>SecEvents: INSERT SecurityEvent<br/>{type: "supervisor_unavailable"}
        ActiveDef-->>Flask: BLOCKED — "Security check unavailable"
    end
```

---

## SD-09: Run Trace Export (Signed)

```mermaid
sequenceDiagram
    actor User
    participant UI as Runs Page<br/>(frontend/app/runs)
    participant Flask as Flask API
    participant ExportInteg as Export Integrity<br/>(backend/security/export_integrity.py)
    participant RunTrace as RunTrace model<br/>(PostgreSQL)
    participant AuditLog as Audit Log<br/>(PostgreSQL)
    participant Sanitizer as Sanitizer<br/>(backend/security/sanitizer.py)

    User->>UI: Click "Export Trace" for run_id
    UI->>Flask: POST /api/runs/{run_id}/export<br/>{format: "json", signed: true}

    Flask->>Flask: RBAC check: DATA_EXPORT permission

    Flask->>RunTrace: Load all RunStep records for run_id<br/>WHERE tenant_id = current_tenant (RLS enforced)
    RunTrace-->>Flask: RunStep list

    Flask->>AuditLog: Load AuditLog entries<br/>linked to run correlation_id
    AuditLog-->>Flask: Audit entries

    Flask->>Sanitizer: Sanitize export payload:<br/>- Strip internal API keys<br/>- Redact encrypted field raw values<br/>- Remove internal IP addresses<br/>- Redact session tokens
    Sanitizer-->>Flask: Sanitized payload

    Flask->>ExportInteg: Sign export envelope<br/>sign(payload, export_key)
    ExportInteg->>ExportInteg: Compute SHA-256 of payload
    ExportInteg->>ExportInteg: Sign with export private key
    ExportInteg-->>Flask: SignedEnvelope{<br/>  payload: sanitized_data,<br/>  signature: base64_sig,<br/>  key_id: export_key_id,<br/>  signed_at: timestamp<br/>}

    Flask->>AuditLog: Write audit_export event<br/>{run_id, user_id, export_time, payload_hash}
    AuditLog-->>Flask: ok

    Flask-->>UI: 200 OK<br/>Content-Disposition: attachment<br/>signed_trace_{run_id}.json

    UI-->>User: Download starts
```

---

## SD-10: OIDC / Azure AD Authentication

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant Flask as Flask API<br/>(routes/auth_routes.py)
    participant OIDCClient as OIDC Client<br/>(Authlib / Flask-Dance)
    participant AzureAD as Azure AD / Entra ID
    participant UserModel as User Model<br/>(models.py)
    participant Redis as Redis<br/>(session store)
    participant AuditLog as Audit Logger

    User->>Browser: Click "Login with Azure AD"
    Browser->>Flask: GET /auth/oidc/login

    Flask->>OIDCClient: Generate authorization URL<br/>+ state parameter (CSRF token)
    OIDCClient-->>Flask: authorization_url + state

    Flask->>Redis: Store state → session[oidc_state] = state
    Flask-->>Browser: 302 Redirect to Azure AD<br/>authorize?client_id=...&state=...&scope=openid+email+profile

    Browser->>AzureAD: Navigate to Azure AD login
    User->>AzureAD: Enter Azure AD credentials<br/>(+ corporate MFA if configured)
    AzureAD-->>Browser: 302 Redirect to /auth/oidc/callback?code=...&state=...

    Browser->>Flask: GET /auth/oidc/callback?code=AUTH_CODE&state=STATE

    Flask->>Redis: Validate state matches session[oidc_state]
    alt State mismatch (CSRF)
        Flask-->>Browser: 400 Invalid state — CSRF detected
    end

    Flask->>OIDCClient: Exchange code for tokens
    OIDCClient->>AzureAD: POST /token {code, client_secret, redirect_uri}
    AzureAD-->>OIDCClient: {access_token, id_token, refresh_token}

    OIDCClient->>OIDCClient: Validate id_token signature<br/>+ verify iss, aud, exp claims

    OIDCClient->>AzureAD: GET /userinfo (using access_token)
    AzureAD-->>OIDCClient: {email, name, oid, groups}

    OIDCClient-->>Flask: Validated claims

    Flask->>UserModel: User.query.filter_by(email=claims.email)
    alt Existing user
        UserModel-->>Flask: User record
        Flask->>UserModel: Update last_successful_login
    else First OIDC login (new user)
        Flask->>UserModel: Create User{<br/>  email: claims.email,<br/>  username: claims.preferred_username,<br/>  role: 'user',<br/>  oidc_sub: claims.oid<br/>}
        UserModel-->>Flask: New user record
    end

    Flask->>Redis: Create encrypted session<br/>session[user_id] = user.id
    Redis-->>Flask: Session token

    Flask->>AuditLog: Write oidc_login_success event<br/>{user_id, provider: "azure_ad", oid: claims.oid}
    AuditLog-->>Flask: ok

    Flask-->>Browser: Set-Cookie: session=<token>; HttpOnly; Secure<br/>302 Redirect to /dashboard
    Browser->>Flask: GET /dashboard (with session cookie)
    Flask-->>Browser: Dashboard
    Browser-->>User: Logged in to dashboard
```
