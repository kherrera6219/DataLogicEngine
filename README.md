# Universal Knowledge Graph (UKG) Engine

### Enterprise-Grade AI Knowledge Synthesis & Orchestration Platform

[![Version](https://img.shields.io/badge/Version-2.3.1-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Polyform--Noncommercial-red)](LICENSE)
[![Next.js](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-blue)](https://react.dev/)
[![Hardened](https://img.shields.io/badge/Security-Enterprise--Hardened-success)](docs/SECURITY.md)
[![Compliance](https://img.shields.io/badge/Compliance-SOC2%20/%20ISO--27001%20Ready-success)](docs/PRODUCTION_READINESS.md)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-Session--Hardened-red)](https://redis.io/)

---

> **NOTICE**: Effective 2026-01-15, this project transitioned from the MIT License to the PolyForm Noncommercial License 1.0.0. See [`LICENSE`](LICENSE) for details.

## 🏗️ Executive Summary

The **Universal Knowledge Graph (UKG) Engine** is a sophisticated, hardened middleware platform designed to bridge the gap between enterprise data and Large Language Models. Built for mission-critical applications, it provides a "Reasoning-as-a-Service" layer that ensures every AI interaction is **grounded, traceable, and secure**.

By utilizing a unique **17-Axis Coordinate Framework**, the engine contextualizes unstructured data into a high-fidelity graph, allowing agents to navigate complex regulatory, temporal, and spatial domains with zero hallucination risk.

---

## 🌟 Enterprise Value Proposition

| **Reliability**                                                           | **Security**                                                        | **Performance**                                                       | **Observability**                                                      |
| :------------------------------------------------------------------------ | :------------------------------------------------------------------ | :-------------------------------------------------------------------- | :--------------------------------------------------------------------- |
| **Circuit Breakers**: Automatic failover & recovery for LLM providers.    | **Hardened IAM**: MFA (TOTP), RBAC, and Account Lockout protection. | **Global Caching**: Redis-backed read-through caching for graph ops.  | **Unified Tracing**: End-to-end correlation ID across SDK & API.       |
| **Failover Logic**: Multi-provider resilience (OpenAI, Azure, Anthropic). | **Encryption**: AES-256 field-level encryption for PII at rest.     | **Optimized IO**: Gunicorn/Celery workers for high-concurrency tasks. | **Audit Chain**: Hash-linked audit trails for compliance (SOC2/HIPAA). |

The **Universal Knowledge Graph (UKG) System** is an enterprise-grade AI orchestration platform that acts as an intelligent middleware layer between applications and Large Language Models (LLMs). It injects verified enterprise knowledge into AI reasoning while maintaining complete auditability and compliance.

### What Problem Does It Solve?

**The Challenge**: Standard LLMs operate as "black boxes" - you can't verify their reasoning, ensure they use your enterprise data correctly, or comply with regulatory requirements (SOC2, GDPR, HIPAA, EU AI Act).

**The Solution**: DataLogicEngine intercepts LLM requests, enriches them with your verified knowledge graph, executes reasoning through a **10-Layer High-Fidelity Simulation Stack**, and provides complete audit trails for every decision. **The system is now fully productionized with all mocks removed.**

### Technology Stack

**Frontend:**

- Next.js 16 (App Router) with React 19
- TypeScript 5.x for type safety
- Tailwind CSS 4.x + Shadcn UI (Radix primitives)
- SWR for real-time data fetching

**Backend:**

- Flask 3.1 with Gunicorn (4 workers)
- PostgreSQL 15+ (40+ tables with multi-tenancy)
- Redis 5+ for caching and rate limiting
- Celery for async task processing
- SQLAlchemy 2.0 ORM

**Key Technologies:**

- Model Context Protocol (MCP) for LLM agent integration
- 17-Axis Knowledge Framework for multi-dimensional context
- Hash-chain audit trails (EU AI Act Article 53 compliant)
- Circuit breakers and automatic failover
- **MFA (TOTP)**: Enterprise-grade multi-factor authentication
- **RBAC**: Granular role-based access control with permission inheritance
- **Field-Level Encryption**: AES-256-GCM protection for PII (emails, metadata)
- **GraphQL API** for flexible data querying (`/graphql`)
- **WebSocket** real-time updates (simulation progress, notifications)
- **3D Graph Visualization** with force-directed layout (Three.js)
- **Multi-Persona Consensus** (KA-038) for high-stakes decision validation
- **Local ML Serving** (vLLM/Ollama) with tier-prioritized routing
- **Kubernetes Operator** for self-healing and auto-scaling workers
- **Federated Knowledge Sharing** (KA-114/115) with ZKP verification

---

## Key Features

### 🧠 17-Axis Knowledge Framework

Multi-dimensional knowledge organization contextualizing data across:

| Axis | Name | Description |
|------|------|-------------|
| **1** | Pillar Levels | Core knowledge pillars (FAR, DFARS, CFR) |
| **2** | Sectors | Industry sectors and market areas |
| **3** | Honeycomb | Cross-domain intra-expansion |
| **4** | Branches | Knowledge hierarchies/Methods |
| **5** | Nodes | Specific knowledge nodes/Tools |
| **6** | Octopus Hub | One-to-many regulatory mapping |
| **7** | Spiderweb Mesh | Many-to-many compliance mapping |
| **8** | Knowledge Expert | Expert persona (domain SME) |
| **9** | Sector Expert | Expert persona (practitioner) |
| **10** | Regulatory Expert | Expert persona (octopus-driven) |
| **11** | Compliance Expert | Expert persona (spiderweb-driven) |
| **12** | Location | Geographic and spatial context |
| **13** | Temporal | Time periods, versions, and eras |
| **14** | Risk & Confidence | Probability vectors and trust scores |
| **15** | Federated Intelligence | Cross-tenant and distributed state |
| **16** | Arrows of Time | Causality chains and temporal vectors |
| **17** | Observability | Audit trails and performance markers |

### ⚖️ Truth Engine (5-Tier Workflow)

Sophisticated reasoning with graduated complexity:

1. **Trivial** - Simple lookups (<1s)
2. **Simple** - Single-step logic
3. **Complex** - Multi-step reasoning with validation
4. **Critical** - High-stakes decisions with multiple validators
5. **Expert** - Domain expert involvement required

**Features**: Budget tracking, policy gates, confidence scoring, hash-chain audit trails

### 🔍 Full Execution Traceability

Every AI decision is captured with:

- **TraceRun**: UUID-based execution trace
- **TraceStage**: Stage-by-stage breakdown with timing
- **TraceEvidence**: Supporting evidence items
- **TraceClaim**: Factual claims with verification
- **TracePersona**: Persona involvement tracking
- **TracePolicyDecision**: Policy enforcement audit
- **TraceKAInvocation**: Knowledge Algorithm calls

**Export**: JSON, CSV for compliance reporting

### 🤖 Model Context Protocol (MCP) Server

Native MCP implementation exposing:

- **Resources**: Knowledge graph stats, pillars, algorithms
- **Tools**: 116 Knowledge Algorithms as executable tools
- **Prompts**: Expert persona templates, regulatory analysis

**Compatible with**: Claude AI, GPT-4 with function calling, any MCP-compliant agent

### 🌐 LLM Gateway (Universal Adapter)

Support for multiple providers with intelligent routing:

- **OpenAI** (GPT-4, GPT-4 Turbo)
- **Azure OpenAI** (Enterprise deployments)
- **Anthropic** (Claude 3.5 Sonnet, Opus)
- **Google Vertex AI** (Gemini)

**Features**:

- Encrypted API key storage (Fernet)
- Automatic provider failover
- Circuit breaker pattern for resilience
- Rate limiting (RPM/TPM)
- Request/response streaming
- Usage analytics

### 🏢 Multi-Tenancy & Security

Enterprise-grade tenant isolation:

- `tenant_id` enforcement across all 40+ database tables
- **Hardened User Model**: Account lockout (5 attempts), password expiry, and complexity enforcement
- **MFA**: Native TOTP support with secure backup codes
- **RBAC**: Granular permission system (e.g., `user:manage_roles`, `security:read`)
- **Encryption**: Field-level encryption for PII and sensitive simulation data
- SSO/OIDC integration (Azure AD/Entra ID)
- API key management with encryption and rotation
- SIEM audit logging (Syslog, CSV export)

### 📊 Compliance & Auditing

Production-ready compliance features:

- **EU AI Act Article 53**: Immutable audit trails with hash chains
- **SOC2**: Evidence collection, encryption at rest, access controls
- **GDPR**: Data minimization, tenant isolation, right to be forgotten
- **HIPAA**: Audit trails, encryption, role-based access

---

The **Universal Knowledge Graph (UKG) System** operates as **"API In / API Out"** - an intelligent middleware that enhances LLM reasoning.

---

## 🛠️ "API In / API Out" Architecture

The DataLogicEngine operates as the "Brain" between your interfaces and the raw LLM cloud.

### 1. Request Ingestion

External systems send a standard chat request:

```json
POST /api/v1/gateway/chat
{
  "messages": [
    {"role": "user", "content": "What are AI compliance risks in healthcare?"}
  ],
  "model": "gpt-4o",
  "mode": "ukg",
  "trace_enabled": true
}
```

### 2. Processing (The Knowledge Engine)

Instead of a single LLM pass, the engine executes a multi-layered pipeline:

- **L1 (Context Initialization)**: Parses query into `Coord17Intent`, resolves coordinates, and sets guardrails.
- **L2 (USKD Materialization)**: Materializes a bounded subgraph (the "mini-world") from the UKG into the working memory.
- **L3 (Controlled Expansion)**: Agentic enrichment layer that fills knowledge gaps using specialized KAs.
- **L4 (POV Overlays)**: Adds stakeholder constraints and interpretive weighting without factual mutation.
- **L5 (Quad Persona Projections)**: Parallel multi-persona debate with conflict detection and synthesis.
- **L6 (Validation & Scoring)**: High-fidelity confidence weighting and risk driver mapping.
- **L7 (Scenario Simulation)**: Nested forks (Baseline/Stress/Optimistic) to test outcome robustness.
- **L8 (Consistency Verification)**: Cross-checks claims against constraints with recursive refinement triggers.
- **L9 (Strategic Alignment)**: Aligns the validated state with enterprise strategy and roadmaps.
- **L10 (Final Emergence Gate)**: Release authority gate that detects hallucinations and authorizes output.

#### Knowledge Algorithm (KA) Integration by Layer

Each layer invokes specific KAs from the 123-algorithm registry:

| Layer | KAs Wired | Description |
| :--- | :--- | :--- |
| **L1** | KA-004, KA-005, KA-036, KA-113 | Input validation, query classification, complexity routing |
| **L2** | KA-025, KA-018 | Dependency mapping, source provenance tracking |
| **L3** | KA-009, KA-010, KA-034 | Evidence validation, bias detection, adversarial reasoning |
| **L4** | KA-028, KA-057 | POV expansion, persona emotion adaptation |
| **L5** | KA-012, KA-013, KA-026, KA-038.KA-030 | Multi-persona reasoning, weighting, contradiction detection, consensus |
| **L6** | KA-039, KA-116, KA-014 | Anomaly detection, entropy scoring, confidence scoring |
| **L7** | KA-002, KA-006, KA-021, KA-040 | Tree-of-Thought, deep planning, emergence detection, hypothesis generation |
| **L8** | KA-003, KA-008, KA-014, KA-016, KA-022, KA-023, KA-024, KA-025, KA-026, KA-030, KA-034 | Trust validation gateway, cross-domain consistency, contradiction detection |
| **L9** | L9-KA-001 to L9-KA-007, KA-008, KA-010, KA-022, KA-025 | Meta-reasoning, trace analysis, belief drift, persona audit, self-critique |


### 3. Traceable Response

Returns answer **plus** complete audit trail:

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Based on UKG analysis..."
      }
    }
  ],
  "ukg_trace": {
    "trace_id": "abc-123",
    "confidence": 0.92,
    "evidence_count": 23
  }
}
```

---

## 🗺️ System Architecture

```mermaid
graph TD
    User[Enterprise Clients] -->|REST/SDK| GW[Hardened API Gateway]

    subgraph "Core Logic Engine"
        GW -->|Auth/IDP| SSO[OIDC Provider]
        GW -->|Tracing| TM[Correlation Manager]
        GW -->|Circuit Breaker| CB[Failover Manager]
    end

    subgraph "UKG Pipeline"
        CB -->|Context| UKG[17-Axis Graph]
        UKG -->|Retrieval| KA[Knowledge Algorithms]
        KA -->|Audit| AS[Hash-Chained Audit Store]
    end

    UKG -->|Grounded Prompt| LLM[LLM Cloud]
    LLM -->|Response| GW
```

### High-Level System Design

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        API[External API Client]
    end

    subgraph "Frontend Layer (Next.js 16)"
        NextJS[Next.js App Router]
        Dashboard[Dashboard]
        Chat[Chat Interface]
        Trace[Trace Explorer]
        Admin[Admin Panel]
    end

    subgraph "Backend Layer (Flask 3.1)"
        Gateway[LLM Gateway]
        Truth[Truth Engine]
        Tracing[Tracing System]
        MCP[MCP Server]
        Auth[Auth System]
    end

    subgraph "Core Engine"
        Axes[17-Axis Framework]
        KA[Knowledge Algorithms]
        Sim[Simulation Engine]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL 15+<br/>40+ Tables)]
        Redis[(Redis 5+<br/>Cache/Queue)]
    end

    subgraph "External Services"
        OpenAI[OpenAI]
        Azure[Azure OpenAI]
        Anthropic[Anthropic]
        Vertex[Google Vertex]
    end

    Browser -->|HTTPS :3000| NextJS
    API -->|REST :5000| Gateway
    NextJS -->|Proxy /api/*| Gateway
    NextJS --> Dashboard & Chat & Trace & Admin

    Gateway --> Truth
    Gateway --> MCP
    Gateway --> Tracing
    Gateway --> Auth

    Truth --> Axes
    Truth --> KA
    Truth --> Sim

    Gateway --> PG
    Gateway --> Redis
    Tracing --> PG
    Auth --> PG

    Gateway -.->|Circuit Breaker| OpenAI
    Gateway -.->|Failover| Azure
    Gateway -.->|Failover| Anthropic
    Gateway -.->|Failover| Vertex
```

### Component Breakdown

**Frontend** (`/frontend` - 15+ pages)

- Trace run explorer (stage-by-stage)
- Knowledge graph visualization
- Admin compliance dashboard
- MCP server management
- User settings and profiles

**Backend** (`/backend` - 7 core modules)

- `llm_gateway/`: Universal LLM adapter
- `truth_engine/`: 5-tier reasoning framework
- `tracing/`: Execution traceability (9 tables)
- `auth/`: SSO/OIDC, API keys, 2FA
- `security/`: Headers, audit logging, SIEM
- `middleware/`: Correlation IDs, rate limiting
- `routes/`: 8 API blueprints

**Core** (`/core` - Knowledge engine)

- `axes/`: 17-Axis Framework (30+ KB modules)
- `mcp/`: Model Context Protocol server
- `simulation/`: Scenario simulation engine
- `knowledge_algorithm/`: 116 enterprise-hardened algorithm implementations with Pydantic validation and failsafe hooks

**Database** (40+ tables)

- User & Access Control (4 tables)
- Knowledge Graph (6 tables, dual representation)
- Chat & Sessions (4 tables)
- Tracing (9 tables)
- Truth Engine (5 tables)
- MCP (4 tables)
- LLM Gateway (3 tables)
- Compliance (3 tables)
- Simulations (3 tables)

---

## Prerequisites

### Required Software

| Component      | Version | Purpose                | Installation                                     |
| -------------- | ------- | ---------------------- | ------------------------------------------------ |
| **Node.js**    | 18.17+  | Frontend runtime       | [Download](https://nodejs.org/)                  |
| **Python**     | 3.11+   | Backend runtime        | [Download](https://www.python.org/downloads/)    |
| **PostgreSQL** | 15+     | Primary database       | [Download](https://www.postgresql.org/download/) |
| **Redis**      | 5+      | Cache/queue (optional) | [Download](https://redis.io/download)            |
| **Git**        | Latest  | Version control        | [Download](https://git-scm.com/)                 |

### System Requirements

**Development:**

- CPU: 2+ cores
- RAM: 8GB minimum, 16GB recommended
- Disk: 10GB free space
- OS: Linux, macOS, Windows (WSL2 recommended)

**Production:**

- CPU: 4+ cores
- RAM: 16GB minimum, 32GB recommended
- Disk: 50GB+ SSD
- Network: 100Mbps+

### External Services (Optional)

For full functionality, configure at least one:

- **OpenAI API Key** for GPT-4 access
- **Azure OpenAI** deployment
- **Anthropic API Key** for Claude access
- **Google Vertex AI** credentials

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/kherrera6219/DataLogicEngine.git
cd DataLogicEngine
```

### 2. Database Setup

**PostgreSQL:**

```bash
# Create database
createdb ukg_db

# Or using psql
psql -U postgres
CREATE DATABASE ukg_db;
\q
```

**Redis (optional):**

```bash
# Linux/macOS
redis-server

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### 3. Backend Setup

```bash
# Navigate to project root
cd DataLogicEngine

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your DATABASE_URL and other settings

# Run database migrations
flask db upgrade

# Seed initial data (optional)
python backend/seed_data.py

# Start backend server
python main.py
```

Backend will start on **http://localhost:5000**

### 4. Frontend Setup

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will start on **http://localhost:3000**

### 5. Verify Installation

1. Open browser to http://localhost:3000
2. You should see the landing page
3. Navigate to `/dashboard` (may require login)
4. Check backend health: http://localhost:5000/health

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here-min-32-chars
SESSION_SECRET=your-session-secret-here

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/ukg_db
DB_POOL_SIZE=20
DB_POOL_RECYCLE=300

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET_KEY=your-jwt-secret-key
SESSION_LIFETIME_MINUTES=30
PASSWORD_MIN_LENGTH=12
ENCRYPTION_KEK_SECRET=your-32-byte-base64-encoded-kek-secret

# SSO/OIDC (optional)
OIDC_CLIENT_ID=your-azure-app-id
OIDC_CLIENT_SECRET=your-azure-client-secret
OIDC_DISCOVERY_URL=https://login.microsoftonline.com/{tenant}/.well-known/openid-configuration

# LLM Providers (at least one required)
OPENAI_API_KEY=sk-...
AZURE_OPENAI_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_VERTEX_PROJECT_ID=your-project

# Security
MAX_CONTENT_LENGTH=16777216  # 16 MB
GLOBAL_RATE_LIMIT=200 per hour
ENABLE_CORS=True
CORS_ORIGINS=http://localhost:3000

# Observability
SENTRY_DSN=https://...@sentry.io/...
ENABLE_AUDIT_LOGGING=True
SIEM_SYSLOG_HOST=syslog.example.com
SIEM_SYSLOG_PORT=514

# MCP Configuration
MCP_ENABLED=True
MCP_DEFAULT_SERVER_NAME=DataLogicEngine-UKG
```

### Frontend Configuration

Create `frontend/.env.local`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:5000

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_MCP_CONSOLE=true
```

### Database Migrations

```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade

# View migration history
flask db history
```

---

## Core Components

### 1. 17-Axis Knowledge Framework

The foundation of contextual knowledge organization:

```python
# Example: Query resolution to axes
query = "What are GDPR compliance requirements for AI in healthcare?"

# Resolved Axes:
axes = {
    "axis_2_sector": "Healthcare",
    "axis_3_domain": "AI",
    "axis_6_regulatory": ["GDPR", "HIPAA"],
    "axis_7_compliance": ["Data Privacy", "AI Governance"],
    "axis_12_location": "EU",
    "axis_13_time": "2024"
}

# Knowledge retrieval filtered by these coordinates
results = knowledge_graph.query(axes=axes)
```

**All 17 Axes:**

| # | Name | Purpose |
|---|------|----------|
| 1 | Pillar Levels | Core knowledge pillars (FAR, DFARS, CFR) |
| 2 | Sectors | Industry sectors (NAICS, SIC, PSC) |
| 3 | Honeycomb | Cross-domain intra-expansion |
| 4 | Branches | Knowledge sub-branches |
| 5 | Nodes | Atomic knowledge nodes |
| 6 | Octopus Crosswalk | One-to-many regulatory mapping |
| 7 | Spiderweb Crosswalk | Many-to-many compliance mapping |
| 8 | Knowledge Expert | Expert persona (knowledge SME) |
| 9 | Sector Expert | Expert persona (industry practitioner) |
| 10 | Regulatory Expert | Expert persona (octopus-driven) |
| 11 | Compliance Expert | Expert persona (spiderweb-driven) |
| 12 | Location | Geospatial and jurisdiction |
| 13 | Temporal | Time periods and versions |
| 14 | Source Provenance | Where did this come from? (lineage) |
| 15 | Object Type | What kind of thing is this? (clause, control) |
| 16 | Validation State | How verified? (raw → audited) |
| 17 | Security/Access | Who can see/use this? (public, CUI) |

### 2. Truth Engine

5-tier reasoning with budget and compliance:

```python
# Create Truth Session
session = TruthSession(
    tier="complex",  # Tier level
    budget_tokens=10000,  # Token limit
    budget_cost_usd=1.00,  # Cost limit
    policy_pack="enterprise_v2.5"
)

# Execute reasoning
result = truth_engine.execute(
    session=session,
    query="Analyze merger compliance risks",
    context={...}
)

# Audit trail automatically created
audit_events = session.get_audit_trail()
# Returns hash-chain immutable events
```

### 3. Tracing System

Complete execution visibility:

```python
# Every execution creates a TraceRun
from ukg_sdk import UKGClient

client = UKGClient(base_url="http://localhost:5000/api/v1", api_key="...")

# List recent runs
runs = client.runs.list(status="pass", page=1, per_page=20)

# Get detailed trace
trace = client.runs.get("abc-123-def-456")
print(f"Confidence: {trace.scores.confidence}")
print(f"Duration: {trace.duration_seconds}s")

# Get execution stages
stages = client.runs.stages("abc-123-def-456")
for stage in stages:
    print(f"{stage.name}: {stage.duration_seconds}s")

# Get supporting evidence
evidence = client.runs.evidence("abc-123-def-456")
for e in evidence:
    print(f"Source: {e.source.type} - {e.snippet}")

# Export for compliance
export = client.exports.create("abc-123-def-456", format="json")
client.exports.download(export.export_id, "audit-trail.json")
```

### 4. MCP Server

Expose knowledge as tools for LLM agents:

```python
# MCP Server automatically exposes 100+ tools
# Example tool definitions:

{
  "name": "query_knowledge_graph",
  "description": "Query the Universal Knowledge Graph",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {"type": "string"},
      "axes": {"type": "object"}
    }
  }
}

{
  "name": "check_compliance",
  "description": "Check compliance with regulatory framework",
  "input_schema": {
    "type": "object",
    "properties": {
      "framework": {"type": "string", "enum": ["GDPR", "HIPAA", "SOC2"]},
      "context": {"type": "object"}
    }
  }
}
```

**Claude AI Integration:**

```python
# Claude can now use these tools natively
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "What are healthcare AI compliance risks?"}],
    tools=[
        # MCP tools automatically injected
        {"name": "query_knowledge_graph", ...},
        {"name": "check_compliance", ...}
    ]
)
```

### 5. Knowledge Algorithms (116)

Enterprise-hardened algorithms for complex reasoning, planning, and validation. Every KA is strictly typed via Pydantic and includes graceful degradation hooks.

```bash
GET /api/v1/ka/algorithms
# Returns list of 100+ algorithms

POST /api/v1/ka/execute
{
  "algorithm_id": "ka056_recursive_planning",
  "params": {
    "goal": "Implement compliance framework",
    "depth": 5
  }
}
```

**Algorithm Categories:**

- Knowledge Retrieval (KA001-KA025)
- Risk Assessment (KA026-KA050)
- Compliance Checking (KA051-KA075)
- Data Lifecycle (KA076-KA090)
- System Optimization (KA091-KA105)
- Integration & Scaling (KA106-KA110)
- Advanced Orchestration (KA111-KA116)

---

## Enterprise Features

### Security Architecture

**Layers of Defense:**

1. **Network**: HTTPS enforcement, TLS 1.3, reverse proxy support
2. **Application**: CSRF, XSS, SQL injection prevention
3. **Authentication**: Session, SSO, API keys, OAuth, JWT
4. **Authorization**: RBAC, tenant isolation, API key scoping
5. **Data**: Encryption at rest, encryption in transit, Fernet key storage
6. **Audit**: Complete request logging, SIEM integration

**Security Headers Applied:**

```
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
```

### Multi-Tenancy

Complete data isolation per tenant:

```python
# All queries automatically filter by tenant
@login_required
def get_knowledge_nodes():
    tenant_id = g.tenant_id  # From session/SSO token
    nodes = Node.query.filter_by(tenant_id=tenant_id).all()
    return jsonify(nodes)
```

**Tenant ID Sources:**

1. User.tenant_id from database
2. Azure AD 'tid' claim from SSO token
3. API key tenant association

**Isolation Scope:**

- Knowledge graph nodes/edges
- Chat sessions and messages
- Trace runs and stages
- Audit logs
- API keys
- All 40+ database tables

### Compliance Reporting

```bash
# Export audit logs
GET /api/v1/compliance/audit/export?days=30&format=csv
# Returns CSV with all audit events

# Get compliance standards
GET /api/v1/compliance/standards
# Returns active compliance frameworks

# Generate SOC2 evidence
POST /api/v1/compliance/evidence/generate
{
  "type": "soc2",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

### High Availability

**Connection Pooling:**

```python
# PostgreSQL
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_recycle": 300,
    "pool_pre_ping": True
}
```

**Circuit Breakers:**

```python
# LLM Gateway automatic circuit breaking
if provider_failure_rate > 0.5:
    circuit_breaker.open()
    fallback_to_secondary_provider()
```

**Health Checks:**

```bash
GET /health
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "llm_providers": {
      "openai": "available",
      "azure": "available"
    }
  },
  "uptime_seconds": 86400
}
```

---

## Python SDKs

### UKG Python SDK (`/sdk/python`)

Lightweight client for trace API:

```bash
pip install ukg-sdk
```

```python
from ukg_sdk import UKGClient

# Initialize
client = UKGClient(
    base_url="http://localhost:5000/api/v1",
    api_key="your-api-key"
)

# List runs with filtering
runs = client.runs.list(
    status="pass",
    start_date="2024-01-01",
    end_date="2024-12-31",
    page=1,
    per_page=50
)

# Get comprehensive run details
run = client.runs.get("run-uuid")
print(f"Status: {run.status}")
print(f"Confidence: {run.scores.confidence}")
print(f"Duration: {run.duration_seconds}s")

# Get execution stages
stages = client.runs.stages("run-uuid")
for stage in stages:
    print(f"{stage.name}: {stage.status} ({stage.duration_seconds}s)")

# Get evidence
evidence = client.runs.evidence("run-uuid")
for e in evidence:
    print(f"{e.source.type}: {e.snippet}")

# Get claims
claims = client.runs.claims("run-uuid")
for claim in claims:
    print(f"{claim.claim_text} (confidence: {claim.confidence})")

# Export trace
export = client.exports.create("run-uuid", format="json")
client.exports.download(export.export_id, "trace.json")

# Async support
from ukg_sdk import UKGAsyncClient

async def get_runs():
    async with UKGAsyncClient(base_url="...", api_key="...") as client:
        runs = await client.runs.list(status="pass")
        return runs
```

### UKG Overlay SDK (`/sdk/UKG_Python_SDK`)

Full-featured SDK with embedded reasoning:

```bash
cd sdk/UKG_Python_SDK
pip install -e ".[postgres,redis,registries]"
```

```python
import asyncio
from ukg_sdk import UKGOverlay
from ukg_sdk.providers import OpenAIProvider, AnthropicProvider

async def main():
    # Initialize with provider
    provider = OpenAIProvider()  # Reads OPENAI_API_KEY
    ukg = UKGOverlay(
        provider=provider,
        model="gpt-4o-mini",
        memory_adapter="postgres",  # or "redis", "memory"
        audit_storage="postgres"
    )

    # Run query with UKG reasoning
    result = await ukg.run(
        query="What are the compliance risks for AI in healthcare?",
        user_id="user-123",
        meta={
            "pillar": "PL-001",
            "axis2": "Healthcare",
            "axis3": "AI",
            "date": "2024-01-09"
        }
    )

    print(f"Answer: {result['answer']}")
    print(f"Tier: {result['tier']}")
    print(f"Coordinate: {result['coordinate']}")
    print(f"Confidence: {result['confidence']}")

    # Switch providers dynamically
    anthropic_provider = AnthropicProvider()
    ukg.provider = anthropic_provider

    result2 = await ukg.run(query="...", user_id="user-123")

asyncio.run(main())
```

**Features:**

- 17-axis coordinate resolver
- Memory adapters (in-memory, Postgres, Redis)
- Compliance-grade audit storage
- Bundled canonical configs and datasets
- Multiple LLM provider support

---

## API Documentation

### Authentication

All endpoints require one of:

**Session Cookie** (Frontend):

```javascript
// Automatic with frontend proxy
fetch("/api/v1/knowledge/nodes");
```

**Bearer Token** (External):

```bash
curl -H "Authorization: Bearer your-jwt-token" \
  http://localhost:5000/api/v1/trace/runs
```

**API Key** (Programmatic):

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:5000/api/v1/gateway/chat
```

### Endpoint Categories

| Service        | Prefix               | Description             | Key Endpoints                                   |
| -------------- | -------------------- | ----------------------- | ----------------------------------------------- |
| **Auth**       | `/api/v1/auth`       | Authentication & SSO    | `POST /login`, `GET /login/sso`, `POST /logout` |
| **Gateway**    | `/api/v1/gateway`    | LLM orchestration       | `POST /chat`, `POST /stream`                    |
| **Trace**      | `/api/v1/trace`      | Execution tracing       | `GET /runs`, `GET /runs/:id/stages`             |
| **MCP**        | `/api/v1/mcp`        | Model Context Protocol  | `GET /servers`, `POST /tools/:id/call`          |
| **Knowledge**  | `/api/v1/knowledge`  | Graph operations        | `GET /nodes`, `POST /edges`                     |
| **KA**         | `/api/v1/ka`         | Algorithm execution     | `GET /algorithms`, `POST /execute`              |
| **Compliance** | `/api/v1/compliance` | Audit & reporting       | `GET /audit-logs`, `GET /audit/export`          |
| **Analytics**  | `/api/v1/analytics`  | Dashboard metrics       | `GET /summary`, `GET /trends`, `GET /axis-distribution` |
| **GraphQL**    | `/graphql`           | Flexible queries        | GraphiQL IDE, queries, mutations                |
| **Admin**      | `/api/v1/admin`      | User & provider mgmt    | `GET /users`, `POST /providers`                 |
| **Simulation** | `/api/v1/simulation` | Scenario simulation     | `POST /start`, `GET /:id`                       |
| **System**     | `/health`            | Health check            | `GET /health`                                   |

### Example Requests

**Chat with UKG Context:**

```bash
curl -X POST http://localhost:5000/api/v1/gateway/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "messages": [
      {"role": "user", "content": "What are GDPR compliance requirements?"}
    ],
    "model": "gpt-4o",
    "mode": "ukg",
    "trace_enabled": true
  }'
```

**Get Trace Runs:**

```bash
curl -X GET "http://localhost:5000/api/v1/trace/runs?status=pass&page=1&per_page=20" \
  -H "Authorization: Bearer your-token"
```

**Execute Knowledge Algorithm:**

```bash
curl -X POST http://localhost:5000/api/v1/ka/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "algorithm_id": "ka056_recursive_planning",
    "params": {
      "goal": "Implement data governance",
      "depth": 5
    }
  }'
```

**Export Compliance Audit:**

```bash
curl -X GET "http://localhost:5000/api/v1/compliance/audit/export?days=30&format=csv" \
  -H "Authorization: Bearer admin-token" \
  > audit-export.csv
```

For complete API documentation with request/response schemas, see:

- **[docs/API.md](docs/API.md)** - Full endpoint reference
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture
- **[docs/MCP_INTEGRATION.md](docs/MCP_INTEGRATION.md)** - MCP protocol details

---

## Deployment

### Docker Compose (Recommended for Development)

```bash
# Build and start all services
docker-compose up -d

# Services started:
# - backend (Flask) on :5000
# - frontend (Next.js) on :3000
# - postgres on :5432
# - redis on :6379

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Kubernetes (Production)

```bash
# Apply configurations
kubectl apply -f deploy/k8s/

# Components deployed:
# - Backend Deployment (4 replicas)
# - Frontend Deployment (2 replicas)
# - PostgreSQL StatefulSet
# - Redis Deployment
# - Ingress
# - ConfigMaps, Secrets
```

### Cloud Platforms

**Azure:**

- Azure App Service (Backend)
- Azure Static Web Apps (Frontend)
- Azure Database for PostgreSQL
- Azure Redis Cache
- See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for details

**AWS:**

- ECS/EKS for containers
- RDS for PostgreSQL
- ElastiCache for Redis
- CloudFront for frontend
- See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for details

---

## Testing

### Backend Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_llm_gateway.py

# Run with coverage
pytest --cov=backend --cov-report=html tests/

# Run integration tests only
pytest -m integration tests/
```

### Frontend Tests

```bash
cd frontend

# Type checking
npm run type-check

# Linting
npm run lint

# Build verification
npm run build

# Unit tests (if configured)
npm test
```

### End-to-End Tests

```bash
# Start services
docker-compose up -d

# Run E2E tests
npm run test:e2e

# Cleanup
docker-compose down
```

---

## Troubleshooting

### Common Issues

#### Database Connection Errors

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solution**:

```bash
# Check PostgreSQL is running
pg_isready

# Verify DATABASE_URL in .env
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check logs
tail -f /var/log/postgresql/postgresql-15-main.log
```

#### Redis Connection Issues

**Problem**: `redis.exceptions.ConnectionError`

**Solution**:

```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Restart Redis
redis-server

# Or with Docker
docker start redis
```

```bash
cd frontend

# Clear cache and reinstall
rm -rf node_modules .next
npm install

# Clear Next.js cache
rm -rf .next

# Rebuild
npm run build
```

#### Migration Errors

**Problem**: `alembic.util.exc.CommandError: Can't locate revision`

**Solution**:

```bash
# Check current revision
flask db current

# View migration history
flask db history

# Stamp database at head
flask db stamp head

# Try upgrade again
flask db upgrade
```

#### LLM Provider Timeouts

**Problem**: `Timeout waiting for LLM response`

**Solution**:

```python
# In .env, increase timeout
LLM_TIMEOUT_SECONDS=120

# Enable circuit breaker logging
ENABLE_CIRCUIT_BREAKER_LOGGING=True

# Check provider status
GET /api/v1/admin/providers
```

### Debug Mode

Enable detailed logging:

```bash
# .env
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
ENABLE_SQL_ECHO=True
```

### Health Checks

```bash
# System health
curl http://localhost:5000/health

# Database health
flask db current

# Redis health
redis-cli ping

# Frontend build
cd frontend && npm run build
```

### Performance Issues

**Slow database queries:**

```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Analyze table
ANALYZE nodes;

-- Check indexes
\d nodes
```

**High memory usage:**

```bash
# Check Python memory
import tracemalloc
tracemalloc.start()

# Monitor with htop
htop

# Adjust pool size in .env
DB_POOL_SIZE=10
```

---

## Contributing

We welcome contributions! Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards

**Backend (Python):**

- Follow PEP 8 style guide
- Use type hints where possible
- Add docstrings to all functions
- Run `black` and `flake8` before committing
- Maintain test coverage above 80%

**Frontend (TypeScript):**

- Follow ESLint rules
- Use TypeScript for type safety
- Follow component naming conventions (PascalCase)
- Use Tailwind CSS for styling
- Test in both light and dark modes

### Pull Request Guidelines

- Clearly describe the changes and their purpose
- Link to related issues
- Include tests for new features
- Update documentation as needed
- Ensure CI/CD passes
- Request review from maintainers

---

## Security

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Please report security issues to: [security@example.com](mailto:security@example.com)

See [`SECURITY.md`](SECURITY.md) for our security policy and response process.

### Security Best Practices

**For Deployment:**

- Use strong `SECRET_KEY` (32+ random characters)
- Enable HTTPS in production
- Configure firewall rules
- Use environment variables for secrets
- Enable audit logging
- Regularly update dependencies
- Implement rate limiting
- Use strong password policies
- Enable 2FA for admin accounts

**For Development:**

- Never commit secrets to Git
- Use `.env` for local configuration
- Keep dependencies updated
- Run security scans regularly
- Review code for SQL injection, XSS
- Use parameterized queries
- Validate all inputs

---

## Support

### Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System architecture deep-dive
- **[API Reference](docs/API.md)** - Complete API documentation
- **[MCP Integration](docs/MCP_INTEGRATION.md)** - Model Context Protocol guide
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment
- **[File Structure](docs/FILE_STRUCTURE.md)** - Project organization

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/kherrera6219/DataLogicEngine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kherrera6219/DataLogicEngine/discussions)
- **Email**: support@example.com

### Community

- **Code of Conduct**: See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- **Contributing**: See [`CONTRIBUTING.md`](CONTRIBUTING.md)
- **Changelog**: See [`CHANGELOG.md`](CHANGELOG.md)

---

## Roadmap

### Current Status: Production-Ready ✅

**Completed (v1.0):**

- ✅ Core Knowledge Graph implementation
- ✅ 17-Axis Framework
- ✅ Truth Engine with 5-tier workflow
- ✅ Complete tracing system (40+ tables)
- ✅ MCP server with 123+ tools
- ✅ LLM Gateway (4 providers)
- ✅ Multi-tenancy support
- ✅ SSO/OIDC integration
- ✅ Frontend dashboard (20+ pages)
- ✅ Python SDKs
- ✅ Compliance features (SOC2, GDPR, HIPAA)
- ✅ WebSocket real-time updates
- ✅ Advanced 3D Graph Visualization
- ✅ Enhanced analytics dashboard
- ✅ GraphQL API (Queries/Mutations)
- ✅ Internationalization (i18n) support
- ✅ Mobile PWA support
- ✅ 123 Hardened Knowledge Algorithms
- ✅ Multi-persona consensus system (KA-038)
- ✅ Local ML model serving (Ollama/vLLM)
- ✅ Layer 8 Trust Validation Gateway
- ✅ Layer 9 Meta-Reasoning Controller

**Planned (v3.0):**

- 📋 Mobile applications (React Native)
- 📋 Kubernetes operator for automated ops (v1 ongoing)
- 📋 Federated knowledge sharing (POC)

---

## Acknowledgments

### Built With

- **[Next.js](https://nextjs.org/)** - React framework for production
- **[Flask](https://flask.palletsprojects.com/)** - Python web framework
- **[PostgreSQL](https://www.postgresql.org/)** - Advanced open source database
- **[Redis](https://redis.io/)** - In-memory data structure store
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - Python SQL toolkit
- **[Tailwind CSS](https://tailwindcss.com/)** - Utility-first CSS framework
- **[Shadcn UI](https://ui.shadcn.com/)** - Re-usable components
- **[SWR](https://swr.vercel.app/)** - React Hooks for data fetching

### Special Thanks

- Anthropic for Model Context Protocol specification
- OpenAI for GPT-4 API
- The open-source community

---

## 📂 Documentation Matrix

- **[Architecture Deep-Dive](docs/ARCHITECTURE.md)**: Detailed breakdown of the middleware stack and graph processing.
- **[Security & Compliance](docs/SECURITY.md)**: Details on Multi-tenancy, SSO, and SOC2 auditability.
- **[Production Readiness](docs/PRODUCTION_READINESS.md)**: Hardening checklist, scaling, and disaster recovery.
- **[API Reference](docs/API.md)**: Comprehensive guide to the REST and MCP endpoints.
- **[Deployment Guide](docs/DEPLOYMENT.md)**: Docker, Kubernetes, and Cloud deployment patterns.

---

## 🤝 Support & Compliance

For enterprise support, SOC2 report requests, or HIPAA BAA inquiries, please contact the security team via the [Security portal](SECURITY.md).

---

# © 2026 DataLogicEngine. All Rights Reserved. Confidential & Proprietary.

## ⚖️ License

This software is licensed under the **PolyForm Noncommercial License 1.0.0**.

- **Personal/Educational Use:** Free and encouraged.
- **Commercial/Business Use:** Requires a commercial license agreement.
- **Attribution:** Required for all uses.

For commercial licensing inquiries, please reach out to [support@example.com](mailto:support@example.com).
See [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for details on commercial use definitions.

---

## Project Status

**Current Version**: v2.3.0
**Status**: Production-Ready ✅
**Last Updated**: January 15, 2026
**Maintainers**: [@kherrera6219](https://github.com/kherrera6219)

---

</div>
