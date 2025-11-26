# Capability Update Plan

This plan sequences the work needed to remediate gaps identified in the Universal Knowledge Graph (UKG) application and to harden the platform. Each phase is scoped to be independently deliverable while building momentum toward the full target state.

> For a runtime-focused gap analysis and the current Phase 1 runbook, see [runtime_gap_analysis.md](runtime_gap_analysis.md).

## Phase 1 – Runtime stabilization (in progress)
- **Goal:** Remove immediate deployment blockers and ensure the backend runs consistently without port collisions or duplicate entry points.
- **Scope:**
  - Normalize the backend port configuration to default to `8080` (configurable via `PORT` or `BACKEND_PORT`).
  - Ensure both `main.py` and direct `app.py` execution paths rely on the same default port.
  - Document runtime expectations for backend start commands.
- **Exit criteria:** Backend can start from any entry point using the same default port, with override support through environment variables.

## Phase 2 – Application structure consolidation
- **Goal:** Simplify service initialization and prepare for modular blueprints.
- **Scope:**
  - Introduce an application factory pattern to centralize configuration and extension wiring.
  - Consolidate route registration and error handlers under blueprints.
  - Add lightweight health checks for readiness and liveness.
- **Exit criteria:** Single canonical entry point that builds the Flask app; routes and extensions are registered in one place with health endpoints available.

## Phase 3 – Data and migration reliability
- **Goal:** Improve database correctness and lifecycle management.
- **Scope:**
  - Refine SQLAlchemy models (type correctness, relationships, and validation).
  - Add Flask-Migrate with initial migration scripts and developer runbooks.
  - Harden connection pooling settings for production use.
- **Exit criteria:** Database schema creation is reproducible via migrations; models pass validation linting; configuration covers local and production pools.

## Phase 4 – API and simulation maturity
- **Goal:** Standardize API behavior and extend simulation capabilities beyond the initial axes.
- **Scope:**
  - Introduce a consistent response envelope and error handling middleware.
  - Add authentication/authorization guards for sensitive endpoints.
  - Begin persisting simulation results and broaden coverage toward the 13-axis model.
- **Exit criteria:** APIs return consistent envelopes with authenticated access where required; simulation outputs are persisted and traceable.
