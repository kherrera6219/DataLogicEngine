# DataLogicEngine — Documentation Portal

**Document Control**

| Field | Value |
|-------|-------|
| Owner | Platform Engineering |
| Last Updated | May 23, 2026 |
| Status | Active |
| Review Cadence | Every 30 days |
| Version | 4.1.21 |

---

## Overview

This portal is the authoritative entry point for all DataLogicEngine documentation. It is organized by audience and use case to allow rapid navigation to relevant reference material.

All documents listed here are **active and maintained**. Current planning belongs in the root [`TODO.md`](../TODO.md); do not create separate roadmap, project-plan, or assessment TODO documents.

Historical PDFs, old release notes, wireframes, and research spikes are preserved under [`docs/archive/`](archive/README.md). Archived material is reference-only and must be validated against current code before being used for implementation decisions.

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
9. [Current Planning](#current-planning)
10. [Repository Inventory and Maps](#repository-inventory-and-maps)
11. [Archive](#archive)
12. [Documentation Standards](#documentation-standards-1)
13. [Document Classification](#document-classification)

---

## Platform Status

**Current Version:** 4.1.21 | **As of:** May 23, 2026

DataLogicEngine is currently in application-readiness cleanup and release-preparation status. The local-first Windows/Electron application, web console, backend API, AI gateway, graph surfaces, storage controls, MCP administration, privacy controls, and core governance evidence are implemented and actively documented.

### Production-Ready

| Capability | Status |
|------------|--------|
| Core routing (dashboard, chat, projects, admin, runs, simulations, graph) | Operational |
| Desktop no-login startup (Electron, Windows 11) | Operational |
| API key save/test and AI model configuration | Operational |
| Storage health checks and local service lifecycle (`Start All` / `Stop All`) | Operational |
| Storage cloud configuration persistence | Operational |
| Notification preferences | Operational |
| MCP server add/list/delete admin actions | Operational |
| MCP connector scope enforcement and OAuth lifecycle | Operational |
| Connector and AI latency telemetry (p50/p95/p99) | Operational |
| SSRF protection on API gateway | Operational |
| CI/release gates (schema parity, installer integrity, startup determinism) | Operational |
| Postgres tenant Row-Level Security (RLS) bootstrap | Operational |
| Vault-backed secret resolution in production | Operational |
| Signed/encrypted trace export envelopes | Operational |
| Immutable audit hash-chain replication and verification | Operational |
| AI and connector p95/p99 latency SLO gauges | Operational |
| Windows installer code-signing governance | Operational |
| Crash reporting with fallback IDs and pipeline probe | Operational |
| Diagnostic support-bundle generator (sanitized) | Operational |
| Desktop safe secret storage (`safeStorage`) and log path governance | Operational |
| Repository pre-commit hooks (lint + typecheck) | Operational |
| Environment parity and lockfile integrity CI gate | Operational |
| Python lint baseline (Ruff) — zero findings | Operational |
| ADR baseline, branch protection, and code-owner policy | Operational |
| Public README architecture asset | Operational |
| Keyboard navigation Playwright evidence | Operational |
| UI placeholder audit evidence | Operational |
| Local release-governance command evidence | Operational |

### In Progress

| Item | Status |
|------|--------|
| Registration flow | `/register` redirects to `/dashboard`; web self-registration is disabled in the current local-first build. |
| Application-readiness evidence | Automated WCAG, keyboard navigation, failure-mode, export/delete, and UI placeholder audit evidence is captured under `reports/app-readiness/`; manual NVDA evidence is still tracked in `TODO.md`. |
| Release signing | Release signing workflow exists, but trusted production certificate provisioning and signed artifact validation remain external release tasks. |
| Release approval evidence | CI/security scan review, code-owner approval, rollback plan, and disaster recovery review remain release-ticket tasks. |
| Staging and connector validation | Provider-backed staging validation and production connector checks require real external systems. |

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
| [`TODO.md`](../TODO.md) | Canonical roadmap, backlog, and open work list | Developers, release owners |
| [`docs/RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) | Release validation gates and sign-off process | Developers, SRE |
| [`docs/BRANCH_PROTECTION_POLICY.md`](BRANCH_PROTECTION_POLICY.md) | Branch protection rules and code-owner policy | Developers, leads |
| [`docs/DOCUMENTATION_VERSIONING.md`](DOCUMENTATION_VERSIONING.md) | Documentation version control and change management policy | All |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Contribution guidelines, coding standards, PR process | Contributors |
| [`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md) | Community standards and enforcement policy | All |

---

## Current Planning

[`TODO.md`](../TODO.md) is the only active planning and outstanding-work list. Historical assessment documents, project plans, and roadmap drafts were removed from the active documentation set to avoid conflicting guidance for contributors and AI agents.

Current open work is concentrated in external/manual release tasks, NVDA validation, trusted code-signing certificate provisioning, signed artifact validation, CI/security review, release approvals, rollback/disaster-recovery review, provider-backed staging validation, and production connector validation.

Current local evidence includes:

| Evidence | Purpose |
|----------|---------|
| [`reports/app-readiness/a11y-ci-report.json`](../reports/app-readiness/a11y-ci-report.json) | Authenticated accessibility route evidence |
| [`reports/app-readiness/keyboard-navigation-report.json`](../reports/app-readiness/keyboard-navigation-report.json) | Keyboard navigation evidence |
| [`reports/app-readiness/playwright-app-readiness-report.json`](../reports/app-readiness/playwright-app-readiness-report.json) | Failure-mode and privacy export/delete evidence |
| [`reports/app-readiness/ui-placeholder-audit.md`](../reports/app-readiness/ui-placeholder-audit.md) | MCP, admin, and toolbar placeholder audit |
| [`reports/production-code-review-2026-05-23.md`](../reports/production-code-review-2026-05-23.md) | Production code-review findings and remediation source |
| [`reports/release-readiness/local-release-evidence-2026-05-23.md`](../reports/release-readiness/local-release-evidence-2026-05-23.md) | Local release-governance command evidence |

---

## Repository Inventory and Maps

These artifacts are **generated automatically** by repository tooling. Do not edit manually.

| Artifact | Description | Generation Script |
|----------|-------------|------------------|
| [`docs/FILE_INVENTORY.csv`](FILE_INVENTORY.csv) | Complete file inventory with metadata | `scripts/generate_docs.py` |
| [`docs/GENERATED_STRUCTURE.md`](GENERATED_STRUCTURE.md) | Repository structure summary | `scripts/generate_docs.py` |
| [`docs/DOCUMENTATION_COVERAGE_MATRIX.md`](DOCUMENTATION_COVERAGE_MATRIX.md) | Documentation coverage by module | Maintained manually |

---

## Archive

Historical and reference-only documents are preserved in [`docs/archive/`](archive/README.md).

| Archive Area | Contents |
|--------------|----------|
| [`docs/archive/historical-documents/`](archive/historical-documents/) | Imported planning PDFs, MVP plans, mathematical framework papers, and source research documents |
| [`docs/archive/whitepapers/`](archive/whitepapers/) | UKG/USKD whitepapers and deep architecture narratives |
| [`docs/archive/wireframes/`](archive/wireframes/) | 2025 design-system and wireframe drafts |
| [`docs/archive/research/`](archive/research/) | Old release notes, platform research, cross-user testing notes, and design spikes |

Archived material is not active implementation guidance. Fold actionable items into [`TODO.md`](../TODO.md) before using archived documents for current work.

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
| **Reference** | Informational only — stored in `docs/archive/` — not operational runbooks |

---

## Document Classification

All documentation in this repository is classified as follows unless otherwise noted:

| Class | Definition |
|-------|-----------|
| **Public** | Suitable for external publication (README, CODE_OF_CONDUCT, CONTRIBUTING) |
| **Internal** | Suitable for contributors and community members (architecture, developer guides) |
| **Restricted** | Sensitive operational material (security architecture details, incident runbooks) |

---

*This portal is the authoritative documentation index for DataLogicEngine. All other documentation entry points should link here. Reviewed: May 23, 2026.*
