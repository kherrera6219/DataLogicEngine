# DataLogicEngine — Documentation Portal

**Document Control**

| Field | Value |
|-------|-------|
| Owner | Platform Engineering |
| Last Updated | March 2026 |
| Status | Active |
| Review Cadence | Every 30 days |
| Version | 4.1.19 |

---

## Overview

This portal is the authoritative entry point for all DataLogicEngine documentation. It is organized by audience and use case to allow rapid navigation to relevant reference material.

Documents listed here are intended to be **active references**. Archived documents (historical assessments, prior reviews) are stored in `docs/archive/` and retained for audit traceability but are not operational references.

---

## Table of Contents

1. [Platform Status](#platform-status)
2. [Getting Started — By Role](#getting-started--by-role)
3. [Product Documentation](#product-documentation)
4. [Engineering and Architecture](#engineering-and-architecture)
5. [Engineer Onboarding and Diagrams](#engineer-onboarding-and-diagrams)
6. [Security and Compliance](#security-and-compliance)
7. [Operations and Deployment](#operations-and-deployment)
7. [Testing Standards](#testing-standards)
8. [Governance and Process](#governance-and-process)
9. [Repository Inventory and Maps](#repository-inventory-and-maps)
10. [Documentation Standards](#documentation-standards-1)
11. [Archived Assessments](#archived-assessments)
12. [Document Classification](#document-classification)

---

## Platform Status

**Current Version:** 4.1.19 | **As of:** March 2026

### Implemented in Codebase (Static Validation)

| Capability | Status |
|------------|--------|
| Core routing (dashboard, chat, projects, admin, runs, simulations, graph) | Implemented (feature coverage varies by route) |
| Desktop no-login startup (Electron, Windows 11) | Implemented |
| API key save/test and AI model configuration | Implemented |
| Storage health checks and local service lifecycle (`Start All` / `Stop All`) | Implemented |
| MCP connector scope enforcement and OAuth lifecycle | Implemented (runtime validation depends on connector setup) |
| Connector and AI latency telemetry (p50/p95/p99) | Implemented |
| SSRF protection on API gateway | Implemented |
| CI/release gates (schema parity, installer integrity, startup determinism) | Implemented in scripts/workflows |
| Postgres tenant Row-Level Security (RLS) bootstrap | Implemented (Postgres-only path) |
| Vault-backed secret resolution in production | Implemented secret-resolution chain (deployment-specific backing store) |
| Signed/encrypted trace export envelopes | Implemented |
| Immutable audit hash-chain replication and verification | Implemented |
| AI and connector p95/p99 latency SLO gauges | Implemented |
| Windows installer code-signing governance | Implemented in installer/build scripts |
| Crash reporting with fallback IDs and pipeline probe | Implemented |
| Diagnostic support-bundle generator (sanitized) | Implemented |
| Desktop safe secret storage (`safeStorage`) and log path governance | Implemented |
| Repository pre-commit hooks (lint + typecheck) | Implemented |
| Environment parity and lockfile integrity CI gate | Implemented |
| Python lint baseline (Ruff) — zero findings | Tracked via lint workflows/reports |
| ADR baseline, branch protection, and code-owner policy | Implemented |

### In Progress

| Item | Status |
|------|--------|
| Settings > Notifications | Placeholder UI — not wired |
| Settings > Storage > Cloud Config | Form fields not fully persisted |
| MCP > Add Server (admin UI actions) | Disabled in UI |
| Registration submit flow | UI exists; submit not wired |

---

## Getting Started — By Role

### End Users

| Document | Purpose |
|----------|---------|
| [`docs/USER_GUIDE.md`](USER_GUIDE.md) | Application features, workflows, and UI reference |
| [`docs/PRODUCT_OVERVIEW.md`](PRODUCT_OVERVIEW.md) | Capability status matrix |
| [`docs/WINDOWS_11_LOCAL_RUNBOOK.md`](WINDOWS_11_LOCAL_RUNBOOK.md) | Windows 11 local installation and startup |

### Developers and Contributors

| Document | Purpose |
|----------|---------|
| [`docs/ENGINEER_ONBOARDING.md`](ENGINEER_ONBOARDING.md) | Day 1–4 week structured onboarding guide for new engineers |
| [`docs/COMPONENT_MAP.md`](COMPONENT_MAP.md) | Module-level component diagrams across all subsystems |
| [`docs/DATA_FLOW_DIAGRAMS.md`](DATA_FLOW_DIAGRAMS.md) | End-to-end data flow diagrams (9 DFDs, multiple levels) |
| [`docs/SEQUENCE_DIAGRAMS.md`](SEQUENCE_DIAGRAMS.md) | UML sequence diagrams for key operations (10 diagrams) |
| [`docs/PROCESS_MAP.md`](PROCESS_MAP.md) | Business process maps for all major workflows (10 maps) |
| [`docs/DECISION_LOGIC.md`](DECISION_LOGIC.md) | Decision trees for Truth Engine, LLM routing, security (12 trees) |
| [`docs/DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md) | ER diagrams and complete database schema reference |
| [`docs/DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) | Development environment setup and contribution workflow |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Coding standards, commit guidelines, PR process |
| [`docs/API.md`](API.md) | REST API reference and versioning |
| [`docs/TESTING.md`](TESTING.md) | Test framework, coverage requirements, and test types |
| [`docs/FILE_STRUCTURE.md`](FILE_STRUCTURE.md) | Repository structure and file naming conventions |

### Security Engineers

| Document | Purpose |
|----------|---------|
| [`SECURITY.md`](../SECURITY.md) | Vulnerability reporting policy and response SLAs |
| [`docs/SECURITY.md`](SECURITY.md) | Security architecture, controls, and hardening reference |
| [`docs/PRODUCTION_READINESS.md`](PRODUCTION_READINESS.md) | Production hardening checklist |

### Platform Architects

| Document | Purpose |
|----------|---------|
| [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) | System architecture — components, data flow, middleware |
| [`docs/ARCHITECTURE_MAP.md`](ARCHITECTURE_MAP.md) | Implementation-mapped component diagram |
| [`docs/adr/README.md`](adr/README.md) | Architecture Decision Record index |
| [`docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md`](AI_PRODUCTION_DOCUMENTATION_BASELINE.md) | AI vendor-aligned production standards |

### SRE and Operations

| Document | Purpose |
|----------|---------|
| [`docs/OPERATIONAL_RUNBOOKS.md`](OPERATIONAL_RUNBOOKS.md) | Incident response, escalation, and operational procedures |
| [`docs/DEPLOYMENT.md`](DEPLOYMENT.md) | Deployment patterns (local, Docker, Kubernetes, cloud) |
| [`deploy/DEPLOYMENT_CHECKLIST.md`](../deploy/DEPLOYMENT_CHECKLIST.md) | Pre-deployment validation checklist |
| [`deploy/DISASTER_RECOVERY.md`](../deploy/DISASTER_RECOVERY.md) | Disaster recovery procedures |

---

## Product Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| [`docs/PRODUCT_OVERVIEW.md`](PRODUCT_OVERVIEW.md) | Feature capability status matrix; authoritative capability inventory | All |
| [`docs/USER_GUIDE.md`](USER_GUIDE.md) | End-user documentation for all application features and workflows | End users |
| [`docs/WINDOWS_11_LOCAL_RUNBOOK.md`](WINDOWS_11_LOCAL_RUNBOOK.md) | Windows 11 local stack setup, startup, and daily operation | End users, developers |

---

## Engineering and Architecture

| Document | Description | Audience |
|----------|-------------|----------|
| [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) | System architecture: components, data flows, middleware stack, hardening layers | Architects, engineers |
| [`docs/ARCHITECTURE_MAP.md`](ARCHITECTURE_MAP.md) | Implementation-mapped component diagram — maps architecture to source files | Architects, engineers |
| [`docs/DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) | Developer setup, code structure, contribution workflow | Developers |
| [`docs/API.md`](API.md) | REST API reference: endpoints, authentication, versioning, rate limits | Developers, integrators |
| [`docs/FILE_STRUCTURE.md`](FILE_STRUCTURE.md) | Repository file naming conventions and module organization policy | Developers |
| [`docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md`](AI_PRODUCTION_DOCUMENTATION_BASELINE.md) | Vendor-aligned AI production documentation standards | Architects, engineers |
| [`docs/adr/README.md`](adr/README.md) | Index of Architecture Decision Records (ADRs) | Architects |

---

## Engineer Onboarding and Diagrams

These documents are produced to the Microsoft enterprise standard for engineering onboarding. They provide the diagrams, decision trees, and reference materials a new engineer needs to understand how the application works without reading all the source code first.

| Document | Description | Audience |
|----------|-------------|----------|
| [`docs/ENGINEER_ONBOARDING.md`](ENGINEER_ONBOARDING.md) | Structured Day 1 through Week 4 onboarding guide with layered mental model, read order, and contribution checklist | New engineers |
| [`docs/COMPONENT_MAP.md`](COMPONENT_MAP.md) | Module-level component diagrams for all subsystems: backend, frontend, core engine, security, Truth Engine, observability | All engineers |
| [`docs/DATA_FLOW_DIAGRAMS.md`](DATA_FLOW_DIAGRAMS.md) | 9 data flow diagrams across 3 levels: system context (L0), top-level flows (L1), and detailed chat/security/MCP/audit/secret flows (L2) | Engineers, architects |
| [`docs/SEQUENCE_DIAGRAMS.md`](SEQUENCE_DIAGRAMS.md) | 10 UML sequence diagrams: web login with MFA, desktop auto-login, chat round-trip, LLM failover, MCP tool call, knowledge node write, RBAC check, active defense, signed trace export, OIDC auth | Engineers, QA |
| [`docs/PROCESS_MAP.md`](PROCESS_MAP.md) | 10 BPMN-style process maps: user onboarding, chat workflow, knowledge node creation, MCP connector registration, run lifecycle, LLM provider config, simulation execution, incident response, release/deployment, vulnerability response | Engineers, ops |
| [`docs/DECISION_LOGIC.md`](DECISION_LOGIC.md) | 12 annotated decision trees: Truth Engine tier selection, LLM routing and failover, active defense threat classification, RBAC resolution, secret priority chain, auth path selection, account lockout/MFA gate, coordinate validation, MCP scope enforcement, simulation layer selection, TruthGate budget/compliance, circuit breaker state machine | Engineers, architects, security |
| [`docs/DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md) | 4 ER diagrams (core, trace/audit, knowledge graph, MCP/AI config domains), complete table reference (50+ models), tenant isolation pattern, field-level encryption pattern, key indexes | Engineers, DBAs |

---

## Security and Compliance

| Document | Description | Audience |
|----------|-------------|----------|
| [`SECURITY.md`](../SECURITY.md) | Vulnerability reporting policy, response SLAs, disclosure process | All |
| [`docs/SECURITY.md`](SECURITY.md) | Full security architecture: controls, hardening, compliance alignment | Security engineers, architects |
| [`docs/PRODUCTION_READINESS.md`](PRODUCTION_READINESS.md) | Production hardening checklist — security controls, infra requirements | SRE, security |

---

## Operations and Deployment

| Document | Description | Audience |
|----------|-------------|----------|
| [`docs/DEPLOYMENT.md`](DEPLOYMENT.md) | Deployment patterns: local, Docker Compose, Kubernetes, AWS, GCP, Azure | SRE, operations |
| [`docs/OPERATIONAL_RUNBOOKS.md`](OPERATIONAL_RUNBOOKS.md) | Incident response procedures, escalation paths, operational playbooks | SRE, operations |
| [`deploy/DEPLOYMENT_CHECKLIST.md`](../deploy/DEPLOYMENT_CHECKLIST.md) | Pre-production deployment validation gate | SRE, operations |
| [`deploy/DISASTER_RECOVERY.md`](../deploy/DISASTER_RECOVERY.md) | Disaster recovery and business continuity procedures | SRE, operations |

---

## Testing Standards

| Document | Description | Audience |
|----------|-------------|----------|
| [`docs/TESTING.md`](TESTING.md) | Test framework, coverage requirements, test types, and CI gates | Developers, QA |

---

## Governance and Process

| Document | Description | Audience |
|----------|-------------|----------|
| [`docs/RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) | Release validation gates and sign-off process | Developers, SRE |
| [`docs/BRANCH_PROTECTION_POLICY.md`](BRANCH_PROTECTION_POLICY.md) | Branch protection rules and code-owner policy | Developers, leads |
| [`docs/DOCUMENTATION_VERSIONING.md`](DOCUMENTATION_VERSIONING.md) | Documentation version control and change management policy | All |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Contribution guidelines, coding standards, PR process | Contributors |
| [`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md) | Community standards and enforcement policy | All |

---

## Repository Inventory and Maps

These artifacts are **generated automatically** by repository tooling. Do not edit manually.

| Artifact | Description | Generation Script |
|----------|-------------|------------------|
| [`docs/FILE_INVENTORY.csv`](FILE_INVENTORY.csv) | Complete file inventory with metadata | `scripts/generate_file_inventory.py` |
| [`docs/GENERATED_STRUCTURE.md`](GENERATED_STRUCTURE.md) | Repository structure summary | `scripts/generate_repo_structure.py` |
| [`docs/DOCUMENTATION_COVERAGE_MATRIX.md`](DOCUMENTATION_COVERAGE_MATRIX.md) | Documentation coverage by module | `scripts/generate_coverage_matrix.py` |

---

## Documentation Standards

| Document | Description |
|----------|-------------|
| [`docs/DOCUMENTATION_STANDARDS.md`](DOCUMENTATION_STANDARDS.md) | Authoring standards, formatting rules, and review requirements |
| [`docs/DOCUMENTATION_COVERAGE_MATRIX.md`](DOCUMENTATION_COVERAGE_MATRIX.md) | Coverage mapping — which modules have documentation |

### Document Lifecycle

| Status | Meaning |
|--------|---------|
| **Active** | Current, maintained, and authoritative — listed in this portal |
| **Historical** | Retained for audit traceability — stored in `docs/archive/` — not operational |
| **Reference** | Informational only — stored in `docs/whitepapers/` — not operational runbooks |
| **Assessment** | Periodic review snapshots — stored in `docs/archive/assessments/` |

---

## Archived Assessments

The following assessment documents are retained for audit traceability. They are **not** active references. See `docs/archive/assessments/2026-02/` for the full set.

| Document | Date | Description |
|----------|------|-------------|
| `APPLICATION_REVIEW_RECOMMENDED_IMPROVEMENTS_2026-02-10.md` | 2026-02-10 | Full application review with recommended improvements |
| `SUBSYSTEMS_SECTIONS_1_TO_4_UPDATED_REPORT_2026-02-16.md` | 2026-02-16 | Subsystem review: sections 1–4 |
| `SUBSYSTEMS_SECTIONS_5_TO_8_REVIEW_2026-02-16.md` | 2026-02-16 | Subsystem review: sections 5–8 |
| `SUBSYSTEMS_SECTIONS_9_TO_11_REVIEW_2026-02-16.md` | 2026-02-16 | Subsystem review: sections 9–11 |
| `REPO_CLEANUP_AND_WIRING_AUDIT_2026-02-16.md` | 2026-02-16 | Repository cleanup and wiring audit |
| `LINT_STYLE_SWEEP_PHASE9_2026-02-17.md` | 2026-02-17 | Python lint sweep Phase 9 execution report |
| `LINT_STYLE_SWEEP_PHASE10_2026-02-17.md` | 2026-02-17 | Python lint sweep Phase 10 execution report |
| `LINT_STYLE_SWEEP_PHASE11_2026-02-17.md` | 2026-02-17 | Python lint sweep Phase 11 execution report |

---

## Document Classification

All documentation in this repository is classified as follows unless otherwise noted:

| Class | Definition |
|-------|-----------|
| **Public** | Suitable for external publication (README, CODE_OF_CONDUCT, CONTRIBUTING) |
| **Internal** | Suitable for contributors and community members (architecture, developer guides) |
| **Restricted** | Sensitive operational material (security architecture details, incident runbooks) |

---

*This portal is the authoritative documentation index for DataLogicEngine. All other documentation entry points should link here. Reviewed: March 2026.*
