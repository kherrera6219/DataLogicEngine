# Application File Structure

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-05-30 |
| Status | Active |
| Owner | Platform Engineering |
| Review cadence | Every 30 days |

## Purpose

Define repository layout, ownership boundaries, naming conventions, inventory generation standards, and reviewer navigation guidance for DataLogicEngine.

## Audience

1. Engineers and contributors
2. Architecture and platform teams
3. Release engineers
4. Security reviewers
5. Technical judges and evaluators

---

## Repository layout (high level)

```text
DataLogicEngine/
├── backend/           # DMRF, Truth Engine, security, storage, APIs
├── core/              # 17-axis, FROST, domain abstractions
├── frontend/          # Next.js UI and Electron desktop runtime
├── routes/            # Route wiring and compatibility surfaces
├── scripts/           # Validation, generation, packaging, governance
├── tests/             # Unit, integration, security, parity, E2E
├── docs/              # Active docs, diagrams, ADRs, standards
├── deploy/            # Deployment and platform assets
├── migrations/        # Database migrations
├── .github/workflows/ # CI, deployment, release automation
├── app.py             # Flask application assembly
├── models.py          # SQLAlchemy model layer
└── main.py            # Application entry point
```

---

## Architecture ownership map

| Area | Primary paths |
|---|---|
| Frontend product surfaces | `frontend/app/`, `frontend/components/` |
| Electron desktop runtime | `frontend/electron/` |
| Runtime policy | `frontend/lib/runtime/` |
| API/security envelope | `app.py`, `backend/auth/`, `backend/security/` |
| DMRF | `backend/dmrf/` |
| Truth Engine | `backend/truth_engine/` |
| DSQP | `backend/dsqp/` |
| LLM Gateway | `backend/llm_gateway/` |
| MCP/connectors | `backend/mcp_server/` |
| Data and memory | `backend/storage/`, `backend/memory/`, `models.py` |
| Tests | `tests/` |
| Documentation | `docs/`, `docs/diagrams/` |
| Release governance | `scripts/`, `.github/workflows/` |

---

## Naming conventions

### Python

- Files/modules: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### TypeScript/React

- Components: `PascalCase.tsx`
- Hooks: `useX.ts`
- Utilities: descriptive lower/camel case
- Routes: Next.js App Router folders

### Scripts

- Validation: `verify_<area>.py`
- Generation: `generate_<area>.py`
- Windows operations: verb-first PowerShell (`start_*`, `stop_*`, `verify_*`)

---

## Reviewer navigation path

If you are new to the repository, inspect in this order:

1. `docs/PRODUCT_OVERVIEW.md`
2. `docs/ARCHITECTURE.md`
3. `docs/ARCHITECTURE_MAP.md`
4. `docs/diagrams/12_end_to_end_request_lifecycle.md`
5. `app.py`
6. `backend/dmrf/orchestrator.py`
7. `backend/truth_engine/api.py`
8. `frontend/app/layout.tsx`
9. `.github/workflows/ci.yml`

---

## Generated inventory artifacts

1. `docs/FILE_INVENTORY.csv`
2. `docs/GENERATED_STRUCTURE.md`
3. `docs/ARCHITECTURE_MAP.md`

These artifacts help reviewers navigate a repository containing thousands of files and generated assets.

---

## Generation procedure

```powershell
.venv\Scripts\python.exe .\scripts\generate_docs.py
```

Expected outputs:

1. `docs/FILE_INVENTORY.csv`
2. `docs/GENERATED_STRUCTURE.md`

---

## Validation

```powershell
python scripts/verify_docs_references.py
python scripts/verify_environment_parity.py --strict
python scripts/verify_lockfiles.py
python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process
```

---

## Related documents

1. `docs/ARCHITECTURE_MAP.md`
2. `docs/ENGINEER_ONBOARDING.md`
3. `docs/DOCUMENTATION_STANDARDS.md`
4. `docs/DOCUMENTATION_COVERAGE_MATRIX.md`
5. `docs/PRODUCT_OVERVIEW.md`

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Updated repository structure around DMRF, Truth Engine, DSQP, Electron, and governance workflows.
3. Added architecture ownership map.
4. Added reviewer navigation path.
5. Updated validation and generation guidance.
