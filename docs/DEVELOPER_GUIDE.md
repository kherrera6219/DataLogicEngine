# DataLogicEngine Developer Guide

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ENG-006 |
| Title | Developer build, test, packaging, and reproducibility guide |
| Document version | v3.2.0 |
| Product version | 4.3.0 |
| Status | active |
| Audience | Contributors, maintainers, quality engineers, release engineers, and reviewers |
| Owner | Platform Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Build scripts, exact dependency locks, CI workflows, and release controls |
| Confidentiality | Public |
| Last reviewed | 2026-08-11 |
| Next-review trigger | Toolchain, build, test, packaging, reproducibility, or CI-policy change |
| Requirements and evidence | Source tree, workflows, release locks, root plan, and phase evidence |

## Purpose

Provide the developer onboarding path and daily engineering workflow for DataLogicEngine.

The CP19-L clean-build baseline passed on 2026-08-10: 3,098 backend tests with
19 skipped, 430 frontend tests, 36 Python SDK tests, seven TypeScript SDK tests,
clean dependency/security gates, and the release payload/integrity checks. The
rebuilt unsigned candidate installed and reached readiness; CP19-M remains the
exact signed installed acceptance boundary.

This version aligns onboarding with the current local-first architecture, DMRF control plane, Truth Engine v7.3, canonical `/api/v1/*` route policy, multi-store data architecture, testing/release gates, and versioned documentation standard.

## Audience

1. New contributors
2. Backend engineers
3. Frontend engineers
4. QA/release engineers
5. AI architecture reviewers
6. Technical judges inspecting the repository

## Prerequisites

Required:

1. Python `3.11`.
2. Node.js `24`.
3. npm compatible with the checked-in `frontend/package-lock.json`.
4. Windows PowerShell for Windows local stack and packaging scripts.
5. Git with hooks support.

Optional:

1. Docker Desktop for container/build verification.
2. Provider API key for end-to-end LLM provider testing.
3. Local data services where testing full storage behavior.

Provider keys are not required for most deterministic unit/contract/parity tests.

## Initial setup

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

Run readiness checks before starting services:

```powershell
.\.venv\Scripts\python.exe .\scripts\dev_doctor.py --skip-ports
python .\scripts\runtime_precheck.py --strict --skip-ports --allow-env-from-process
python .\scripts\verify_lockfiles.py
python .\scripts\verify_environment_parity.py --strict
```

## Required environment values

Set in `.env`:

1. `SESSION_SECRET` — required for persistent sessions. Development may generate an ephemeral secret, but production refuses unsafe startup. Generate a value with:
   ```powershell
   python scripts/generate_secrets.py
   ```
2. Provider keys only when testing provider-backed flows:
   - `OPENAI_API_KEY`
   - `GEMINI_API_KEY` / `GOOGLE_API_KEY`
   - `LLM_DEFAULT_PROVIDER=google` when both OpenAI and Google keys are present and Google should be the env fallback default
   - The app uses one user-selected cloud model (OpenAI `gpt-5.5` or Google `gemini-3.1-pro-preview`); set `OPENAI_API_KEY` or `GOOGLE_API_KEY`, or save a key in Settings → AI/Model. Reasoning requires an API key + internet.
3. Runtime mode/storage values only when overriding defaults. The current supported data modes are local, VM, and auto internal service modes.

Do not carry `AUTO_CREATE_SCHEMA=true` into shared or production environments.

## Architecture orientation for developers

Read these first:

1. `docs/ARCHITECTURE.md`
2. `docs/INTERFACE_INTEGRATION.md`
3. `docs/DATA_ARCHITECTURE.md`
4. `docs/SECURITY_ARCHITECTURE.md`
5. `docs/PRODUCT_REQUIREMENTS.md`
6. `docs/KA_TRUTHCORE_VALIDATION_DOSSIER.md`
7. `docs/VERIFICATION_VALIDATION_REPORT.md`
8. `docs/generated/PRODUCTION_CONTRACT_INDEX.md`

The current request lifecycle is:

```text
frontend prompt
  -> Flask API/security envelope
  -> DMRF control plane
  -> TruthGate
  -> tier classification
  -> 17-axis routing
  -> DSQP persona construction
  -> TruthCore workflow planning
  -> model/tool execution when required
  -> evidence/convergence policy
  -> memory/audit/artifact persistence
  -> trace review/export
```

### Current build identity

The latest local engineering installer was built from runtime source commit
`a3879446c5191289cfb528586c07e7f18ea155f5`; subsequent commits through the
documentation reconciliation change build evidence or documentation, not the
runtime. The artifact is unsigned and has not passed installed-mode acceptance.
Use `docs/RELEASE_READINESS_RECORD.md` for its exact size/hash and the separate
last-installed qualification identity. Never transfer installed results between
artifact hashes.

### Phase 19 KA integration boundary

Retained CP18-B work replaced the conflicting KA registries/engines with one
generated manifest and canonical controller. Phase 18 subsequently reached 213
unique implementation owners and zero source gaps, but
CP18-D failed the whole-application wiring audit. Phase 19 is therefore the
active integration authority and the signed rebuild remains paused through
CP19-L. Before changing a KA identity or purpose, update the reviewed CP18-A
crosswalk and preserve compatible aliases. Do not join historical metadata to
an implementation by numeric ID unless the manifest proves semantic identity.

CP19-A passed on 2026-07-25. Run
`python scripts/build_ka_integration_authority.py --check` and
`python scripts/verify_ka_integration_authority.py` after changing owner,
consumer, stage, selector, effect-port, workflow-disposition, or evidence
metadata. The generated 213-row JSON/CSV authority under
`reports/production-readiness/2026/phase-19/` is planning and verification
metadata carried by the one runtime manifest, not another executable registry.
The CP19-A checkpoint baseline was 726 passing KA tests. CP19-B then migrated
all existing production callers to the typed result boundary: 621 production
Python files scanned, 18 caller/API/SDK surfaces verified, 32 typed call sites,
and zero legacy result calls. CP19-C adds
`backend/knowledge_algorithms/selection.py`, generated fixtures under
`tests/knowledge_algorithms/phase19/`, and
`scripts/verify_ka_selector_dag.py`. It verifies 213 positive and 213 negative
cases, a base 119-edge zero-cycle graph, bounded concurrency/budgets/cancellation,
and proposal-only effects. The KA/Python-SDK suite passes 781 and the full
CP19-C source suite passes 2,499 with 18 skipped. CP19-D adds typed
`GovernedReasoningState`, transport-neutral L1-L10 stage executors, a
production-mode selector-backed L1 recipe, causal/release regressions, and
durable layer/KA trace binding inside the one governed orchestrator. CP19-E
registers and production-admits all 14 L9/L10 KAs, derives invocation lists
from committed child traces,
redacts PII from release and trace state, and fails closed on required
failure/timeout, containment, confidence, recursion, promotion, and false
effect receipts. Its focused set passes 104 and the full source suite passes
2,522 with 18 skipped. CP19-F then production-admits the deterministic
`KA-012` -> `KA-013` -> `KA-030` persona chain, corrected the CP19-F graph to
132 edges/zero cycles, consumes all four axes 8-11 profiles, preserves dissent
and measured sufficiency without inventing confidence, and makes the result
causal to the one provider prompt. CP19-G canonical 12-step refinement is
also complete: one manifest registry accounts for all 12 steps, executes new
applicable KAs through the selector/DAG, makes zero provider subcalls, permits
one rewrite, revalidates L6-L10, and leaves memory/lifecycle work as an
unapplied proposal. The CP19-G manifest had 29 production-enabled
capabilities and 131 dependency edges with zero cycles. CP19-H then connects
the Truth/data/knowledge lifecycle. CP19-I connects bounded simulation,
MCP/security/operations, provider monitoring, durable jobs, and authoritative
effect receipts, and enforces `max_effects` before execution. The CP19-I
manifest production-enabled 149 capabilities with 136 zero-cycle dependency
edges. CP19-J adds the authenticated `/api/v1/ka/runs` plan, status, execute,
cancel, result, trace, artifact, and effect contract plus matching Python,
TypeScript, and desktop clients. Requests and results are encrypted at rest;
list/status data are content-free; idempotency and visibility are bound to the
exact session-or-key principal. High/critical and effect-oriented plans require
the copy-once exact-plan token. Compatibility one-shot execution still routes
through the selector and rejects work that requires review. Production workers
coordinate each run with a content-free Redis lease, renew it while executing,
and fail an unleased interrupted run without replaying it.

Implement Phase 19 in its required order: result-contract parity; manifest
selector and bounded dependency DAG; the canonical ten-layer path; corrected
fail-closed L9/L10; causal KA-backed Quad Persona/DSQP; one production 12-step
refinement workflow; Truth/data/knowledge and extended-subsystem service ports;
API/SDK/desktop workflow; and the 213-row per-KA proof matrix. Every KA has one
implementation owner and one primary owning subsystem. All other consumers use
the canonical controller; none may create a second implementation, registry,
selector, private execution path, or competing refinement workflow.

The following CP18-C batch notes are retained historical source-completion
evidence, not proof of current application integration. Batch 01 qualified 11
existing implementations by replacing unrecorded-random/mock outputs with
bounded deterministic behavior or honest
effect proposals. Its full KA regression is 469 passed. Continue in semantic
batches, retain one individually named test per KA, and never convert a proposed
effect into an applied-effect claim without the authoritative service receipt.

CP18-C Batch 02 restored eight original-design analysis capabilities under
canonical 1000-series IDs. Restored files follow
`ka_<canonical-number>_<capability>.py`; the inventory resolver accepts exactly
one such source per restored ID and fails on multiple owners. Add a bounded JSON
Schema example to every new top-level input model so API/UI tooling and the
generic contract harness can construct a valid representative request. Current
authority is 140 implementations and 73 gaps; the KA suite is 493 passed.

CP18-C Batch 03 restores eight governed decision-support KAs. Keep admission,
measurement, and coverage algorithms read-only: they return a decision and
limitations, never start work, mutate state, or convert agreement/statistical
deviation into truth. Current authority is 148 implementations and 65 gaps; the
KA suite is 517 passed.

CP18-C Batch 04 restores the final six missing original-design
knowledge-evolution KAs. Drift/alignment/lineage algorithms evaluate
caller-supplied snapshots and graphs; composition outputs remain unverified
evidence-linked candidates; memory patches and ontology resolutions remain
versioned proposals for owning-service authorization. Each canonical ID has one
source owner and one named semantic test. Current authority is 154
implementations and 59 gaps; the KA suite is 536 passed.

CP18-C Batch 05 restores ten lifecycle-governance KAs. Keep provenance,
privacy, scoring, drift, and usage algorithms observational; keep graph,
schedule, tier, and lifecycle outputs as owning-service proposals. The
authority is 164 implementations and 49 gaps; the KA suite is 567 passed.

CP18-C Batch 06 restores eight policy/release KAs. Policy and compliance
algorithms compare declared versions/results; archive, trust, quarantine,
review, and release outputs remain owning-service proposals. The authority is
172 implementations and 41 gaps; the KA suite is 592 passed.

Run both `python scripts/verify_ka_capability_inventory.py` and
`python scripts/verify_ka_runtime_authority.py` after any manifest, controller,
adapter, SDK catalog, or KA identity change. These gates reject duplicate
canonical semantics, multiple owners for one implementation, stale generated
catalogs, and private runtime bypasses.

All production KA work uses the canonical typed execution context/result/effect/
trace contract. Pure algorithms return typed values or proposals. Effectful
algorithms call only approved app-owned service ports after policy,
authorization, confirmation, idempotency, and transaction checks and must return
the authoritative receipt. Do not add direct provider/database/queue/network
paths, SDK-local handlers, generic success fallbacks, or silent exception skips.

Every canonical KA requires:

1. strict input/output schemas, version, limitations, prerequisites,
   determinism/seed policy, risk, budgets, and stable failures;
2. a selector fixture proving when it is and is not chosen;
3. at least one real owning-subsystem call path;
4. one individually named functional test of its production entry point;
5. applicable boundary, failure, security, cancellation, idempotency,
   side-effect/recovery, and performance tests;
6. causal trace assertions covering ID/version/input/output/dependencies/status/
   duration/evidence/effect receipt.

Run the focused KA/manifest/call-path tests before the full backend, SDK,
frontend, Electron/browser, security, documentation, and packaging-smoke gates.
Phase evidence belongs under
`reports/production-readiness/2026/phase-19/`; retained Phase 18 identity and
source evidence remains under its historical phase directory.

## Candidate training-dataset export tooling

`backend/dataset_exporter/` converts caller-supplied or persisted, explicitly
released traces into candidate SFT or status-labelled PRM records. It is an
owner-operated export tool, not a background training pipeline. Redaction is
mandatory. The database/API does not expose DPO because current trace storage
does not persist a governed rejected candidate.

The CLI accepts JSONL trace dictionaries rather than generating sample evidence:

```powershell
python -m backend.dataset_exporter.cli --input-jsonl .\datasets\released-traces.jsonl --type sft --format jsonl --out .\datasets\sft-export.jsonl
```

Run the focused verification with:

```powershell
python -m pytest tests/backend/test_dataset_exporter.py -q
cd frontend
npx vitest run components/settings/DatasetExporterSettings.test.tsx
npx eslint components/settings/DatasetExporterSettings.tsx components/settings/DatasetExporterSettings.test.tsx
```

Do not reinterpret PRM stage-status labels as externally validated rewards or
enable DPO without durable chosen/rejected provenance.

## Local run modes

### Fast local mode

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
```

### Full local data stack

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1 -WithDataServices
```

### Stop local stack

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\stop_local_stack.ps1
```

## Build and packaging

### Frontend build

```powershell
npm --prefix frontend run build
```

### Electron compile

```powershell
npm --prefix frontend run electron:build
```

### Desktop installer

Rebuild the backend first, then build the Electron/NSIS installer:

```powershell
.\.venv\Scripts\python.exe scripts\build_backend.py
$env:CSC_SKIP = "true"
npm --prefix frontend run electron:dist
```

### Packaging smoke, integrity, and NSIS governance

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1 -RepoRoot (Get-Location).Path
.\.venv\Scripts\python.exe scripts\verify_installer_integrity.py --require-artifacts
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path -Mode installer
```

## Daily testing workflow

### Bootstrap smoke check

```powershell
.\.venv\Scripts\python.exe .\scripts\test_smoke.py
```

### Developer environment doctor

```powershell
.\.venv\Scripts\python.exe .\scripts\dev_doctor.py --skip-ports
```

### Backend suite

```powershell
.\.venv\Scripts\python.exe -m pytest tests --maxfail=20
```

### Backend contract, parity, and security sweeps

```powershell
.\.venv\Scripts\python.exe -m pytest -q --no-cov tests\contract\test_api_contract.py
.\.venv\Scripts\python.exe -m pytest -q --no-cov tests\parity\test_local_mode_parity.py
.\.venv\Scripts\python.exe -m pytest -q --no-cov tests\security\test_security_headers.py tests\security\test_request_limits.py
```

### Frontend tests

```powershell
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build
```

### Frontend E2E and visual regression

```powershell
cd frontend
npm run test:e2e -- tests/e2e/route-sidebar-smoke.spec.ts
npm run test:e2e:visual
cd ..
```

### Provider/model validation

```powershell
.venv\Scripts\python.exe .\scripts\verify_api_keys.py
```

### Local data plane validation

```powershell
.venv\Scripts\python.exe .\scripts\verify_local_data_stack.py
python .\scripts\validate_schema_parity.py --report reports\schema_parity_report_local.json
```

### Documentation reference validation

```powershell
.venv\Scripts\python.exe .\scripts\verify_docs_references.py
```

### Governance checks

```powershell
python .\scripts\verify_environment_parity.py --strict --json-report reports\environment_parity_report_local.json
python .\scripts\verify_lockfiles.py --json-report reports\lockfile_governance_report_local.json
python .\scripts\dev\run_precommit_checks.py
```

## Repository structure

```text
DataLogicEngine/
├── app.py                 # Flask app assembly, middleware, route registration
├── backend/               # Backend services, DMRF, Truth Engine, storage, security, APIs
├── core/                  # Core axes, FROST, knowledge framework primitives
├── frontend/              # Next.js UI and Electron runtime
├── scripts/               # Local ops, validation, packaging, governance scripts
├── tests/                 # Backend tests
├── docs/                  # Active docs, diagrams, ADRs, archived material
├── sdk/                   # SDKs
├── models.py              # SQLAlchemy model layer
└── .github/workflows/     # CI, deploy, and release signing workflows
```

## Important backend areas

| Area | Path | Purpose |
|---|---|---|
| App assembly | `app.py` | Flask app, middleware, route registration, health/metrics. |
| DMRF | `backend/dmrf/` | AI control plane. |
| Truth Engine | `backend/truth_engine/` | TruthGate, TruthCore, TruthMemory, TruthLink. |
| DSQP | `backend/dsqp/` | Deterministic seven-part personas for axes 8-11. |
| Axes | `core/axes/` | 17-axis model and Axis 17 FROST mode. |
| Storage | `backend/storage/` | connection manager, graph, vector, object, USKD memory graph. |
| Memory | `backend/memory/` | UnifiedMemory structured reasoning memory. |
| Security | `backend/security/` | desktop auth, DPAPI, encryption, export integrity, guardrails. |
| LLM Gateway | `backend/llm_gateway/` | provider routing and model access. |
| Tracing | `backend/tracing/` | trace/run surfaces. |

## Important frontend areas

| Area | Path | Purpose |
|---|---|---|
| Root layout | `frontend/app/layout.tsx` | Provider stack, sidebar, nav, disclosure, desktop status. |
| Chat | `frontend/app/chat/`, `frontend/components/Chat/` | Enterprise AI interaction surface. |
| Trace | `frontend/app/runs/`, `frontend/lib/api/trace.ts` | Trace Explorer and run review/export. |
| Graph | `frontend/app/graph/`, `frontend/app/knowledge/` | Knowledge graph and node/edge review. |
| Truth monitor | `frontend/app/truth-engine/` | Truth Engine status surface. |
| MCP hub | `frontend/app/mcp/`, `frontend/components/mcp/` | Connector/server management. |
| Admin | `frontend/app/admin/` | Admin compliance/provider/MCP views (single owner; no user management). |
| Runtime policy | `frontend/lib/runtime/policy.ts` | local/hybrid/cloud runtime behavior. |
| Electron | `frontend/electron/` | desktop shell and safe IPC bridge. |

## API development rules

1. New application routes should use canonical `/api/v1/*` paths.
2. Legacy `/api/*` aliases are compatibility-only and must emit transition/deprecation headers where applicable.
3. Canonical API auth failures must return JSON-native `401`, not browser redirects.
4. Malformed canonical API requests should return deterministic validation errors.
5. Route changes require contract tests.
6. High-risk route changes require integration and security regression tests.
7. Update `docs/INTERFACE_INTEGRATION.md` when public route behavior changes.

## Data development rules

1. Keep SQL schema changes migration-controlled.
2. Do not use `AUTO_CREATE_SCHEMA=true` outside disposable local workflows.
3. Run schema parity validation after model/migration changes.
4. Use app-owned storage modes unless architecture explicitly approves a different runtime model.
5. Object-store keys must not allow absolute paths, null bytes, or traversal.
6. ChromaDB/Neo4j/USKD/UnifiedMemory changes should update `docs/DATA_ARCHITECTURE.md` when behavior changes.

## Documentation maintenance

Active documents must include:

```markdown
## Document metadata

| Field | Value |
|---|---|
| Document version | vX.Y.Z |
| Last updated | YYYY-MM-DD |
| Status | Active |
| Owner | Team Name |
| Review cadence | Every N days |
```

After major repository changes, regenerate inventory/generated structure docs when appropriate:

```powershell
.venv\Scripts\python.exe .\scripts\generate_docs.py
```

Then validate references:

```powershell
.venv\Scripts\python.exe .\scripts\verify_docs_references.py
```

## Local workflow notes

1. `/api/v1/*` is the supported REST surface for application integrations.
2. Older `/api/*` aliases are compatibility-only.
3. `AUTO_CREATE_SCHEMA=true` is local-only.
4. Run `dev_doctor` before escalating local setup issues.
5. Keep Python/Node versions aligned with CI.
6. Prefer deterministic tests without external network calls unless specifically validating provider integration.
7. Update docs and diagrams when code changes architecture, routes, storage, security, or release behavior.

## Related documents

1. `docs/ARCHITECTURE.md`
2. `docs/INTERFACE_INTEGRATION.md`
3. `docs/DATA_ARCHITECTURE.md`
4. `docs/VERIFICATION_VALIDATION_REPORT.md`
5. `docs/ADMINISTRATOR_OPERATIONS_GUIDE.md`
6. `docs/VERIFICATION_VALIDATION_REPORT.md`
7. `docs/INSTALLATION_GUIDE.md`
8. `docs/DEVELOPER_GUIDE.md`

## Change notes for v2.7.0

1. Updated version/date for the July 2026 rebuild documentation refresh.
2. Made the backend-before-installer packaging order explicit for local developers.
3. Added installer integrity plus installer-mode smoke validation to the daily packaging workflow.
4. Removed Anthropic from the user-facing provider setup list; current app settings support OpenAI and Google/Gemini.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Updated setup to use `npm ci` and current readiness checks.
3. Added architecture orientation for DMRF, Truth Engine, 17-axis, DSQP, memory, and trace/export lifecycle.
4. Added current backend/frontend area maps.
5. Added API and data development rules.
6. Expanded daily testing workflow to include contract, parity, security, schema, docs, environment, lockfile, packaging, and governance checks.
7. Added documentation metadata standard for future document updates.
