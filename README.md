# Universal Knowledge Graph (UKG) Engine

## Enterprise-Grade AI Knowledge Synthesis & Orchestration Platform

[![Version](https://img.shields.io/badge/Version-4.1.0-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Polyform--Noncommercial-red)](LICENSE)
[![Next.js](https://img.shields.io/badge/Next.js-15.1-black)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-18.3-blue)](https://react.dev/)
[![Hardened](https://img.shields.io/badge/Security-Enterprise--Hardened-success)](docs/SECURITY.md)
[![Compliance](https://img.shields.io/badge/Compliance-SOC2%20/%20ISO--27001%20Ready-success)](docs/PRODUCTION_READINESS.md)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-Session--Hardened-red)](https://redis.io/)

---

> **NOTICE**: Effective 2026-01-15, this project transitioned from the MIT License to the PolyForm Noncommercial License 1.0.0. See [`LICENSE`](LICENSE) for details.

> **DEPLOYMENT MODES**: This application supports **two separate deployment modes**:
>
> - **Cloud Mode**: Traditional SaaS deployment with OAuth/SSO authentication.
> - **Desktop Mode**: Windows-native installation with zero-login identity system.
>
> These are **mutually exclusive** modes.

## 🏗️ Executive Summary

The **Universal Knowledge Graph (UKG) Engine** is a graduated, enterprise-hardened AI orchestration platform. It provides a mission-critical **"Reasoning-as-a-Service"** layer that ensures every interaction is **grounded, traceable, and secure**.

By utilizing a unique **17-Axis Coordinate Framework**, the engine contextualizes unstructured data into a high-fidelity graph. With the recently graduated **SimulationEngine** and **QuadPersonaEngine**, it offers deep counterfactual reasoning and multi-expert validation with zero hallucination risk.

---

## 🌟 Enterprise Value Proposition

| **Reliability** | **Security** | **Performance** | **Observability** |
| :--- | :--- | :--- | :--- |
| **Circuit Breakers**: Automatic failover & recovery for LLM providers. | **Hardened IAM**: MFA (TOTP), RBAC, and Account Lockout protection. | **Global Caching**: Redis-backed read-through caching for graph ops. | **Unified Tracing**: End-to-end correlation ID across SDK & API. |
| **Failover Logic**: Multi-provider resilience (OpenAI, Azure, Anthropic). | **Encryption**: Fernet (AES-128) field-level encryption for PII at rest. | **Optimized IO**: Gunicorn/Celery workers for high-concurrency tasks. | **Audit Chain**: Hash-linked audit trails for compliance (SOC2/HIPAA). |

The **Universal Knowledge Graph (UKG) System** is an enterprise-grade AI orchestration platform that acts as an intelligent middleware layer between applications and Large Language Models (LLMs).

---

## 🛠️ Technology Stack

### Frontend (v0.1.0)

- **Next.js 15.1** (App Router) with React 18.3
- **TypeScript 5.x** for type safety
- **Tailwind CSS 4.x** + Shadcn UI (Radix primitives)
- **SWR** for real-time data fetching

### Backend (v0.1.0)

- **Flask 3.1** with Gunicorn (4 workers)
- **Python 3.11+**
- **PostgreSQL 15+** (40+ tables with multi-tenancy)
- **Redis 5+** for caching and queues
- **Celery** for async tasks
- **SQLAlchemy 2.0** ORM

### Core Technologies

- **Model Context Protocol (MCP)**: For LLM agent integration.
- **17-Axis Knowledge Framework**: Implemented via `ukg_api`.
- **Encryption**: Fernet (AES-128-CBC) Key Wrapping.
- **Audit**: Hash-chain audit trails (EU AI Act Compliant).
- **MFA**: Native TOTP (Time-based One-Time Password).

---

## 🌟 Dual-Mode Architecture

DataLogicEngine is built for versatility, supporting two first-class deployment paths:

1. **Enterprise Cloud Logic Layer**: Standard SaaS deployment (Flask + Gunicorn + PostgreSQL) with OAuth/SSO.
2. **Local-First Desktop Engine**: Windows-native executable where the Flask backend is **wrapped in Electron**, using a local SQLite/PostgreSQL instance and Windows-native services for zero-config deployment.

---

## 🧪 System Architecture

### Component Breakdown

**Frontend** (`/frontend`)

- Trace run explorer (stage-by-stage)
- Knowledge graph visualization
- Admin compliance dashboard
- MCP server management

**Backend** (`/backend`)

- `llm_gateway/`: Universal LLM adapter
- `truth_engine/`: 5-tier reasoning framework
- `mcp_server/`: Model Context Protocol server (Tools, Resources, Prompts)
- `simulation/`: Scenario simulation engine
- `knowledge_algorithms/`: 116 enterprise-hardened algorithm implementations
- `tracing/`: Execution traceability
- `auth/`: SSO/OIDC, API keys, 2FA
- `security/`: Headers, audit logging, SIEM

### Data Flow

1. **Request**: `POST /api/v1/gateway/chat`
2. **Gateway**: Authenticates & Validates (Rate Limit, permissions)
3. **Logic**:
    - Resolves **17-Axis Coordinates**
    - Retrieves **Knowledge Graph** slice
    - Executes **Truth Engine** (Reasoning Tiers)
    - Runs **Simulations** (if required)
4. **LLM**: Calls Provider (OpenAI/Anthropic) via Circuit Breaker
5. **Audit**: Logs Trace ID, Cost, and Hash Chain
6. **Response**: Returns Answer + Trace Metadata

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 20.x+**
- **PostgreSQL 15+**
- **Redis 5+**

### 1. Clone Repository

```bash
git clone https://github.com/kherrera6219/DataLogicEngine.git
cd DataLogicEngine
```

### 2. Backend Setup

```bash
# Create venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -r requirements.txt

# Config
cp .env.template .env
# Set DATABASE_URL=postgresql://user:pass@localhost:5432/ukg_db

# Init DB
flask db upgrade
python backend/seed_data.py

# Run
python app.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to access the application.

---

## 🧪 Testing

### Backend (pytest)

Consolidated test suite runs unit, integration, and e2e tests.

```bash
# Run all tests
python run_test_suite.py

# Or via pytest directly
pytest tests/
```

**Coverage Goal**: >70% (Enforced by `pyproject.toml`)

### Frontend (Vitest)

```bash
cd frontend
npm test
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

1. **Fork & Branch** (`feature/amazing-feature`)
2. **Commit** (Conventional Commits: `feat: add new KA`)
3. **Test** (Ensure passing test suite)
4. **Pull Request**

---

## 📄 License

PolyForm Noncommercial License 1.0.0.
See [LICENSE](LICENSE) for details.
