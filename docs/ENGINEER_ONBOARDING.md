# Engineer Onboarding Guide — DataLogicEngine

**Document Control**

| Field | Value |
|-------|-------|
| Owner | Platform Engineering |
| Last Updated | March 2026 |
| Status | Active |
| Audience | New software engineers joining the DataLogicEngine team |
| Review Cadence | Every 60 days |

---

## Table of Contents

1. [What Is DataLogicEngine?](#what-is-datalogicengine)
2. [Mental Model — Read This First](#mental-model--read-this-first)
3. [Environment Setup (Day 1)](#environment-setup-day-1)
4. [Repository Orientation (Day 2)](#repository-orientation-day-2)
5. [Week 1 — Learn the Core Systems](#week-1--learn-the-core-systems)
6. [Week 2 — Learn the Security and Data Layers](#week-2--learn-the-security-and-data-layers)
7. [Week 3 — Integration Systems and Testing](#week-3--integration-systems-and-testing)
8. [Week 4 — First Contribution](#week-4--first-contribution)
9. [Key Reference Files](#key-reference-files)
10. [Team Contacts and Escalation](#team-contacts-and-escalation)
11. [Glossary](#glossary)

---

## What Is DataLogicEngine?

DataLogicEngine (DLE) is a **local-first AI orchestration platform**. At its core, it lets users submit questions and workflows to a multi-layer AI reasoning engine that does much more than send a prompt to an LLM. It:

1. **Classifies the complexity** of the question (trivial → autonomous)
2. **Maps it to a 17-dimensional knowledge coordinate** inside the Universal Knowledge Graph (UKG)
3. **Routes it through the appropriate reasoning workflow** (from a single LLM call up to a 10-step refinement pipeline with simulation and human-in-the-loop)
4. **Pulls external context** from connectors (Jira, Salesforce) via the MCP server
5. **Validates the output** through a security supervisor LLM before returning it
6. **Records the full trace** in an immutable, hash-chained audit log

The platform runs as a **desktop application** (Windows Electron, no login required) or as a **web application** (multi-user, session-based auth).

---

## Mental Model — Read This First

Before touching any code, internalize this layered model. Every feature you will work on lives in one of these layers.

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 0 — USER INTERFACE                                        │
│  Next.js 16 / React 18 / Electron 40                            │
│  Pages: Chat, Projects, Runs, Graph, Simulations, Admin         │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 1 — API GATEWAY                                           │
│  Flask 3.1 · Correlation IDs · Rate Limiting · CSRF · SSRF guard│
│  All requests pass through middleware before hitting routes      │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2 — SECURITY GATE                                         │
│  RBAC (Permission check) · MFA verification · Tenant isolation  │
│  Active Defense (Supervisor LLM analyzes every user message)    │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3 — KNOWLEDGE ENGINE (Core)                              │
│  17-Axis Coordinate System · Knowledge Graph (Neo4j/Postgres)   │
│  Knowledge Algorithms (117 KAs) · QuadPersona System            │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 4 — TRUTH ENGINE                                          │
│  5-Tier Adaptive Reasoning · 10-Step Refinement · AGI Planner   │
│  TruthGate (budget/compliance) · TruthMemory (audit/metrics)    │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 5 — LLM GATEWAY                                           │
│  Provider routing (OpenAI/Anthropic/Gemini/Grok/Codestral)      │
│  Circuit breaker · Failover · Latency metrics                   │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 6 — EXTERNAL CONNECTORS (MCP)                            │
│  Jira · Salesforce · Custom connectors · OAuth lifecycle        │
│  Scope enforcement · Contract validation · Connector metrics    │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 7 — DATA LAYER                                            │
│  PostgreSQL (RLS) · Redis · Neo4j · MinIO · ChromaDB (RAG)      │
│  SQLite (local fallback) · Celery task queue                    │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 8 — OBSERVABILITY                                         │
│  Sentry crash reporting · Prometheus metrics · Audit trail      │
│  SLO tracking · Distributed tracing · Support bundle generator  │
└─────────────────────────────────────────────────────────────────┘
```

**Key insight:** A user submitting a chat message triggers all 8 layers in sequence. A simple admin settings change only triggers layers 0–2. Understanding which layers a feature touches is the first question to ask when reading any ticket.

---

## Environment Setup (Day 1)

### Prerequisites

Ensure these are installed before starting:

| Tool | Minimum Version | Install Command |
|------|----------------|-----------------|
| Python | 3.11 | [python.org](https://www.python.org) |
| Node.js | 20.x LTS | [nodejs.org](https://nodejs.org) |
| Git | 2.40+ | [git-scm.com](https://git-scm.com) |
| Docker Desktop | Latest | [docker.com](https://www.docker.com) |

### Step-by-Step Setup

```powershell
# 1. Clone the repository
git clone https://github.com/kherrera6219/DataLogicEngine.git
cd DataLogicEngine

# 2. Create Python virtual environment
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. Configure environment
Copy-Item .env.template .env
# Open .env and set SESSION_SECRET and at least one AI provider key:
# OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY

# 5. Enable pre-commit hooks
git config core.hooksPath .githooks

# 6. Verify local readiness before boot
.venv\Scripts\python.exe .\scripts\dev_doctor.py --skip-ports

# 7. Start the development stack
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1

# 8. Verify startup
.venv\Scripts\python.exe .\scripts\test_smoke.py
```

### Verify Your Environment

| Check | Command | Expected |
|-------|---------|----------|
| Local readiness | `.venv\Scripts\python.exe .\scripts\dev_doctor.py --skip-ports` | No blocker/error findings |
| Backend health | `curl http://127.0.0.1:5000/health` | `{"status": "healthy"}` |
| Frontend loads | Open `http://127.0.0.1:3000` | Dashboard renders |
| Python lint | `.venv\Scripts\python.exe -m ruff check .` | Zero findings |
| Frontend types | `npm --prefix frontend run typecheck` | Zero errors |
| Backend smoke | `.venv\Scripts\python.exe scripts/test_smoke.py` | All checks pass |

---

## Repository Orientation (Day 2)

### Top-Level Structure

```
DataLogicEngine/
│
├── app.py               ← Flask application factory + middleware setup (START HERE)
├── main.py              ← Desktop/CLI entry point
├── models.py            ← ALL SQLAlchemy models (~3,000 lines — read incrementally)
├── config.py            ← Environment-driven config classes
├── extensions.py        ← Flask extensions (db, login_manager, rbac, encryption)
│
├── backend/             ← Server-side business logic (28 modules)
│   ├── llm_gateway/     ← AI provider routing and circuit breaker
│   ├── truth_engine/    ← 5-tier reasoning engine (the "brain")
│   ├── security/        ← RBAC, encryption, MFA, audit, active defense
│   ├── mcp_server/      ← External connector protocol
│   ├── tracing/         ← Distributed trace management
│   └── ...
│
├── core/                ← Domain logic: 17-axis system, knowledge algorithms
│   ├── coordinate_system.py  ← The 17-dimensional knowledge address space
│   ├── algorithms/      ← 117 Knowledge Algorithm definitions
│   └── graph/           ← Knowledge graph operations
│
├── routes/              ← Flask route handlers (thin controllers)
│   ├── auth_routes.py
│   ├── admin_routes.py
│   ├── mcp_routes.py
│   └── ...
│
├── frontend/            ← Next.js 16 application
│   ├── app/             ← App Router pages (18 route directories)
│   ├── components/      ← React component library
│   └── lib/             ← API client functions
│
├── tests/               ← Test suite (18 categories)
├── docs/                ← All documentation
├── scripts/             ← Operational and validation scripts
└── .github/workflows/   ← 6 CI/CD pipelines
```

### The Most Important Files for a New Engineer

Read these files in this order over your first two days:

| Order | File | Why |
|-------|------|-----|
| 1 | `docs/ARCHITECTURE.md` | Understand the system before touching code |
| 2 | `app.py` (first 200 lines) | Understand Flask startup, middleware, secret resolution |
| 3 | `extensions.py` | Understand what shared objects exist (`db`, `rbac_manager`, `encryption_manager`) |
| 4 | `backend/security/rbac.py` | Understand the Permission enum — you'll see this everywhere |
| 5 | `models.py` (User + Project + Run models) | Understand core data entities |
| 6 | `core/coordinate_system.py` (first 150 lines) | Understand the 17-axis address space |
| 7 | `backend/truth_engine/truth_core/engine.py` | Understand the 5-tier reasoning tiers |
| 8 | `backend/llm_gateway/gateway.py` | Understand how LLM calls are made |

---

## Week 1 — Learn the Core Systems

### Day 3–4: The 17-Axis Knowledge Coordinate System

The UKG uses a 17-dimensional coordinate system to address every piece of knowledge. A knowledge node is identified by:

```
K ≡ (x1, x2, x3, ..., x17)
```

Each axis uses **Nuremberg-style dot-notation** (e.g., `2.13.4.2` means Axis 2, value 13, subvalue 4, subvalue 2).

**Read:** `core/coordinate_system.py`

**The 17 axes:**

| Axis | Name | Purpose |
|------|------|---------|
| 1 | Pillar Levels | Top-level knowledge domain hierarchy |
| 2 | Sectors | Industry/domain classification (e.g., healthcare, finance) |
| 3 | Honeycomb (Cross-domain) | Cross-domain knowledge linkages |
| 4 | Branches | Sub-domain branching within sectors |
| 5 | Nodes | Specific knowledge nodes |
| 6 | Octopus Crosswalk | Multi-domain regulatory crosswalk |
| 7 | Spiderweb Crosswalk | Compliance relationship mapping |
| 8 | Knowledge Role | Expert role associated with knowledge |
| 9 | Qualifications & Skills | Required qualifications/certifications |
| 10 | Octopus Regulatory Expert | Regulatory expert context |
| 11 | Spiderweb Compliance Expert | Compliance expert context |
| 12 | Location | Geographic/jurisdictional context |
| 13 | Temporal | Time-bound knowledge context |
| 14 | Risk & Confidence | Risk level + confidence score |
| 15 | Federated Intelligence | Distributed node sync state |
| 16 | Arrows of Time | Causal chain + temporal vector |
| 17 | Observability & Analytics | Metrics + audit trail marker |

### Day 5: The Truth Engine and 5-Tier Reasoning

The Truth Engine is the reasoning heart of the platform. Every AI query is classified into one of five tiers:

| Tier | SLA | Description | Steps |
|------|-----|-------------|-------|
| **Trivial** | 1s | Direct answer, temperature=0 | intent_parsing → safety_gate |
| **Moderate** | 3s | Hybrid RAG + Chain of Thought | +hybrid_retrieval, +multi_persona |
| **High-Stakes** | 10s | 12-step refinement workflow | +quant_validation, +trust_validation, +meta_reasoning |
| **Extreme** | 60s | GNN/NN/Quantum simulations | +deep_research, +pov_expansion, +agi_planning |
| **Autonomous** | 300s | Governed multi-agent planning | Full 10-step pipeline |

**Read:** `backend/truth_engine/truth_core/engine.py` and `tiers.py`

The Truth Engine has four sub-components:
- **TruthCore** — Adaptive reasoning, tier selection, refinement orchestration
- **TruthGate** — Budget control, compliance checks, trust validation
- **TruthMemory** — Audit trail, metrics, caching
- **TruthLink** — Internal event bus, blockchain adapter for immutable audit

### Day 5 (continued): The QuadPersona System

Every reasoning step is filtered through four concurrent expert personas (each makes a real LLM call simultaneously via `asyncio.gather()`):

| Persona | Axis | Role |
|---------|------|------|
| **Knowledge Expert** | Axis 8 | Deep domain expertise, factual analysis, best practices |
| **Sector Specialist** | Axis 9 | Real-world applications, market dynamics, sector-specific considerations |
| **Regulatory Advisor** | Axis 10 | Regulatory perspective, applicable laws and standards |
| **Compliance Officer** | Axis 11 | Compliance implications, risk management, potential violations |

Each persona returns a `response`, `confidence` (0–1), and `tokens_used`. Max 50 concurrent queries; 120-second timeout per persona.

**Read:** `backend/truth_engine/truth_core/personas.py` and `backend/quad_persona/quad_engine.py`

---

## Week 2 — Learn the Security and Data Layers

### Day 6–7: The Security Layer

The security layer is non-negotiable. Every contribution must respect these controls.

**Read in order:**

| File | What it teaches you |
|------|---------------------|
| `backend/security/rbac.py` | The `Permission` enum (40 permissions across 10 domains) and the `RBACManager`. The `@require_permission()` decorator is used on every protected route. |
| `backend/security/encryption_manager.py` | The KEK/DEK key hierarchy. AES-256 field-level encryption. The `EncryptionManager.encrypt()` / `.decrypt()` methods used transparently on PII model properties. |
| `backend/security/audit_logger.py` | How every security-relevant event is written to the hash-chained audit log. |
| `backend/security/active_defense.py` | The `ActiveDefenseService` — a secondary "Supervisor" LLM that analyzes every incoming user message before it reaches the Truth Engine. If the supervisor cannot be reached, requests are **blocked by default** (fail-closed). |
| `backend/security/mfa.py` | TOTP-based MFA lifecycle (enroll, verify, backup codes). |
| `backend/security/tenant_rls.py` | How Row-Level Security is configured at the PostgreSQL session level to enforce tenant isolation. |

**The RBAC permission check pattern (you will write this):**

```python
from backend.security import require_permission, Permission

@app.route('/api/knowledge/nodes')
@require_permission(Permission.UKG_READ)
def list_knowledge_nodes():
    # RBACManager has already verified the user has UKG_READ
    # All you need to do here is implement the business logic
    ...
```

### Day 8–9: The Database Models

`models.py` is 3,000+ lines. Do not read it all at once. Focus on these key model groups:

| Group | Models | Purpose |
|-------|--------|---------|
| **Identity** | `User`, `APIKey` | Authentication, API access |
| **Knowledge** | `KnowledgeNode`, `KnowledgeEdge`, `KnowledgeProject` | The knowledge graph |
| **Execution** | `Run`, `RunTrace`, `RunStep` | Execution history and tracing |
| **AI Config** | `LLMProvider`, `LLMProviderUsage`, `ChatSession`, `ChatMessage` | LLM provider management and chat history |
| **Connectors** | `MCPConnector`, `MCPOAuthToken` | External tool connectors |
| **Audit** | `AuditLog`, `SecurityEvent` | Immutable event trail |
| **Simulation** | `Simulation`, `SimulationRun` | Simulation engine records |

**Key pattern to learn:** PII fields (like `User._email`) are transparently encrypted using Python properties:

```python
@property
def email(self) -> Optional[str]:
    return encryption_manager.decrypt(self._email, field_name='email')

@email.setter
def email(self, value: Optional[str]) -> None:
    self._email = encryption_manager.encrypt(value, field_name='email')
```

You set `user.email = "alice@example.com"` — it gets encrypted automatically. You read `user.email` — it gets decrypted automatically. Never access `user._email` directly.

### Day 10: The LLM Gateway

**Read:** `backend/llm_gateway/gateway.py`

The LLM Gateway:
1. Resolves which provider/model to use (profile-based routing or explicit request)
2. Runs the request through the UKG pipeline (coordinate resolution, KA execution)
3. Calls the external AI provider with a circuit breaker (fails over to next provider on error)
4. Records latency metrics (p50/p95/p99)
5. Logs usage to `LLMProviderUsage`

**Model routing profiles:**

| Profile | Model Used |
|---------|-----------|
| `code` | Codestral |
| `analysis` | Claude 3.5 Sonnet |
| `long_context` | Gemini 1.5 Pro |
| `reasoning` | Grok 4 Fast |
| `default` | GPT-4o |

---

## Week 3 — Integration Systems and Testing

### Day 11–12: The MCP Server

The MCP (Model Context Protocol) Server allows the platform to call external tools (Jira, Salesforce, custom APIs) during knowledge processing.

**Key concepts:**

| Concept | File | What It Does |
|---------|------|-------------|
| `ToolRegistry` | `backend/mcp_server/registry.py` | Registers and discovers available tools; each tool declares its `required_scopes` |
| `ScopeEnforcement` | `backend/mcp_server/scope_enforcement.py` | Ensures the calling connector has the required OAuth scopes before execution |
| `OAuthManager` | `backend/mcp_server/oauth_manager.py` | Manages the OAuth token lifecycle (obtain, refresh, revoke) per connector |
| `ContractValidation` | `backend/mcp_server/contract_validation.py` | Validates tool inputs and outputs against JSON schemas |
| `ConnectorMetrics` | `backend/mcp_server/connector_metrics.py` | Records p50/p95/p99 latency per connector per tool |

### Day 13: Frontend Architecture

The frontend uses Next.js 16 App Router. Each directory under `frontend/app/` is a route:

| Route | Page |
|-------|------|
| `/` (page.tsx) | Root redirect to dashboard |
| `/dashboard` | Main dashboard with run history |
| `/chat` | AI chat interface |
| `/projects` | Project management |
| `/runs` | Execution run trace viewer |
| `/graph` | 3D knowledge graph visualization (Three.js / React Force Graph) |
| `/simulations` | Simulation management |
| `/algorithms` | Knowledge algorithm browser |
| `/mcp` | MCP connector management |
| `/truth-engine` | Truth Engine monitoring |
| `/admin` | Admin panel (user management, system stats) |
| `/settings` | User and system settings |
| `/analytics` | Usage analytics |

**API calls** are made through `frontend/lib/` API client modules, not directly from components.

### Day 14–15: The CI/CD Pipeline

Before your first PR, understand what CI checks will run:

| Workflow | File | What it checks |
|----------|------|----------------|
| **CI** | `.github/workflows/ci.yml` | Ruff lint, pytest suite, pip-audit, schema parity, startup precheck |
| **Security** | `.github/workflows/security.yml` | Bandit, OWASP dependency check, CodeQL |
| **Deploy** | `.github/workflows/deploy.yml` | Docker build, environment parity, lockfile integrity |
| **Release** | `.github/workflows/release-checklist.yml` | Full release gate sequence |

Run these locally before pushing:

```powershell
# Lint (must be zero findings)
.venv\Scripts\python.exe -m ruff check .

# Tests
python -m pytest tests/ -v

# Schema parity
.venv\Scripts\python.exe scripts/validate_schema_parity.py

# Startup precheck
.venv\Scripts\python.exe scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process
```

---

## Week 4 — First Contribution

### Finding Your First Ticket

- Browse [GitHub Issues](https://github.com/kherrera6219/DataLogicEngine/issues) filtered by `good first issue`
- Comment on the issue before starting
- Ask your onboarding buddy if you are unsure which ticket is appropriate

### Contribution Checklist

Before opening your first PR, verify:

- [ ] All existing tests pass (`python -m pytest tests/ -v`)
- [ ] Lint passes with zero findings (`ruff check .`)
- [ ] TypeScript type check passes (`npm --prefix frontend run typecheck`)
- [ ] New functionality has test coverage
- [ ] Any new API route uses `@require_permission(Permission.X)`
- [ ] Any new model field with PII uses `EncryptionManager` property encryption
- [ ] `CHANGELOG.md` updated under `Unreleased`
- [ ] PR template is fully completed including the security checklist

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for the full process.

---

## Key Reference Files

| Topic | File(s) |
|-------|---------|
| Flask startup and middleware | `app.py` |
| Shared extensions (db, rbac, encryption) | `extensions.py` |
| All database models | `models.py` |
| Environment config classes | `config.py` |
| 17-axis coordinate system | `core/coordinate_system.py` |
| Truth Engine tiers and routing | `backend/truth_engine/truth_core/engine.py`, `tiers.py` |
| QuadPersona definitions | `backend/truth_engine/truth_core/personas.py` |
| Permission definitions (RBAC) | `backend/security/rbac.py` |
| Field-level encryption | `backend/security/encryption_manager.py` |
| Active defense (Supervisor LLM) | `backend/security/active_defense.py` |
| LLM provider routing | `backend/llm_gateway/gateway.py` |
| MCP tool registry | `backend/mcp_server/registry.py` |
| Frontend API clients | `frontend/lib/` |
| Frontend pages | `frontend/app/` |
| CI pipeline | `.github/workflows/ci.yml` |
| Security controls reference | `docs/SECURITY.md` |
| API reference | `docs/API.md` |

---

## Team Contacts and Escalation

| Role | Responsibility | Contact |
|------|----------------|---------|
| Platform Engineering Lead | Architecture questions, PR review | GitHub @mention on PR |
| Security Engineering | Security review questions | [security@datalogicengine.com](mailto:security@datalogicengine.com) |
| SRE / Operations | Production incidents | [ops@datalogicengine.com](mailto:ops@datalogicengine.com) |
| Community / Conduct | Code of conduct questions | [conduct@datalogicengine.com](mailto:conduct@datalogicengine.com) |

For infrastructure questions, consult the operational runbooks at [`docs/OPERATIONAL_RUNBOOKS.md`](OPERATIONAL_RUNBOOKS.md).

---

## Glossary

| Term | Definition |
|------|-----------|
| **UKG** | Universal Knowledge Graph — the 17-axis knowledge space this platform operates in |
| **USKD** | Universal Simulated Knowledge Database — the simulation-layer extension of the UKG |
| **KA** | Knowledge Algorithm — one of 117 discrete reasoning/processing algorithms that can be applied to knowledge nodes |
| **17-Axis System** | The Nuremberg-style hierarchical coordinate system that addresses every knowledge node across 17 dimensions |
| **Truth Engine** | The 5-tier adaptive reasoning engine that classifies and processes every AI query |
| **TruthCore** | The orchestration layer of the Truth Engine — selects tiers and coordinates reasoning steps |
| **TruthGate** | The compliance and budget enforcement gateway within the Truth Engine |
| **TruthMemory** | The audit trail and metrics subsystem of the Truth Engine |
| **TruthLink** | The internal event bus and blockchain adapter for immutable audit records |
| **QuadPersona** | Four epistemic personas (Pillar Expert, Sector Analyst, Cross-Domain Linker, Compliance Guardian) applied during multi-persona reasoning |
| **MCP** | Model Context Protocol — the protocol for calling external tools (Jira, Salesforce) during knowledge processing |
| **Active Defense** | A secondary "Supervisor" LLM that analyzes every user message before it reaches the Truth Engine; uses fail-closed design |
| **RBAC** | Role-Based Access Control — the `Permission` enum + `@require_permission()` decorator pattern enforced on all API routes |
| **KEK/DEK** | Key Encryption Key / Data Encryption Key — the key hierarchy used for AES-256 field-level encryption |
| **Nuremberg Numbering** | Dot-delimited hierarchical notation for knowledge coordinates (e.g., `2.13.4.2`) |
| **Octopus Node** | A knowledge graph node type representing multi-domain regulatory crosswalks |
| **Honeycomb Node** | A knowledge graph node type representing cross-domain knowledge linkages |
| **Spiderweb Node** | A knowledge graph node type representing compliance relationship maps |
| **Circuit Breaker** | The LLM Gateway pattern that automatically fails over to the next provider when a primary provider errors |
| **RLS** | Row-Level Security — PostgreSQL feature enforcing tenant isolation at the database engine level |
| **SLO** | Service Level Objective — the latency and availability targets tracked by the observability layer |
| **Correlation ID** | A UUID assigned to every incoming request and propagated through all service calls for end-to-end tracing |
| **Support Bundle** | A sanitized diagnostic archive generated for incident triage — credentials and PII are stripped before export |
