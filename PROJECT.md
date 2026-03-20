# Project Overview

## Mission

DataLogicEngine provides a secure, traceable, local-first platform for AI-assisted reasoning, knowledge graph operations, and governed enterprise workflows.

## Product pillars

1. **AI orchestration** — route prompts and tasks across supported model providers.
2. **Knowledge graph operations** — store, browse, and analyze a structured 17-axis graph.
3. **Traceability and auditability** — preserve runs, stages, personas, axes, and exportable evidence.
4. **Governance and compliance** — enforce policies around secrets, auth, logging, and release safety.
5. **Cross-surface delivery** — support browser workflows and Windows desktop packaging.

## Main user journeys

- Ask questions or run workflows through the chat interface.
- Inspect recent runs and trace stages.
- Explore graph nodes, relationships, and domain axes.
- Configure providers, local runtime, and MCP integrations.
- Operate and validate the stack through scripted setup and verification flows.

## Repository organization

| Area | Notes |
| --- | --- |
| `app.py` / `main.py` | Flask app bootstrap and local runtime entrypoints |
| `backend/` | Service, API, security, tracing, storage, and orchestration code |
| `frontend/` | Next.js app, Electron shell, shared UI, tests, and stories |
| `docs/` | Long-form reference and governance documentation |
| `tests/` | Python-side validation suites |
| `scripts/` | Setup, validation, deployment, packaging, and support automation |

## Current engineering priorities

- Keep frontend API clients and tests aligned with backend route contracts.
- Improve onboarding by maintaining root-level docs that point to source-of-truth material.
- Preserve production-oriented defaults around security, observability, and release controls.
- Reduce repo friction by documenting the fastest path for local development and support.

## Success criteria for contributions

A change is considered complete when it:

- solves a real product or reliability problem,
- includes or updates relevant automated checks,
- updates the necessary docs,
- keeps security/governance expectations intact,
- is reviewable without requiring tribal knowledge.
