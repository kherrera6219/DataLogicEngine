# Decision Logic Reference — DataLogicEngine

**Document Control**

| Field | Value |
|-------|-------|
| Owner | Platform Architecture |
| Last Updated | March 2026 |
| Status | Active |
| Audience | Software engineers, architects, QA, security reviewers |
| Review Cadence | Every 60 days |

---

## Purpose

This document captures every significant decision point in the DataLogicEngine platform — the conditions evaluated, the outcomes produced, and the code that implements each decision. This is the reference for understanding *why* the system behaves the way it does in any given scenario.

---

## Table of Contents

1. [DL-01: Truth Engine Tier Selection](#dl-01-truth-engine-tier-selection)
2. [DL-02: LLM Provider Routing and Failover](#dl-02-llm-provider-routing-and-failover)
3. [DL-03: Active Defense Threat Classification](#dl-03-active-defense-threat-classification)
4. [DL-04: RBAC Permission Resolution](#dl-04-rbac-permission-resolution)
5. [DL-05: Secret Resolution Priority Chain](#dl-05-secret-resolution-priority-chain)
6. [DL-06: Authentication Path Selection](#dl-06-authentication-path-selection)
7. [DL-07: Account Lockout and MFA Gate Logic](#dl-07-account-lockout-and-mfa-gate-logic)
8. [DL-08: Knowledge Node Coordinate Validation](#dl-08-knowledge-node-coordinate-validation)
9. [DL-09: MCP Scope Enforcement Logic](#dl-09-mcp-scope-enforcement-logic)
10. [DL-10: Simulation Layer Selection](#dl-10-simulation-layer-selection)
11. [DL-11: TruthGate Budget and Compliance Control](#dl-11-truthgate-budget-and-compliance-control)
12. [DL-12: Circuit Breaker State Machine](#dl-12-circuit-breaker-state-machine)

---

## DL-01: Truth Engine Tier Selection

**Source:** `backend/truth_engine/truth_core/engine.py` · `tiers.py`

The tier selector classifies every incoming query into one of five processing tiers, determining the depth of reasoning applied.

### Decision Tree

```
INPUT: Query + user context + constraints

├─ Is query a factual lookup with a deterministic answer?
│   AND word count < 20?
│   AND no external data required?
│   └─ YES → TRIVIAL (SLA: 1s)
│            Steps: intent_parsing → final_safety_gate
│            max_tokens: 1,000 | temperature: 0.0
│
├─ Does query require context retrieval from the knowledge graph?
│   OR Does it require multi-perspective analysis?
│   AND no simulation or quantitative modeling needed?
│   └─ YES → MODERATE (SLA: 3s)
│            Steps: intent_parsing → hybrid_retrieval → multi_persona_reasoning
│                   → final_safety_gate
│            max_tokens: 4,000 | temperature: 0.3
│
├─ Does query involve regulated data, legal/compliance implications,
│   OR require validation against external truth sources?
│   └─ YES → HIGH_STAKES (SLA: 10s)
│            Steps: +deep_research, +quant_validation, +trust_validation,
│                   +meta_reasoning
│            max_tokens: 8,000 | temperature: 0.2
│            requires_validation: True
│
├─ Does query require GNN/NN/quantum modeling,
│   OR cross-domain simulation across multiple knowledge sectors?
│   └─ YES → EXTREME (SLA: 60s)
│            Steps: ALL 10 refinement steps including pov_expansion
│                   + agi_planning
│            max_tokens: 32,000 | temperature: 0.1
│            requires_simulation: True
│
└─ Does query require multi-agent planning with autonomous sub-tasks?
    OR Is budget approval required for execution?
    └─ YES → AUTONOMOUS (SLA: 300s)
             Steps: ALL 10 steps + human_in_the_loop gate
             max_tokens: 128,000 | temperature: 0.1
             requires_human_review: True
             MAX_DEPTH: 3 | MAX_TOTAL_GOALS: 50 (AGI planner guardrails)
```

### Tier Routing Table

| Tier | SLA | Steps | max_tokens | temperature | Simulation | Human Review |
|------|-----|-------|-----------|-------------|-----------|-------------|
| trivial | 1s | 2 | 1,000 | 0.0 | No | No |
| moderate | 3s | 4 | 4,000 | 0.3 | No | No |
| high_stakes | 10s | 7 | 8,000 | 0.2 | No | No |
| extreme | 60s | 10 | 32,000 | 0.1 | Yes | No |
| autonomous | 300s | 10 + HITL | 128,000 | 0.1 | Yes | Yes |

### The 10 Refinement Steps (in order)

| Step | Name | Purpose |
|------|------|---------|
| 1 | `intent_parsing` | Parse and classify the user's intent |
| 2 | `hybrid_retrieval` | RAG retrieval + knowledge graph lookup |
| 3 | `deep_research` | Extended multi-source research |
| 4 | `pov_expansion` | Generate alternative viewpoints |
| 5 | `multi_persona_reasoning` | Apply all 4 QuadPersona perspectives (Knowledge Expert · Sector Specialist · Regulatory Advisor · Compliance Officer) |
| 6 | `quant_validation` | Quantitative/statistical validation |
| 7 | `agi_planning` | Multi-step autonomous goal planning |
| 8 | `trust_validation` | TruthGate trust and compliance check |
| 9 | `meta_reasoning` | Higher-order reasoning evaluation |
| 10 | `final_safety_gate` | Final output safety check before response |

---

## DL-02: LLM Provider Routing and Failover

**Source:** `backend/llm_gateway/gateway.py`

### Task Profile → Model Routing

```
INPUT: GatewayRequest.constraints.profile OR inferred from mode

constraints.profile == 'code'         → Codestral
constraints.profile == 'analysis'     → Claude 3.5 Sonnet
constraints.profile == 'long_context' → Gemini 1.5 Pro
constraints.profile == 'reasoning'    → Grok 4 Fast
constraints.profile == 'default'
  OR no profile set                   → GPT-4o
explicit model override set           → Use specified model
  (ignores profile routing)
```

### Circuit Breaker State Machine

```
STATES: CLOSED (healthy) | OPEN (tripped) | HALF-OPEN (testing)

CLOSED state:
  - Allow all requests through
  - Track error count in rolling window
  - IF error_count > threshold → transition to OPEN
    Log: "Circuit breaker tripped for provider {name}"

OPEN state:
  - Reject all requests immediately
  - Start cooldown timer (configurable, default 60s)
  - After cooldown expires → transition to HALF-OPEN

HALF-OPEN state:
  - Allow ONE test request through
  - IF test request succeeds → transition to CLOSED
    Reset error counter
  - IF test request fails → transition back to OPEN
    Restart cooldown timer

FAILOVER SEQUENCE (when primary is OPEN):
  Primary provider OPEN
    → Try provider[1] (secondary)
    → IF secondary also OPEN → Try provider[2] (tertiary)
    → IF all providers OPEN → Return structured error:
       {"error": "All LLM providers unavailable", "code": "gateway_error"}
```

### UKG Pipeline Decision

```
GatewayRequest.run_ukg_pipeline == True (default):
  → Route through full UKG SDK pipeline:
     1. CoordinateResolver17 — resolve 17-axis coordinate
     2. KAExecutor — run applicable Knowledge Algorithms
     3. UKGOverlay — enrich prompt with knowledge graph context
  → Then call LLM provider with enriched prompt

GatewayRequest.run_ukg_pipeline == False:
  → Bypass UKG pipeline
  → Send raw messages directly to LLM provider
  → Used for: internal system calls, active defense checks,
              simple API key validation calls
```

---

## DL-03: Active Defense Threat Classification

**Source:** `backend/security/active_defense.py` · `backend/security/honeypot.py`

The Active Defense service uses a secondary "Supervisor" LLM to classify every user message before it reaches the Truth Engine.

### Threat Scoring Decision Tree

```
INPUT: user_input + session history summary + user_role

Supervisor LLM analyses for:
├─ Prompt injection patterns
│   (e.g., "ignore previous instructions", "you are now DAN")
├─ Jailbreak attempts
│   (role-play to bypass constraints, system prompt extraction)
├─ Adversarial reasoning manipulation
│   (deliberate contradictions to confuse the reasoning pipeline)
├─ Data exfiltration probes
│   (attempts to extract other users' data or system internals)
└─ Social engineering patterns

OUTPUT: SecurityVerdict {
    is_safe: bool
    threat_score: float  (0.0 = safe, 1.0 = maximum threat)
    threat_type: str
    reason: str
    recommended_action: str
}

ROUTING DECISION:
  threat_score < 0.7  → SAFE  → Proceed to Knowledge Engine
  threat_score ≥ 0.7  → THREAT → Route to HoneypotRouter
    HoneypotRouter:
      - Log forensic capture of the session
      - Return convincing decoy response
      - Never expose real knowledge graph data
      - Flag session for security review in SecurityEvent table

FAIL-SAFE RULE (critical):
  IF Supervisor LLM is unreachable or returns an error:
    → DEFAULT TO BLOCK (fail-closed)
    → Do NOT pass request to Truth Engine
    → Return: {"error": "Security check unavailable"}
    → This prevents bypassing security during a supervisor outage
```

### Prompt Injection Shield (pre-processor)

**Source:** `backend/security/prompt_injection_shield.py`

Applied as a pre-processor before the Supervisor LLM assessment:

```
INPUT: raw user message

PATTERN CHECKS:
  ├─ Contains "ignore previous instructions" → FLAG
  ├─ Contains "forget your instructions" → FLAG
  ├─ Contains "you are now" + role override → FLAG
  ├─ Contains "system:" at start of user message → FLAG
  ├─ Contains base64-encoded payload patterns → FLAG
  ├─ Contains excessive special characters (>20% non-alphanum) → FLAG
  └─ Contains known jailbreak lexicon → FLAG

OUTPUT:
  No flags → Pass message to Supervisor LLM as-is
  Flags detected → Pre-annotate message with:
    "[INJECTION_SHIELD: N patterns detected]"
    Supervisor LLM uses this annotation in its assessment
```

---

## DL-04: RBAC Permission Resolution

**Source:** `backend/security/rbac.py`

### Permission Check Decision Tree

```
DECORATOR: @require_permission(Permission.X)

ON every request to protected route:

1. Is there a valid request context?
   └─ NO → Return 401 Unauthorized

2. Is the current user authenticated?
   (flask_login.current_user.is_authenticated)
   └─ NO → Return 401 Unauthorized

3. Look up user's role in RBACManager.roles[user.role]
   └─ Role not found → Return 403 Forbidden

4. Does role.permissions contain the required Permission?
   └─ NO → Return 403 Forbidden
            Write AUDIT event: "permission_denied"
   └─ YES → Allow request to proceed
             Write AUDIT event: "permission_granted" (for sensitive permissions)
```

### Role Hierarchy and Permissions

```
owner / super_admin → ALL permissions
  │
  ├─ admin
  │   ├─ user:read, user:write, user:delete, user:manage_roles
  │   ├─ ukg:read, ukg:write, ukg:delete, ukg:admin
  │   ├─ simulation:*, mcp:*, security:read, compliance:read
  │   ├─ audit:read, audit:export
  │   ├─ system:config:read, data:export, data:import
  │   └─ api:key:create, api:key:revoke
  │
  ├─ analyst
  │   ├─ ukg:read, ukg:write
  │   ├─ simulation:read, simulation:write, simulation:execute
  │   ├─ mcp:read, mcp:execute
  │   ├─ audit:read
  │   └─ data:export
  │
  ├─ viewer
  │   ├─ ukg:read
  │   ├─ simulation:read
  │   └─ mcp:read
  │
  └─ user (default)
      ├─ ukg:read
      └─ simulation:read
```

---

## DL-05: Secret Resolution Priority Chain

**Source:** `backend/security/secret_resolver.py`

```
resolve_runtime_secret("SESSION_SECRET") executes in priority order:

Priority 1 — File-backed secret
  IF env var SESSION_SECRET_FILE is set:
    Read file at path → return (secret, source="file")
    IF file not readable → raise ConfigurationError

Priority 2 — DPAPI-encrypted secret (Windows)
  IF env var SESSION_SECRET_DPAPI_B64 is set:
    Base64-decode → DPAPI decrypt → return (secret, source="dpapi")

Priority 3 — JSON secret store
  IF env var DLE_SECRET_STORE_JSON is set:
    Open JSON file → read key "SESSION_SECRET" → return (secret, source="json_store")

Priority 4 — Direct environment variable (development only)
  IF env var SESSION_SECRET is set:
    IF production_mode == True AND ALLOW_PLAINTEXT_PROD_SECRETS != "true":
      Return (None, source="plaintext_rejected")
      Log ERROR: vault-backed secret required in production
    ELSE:
      Return (secret, source="env")

Priority 5 — None (unconfigured)
  Return (None, source="missing")

POST-RESOLUTION VALIDATION:
  is_secure_secret_source(source):
    "file" → True
    "dpapi" → True
    "json_store" → True
    "env" → False (development only)
    "plaintext_rejected" → False
    "missing" → False

  IF production_mode AND NOT is_secure_secret_source(source):
    Log ERROR: "SESSION_SECRET is not vault-backed"
    (Does NOT abort — logs error and continues with degraded security posture)
    IF PRODUCTION_VAULT_SECRETS_REQUIRED == "true":
      ABORT application startup
```

---

## DL-06: Authentication Path Selection

**Source:** `app.py` · `backend/auth/` · `routes/auth_routes.py`

```
Incoming request authentication path selection:

1. DESKTOP MODE (Electron, FLASK_DESKTOP_MODE=true)
   └─ Check Windows SID from OS context
      └─ SID found in users table → auto-login as that user
      └─ SID not found → create new "owner" user from SID + hostname → auto-login
   → NO password / MFA required in desktop mode
   → Session is created in Redis

2. WEB MODE — Check Authorization header
   └─ Authorization: Bearer <token> present?
      └─ YES → JWT validation path:
               Decode JWT → verify signature → check expiry
               Extract user_id → load user from DB
               IF token blacklisted → 401
               IF expired → 401 (client must refresh)
      └─ NO → Session cookie path

3. WEB MODE — Session cookie path
   └─ Valid session cookie present?
      └─ YES → Load session from Redis → get user_id → load user from DB
      └─ NO → Check OIDC state cookie (SSO flow in progress?)
               └─ YES → Continue OIDC callback flow
               └─ NO → 401 Unauthorized (redirect to login)

4. OIDC / Azure AD path
   User clicks "Login with Azure AD":
   └─ Generate state parameter → redirect to Azure AD authorize endpoint
   Azure AD redirects back to /auth/oidc/callback:
   └─ Validate state → exchange code for token
   └─ Validate ID token → extract claims (email, name, groups)
   └─ Map claims to local user (create if first login)
   └─ Create Redis session → proceed as authenticated user
```

---

## DL-07: Account Lockout and MFA Gate Logic

**Source:** `models.py` · `backend/security/mfa.py`

### Account Lockout

```
On failed password attempt:

  user.failed_login_attempts += 1

  IF user.failed_login_attempts >= LOCKOUT_THRESHOLD (default: 5):
    user.locked_until = now() + LOCKOUT_DURATION (default: 30 minutes)
    Log SecurityEvent: "account_locked"

On any login attempt:

  IF user.locked_until IS NOT NULL AND now() < user.locked_until:
    Return 423 Account Locked
    Show: "Account locked until {locked_until}"

  IF user.locked_until IS NOT NULL AND now() >= user.locked_until:
    user.failed_login_attempts = 0
    user.locked_until = None
    (Auto-unlock — proceed with login attempt)

On successful login:

  user.failed_login_attempts = 0
  user.locked_until = None
  user.last_successful_login = now()
```

### MFA Gate Logic

```
After successful password verification:

IF user.mfa_enabled == False:
  → Proceed directly to session creation (no MFA required)

IF user.mfa_enabled == True:
  → Present TOTP prompt to user

  User enters 6-digit TOTP code:
    → MFAManager.verify_totp(user.mfa_secret, provided_code)
    → IF valid (within 30-second window ± 1 window drift) → proceed
    → IF invalid → increment mfa_attempts counter
                   Return 401 with "Invalid code"
                   IF mfa_attempts >= 3 → lock account (same as password lockout)

  User enters backup code instead:
    → Check against user.backup_codes list (each is SHA-256 hashed)
    → IF match found → remove used code from list → proceed
    → IF no match → return 401 with "Invalid backup code"
    → Backup codes are single-use; after all 10 are consumed,
      user must re-enroll TOTP
```

---

## DL-08: Knowledge Node Coordinate Validation

**Source:** `core/coordinate_system.py`

```
INPUT: axis_number (int), value (str), optional meta_tag (str)

VALIDATION CHAIN:

Step 1 — Axis number range check:
  IF NOT isinstance(axis_number, int) OR NOT 1 <= axis_number <= 17:
    raise ValueError("Axis number must be between 1 and 17")

Step 2 — Value format check:
  IF value contains alphabetic characters AND meta_tag is None:
    Log WARNING: "Axis {n} value '{v}' contains letters but no meta_tag"
    (This is a warning, not an error — non-numeric values are allowed
     when accompanied by a meta_tag for regulatory source preservation)

Step 3 — Nuremberg notation parsing:
  Split value on '.' → parse each part as integer
  IF any part is not a valid integer → levels = []
  IF levels is empty → coordinate depth = 0
  IF levels populated → coordinate depth = len(levels)

Step 4 — Parent coordinate derivation:
  IF depth > 1 → parent = '.'.join(levels[:-1])
  IF depth <= 1 → parent = None

Step 5 — Descendant check (for traversal operations):
  coordinate A is descendant of B IF:
    A.axis_number == B.axis_number
    AND A.depth > B.depth
    AND A.levels[:B.depth] == B.levels

Step 6 — Node ID generation:
  coordinate_string = concatenation of all 17 axis values
  node_id = "node_" + SHA-256(coordinate_string)[:16]
```

---

## DL-09: MCP Scope Enforcement Logic

**Source:** `backend/mcp_server/scope_enforcement.py`

```
INPUT: tool_name + ExecutionContext { connector_id, user_id, granted_scopes }

ENFORCEMENT CHAIN:

Step 1 — Look up ToolDefinition in registry:
  tool = ToolRegistry.get_definition(tool_name)
  IF tool not found → raise ToolNotFoundError

Step 2 — Retrieve connector from DB:
  connector = MCPConnector.query.filter_by(
      id=context.connector_id, tenant_id=context.tenant_id
  ).first()
  IF connector is None → raise ConnectorNotFoundError
  IF connector.status != 'active' → raise ConnectorInactiveError

Step 3 — Scope comparison:
  required_scopes = tool.required_scopes  (e.g., ["jira:read", "jira:create"])
  granted_scopes = context.granted_scopes (from OAuth token)

  missing_scopes = required_scopes - granted_scopes
  IF missing_scopes is not empty:
    Write SecurityEvent: "scope_violation"
    raise ScopeViolationError(missing=missing_scopes)
    Return 403: {"error": "insufficient_scope", "missing": [...]}

Step 4 — Token freshness check:
  token = MCPOAuthToken.query.filter_by(
      connector_id=context.connector_id
  ).order_by(desc(expires_at)).first()

  IF token.expires_at - now() < 5 minutes:
    → Proactively refresh token before execution
    → IF refresh fails → raise TokenRefreshError

  IF token is expired AND refresh failed:
    → Return 401 with refresh_required flag

Step 5 — Contract validation (pre-execution):
  validate_tool_arguments(tool_name, input_payload)
  IF invalid → raise ContractViolationError(422)

Step 6 — Execute tool:
  result = tool_function(**input_payload)

Step 7 — Result contract validation (post-execution):
  validate_tool_result(tool_name, result)
  IF invalid → raise ContractViolationError(502)

  Record connector metrics (latency p50/p95/p99)
  Return result to caller
```

---

## DL-10: Simulation Layer Selection

**Source:** `backend/simulation/simulation_engine.py`

```
INPUT: Simulation configuration { scenario, axes, knowledge_algorithms, budget }

LAYER ACTIVATION DECISION:

Layer 1 — Knowledge Retrieval (ALWAYS active):
  Resolve 17-axis coordinates for all scenario inputs
  → Always executed for every simulation

Layer 2 — Vector Similarity (active if):
  simulation.config.use_rag == True (default: True)
  → Retrieve semantically similar knowledge from ChromaDB

Layer 3 — Graph Traversal (active if):
  simulation.config.use_graph == True (default: True)
  → Traverse Neo4j graph for connected nodes and edges

Layer 4 — Cross-Domain Linking (active if):
  any axis 3 (Honeycomb) or axis 6 (Octopus) coordinates are specified
  → Activate cross-domain relationship analysis

Layer 5 — Quantitative Modeling (active if):
  simulation.config.use_quantitative == True
  AND TruthGate budget allows quantitative tier
  → Run GNN / NN computational models

Layer 6 — Scenario Projection (active if):
  simulation.config.projection_steps > 0
  → Project knowledge state forward through temporal axis (axis 13)

Layer 7 — Risk Assessment (ALWAYS active):
  axis 14 (Risk & Confidence) coordinates are always evaluated
  → Calculate risk level + confidence score for simulation output
  → Always executed as final layer
```

---

## DL-11: TruthGate Budget and Compliance Control

**Source:** `backend/truth_engine/truth_gate/gateway.py` · `budget.py` · `compliance.py`

```
INPUT: TruthCore processing request + user context + tier

BUDGET CONTROL:

Per-request token budget:
  tier = 'trivial'    → max_tokens = 1,000
  tier = 'moderate'   → max_tokens = 4,000
  tier = 'high_stakes'→ max_tokens = 8,000
  tier = 'extreme'    → max_tokens = 32,000
  tier = 'autonomous' → max_tokens = 128,000

IF estimated_tokens > budget.remaining:
  → Downgrade tier to next cheaper tier
  → Log: "Budget-aware tier downgrade: extreme → high_stakes"
  → Re-evaluate with reduced tier

IF all tiers exceed budget:
  → Return 402 Payment Required
  → Message: "Request exceeds available token budget"

COMPLIANCE CONTROL:

Before executing high_stakes / extreme / autonomous tiers:
  CHECK: Does content involve regulated data categories?
    → HIPAA PHI: IF HIPAA_MODE == false → block processing
    → GDPR PII: Check data_classification of input nodes
    → EU AI Act: Record traceability markers for audit
    → Export controls: Check axis 12 (Location) for jurisdiction flags

  IF compliance check fails:
    → Return 451 Unavailable For Legal Reasons
    → Write ComplianceViolationEvent to audit log

TRUST VALIDATION:

trust_validation step (layer 8):
  Sources checked:
    1. Internal knowledge graph consistency
    2. Cross-reference with TruthLink blockchain adapter
    3. Confidence score from axis 14 coordinates

  IF trust_score < TRUST_THRESHOLD (default: 0.6):
    → Flag response with low_confidence warning
    → Do NOT block — append caveat to response

  IF trust_score < ABSOLUTE_MINIMUM (0.3):
    → Block response
    → Return: "Response confidence below acceptable threshold"
```

---

## DL-12: Circuit Breaker State Machine

**Source:** `backend/llm_gateway/gateway.py`

```
STATE TRANSITIONS:

CLOSED → OPEN:
  Condition: error_count > ERROR_THRESHOLD within WINDOW_SECONDS
  Default: 5 errors within 60 seconds
  Action: Log circuit trip, start COOLDOWN_SECONDS timer

OPEN → HALF_OPEN:
  Condition: COOLDOWN_SECONDS elapsed since OPEN transition
  Default: 60 seconds
  Action: Allow exactly ONE probe request

HALF_OPEN → CLOSED:
  Condition: Probe request succeeds (HTTP 2xx, no timeout)
  Action: Reset error counter, resume normal operation

HALF_OPEN → OPEN:
  Condition: Probe request fails or times out
  Action: Restart COOLDOWN_SECONDS timer

FAILOVER CHAIN (when OPEN):
  provider_list = [primary, secondary, tertiary]

  FOR each provider in provider_list:
    IF provider.circuit_breaker.state == CLOSED:
      → Attempt request with this provider
      → IF success: return response, record latency
      → IF failure: increment error counter, try next provider
    IF provider.circuit_breaker.state == OPEN:
      → Skip immediately, try next provider

  IF all providers in OPEN state:
    → Return structured gateway error
    → Log: "All LLM providers unavailable"
    → Increment crash_reporting metric

ERROR TYPES THAT TRIP THE CIRCUIT:
  - HTTP 429 (rate limited) → YES — trip immediately
  - HTTP 500/502/503/504 → YES — increment counter
  - Connection timeout → YES — increment counter
  - HTTP 401/403 (auth error) → NO — do not trip;
    these are configuration errors, not transient failures;
    alert admin immediately instead
  - HTTP 400 (bad request) → NO — do not trip;
    these are request errors, not provider failures
```
