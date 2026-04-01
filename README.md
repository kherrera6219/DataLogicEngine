# DataLogicEngine

> Local-first AI orchestration, knowledge graph exploration, traceable reasoning runs, and enterprise governance in one platform.

[![CI](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/ci.yml/badge.svg)](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/ci.yml)
[![Security Scan](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/security.yml/badge.svg)](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/security.yml)
[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-blue.svg)](LICENSE)

**Current version:** 4.1.19  
**Primary stack:** Flask + Next.js + Electron + PostgreSQL/Redis/Neo4j  
**Project status:** Active development with production-oriented security and governance controls

## What this repository contains

DataLogicEngine is a full-stack platform for:

- orchestrating AI conversations and multi-provider model execution,
- visualizing and querying a 17-axis knowledge graph,
- capturing traceable runs and evidence-rich audit artifacts,
- supporting simulation, RAG, MCP connectors, and enterprise policy enforcement,
- shipping both a browser-based experience and a Windows desktop deployment path.

## Core capabilities

- **AI orchestration:** provider routing for OpenAI, Anthropic, and Gemini-backed flows.
- **Traceability:** stored run history, stage/persona/axis inspection, and export-ready evidence packages.
- **Knowledge graph:** interactive graph exploration and structured node/edge APIs.
- **Security and governance:** RBAC, MFA, secret resolution, audit logging, and deployment guardrails.
- **Desktop operations:** Electron packaging and Windows-focused installer/signing workflows.
- **Operational tooling:** testing, release checklists, data-service verification, and documentation coverage checks.

## Repository map

| Path | Purpose |
| --- | --- |
| `backend/` | Flask APIs, tracing, security, storage, MCP, simulation, and orchestration services |
| `frontend/` | Next.js/Electron UI, component tests, stories, and frontend API clients |
| `docs/` | Architecture, deployment, testing, runbooks, API, product, and governance docs |
| `scripts/` | Setup, verification, release, and operational automation |
| `tests/` | Python test suites for backend, security, integration, compliance, and simulation |
| `.github/` | CI/CD workflows, templates, and GitHub collaboration standards |

## Quick start

### 1. Backend setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.template .env
```

Set at minimum:

```env
SESSION_SECRET=<long-random-secret>
OPENAI_API_KEY=<optional-but-recommended>
ANTHROPIC_API_KEY=<optional>
GEMINI_API_KEY=<optional>
```

### 2. Frontend setup

```bash
cd frontend
npm install
cd ..
```

### 3. Run locally

**Backend**

```bash
flask db upgrade
python main.py
```

Use `AUTO_CREATE_SCHEMA=true` only for disposable local environments. Managed and shared environments should use migrations.

**Frontend**

```bash
cd frontend
npm run dev
```

**Windows managed stack**

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
```

## Validation commands

### Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm test
```

### Backend

```bash
pytest tests --maxfail=20
```

### Repo governance checks

```bash
python scripts/verify_environment_parity.py
python scripts/verify_lockfiles.py
python scripts/verify_docs_references.py
```

## Documentation index

### Top-level project docs

- [DEVELOPMENT.md](DEVELOPMENT.md) — contributor setup, workflows, and quality gates
- [PROJECT.md](PROJECT.md) — product scope, milestones, and repository structure
- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution policy and standards
- [SECURITY.md](SECURITY.md) — vulnerability reporting and security support policy
- [SUPPORT.md](SUPPORT.md) — how to get help and where to report what

### Detailed docs

- [docs/README.md](docs/README.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)
- [docs/TESTING.md](docs/TESTING.md)
- [docs/API.md](docs/API.md)
- [docs/PRODUCT_OVERVIEW.md](docs/PRODUCT_OVERVIEW.md)

## GitHub collaboration standards

This repository includes:

- issue forms in `.github/ISSUE_TEMPLATE/`,
- a pull request template in `.github/pull_request_template.md`,
- CI, security, deploy, and release workflows in `.github/workflows/`,
- ownership controls in `.github/CODEOWNERS`,
- a GitHub process guide in `.github/README.md`.

## Recommended repository description

If you want a concise GitHub repository description, use:

**Local-first AI orchestration and traceable knowledge-graph platform with enterprise security, governance, and desktop/web delivery.**

## License

Licensed under the terms described in [LICENSE](LICENSE) and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md).
