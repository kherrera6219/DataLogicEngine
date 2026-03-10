# DataLogicEngine

**Version:** 4.1.19 | **Status:** Production-Ready | **Updated:** March 2026

[![CI](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/ci.yml/badge.svg)](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/ci.yml)
[![Security Scan](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/security.yml/badge.svg)](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/security.yml)
[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-blue.svg)](LICENSE)

---

## Table of Contents

1. [Overview](#overview)
2. [Key Capabilities](#key-capabilities)
3. [Architecture Summary](#architecture-summary)
4. [Prerequisites](#prerequisites)
5. [Getting Started](#getting-started)
6. [Configuration Reference](#configuration-reference)
7. [Deployment Options](#deployment-options)
8. [Desktop Installer](#desktop-installer)
9. [Testing](#testing)
10. [Documentation](#documentation)
11. [Contributing](#contributing)
12. [Security](#security)
13. [License](#license)
14. [Support](#support)

---

## Overview

DataLogicEngine is a **local-first AI orchestration platform** that provides chat-driven AI workflows, traceable execution runs, knowledge graph exploration, multi-layer simulation, and enterprise-grade operations visibility. It is designed for organizations that require secure, auditable AI workflows with full control over data residency and model routing.

The platform runs in two primary modes:

| Mode | Description | Authentication |
|------|-------------|----------------|
| **Desktop (Windows Electron)** | Installed application with native OS integration | No login required — boots directly to dashboard |
| **Web (Browser)** | Browser-based access for multi-user environments | Session-based authentication with MFA support |

---

## Key Capabilities

### Implemented and Production-Ready

| Capability | Description |
|------------|-------------|
| **AI Orchestration** | Multi-provider LLM routing (OpenAI, Anthropic, Google Gemini) with circuit breaker failover |
| **Knowledge Graph** | 17-axis Nuremberg-style hierarchical coordinate system with graph visualization |
| **Traceable Runs** | End-to-end run tracing with hash-chained immutable audit records |
| **Simulation Engine** | Multi-layer simulation with knowledge algorithm execution |
| **MCP Connectors** | Model Context Protocol server with Jira, Salesforce, and custom connector support |
| **Enterprise Security** | AES-256 field-level encryption, RBAC, MFA (TOTP), Azure AD/OIDC integration |
| **Observability** | p50/p95/p99 latency metrics, SLO tracking, Sentry crash reporting |
| **Compliance** | SOC 2, GDPR, HIPAA (configurable), ISO 27001 aligned audit logging |
| **Desktop Packaging** | Windows NSIS installer with code-signing governance and silent install/uninstall |

### In Progress

| Item | Status |
|------|--------|
| Settings > Notifications | Placeholder UI — not yet wired |
| Settings > Storage > Cloud Config | Form fields not fully persisted |
| MCP Admin Actions | Add Server and console actions disabled in UI |
| Registration Submit Flow | UI exists — submit not yet wired |

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    DataLogicEngine Platform                  │
├──────────────────────┬──────────────────────────────────────┤
│   Frontend           │   Backend                           │
│   Next.js 16.1       │   Flask 3.1 (Python 3.11+)         │
│   React 18.3         │   SQLAlchemy 2.0                    │
│   Electron 40.x      │   Celery 5.6 + Redis                │
│   TypeScript 5.x     │   LLM Gateway (circuit breaker)     │
│   Shadcn UI          │   MCP Server                        │
│   Tailwind CSS 4.x   │   17-Axis Knowledge Engine          │
├──────────────────────┴──────────────────────────────────────┤
│   Data Layer                                                │
│   PostgreSQL 15+ (RLS) │ Redis 5+ │ Neo4j 5 │ MinIO        │
│   ChromaDB 1.4 (RAG)  │ SQLite (local fallback)            │
└─────────────────────────────────────────────────────────────┘
```

For detailed architecture documentation, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/ARCHITECTURE_MAP.md`](docs/ARCHITECTURE_MAP.md).

---

## Prerequisites

### Required

| Requirement | Minimum Version | Notes |
|-------------|----------------|-------|
| Windows | 11 | For desktop/local mode |
| Python | 3.11 | 3.12+ supported |
| Node.js | 20.x LTS | For frontend and Electron |
| Git | 2.40+ | |

### For Production / Full Data Stack

| Service | Version | Purpose |
|---------|---------|---------|
| PostgreSQL | 15+ | Primary relational database |
| Redis | 5+ | Caching, sessions, task queue |
| Neo4j | 5+ | Knowledge graph (optional) |
| MinIO | Latest | Object storage (optional) |
| Docker Desktop | Latest | Required for data services stack |

### AI Provider Keys (one required)

- `OPENAI_API_KEY` — OpenAI GPT models
- `ANTHROPIC_API_KEY` — Anthropic Claude models
- `GEMINI_API_KEY` / `GOOGLE_API_KEY` — Google Gemini models

---

## Getting Started

### 1. Clone and Install Dependencies

```powershell
git clone https://github.com/kherrera6219/DataLogicEngine.git
cd DataLogicEngine

# Create and activate Python virtual environment
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Copy environment template
Copy-Item .env.template .env

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Environment

Open `.env` and set the minimum required variables:

```env
# Required: Session security key (generate a long random string)
SESSION_SECRET=<your-long-random-secret>

# Required: At least one AI provider key
OPENAI_API_KEY=<your-openai-key>
# or
ANTHROPIC_API_KEY=<your-anthropic-key>
# or
GEMINI_API_KEY=<your-gemini-key>
```

> **Production Vault Integration:** For production deployments, secrets can be sourced from vault-backed stores instead of `.env` files. See [Configuration Reference](#configuration-reference) for details.

### 3. Start the Local Stack

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
```

Default service endpoints:

| Service | URL |
|---------|-----|
| Frontend | `http://127.0.0.1:3000` |
| Backend API | `http://127.0.0.1:5000` |
| Backend Health | `http://127.0.0.1:5000/health` |

### 4. Stop the Local Stack

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\stop_local_stack.ps1
```

---

## Configuration Reference

### Secret Resolution Priority

DataLogicEngine resolves secrets in the following order of precedence:

1. `SESSION_SECRET_FILE=<path>` — Read secret from a file path
2. `SESSION_SECRET_DPAPI_B64=<value>` — DPAPI-encrypted secret (Windows)
3. `DLE_SECRET_STORE_JSON=<path>` — JSON secret store file
4. `SESSION_SECRET=<value>` — Direct environment variable (development only)

### Production Security Controls

```env
# Enforce vault-backed secrets in production (disables plaintext fallback)
PRODUCTION_VAULT_SECRETS_REQUIRED=true
ALLOW_PLAINTEXT_PROD_SECRETS=false
```

### Optional Data Services Stack

Start with full PostgreSQL, Redis, Neo4j, and MinIO services:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1 -WithDataServices
```

Validate data services:

```powershell
.venv\Scripts\python.exe .\scripts\verify_api_keys.py
.venv\Scripts\python.exe .\scripts\verify_local_data_stack.py
```

---

## Deployment Options

| Target | Tooling | Documentation |
|--------|---------|---------------|
| **Local (Windows)** | PowerShell scripts | [`docs/WINDOWS_11_LOCAL_RUNBOOK.md`](docs/WINDOWS_11_LOCAL_RUNBOOK.md) |
| **Docker Compose** | `docker-compose.yml` | [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) |
| **Kubernetes** | `k8s/` manifests + CRD operator | [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) |
| **AWS (ECS)** | `deploy/aws/` CloudFormation | [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) |
| **GCP (Cloud Run)** | `deploy/gcp/` Cloud Build | [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) |
| **Azure (App Service)** | `deploy/azure/` Pipelines | [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) |

### Docker Compose (Quick Start)

```bash
docker-compose up -d
```

This brings up: PostgreSQL 15, Redis 7, Neo4j 5, MinIO — with backend on port 5000 and frontend on port 3000.

---

## Desktop Installer

### Build the Installer

```powershell
npm --prefix frontend run electron:dist
```

### Build Artifacts

| File | Description |
|------|-------------|
| `DataLogicEngine Setup Latest.exe` | Latest version installer |
| `DataLogicEngine Setup <version>.exe` | Version-pinned installer |
| `DataLogicEngine Setup Latest.exe.sha256` | SHA256 checksum for latest |
| `DataLogicEngine Setup <version>.exe.sha256` | SHA256 checksum for versioned |
| `frontend/dist/` | Full packaging output directory |

### Install and Uninstall

```powershell
# Run installer (interactive)
.\DataLogicEngine Setup Latest.exe

# Silent install
powershell -ExecutionPolicy Bypass -File .\scripts\windows\install_silent.ps1

# Silent uninstall (preserve user data)
powershell -ExecutionPolicy Bypass -File .\scripts\windows\uninstall.ps1 -Silent -KeepData

# Silent uninstall (remove all data)
powershell -ExecutionPolicy Bypass -File .\scripts\windows\uninstall.ps1 -Silent -DeleteData
```

### Verify Installer Integrity

```powershell
# Verify artifact checksums
python .\scripts\verify_installer_integrity.py --require-artifacts

# Verify code-signing signature
powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_installer_signature.ps1 -RequireArtifacts -CheckRevocation

# Verify certificate health
powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_signing_certificate_health.ps1 `
    -CertificatePath .\codesign.pfx -CertificatePassword "<password>" -CheckRevocation

# Validate NSIS governance
powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1

# Run packaging smoke tests
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -Mode portable
```

---

## Testing

### Backend Smoke Check

```powershell
python .\scripts\test_smoke.py
```

### Full Backend Test Suite

```powershell
python run_test_suite.py
```

### Frontend Tests

```powershell
cd frontend

# Type checking
npm run typecheck

# Unit tests
npm test

# E2E visual regression
npm run test:e2e:visual

# Route E2E smoke
npm run test:e2e -- tests/e2e/route-sidebar-smoke.spec.ts
```

### Operational Hardening Checks

```powershell
# Schema parity (SQLite vs PostgreSQL)
python .\scripts\validate_schema_parity.py

# Installer integrity
python .\scripts\verify_installer_integrity.py --require-artifacts

# Runtime startup precheck
python .\scripts\runtime_precheck.py --strict --skip-ports --allow-env-from-process

# Support bundle generation (sanitized)
python .\scripts\generate_support_bundle.py --skip-http

# Packaging smoke tests
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1
```

### Test Coverage Requirements

| Category | Minimum Coverage |
|----------|-----------------|
| Python backend | 70% |
| Core algorithms | 80% |
| Security modules | 80% |

---

## Documentation

### Primary References

| Document | Description |
|----------|-------------|
| [`docs/PRODUCT_OVERVIEW.md`](docs/PRODUCT_OVERVIEW.md) | Feature capability status matrix |
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | End-user guide and workflow documentation |
| [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) | Developer setup, standards, and contribution workflow |
| [`docs/WINDOWS_11_LOCAL_RUNBOOK.md`](docs/WINDOWS_11_LOCAL_RUNBOOK.md) | Windows 11 local deployment runbook |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System architecture reference |
| [`docs/ARCHITECTURE_MAP.md`](docs/ARCHITECTURE_MAP.md) | Implementation-mapped component diagram |
| [`docs/API.md`](docs/API.md) | REST API reference and versioning |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Security controls and hardening documentation |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Production deployment patterns |
| [`docs/TESTING.md`](docs/TESTING.md) | Testing framework and standards |
| [`docs/OPERATIONAL_RUNBOOKS.md`](docs/OPERATIONAL_RUNBOOKS.md) | Incident response and operational procedures |
| [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md) | Release process and validation gates |
| [`docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md`](docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md) | AI vendor-aligned production standards |

### Documentation Portal

The complete documentation index is available at [`docs/README.md`](docs/README.md).

---

## Contributing

We welcome contributions from the community and enterprise partners. Please review the following before submitting:

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — Contribution guidelines, coding standards, and PR process
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) — Community standards and enforcement policy
- [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) — Developer environment setup

### Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

Examples:
  feat(knowledge-graph): add node filtering capability
  fix(auth): resolve JWT token expiration issue
  docs(readme): update installation instructions
```

---

## Security

DataLogicEngine is designed with enterprise-grade security controls including:

- **AES-256 field-level encryption** for all PII data
- **RBAC with granular permissions** (`user:manage_roles`, `data:export`, etc.)
- **MFA (TOTP)** with backup codes
- **Azure AD / Entra ID (OIDC)** SSO integration
- **Row-Level Security (RLS)** for PostgreSQL tenant isolation
- **Immutable audit trail** with hash-chain verification
- **Dual-LLM active defense** pipeline for prompt injection protection
- **SSRF protection** on all external API gateway calls

### Reporting Vulnerabilities

**Do not report security vulnerabilities through public GitHub issues.**

Please report security vulnerabilities by email to: **security@datalogicengine.com**

You will receive an acknowledgement within 48 hours. For full details on our security policy, disclosure process, and supported versions, see [`SECURITY.md`](SECURITY.md).

---

## License

This project is licensed under the **PolyForm Noncommercial License 1.0.0**. See [`LICENSE`](LICENSE) for full terms.

For commercial use, see [`COMMERCIAL_LICENSE.md`](COMMERCIAL_LICENSE.md) or contact the project maintainers.

---

## Support

| Channel | Description |
|---------|-------------|
| [GitHub Issues](https://github.com/kherrera6219/DataLogicEngine/issues) | Bug reports and feature requests |
| [GitHub Discussions](https://github.com/kherrera6219/DataLogicEngine/discussions) | Questions, ideas, community support |
| [Security Reports](mailto:security@datalogicengine.com) | Responsible vulnerability disclosure |

---

*For a complete history of changes, see [`CHANGELOG.md`](CHANGELOG.md).*
