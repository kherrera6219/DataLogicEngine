# DataLogicEngine

Local-first governed AI orchestration, traceable reasoning, and enterprise knowledge workflows in one deployable platform.

[![CI](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/ci.yml/badge.svg)](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/ci.yml)
[![Security](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/security.yml/badge.svg)](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/security.yml)
[![Deploy](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/deploy.yml/badge.svg)](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/deploy.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB)](requirements.txt)
[![Node](https://img.shields.io/badge/node-24%2B-339933)](frontend/package.json)
[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial-blue)](LICENSE)

DataLogicEngine is a full-stack platform for building inspectable AI systems over structured enterprise knowledge. It combines a Windows/Electron local-first runtime, Next.js console, Flask API/security envelope, DMRF governed AI control plane, Truth Engine, 17-axis routing, DSQP persona construction, MCP connector governance, trace/export review, and multi-store memory architecture.

## Current status

As of 2026-05-30, the active documentation set has been modernized around the current platform architecture:

1. local-first Windows desktop and controlled web/cloud modes;
2. DMRF as the governed AI lifecycle control plane;
3. Truth Engine for policy, reasoning, memory, and event flow;
4. 17-axis routing and DSQP structured persona construction;
5. Trace Explorer and export integrity;
6. MCP connector scope and contract governance;
7. multi-store data and memory architecture;
8. release, security, privacy, and documentation governance.

The canonical backlog and planning source is [`TODO.md`](TODO.md).

Known release caveats are tracked in [`docs/PRODUCTION_READINESS.md`](docs/PRODUCTION_READINESS.md) and [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md). Current caveats may include trusted production code-signing, signed installer validation, provider-backed staging validation, external connector validation, manual accessibility evidence, and final release approval evidence.

## Quickstart

Run the full local stack with Docker:

```bash
git clone https://github.com/kherrera6219/DataLogicEngine.git
cd DataLogicEngine
cp .env.template .env
docker compose up --build
```

Open:

| Service | URL |
|---|---|
| Web console | `http://localhost:3000` |
| Backend API | `http://localhost:5000` |
| Health probe | `http://localhost:5000/health` |
| Metrics | `http://localhost:5000/metrics` |
| Swagger UI | `http://localhost:5000/api/docs` |

Minimal API call:

```bash
curl http://localhost:5000/health
```

## Why DataLogicEngine

DataLogicEngine is designed for teams that need AI workflows to be explainable, inspectable, and operable in regulated or high-accountability environments.

| Capability | What it provides |
|---|---|
| Local-first runtime | Windows/Electron desktop operation with loopback/local trust controls and app-owned local services. |
| DMRF control plane | Governed AI request lifecycle with injection defense, tiering, routing, evidence, convergence, memory, and trace hooks. |
| Truth Engine | TruthGate, TruthCore, TruthMemory, and TruthLink components for policy, reasoning, audit, memory, and events. |
| 17-axis routing | Structured coordinate/risk/context routing for knowledge workflows. |
| DSQP | Deterministic structured persona construction for Knowledge, Sector, Regulatory, and Compliance expert perspectives. |
| Traceability | Runs, stages, evidence, claims, policy decisions, personas, hashes, and export manifests for review. |
| MCP governance | Connector registration, scope enforcement, contract validation, metrics, and audit path. |
| Multi-store memory | SQLAlchemy DB, Redis, Neo4j, ChromaDB, object storage, USKD graph, UnifiedMemory, and TruthMemory. |
| Release governance | CI, tests, schema parity, runtime precheck, docs validation, packaging smoke, signing checks, and release checklist evidence. |

## Architecture

![DataLogicEngine architecture overview](docs/assets/readme/architecture-overview.svg)

```mermaid
flowchart LR
    User[User / Analyst] --> UI[Next.js / Electron UI]
    UI --> API[Flask API / Security Envelope]
    API --> DMRF[DMRF Control Plane]
    DMRF --> Gate[InjectionDefense + TruthGate]
    Gate --> Route[TierClassifier + 17-Axis Router]
    Route --> DSQP[DSQP Persona Builder]
    DSQP --> Core[TruthCore]
    Core --> Provider[LLM Gateway / AI Providers]
    Core --> MCP[MCP Connectors]
    Core --> Data[(SQL / Redis / Neo4j / Chroma / Object Store / Memory)]
    Core --> Trace[Trace Explorer / Export Integrity]
    API --> Ops[/health /ready /metrics]
```

### Runtime components

| Layer | Components | Notes |
|---|---|---|
| Frontend | Next.js, React, Electron | Web console, desktop shell, trace/runs, graph, admin, settings, MCP surfaces. |
| Backend | Flask, SQLAlchemy, route modules | API routing, auth/security envelope, governance lifecycle, storage, tracing. |
| Control plane | DMRF, Truth Engine, 17-axis router, DSQP | AI lifecycle governance and reasoning workflow. |
| Data/memory | SQL, Redis, Neo4j, ChromaDB, object store, USKD, UnifiedMemory, TruthMemory | Multi-store persistence and memory. |
| Integration | LLM Gateway, MCP server | Provider/model calls and external tool execution where configured. |
| Quality/release | Pytest, frontend tests, GitHub Actions, governance scripts, Windows packaging checks | Validation and release evidence. |

## Installation

### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Backend runtime and tests. |
| Node.js | 24+ | Frontend and Electron tooling. |
| Docker | Current stable | Local full-stack development. |
| PostgreSQL | 15+ | Relational store where configured. |
| Redis | 7+ | Cache, rate limiting, async support where configured. |
| Neo4j | 5+ | Graph storage where configured. |

### Backend development

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.template .env
python app.py
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.template .env
python app.py
```

### Frontend development

```bash
cd frontend
npm ci
npm run dev
```

## Validation

Common checks:

```bash
python scripts/verify_docs_references.py
python scripts/verify_environment_parity.py --strict
python scripts/verify_lockfiles.py
python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process
```

Backend tests:

```bash
python -m pytest tests --maxfail=20
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run typecheck
npm test
```

Windows packaging checks:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1 -RepoRoot (Get-Location).Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path
```

## Documentation

Start with the documentation portal:

1. [`docs/README.md`](docs/README.md)
2. [`docs/PRODUCT_OVERVIEW.md`](docs/PRODUCT_OVERVIEW.md)
3. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
4. [`docs/ARCHITECTURE_MAP.md`](docs/ARCHITECTURE_MAP.md)
5. [`docs/WORKFLOW.md`](docs/WORKFLOW.md)
6. [`docs/DATA_FLOW_DIAGRAMS.md`](docs/DATA_FLOW_DIAGRAMS.md)
7. [`docs/DECISION_LOGIC.md`](docs/DECISION_LOGIC.md)
8. [`docs/SECURITY.md`](docs/SECURITY.md)
9. [`docs/PRODUCTION_READINESS.md`](docs/PRODUCTION_READINESS.md)

Historical material under `docs/archive/` is reference-only and should be validated against current active docs before use.

## Security

Report vulnerabilities privately. See [`SECURITY.md`](SECURITY.md).

Security architecture details are documented in [`docs/SECURITY.md`](docs/SECURITY.md). Security/compliance mapping documents are evidence-guided references and should not be treated as formal certification claims unless a separate attestation is provided.

## License

This project is licensed under the PolyForm Noncommercial License. See [`LICENSE`](LICENSE).
