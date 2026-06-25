# Engineer Onboarding Guide — DataLogicEngine

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-05-30 |
| Status | Active |
| Owner | Platform Engineering |
| Audience | New software engineers and technical reviewers |
| Review cadence | Every 60 days |

## Purpose

Give new engineers and technical reviewers a practical path to understand, run, test, and safely contribute to DataLogicEngine.

This version reflects the current architecture: local-first Windows/Electron runtime, Flask API/security envelope, DMRF control plane, Truth Engine v7.3, 17-axis routing, DSQP personas, trace/export integrity, multi-store data architecture, and CI/release governance.

---

## What DataLogicEngine is

DataLogicEngine is a local-first AI governance and knowledge-reasoning platform. It is not just an LLM chat wrapper.

A governed request can flow through:

```text
frontend prompt
  -> Flask API/security envelope
  -> DMRF injection defense
  -> TruthGate
  -> tier classification
  -> 17-axis routing
  -> DSQP persona construction
  -> TruthCore workflow planning
  -> model/tool execution where required
  -> evidence/convergence policy
  -> memory/audit/artifact persistence
  -> TruthLink event publication
  -> Trace Explorer / export
```

The platform can run as:

1. a Windows Electron desktop app;
2. the same Windows app stack inside a VM;
3. a controlled web/cloud deployment where explicitly configured.

---

## Mental model

Every feature usually touches one or more of these layers:

| Layer | Current role | Key paths |
|---|---|---|
| Product UI | Dashboard, chat, traces, graph, Truth Engine, MCP, settings, admin. | `frontend/app/`, `frontend/components/` |
| Runtime policy | local/hybrid/cloud behavior and Electron integration. | `frontend/lib/runtime/policy.ts`, `frontend/electron/` |
| API/security envelope | Flask app, middleware, sessions, auth, CSRF, CORS, metrics, health. | `app.py`, `backend/routes/`, `backend/auth/`, `backend/security/` |
| DMRF | AI control plane and governed request lifecycle. | `backend/dmrf/` |
| Truth Engine | TruthGate, TruthCore, TruthMemory, TruthLink. | `backend/truth_engine/` |
| 17-axis model | coordinate/risk/trust/FROST routing context. | `core/axes/`, `backend/dmrf/router.py` |
| DSQP | structured expert persona construction. | `backend/dsqp/` |
| LLM Gateway | provider routing, model calls, usage/latency behavior. | `backend/llm_gateway/` |
| Data and memory | SQL, Redis, Neo4j, USKD, ChromaDB, object store, UnifiedMemory, TruthMemory. | `models.py`, `backend/storage/`, `backend/memory/` |
| Trace/export | run history, evidence, claims, export integrity. | `backend/tracing/`, `backend/security/export_integrity.py`, `frontend/app/runs/` |
| Governance | CI, release, runtime precheck, packaging, docs, parity. | `.github/workflows/`, `scripts/`, `docs/` |

The most important engineering question is: **which layers does this change touch?**

---

## Day 1: environment setup

### Prerequisites

| Tool | Version |
|---|---|
| Python | `3.11` |
| Node.js | `24` |
| Git | current stable |
| PowerShell | Windows PowerShell or PowerShell 7 |
| Docker Desktop | optional |

### Setup commands

```powershell
git clone https://github.com/kherrera6219/DataLogicEngine.git
cd DataLogicEngine

python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

Copy-Item .env.template .env
git config core.hooksPath .githooks

cd frontend
npm ci
cd ..
```

Set in `.env`:

1. `SESSION_SECRET`
2. optional provider key for provider-backed tests:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `GEMINI_API_KEY` / `GOOGLE_API_KEY`
   - Local Ollama: no key needed. Install from [ollama.com](https://ollama.com) and run `ollama pull gemma4:12b`. Set `OLLAMA_BASE_URL` only if Ollama is on a non-default host/port. Integration tests for T0–T3 auto-skip when Ollama is offline.

### Readiness checks

```powershell
.venv\Scripts\python.exe .\scripts\dev_doctor.py --skip-ports
python .\scripts\runtime_precheck.py --strict --skip-ports --allow-env-from-process
python .\scripts\verify_lockfiles.py
python .\scripts\verify_environment_parity.py --strict
```

### Start local stack

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
```

### Verify startup

```powershell
.venv\Scripts\python.exe .\scripts\test_smoke.py
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/ready
curl http://127.0.0.1:5000/metrics
```

---

## Day 2: repository orientation

Top-level paths:

```text
DataLogicEngine/
├── app.py                     # Flask app assembly, middleware, route registration
├── main.py                    # app entry point
├── models.py                  # SQLAlchemy model layer
├── extensions.py              # shared Flask extensions
├── backend/                   # backend services, DMRF, Truth Engine, storage, security
├── core/                      # axes, FROST, knowledge framework primitives
├── frontend/                  # Next.js UI and Electron runtime
├── scripts/                   # validation, packaging, governance, local ops
├── tests/                     # backend test suites
├── docs/                      # active docs, diagrams, archived material
└── .github/workflows/         # CI/deploy/signing workflows
```

Read these first:

| Order | File | Why |
|---|---|---|
| 1 | `docs/PRODUCT_OVERVIEW.md` | product context. |
| 2 | `docs/ARCHITECTURE.md` | system architecture. |
| 3 | `docs/diagrams/12_end_to_end_request_lifecycle.md` | request lifecycle. |
| 4 | `app.py` | app assembly and middleware. |
| 5 | `backend/dmrf/orchestrator.py` | governed AI lifecycle. |
| 6 | `backend/truth_engine/api.py` | Truth Engine API surface. |
| 7 | `backend/truth_engine/truth_gate/gateway.py` | policy gate. |
| 8 | `backend/truth_engine/truth_core/engine.py` | workflow engine. |
| 9 | `backend/dsqp/dsqp_chain.py` | structured personas. |
| 10 | `backend/storage/connection_manager.py` | local/VM/auto storage policy. |
| 11 | `frontend/app/layout.tsx` | frontend provider stack and product shell. |
| 12 | `.github/workflows/ci.yml` | CI quality gates. |

---

## Week 1: core product and AI lifecycle

### DMRF

DMRF is the AI control plane. It coordinates:

1. injection defense;
2. TruthGate;
3. tier classification;
4. 17-axis routing;
5. DSQP persona construction;
6. TruthCore workflow planning;
7. evidence/convergence policy;
8. memory and audit persistence;
9. TruthLink event publication.

Read:

- `backend/dmrf/orchestrator.py`
- `backend/dmrf/injection_defense.py`
- `backend/dmrf/tier_classifier.py`
- `backend/dmrf/router.py`
- `backend/dmrf/evidence_model.py`
- `backend/dmrf/convergence_policy.py`

### Truth Engine

Truth Engine components:

| Component | Role |
|---|---|
| TruthGate | security, trust, budget, compliance, priority checks. |
| TruthCore | tiered workflow planning and execution. |
| TruthMemory | audit, metrics, artifacts, explainability, cache. |
| TruthLink | event publication and integration bus behavior. |

Read:

- `backend/truth_engine/api.py`
- `backend/truth_engine/truth_gate/gateway.py`
- `backend/truth_engine/truth_core/engine.py`
- `backend/truth_engine/truth_memory/manager.py`
- `backend/truth_engine/truth_link/bus.py`

### 17-axis model

The current 17-axis model provides coordinate and routing context. Pay special attention to:

1. Axis 15 — risk/threat domain.
2. Axis 16 — ethics/trust/criticality.
3. Axis 17 — FROST mode / TruthCore routing depth.

Read:

- `core/axes/`
- `backend/dmrf/router.py`
- `docs/diagrams/04_17_axis_coordinate_model.md`

### DSQP personas

DSQP constructs deterministic personas from axes 8-11:

1. Knowledge Expert.
2. Sector Expert.
3. Regulatory Expert.
4. Compliance Expert.

Each persona is structured by seven components:

1. job role;
2. education;
3. certifications;
4. skills;
5. training;
6. career path;
7. related jobs.

Read:

- `backend/dsqp/dsqp_chain.py`
- `docs/diagrams/10_dsqp_persona_construction_architecture.md`

---

## Week 2: security, data, and local-first runtime

### Security

Read:

- `docs/SECURITY.md`
- `docs/diagrams/06_local_first_security_model.md`
- `backend/security/desktop_local_auth.py`
- `backend/security/dpapi_store.py`
- `backend/security/export_integrity.py`
- `backend/auth/api_decorators.py`

Focus areas:

1. desktop local-auth;
2. CSRF/CORS/trusted-host/session controls;
3. DMRF injection defense;
4. TruthGate;
5. field encryption and DPAPI local protection;
6. export integrity;
7. MCP connector security.

### Data architecture

Read:

- `docs/DATABASE_SCHEMA.md`
- `backend/storage/connection_manager.py`
- `backend/storage/object_store.py`
- `backend/storage/vector_store.py`
- `backend/storage/graph_store.py`
- `backend/storage/uskd_memory_graph.py`
- `backend/memory/unified_memory_service.py`

Understand these stores:

1. SQLAlchemy DB;
2. Redis;
3. Neo4j;
4. ChromaDB;
5. local object store;
6. USKD RAM graph;
7. UnifiedMemory;
8. TruthMemory.

### Local-first runtime

Read:

- `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
- `docs/DEPLOYMENT.md`
- `frontend/electron/main.ts`
- `frontend/electron/preload.ts`
- `frontend/lib/runtime/policy.ts`

---

## Week 3: testing, CI, release, and operations

Read:

1. `docs/TESTING.md`
2. `docs/PRODUCTION_READINESS.md`
3. `docs/RELEASE_CHECKLIST.md`
4. `docs/OPERATIONAL_RUNBOOKS.md`
5. `.github/workflows/ci.yml`
6. `.github/workflows/deploy.yml`
7. `.github/workflows/release-installer-signing.yml`

Run core validation:

```powershell
python -m pytest tests --maxfail=20
python -m pytest -q --no-cov tests\contract\test_api_contract.py
python -m pytest -q --no-cov tests\parity\test_local_mode_parity.py
python -m pytest -q --no-cov tests\security\test_security_headers.py tests\security\test_request_limits.py
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build
python .\scripts\verify_docs_references.py
python .\scripts\validate_schema_parity.py
```

---

## Week 4: first contribution

Pick a low-risk contribution first:

1. documentation correction;
2. missing test for an existing behavior;
3. small UI empty-state improvement;
4. route contract clarification;
5. runbook troubleshooting update.

Before opening a PR:

1. identify touched layers;
2. run targeted tests;
3. update docs if architecture/routes/security/storage changed;
4. include before/after behavior;
5. include screenshots for UI changes;
6. include release/security impact statement.

PR checklist:

```text
[ ] Touched layers identified
[ ] Tests added/updated
[ ] Docs updated if needed
[ ] Security impact considered
[ ] Privacy impact considered
[ ] Release impact considered
[ ] Local validation commands included
```

---

## Common engineering rules

1. Prefer canonical `/api/v1/*` routes for new integrations.
2. Legacy `/api/*` aliases are compatibility-only.
3. API auth failures must be JSON-native for canonical routes.
4. Do not silently return synthetic success for provider/gateway failures.
5. Do not use `AUTO_CREATE_SCHEMA=true` outside disposable local workflows.
6. Do not add externally hosted runtime databases as default local/VM dependencies.
7. Do not put secrets in docs, logs, fixtures, or screenshots.
8. Update tests for security, route, storage, or AI-control changes.
9. Update diagrams/docs when architecture changes.
10. Avoid overclaiming compliance/tooling not backed by repo evidence.

---

## Glossary

| Term | Meaning |
|---|---|
| DMRF | Dynamic Multi-layer Reasoning Framework, the AI control plane. |
| TruthGate | Gate for security, trust, budget, compliance, and priority checks. |
| TruthCore | Tiered reasoning/workflow engine. |
| TruthMemory | Audit/explainability memory and artifact manager. |
| TruthLink | Event publication/integration bus. |
| DSQP | Dynamic Skill Qualification Persona system. |
| USKD | Universal Simulated Knowledge Database; in this repo includes RAM graph behavior. |
| FROST | Layer/depth model used for reasoning and simulation routing. |
| MCP | Model Context Protocol-style connector/tool layer. |
| Trace Explorer | UI/API surface for run evidence, claims, stages, personas, and exports. |
| Local-first | Data and runtime are app-owned/local by default, while provider/connectors may still send selected data externally. |

---

## Related documents

1. `docs/DEVELOPER_GUIDE.md`
2. `docs/PRODUCT_OVERVIEW.md`
3. `docs/ARCHITECTURE.md`
4. `docs/API.md`
5. `docs/DATABASE_SCHEMA.md`
6. `docs/TESTING.md`
7. `docs/SECURITY.md`
8. `docs/PRODUCTION_READINESS.md`
9. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Replaced older layer model with current DMRF/Truth Engine/DSQP/local-first architecture.
3. Updated onboarding path for Day 1, Day 2, Week 1, Week 2, Week 3, and Week 4.
4. Added current validation commands, contribution checklist, and engineering rules.
5. Updated glossary to reflect current architecture.
