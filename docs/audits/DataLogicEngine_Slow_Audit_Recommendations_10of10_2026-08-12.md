# DataLogicEngine — Section-by-Section Recommendations (Target 10/10)

| Field | Value |
|---|---|
| Document ID | DLE-AUDIT-RECS-10-2026-08-12 |
| Title | Slow-audit recommendations to reach 10/10 per section |
| Product | DataLogicEngine Desktop |
| Product version baseline | 4.3.0 |
| Date | 2026-08-12 |
| Depends on | `docs/audits/DataLogicEngine_Slow_Section_Audit_Findings_2026-08-11.md` (v1.1) |
| Companion | `docs/audits/ORPHAN_MODULE_DISPOSITION_WORKSHEET_2026-08-11.md` |
| Intent | Actionable recommendations for Codex / implementers: updates, new files, refactors |
| Status | Recommendations only — not a release authorization |
| Phased implementation plan | `docs/audits/DataLogicEngine_Phased_Implementation_Plan_2026-08-12.md` |

---

## 1. How to use this document

1. Read the **findings** doc first (identity constraints, finding IDs F-00x, preserve list).
2. Use this doc for **what to build/change** to close gaps to **10/10 per section**.
3. Prefer small, test-gated PRs. Do not rewrite the governed spine for vanity scores.
4. Some 10/10 targets require **product decisions** (local generative B0/B1) or **release authority** (signing). Those are called out explicitly — code alone cannot fake them.
5. **Do not** treat gitignored `API KEY/`, `certs/`, or worktrees as product defects.

### Score meaning for this plan

| Score band | Meaning |
|---|---|
| Current | Slow-audit judgment (~7.2 average) |
| **10/10 section** | Section is coherent, single-path, residual-free, tested, docs match code, and product claims for that area are true |
| Global product 10/10 | Average of sections **plus** honest release posture (signed only when truly ready) |

### Global invariants (never regress)

- Single answer path: gateway → `GovernedExecutionOrchestrator` → trace
- Thin SDKs (transport only)
- Desktop single-owner auth (no accidental multi-tenant SaaS)
- Fail-closed auto-update until trust policy is real
- Simulation stays bounded and off the chat path
- Client keys never expose provider credentials

---

## 2. Current scores → target

| # | Section | Now | Target | Primary lever |
|---:|---|---:|---:|---|
| 1 | Runtime / entry | 7.5 | 10 | Single factory; version authority; clean startup |
| 2 | Auth / desktop security | 6.5 | 10 | Residue purge; auth matrix tests; no dual modes |
| 3 | LLM Gateway | 7.0 | 10 | Locality decision + god-file split + provider honesty |
| 4 | Governed execution | 8.0 | 10 | Decompose orchestrator; layer contracts; coverage |
| 5 | DMRF / Truth | 6.5 | 10 | Naming honesty; single integration path; docs |
| 6 | Axes | 7.0 | 10 | Orphan purge; alignment tests; unmanaged contracts |
| 7 | DSQP | 7.5 | 10 | Dual-engine retirement; contract freeze |
| 8 | Knowledge Algorithms | 8.0 | 10 | Manifest parity; residual KA modules; UX evidence |
| 9 | Storage | 8.0 | 10 | Desktop profile purity; Pinecone disposition |
| 10 | Ingestion / memory | 7.0 | 10 | Memory authority matrix; one write path |
| 11 | MCP | 7.5 | 10 | Route split; orphan connectors; qualification |
| 12 | Simulation | 7.5 | 10 | Residue purge; invariant tests; UI honesty |
| 13 | Training / dataset | 6.5 | 10 | Naming + DPO path or explicit non-support |
| 14 | Tracing / audit | 8.0 | 10 | Export UX; completeness SLIs; no dual SoR |
| 15 | Routes / API | 7.0 | 10 | Dual-prefix kill; admin/compliance uniqueness |
| 16 | Frontend control center | 7.5 | 10 | Copy; deps; probe framing; settings completeness |
| 17 | Electron / packaging | 7.5 | 10 | main split; first-run; trust gates real or clearly staged |
| 18 | SDK | 7.5 | 10 | Publish hygiene; manifest parity; license clarity |
| 19 | Tests / reports | 8.0 | 10 | Suite path fix; CI gates; coverage policy |
| 20 | Orphans / worktrees | 6.0 | 10 | Full purge + automated orphan guard |

---

## 3. Recommended work waves (cross-section)

Execute roughly in this order so later refactors do not thrash:

| Wave | Focus | Sections primarily lifted |
|---|---|---|
| **W0** | Owner decisions (B0/B1 generative, dual API flag policy, GraphQL keep/drop) | 3, 5, 15, 17 |
| **W1** | Orphan pyc purge + legacy-retirement map + suite path fix | 2, 6, 7, 18, 19, 20 |
| **W2** | API surface uniqueness (compliance, admin, dual prefixes) | 15, 1, 2 |
| **W3** | Generative locality (B0 purge **or** B1 restore) | 3, 5, 16, 17, 18 |
| **W4** | Memory/storage authority | 9, 10, 14 |
| **W5** | God-file decompositions (gateway api, orchestrator, mcp routes, electron main) | 3, 4, 11, 17 |
| **W6** | Frontend control-center polish + SDK publish | 16, 18 |
| **W7** | CI/coverage/a11y hardening + packaging UX | 17, 19 |
| **W8** | Release authority (signing, trust JSON, evidence) — only when ready | 17, 19, release docs |

---

## 4. Section-by-section recommendations

Each section: **gap**, **10/10 definition**, **actions** (U=update, N=new, R=refactor), **verify**, **exit**.

---

### Section 1 — Runtime / entry (7.5 → 10)

**Gap:** Dual factories (`create_app` vs legacy `backend/__init__`); version string drift; startup complexity in `app.py`.

**10/10 means:** Exactly one supported app factory for desktop/prod; product version from single authority; startup order documented and tested; no Replit/legacy boot by accident.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R1-1 | Make `create_app` the only production entry; mark legacy factory deprecated and unimported by `main.py`/`wsgi.py` | U/R | `app.py`, `main.py`, `wsgi.py`, `backend/__init__.py` |
| R1-2 | Delete or quarantine `create_legacy_app` behind `DLE_ALLOW_LEGACY_APP=1` (default off) with loud log | U | `backend/__init__.py` |
| R1-3 | Single version authority: all health/about/UI read `config/product-versions.json` via `backend/product_version.py` | U | `backend/product_version.py`, `backend/config.py`, `api_routes` health |
| R1-4 | **New** startup contract module listing required env, data-plane profile, stores init order | N | `backend/runtime/startup_contract.py` |
| R1-5 | Remove or permanently disable Replit registration path for desktop product | U | `app.py` |
| R1-6 | Test: only one factory binds routes in production config | N | `tests/unit/test_application_factory_isolation.py` (extend) |

**Verify:** factory isolation tests; health version == 4.3.0; desktop boot smoke.
**Exit:** No dual factory imports on default path; version consistent.

---

### Section 2 — Auth / desktop security (6.5 → 10)

**Gap:** Strong desktop path diluted by security orphan residue and historical multi-user concepts; complexity for auditors.

**10/10 means:** Only desktop + session + client-key surfaces exist; retired auth modules gone; authz matrix documented and tested; no MFA/RBAC/tenant_rls artifacts.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R2-1 | Purge security orphan pyc (mfa, rbac, tenant_rls, honeypot, defense_supervisor, …) per findings §18 | U | `backend/security/__pycache__/` |
| R2-2 | Extend `legacy-retirement.json` with security multi-user cluster | U | `config/legacy-retirement.json` |
| R2-3 | **New** auth surface matrix (who may call what: session vs desktop HMAC vs `ukg_` key scopes) | N | `docs/AUTH_SURFACE_MATRIX.md` or `backend/auth/SURFACE.md` |
| R2-4 | Strengthen wiring tests so retired modules cannot reappear in release payload | U | `tests/security/test_security_module_wiring.py` |
| R2-5 | Audit `api_decorators.py` for dead SSO/password branches; remove or hard-fail | U/R | `backend/auth/api_decorators.py`, `sso.py` |
| R2-6 | Ensure `sso.py` / unused auth modules are not registered | U | `backend/auth/*`, `app.py` |

**Verify:** desktop auto-login security tests; security wiring; no import of retired names.
**Exit:** Clean security package listing only live modules; matrix matches code.

---

### Section 3 — LLM Gateway (7.0 → 10)

**Gap:** Cloud-only mainline vs airgap ambition; god-file `api.py`; hollow local model; leftover tier classifiers as pyc.

**10/10 means:** Provider locality is intentional and complete (B0 **or** B1); public contract stable; admin routes namespaced; modules sized for review; no dead local stubs pretending to be real.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R3-1 | **Owner B0/B1 decision** then execute: purge local_model **or** restore from worktree | U | `backend/local_model_acceleration/`, worktree sources |
| R3-2 | If B0: delete gateway tier pyc (`complexity_classifier`, `escalation_config`, `tier_availability`); document cloud-only in capabilities | U | `backend/llm_gateway/*`, `external_contract.py` |
| R3-3 | If B1: restore local provider **server-side only**; virtual model matrix includes real local path; Electron status truthful | U/N | providers, `active_model.py`, Electron main |
| R3-4 | **Refactor** split `llm_gateway/api.py` into packages: chat, runs, admin_providers, admin_keys, openai_compat | R | `backend/llm_gateway/api.py` → `api/` package |
| R3-5 | Namespace gateway admin under `/api/v1/admin/gateway/*` if dual admin remains (coord with §15) | U | `llm_gateway/api.py`, frontend `lib/api/gateway.ts` |
| R3-6 | Capabilities endpoint returns explicit `generative_locality: cloud_byok | local | hybrid` | U | capabilities route + OpenAPI |
| R3-7 | Contract tests for OpenAI-compat + gateway v1 unchanged except versioned additions | U | `tests/contract/*` |

**Verify:** gateway unit/integration; contract; single-path still holds.
**Exit:** No hollow local stack; api package < ~400 LOC per file; capabilities honest.

---

### Section 4 — Governed execution L1–L10 (8.0 → 10)

**Gap:** `orchestrator.py` size; layer boundaries hard to review; extended subsystems density.

**10/10 means:** Orchestrator is a thin director; each layer has a clear module + contract tests; refinement and quality gates documented with invariants.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R4-1 | **Refactor** extract stage runners from `orchestrator.py` (intake, retrieve, persona, ka, refine, validate, persist) | R | `backend/governed_execution/orchestrator.py` → `stages/*.py` |
| R4-2 | **New** layer contract schema (inputs/outputs/side-effects allowed) | N | `backend/governed_execution/layer_contracts.py` + tests |
| R4-3 | Ensure dynamic skip path for easy problems is explicit + traced (tier-based short circuit) | U | orchestrator, DMRF tier, trace stages |
| R4-4 | Coverage map: each L1–L10 has at least one unit/integration assertion | U/N | `tests/governed_execution/*` |
| R4-5 | Document 12-step refinement mapping to code symbols | U | `docs/` or module docstring only if code-owned |

**Verify:** existing orchestrator + single-path + refinement tests; no behavior change without fixture diffs.
**Exit:** orchestrator director pattern; layer contracts enforced in tests.

---

### Section 5 — DMRF / Truth (6.5 → 10)

**Gap:** Truth library language overshoots live path; dual mental models; blockchain/web3-ish residue risk.

**10/10 means:** DMRF is clearly the live router; Truth modules that are live are named/docs-aligned; non-live Truth paths are retired or behind experimental flags; UI matches.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R5-1 | Soften public names/claims: Truth Engine UI = “Truth gate telemetry / evidence” unless full private workflow restored | U | `frontend/app/truth-engine/*`, about copy |
| R5-2 | Inventory `truth_engine/` for unused blockchain/web3 adapters; retire or flag experimental | U | `backend/truth_engine/*` |
| R5-3 | Single integration entry: DMRF truth adapter only on L1; document call graph | U | `backend/dmrf/truth_integration/*` |
| R5-4 | Delete orphan truth_core router/persona_sufficiency pyc | U | orphan purge |
| R5-5 | **New** architecture note: DMRF vs TruthCore responsibilities (code-aligned) | N | `docs/adr/` or short `docs/DMRF_TRUTH_BOUNDARY.md` |
| R5-6 | Keep `test_single_path` asserting TruthCore public process uses gateway | U | `tests/governed_execution/test_single_path.py` |

**Verify:** DMRF integration tests; truth API tests; no second generative path.
**Exit:** Naming matches behavior; experimental modules quarantined.

---

### Section 6 — Axes (7.0 → 10)

**Gap:** Orphan old axis names; historical rename debt; unmanaged Axis 5 contract.

**10/10 means:** One manager per axis number; no old-name pyc; alignment tests for all registered axes; unmanaged axes explicit and tested.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R6-1 | Delete axis orphan pyc (axis3_domain, axis5_honeycomb old, axis14_provenance, …) | U | `core/axes/__pycache__/` |
| R6-2 | Finish rename consistency (filenames match axis numbers) per prior work queue | U | `core/axes/*`, `axis_system.py` |
| R6-3 | Axis 5 unmanaged: either implement manager **or** hard contract test for unmanaged shape | U/N | `axis_system.py`, tests |
| R6-4 | Extend `test_axis_alignment.py` for 14–17 live names | U | `tests/unit/test_axis_alignment.py` |
| R6-5 | Compact DMRF vector vs full 17-axis: document which path is live on chat | U | dmrf + coordinate_system |

**Verify:** axis alignment + persona axes tests.
**Exit:** zero axis orphans; registration table matches files 1:1.

---

### Section 7 — DSQP (7.5 → 10)

**Gap:** Non-live quad/persona packages and orphan engines; IP-sensitive component count decisions.

**10/10 means:** Only `backend/dsqp` constructs personas for governed runs; other engines retired; component contract frozen and tested.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R7-1 | Purge `core/persona` orphan engines pyc; retire unused imports from master workflow | U | `core/persona/*`, `core/orchestration/*` |
| R7-2 | Confirm `backend/quad_persona` vs `core/persona/quad` vs DSQP — keep one live, mark others legacy-retirement | U | packages + `legacy-retirement.json` |
| R7-3 | Freeze DSQP component count in a single contract test (5-part or 7-part after owner D-1) | U/N | `dsqp_chain.py`, tests |
| R7-4 | Ensure gateway/DSQP status IPC matches backend | U | Electron + gateway status routes |

**Verify:** DSQP unit/benchmark; phase D tests.
**Exit:** one persona construction authority on live path.

---

### Section 8 — Knowledge Algorithms (8.0 → 10)

**Gap:** Residual KA modules; TS manifest bulk/staleness; a few non-executable slots need clear UX.

**10/10 means:** Manifest is single SoR; all production-enabled KAs have fixtures; client manifests hash-match server; product workflow plan→confirm→execute fully instrumented.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R8-1 | Delete orphan KA pyc (`ka_50_...`) | U | knowledge_algorithms pyc |
| R8-2 | Server endpoint for manifest hash/version; SDKs/frontend pin and verify | N/U | KA routes, TS SDK, algorithms page |
| R8-3 | Generate TS `ka-manifest` at build from server file (optional thin client without 746KB embed) | R/N | `sdk/DataLogicEngine_TypeScript_SDK/`, build script |
| R8-4 | Expand per-KA semantic fixtures for any production-enabled gap | U | `tests/knowledge_algorithms/*` |
| R8-5 | Algorithms UI: always show admission/rejection reasons (already partial) + link to trace | U | `frontend/app/algorithms/page.tsx` |

**Verify:** phase18/19 KA tests; algorithms frontend tests.
**Exit:** manifest parity check green; no orphan KA modules.

---

### Section 9 — Storage (8.0 → 10)

**Gap:** Pinecone/cloud vector code paths; residual route pyc; profile purity for desktop.

**10/10 means:** Desktop profile only initializes local stores; cloud vector backends absent or impossible in desktop mode; storage health complete; orphan routes gone.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R9-1 | Gate or remove Pinecone and non-desktop object backends when `DLE_DESKTOP_MODE` / data plane profile is desktop | U | `backend/storage/vector_store.py`, object_store |
| R9-2 | Delete storage_* orphan route pyc | U | `backend/routes/__pycache__/` |
| R9-3 | Storage health returns all plane components with required/optional flags | U | `storage_routes.py` |
| R9-4 | **New** data-plane profile matrix test (qualification vs production vs blocked) | N | `tests/storage/*`, `tests/unit/test_data_plane_*` |
| R9-5 | Document authority: Postgres (or SQLite desktop) SoR + outbox materializations | U | `docs/DATA_ARCHITECTURE.md` only if code already true |

**Verify:** storage tests; packaging data-plane init.
**Exit:** no unexpected network vector backends on desktop profile.

---

### Section 10 — Ingestion / memory (7.0 → 10)

**Gap:** Multiple memory systems (UnifiedMemory, TruthMemory, lifecycle, graph JSON).

**10/10 means:** One write-authority model for operator-visible memory; ingestion outcomes always materialize to that model; review/export/compact APIs consistent.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R10-1 | **New** memory authority matrix (write/read owners per store) | N | `docs/MEMORY_AUTHORITY.md` + `backend/memory/authority.py` constants |
| R10-2 | Route all operator memory APIs through `UnifiedMemoryService` (or rename to the true SoR) | U/R | `memory_routes.py`, services |
| R10-3 | Ingestion completion hooks update memory + graph consistently; reconciliation job | U | `backend/ingestion/*` |
| R10-4 | Deprecate duplicate TruthMemory public APIs or proxy them | U | truth_engine memory |
| R10-5 | Frontend MemoryManagementSettings reflects authority (no dead controls) | U | `frontend/components/settings/MemoryManagementSettings.tsx` |

**Verify:** memory tests; ingestion tests; settings tests.
**Exit:** one documented write path; no dual memory SoR in UI.

---

### Section 11 — MCP (7.5 → 10)

**Gap:** 70KB route god-file; orphan jira/salesforce; qualification flags complexity.

**10/10 means:** MCP routes modular; only qualified connectors ship; consent fingerprint enforced everywhere; orphans gone.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R11-1 | **Refactor** split `mcp_routes.py` into servers/tools/consent/lifecycle blueprints | R | `backend/routes/mcp_routes.py` → `mcp_routes/` |
| R11-2 | Delete jira/salesforce orphan pyc (or WIRE only if owner Decision D) | U | `mcp_server/tools/` |
| R11-3 | Centralize connector qualification gate (single function) | U | `mcp_server/policy.py`, registry |
| R11-4 | Frontend MCP hub + admin pages share one client module contract | U | `frontend/lib/api/mcp.ts`, pages |
| R11-5 | Malicious stdio + consent tests remain required CI slice | U | `tests/mcp/*` |

**Verify:** phase11 MCP tests; route auth boundaries.
**Exit:** modular routes; no unqualified connector defaults.

---

### Section 12 — Simulation (7.5 → 10)

**Gap:** Residual old engines; ensure UI cannot imply chat-time simulation.

**10/10 means:** Only bounded simulation package is live; chat refuses simulation provider; UI budgets visible; orphan sim engines gone.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R12-1 | Delete `backend/simulation/simulation_engine` pyc + old core sim orphans | U | orphan purge |
| R12-2 | Hard invariant test: gateway chat rejects simulation virtual models / provider | U/N | gateway + simulation tests |
| R12-3 | Simulations UI shows call budgets (4/5/7) and depth limits from contracts | U | `frontend/app/simulations/page.tsx` |
| R12-4 | Align core/simulation vs backend/simulation — document which is live for product sim | U | packages + retirement JSON |

**Verify:** simulation stack tests; chat path tests.
**Exit:** one product simulation engine; chat isolation proven.

---

### Section 13 — Training / dataset (6.5 → 10)

**Gap:** No in-app trainer; DPO incomplete; naming can oversell.

**10/10 means:** Either (A) honest “dataset export only” product with complete SFT/PRM/admission UX and docs, **or** (B) real trainer integration. Prefer (A) for hobby scope.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R13-1 | Rename UI/docs to “Dataset preparation / export” everywhere training implies train-in-app | U | settings DatasetExporter, README snippets |
| R13-2 | Explicit API error contracts for DPO-without-rejects (already fail-closed) + OpenAPI | U | `dataset_routes.py`, openapi |
| R13-3 | **New** optional external trainer handoff guide (export layout → recommended tools) | N | `docs/DATASET_EXPORT_HANDOFF.md` |
| R13-4 | If owner wants 10/10 “training product”: design trainer adapter (out of process) — **new** `backend/dataset_exporter/trainer_handoff.py` | N | only if product expands |
| R13-5 | Sidebar or settings badge: “Export only — no local trainer” | U | frontend |

**Verify:** dataset exporter tests.
**Exit:** zero oversell; export path complete and documented.

---

### Section 14 — Tracing / audit (8.0 → 10)

**Gap:** Minor dual feed paths; export UX; completeness metrics.

**10/10 means:** TraceRun is undisputed SoR; export always signed/verifiable; live progress + explorer consistent; audit log retention clear.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R14-1 | Unify live-progress + ka-execution-feed under one trace API family | U/R | `backend/tracing/api.py` |
| R14-2 | Export always produces integrity metadata; UI download + verify action | U | export_integrity, frontend runs/view |
| R14-3 | SLI: % runs with full stage graph; surface on diagnostics | U/N | diagnostics page + metrics |
| R14-4 | AuditLogger retention/rotation config for desktop runtime dir | U | `backend/security/audit_logger.py` |

**Verify:** trace tests; export authenticity tests.
**Exit:** end-to-end export verify on desktop smoke.

---

### Section 15 — Routes / API surface (7.0 → 10)

**Gap:** Dual prefixes; dual compliance; dual admin; OpenAPI/Swagger drift; GraphQL GraphiQL; unregistered APIs.

**10/10 means:** One prefix policy; unique routes; OpenAPI version aligned; dead modules gone; GraphQL policy explicit.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R15-1 | **Fix F-001:** single compliance owner; merge or rename second blueprint | U/R | `regulatory_api.py`, `compliance_routes.py`, `app.py` |
| R15-2 | **Fix F-002:** legacy `/api/*` mirrors behind `DLE_LEGACY_API_PREFIXES=0` default off for new installs | U | `app.py`, `routes/__init__.py` |
| R15-3 | **Fix F-003:** namespace admin ops vs gateway admin | U | admin_routes, llm_gateway admin, frontend |
| R15-4 | OpenAPI `info.version` → product 4.3.0; regenerate subset; ship swagger.json **or** remove Swagger UI | U/N | `docs/openapi.yaml`, static assets |
| R15-5 | Dispose unregistered `security_api` / `time_api` (archive or register intentionally) | U | backend/*api.py |
| R15-6 | GraphQL: disable GraphiQL outside dev; require auth on all ops | U | `graphql_schema.py` |
| R15-7 | **New** route uniqueness CI script | N | `scripts/verify_route_uniqueness.py` + test |
| R15-8 | Health version from product-versions (F-012) | U | `api_routes.py` |

**Verify:** route uniqueness; contract tests; integration_routes.
**Exit:** zero colliding rules; OpenAPI matches public contract; legacy off by default.

---

### Section 16 — Frontend control center (7.5 → 10)

**Gap:** Home/chat-forward copy; dependency classification; probe vs product framing.

**10/10 means:** Control center is obvious; chat labeled probe; settings complete; deps correct; no dead pages.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R16-1 | Home page: lead with Dashboard/Settings/Gateway; chat as “Path probe” | U | `frontend/app/page.tsx` |
| R16-2 | Sidebar: rename “Enterprise AI” → “Chat probe” or “Governed chat” | U | `AppSidebar.tsx` |
| R16-3 | Move Next/React to correct dependency section for install mode **or** document electron-only | U | `frontend/package.json` |
| R16-4 | Settings tabs cover all ops surfaces; deep-link table in developer guide | U | settings page + components |
| R16-5 | Cloud disclosure remains; locality badge from gateway capabilities | U | CloudDisclosureBanner, DesktopStatus |
| R16-6 | Remove unused PlaceholderPage paths if any reappear | U | components |

**Verify:** vitest; playwright route smoke; a11y.
**Exit:** copy matches product identity; npm install story clear.

---

### Section 17 — Electron / packaging (7.5 → 10)

**Gap:** main.ts monolith; Podman first-run UX; CSP unsafe-inline; ship gates vs engineering quality.

**10/10 means:** Modular main process; excellent first-run; security headers tight as practical; update trust either fully qualified **or** clearly engineering-only with no unsigned “production” claims.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R17-1 | **Refactor** split `main.ts` → `electron/main/{secrets,backend,ipc,protocol,updater,window}.ts` | R | `frontend/electron/main.ts` |
| R17-2 | First-run wizard when Podman machine missing (actionable error, not only quit) | U/N | main + optional React route |
| R17-3 | CSP: migrate toward nonces/hashes where static export allows; document residual risk | U | main CSP block |
| R17-4 | Keep update fail-closed until real publisher subjects + gates true | U | update-trust, release-trust-policy |
| R17-5 | If B1: local-model-status truthful; if B0: remove IPC channel or label “not available” | U | main.ts, preload |
| R17-6 | Packaging smoke asserts backend exe + policies + release JSON present | U | CI windows-packaging-smoke |
| R17-7 | **Release authority track:** production codesign, trust policy true only with evidence | U | certs process, release JSON — owner-led |

**Verify:** electron unit tests; packaging smoke; update-trust tests.
**Exit:** modular main; first-run UX; honesty on signing.

**Note:** Full commercial 10/10 for *shipping* requires Wave W8 (real signing). Engineering 10/10 can be “fail-closed + modular + smoke green.”

---

### Section 18 — SDK (7.5 → 10)

**Gap:** Stale 0.3.1 wheel; provider pyc; naming UKG vs DataLogicEngine; huge TS manifest.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R18-1 | Delete provider/handler orphan pyc; remove empty packages | U | `sdk/UKG_Python_SDK/ukg_sdk/providers` |
| R18-2 | Rebuild wheel/sdist **0.7.0**; delete 0.3.1 artifacts | U | `dist/` under SDK |
| R18-3 | Align package display name / User-Agent with DataLogicEngine while keeping import `ukg_sdk` if needed | U | pyproject, __init__, README |
| R18-4 | TS SDK: manifest hash check or generate-on-build; drop giant commit churn if possible | R | TypeScript SDK |
| R18-5 | License notice: MIT SDK vs PolyForm app — **new** `sdk/LICENSE_NOTICE.md` | N | sdk/ |
| R18-6 | Examples gate: run against local gateway in CI optional job | U | `examples/gateway/*` |

**Verify:** SDK pytest + TS gateway tests.
**Exit:** installable 0.7.0 only; no client providers; docs match thin client.

---

### Section 19 — Tests / reports (8.0 → 10)

**Gap:** `tests/resilience` missing; CI `--no-cov`; soft a11y; dual e2e trees.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R19-1 | Fix `run_test_suite.py` Phase 4 (remove resilience or restore package) | U | `run_test_suite.py`, optional `tests/resilience/` |
| R19-2 | CI policy: either enable coverage fail_under with realistic threshold **or** document “coverage local-only” in TESTING | U | `ci.yml`, `pyproject.toml`, docs |
| R19-3 | Promote a11y from continue-on-error when release claims a11y | U | `ci.yml` |
| R19-4 | Naming map for e2e trees (backend e2e vs end_to_end vs frontend playwright) | U | `docs` testing section / README tests |
| R19-5 | **New** orphan-pyc guard test | N | `tests/unit/test_no_orphan_pyc.py` |
| R19-6 | **New** route uniqueness test (ties §15) | N | tests/contract |
| R19-7 | Keep production-readiness reports updated when gates flip — process, not code | U | `reports/`, release readiness |

**Verify:** phased runner green; CI green.
**Exit:** no broken suite paths; policy on coverage/a11y explicit.

---

### Section 20 — Orphans / worktrees (6.0 → 10)

**Gap:** ~78 orphan modules; incomplete retirement map.

**10/10 means:** Zero orphan pyc on main; retirement JSON complete; automated guard; worktrees documented as non-product.

| ID | Action | Type | Primary paths |
|---|---|---|---|
| R20-1 | Execute findings §18 disposition (default DELETE all except B1 if chosen) | U | whole tree pyc |
| R20-2 | Extend `config/legacy-retirement.json` for every major cluster | U | config |
| R20-3 | Script `scripts/scan_orphan_pyc.py` + CI optional job | N | scripts/, ci |
| R20-4 | Document worktrees: never ship; recovery only | U | CONTRIBUTING or HANDOFF note |
| R20-5 | Do not delete owner gitignored keys/certs | — | n/a |

**Verify:** scan returns 0 orphans; security wiring tests.
**Exit:** clean main tree bytecode; retirement map complete.

---

## 5. New files summary (recommended creates)

| New file / package | Purpose | Sections |
|---|---|---|
| `backend/runtime/startup_contract.py` | Startup order / required env | 1 |
| `backend/governed_execution/stages/*.py` | Orchestrator split | 4 |
| `backend/governed_execution/layer_contracts.py` | Layer I/O contracts | 4 |
| `backend/llm_gateway/api/` package | Split god api.py | 3, 15 |
| `backend/routes/mcp_routes/` package | Split MCP routes | 11 |
| `backend/memory/authority.py` | Memory SoR constants | 10 |
| `docs/MEMORY_AUTHORITY.md` | Operator-visible memory map | 10 |
| `docs/AUTH_SURFACE_MATRIX.md` | Authz matrix | 2 |
| `docs/DMRF_TRUTH_BOUNDARY.md` | Naming/boundary honesty | 5 |
| `docs/DATASET_EXPORT_HANDOFF.md` | Training honesty | 13 |
| `sdk/LICENSE_NOTICE.md` | Dual license clarity | 18 |
| `scripts/verify_route_uniqueness.py` | Route collision guard | 15, 19 |
| `scripts/scan_orphan_pyc.py` | Orphan guard | 20, 19 |
| `tests/unit/test_no_orphan_pyc.py` | CI guard | 19, 20 |
| `frontend/electron/main/*.ts` | Split electron main | 17 |
| Optional `tests/resilience/` | Only if keeping phased target | 19 |

---

## 6. Refactor targets (size / ownership)

| Current file | Problem | Direction |
|---|---|---|
| `app.py` | Registration + lifecycle bulk | Keep registration; extract startup_contract |
| `backend/llm_gateway/api.py` | 50+ routes | Package by domain |
| `backend/governed_execution/orchestrator.py` | God director | stages/* |
| `backend/routes/mcp_routes.py` | ~70KB | mcp_routes package |
| `frontend/electron/main.ts` | ~1.8k lines | electron/main/* |
| `frontend/app/algorithms/page.tsx` | Large but OK | extract hooks/components if needed |
| Dual compliance/admin blueprints | Collisions | merge/namespace |

---

## 7. Definition of done for “all sections 10/10”

A section may be marked 10/10 only when **all** are true:

1. Recommended actions for that section closed or explicitly waived by owner with written residual risk.
2. Related finding IDs closed or waived.
3. Automated tests for that section green in CI.
4. Docs/UI claims for that section match code.
5. No orphan pyc related to that section.
6. No dual live path for that section’s authority.

**Product-wide average 10/10** additionally requires:

- Owner B0/B1 executed completely.
- API uniqueness (W2) complete.
- Orphan scan = 0.
- Release JSON still honest (production_authorized only when signing evidence exists).

---

## 8. Mapping to findings (quick)

| Findings | Recommendation sections |
|---|---|
| F-001..F-003, F-007, F-011, F-012 | §15 |
| F-004, F-010, F-034, §18 orphans | §20, §2, §6 |
| F-005, local model | §3, §17, §18 |
| F-006 update trust | §17 |
| F-008 dual factory | §1 |
| F-009 unregistered APIs | §15 |
| F-013 memory | §10 |
| F-014 dual persona | §7 |
| F-015 god files | §3, §4, §11, §17 |
| F-016 training | §13 |
| F-017 Truth naming | §5 |
| F-018 MCP | §11 |
| F-020..F-021 SDK | §18 |
| F-022..F-023 frontend | §16 |
| F-025..F-027 tests | §19 |
| F-029..F-031 Electron | §17 |
| F-033 Pinecone | §9 |

---

## 9. Owner decisions required before coding (blockers)

| ID | Decision | Blocks |
|---|---|---|
| D-GEN | **B0** cloud-BYOK only vs **B1** restore local generative | §3, §17, §18, §20 |
| D-API | Legacy `/api/*` hard-off vs long deprecation | §15 |
| D-GQL | Keep GraphQL (auth+no GraphiQL) vs remove | §15 |
| D-DSQP | 5-part vs 7-part persona contract (IP) | §7 |
| D-TRAIN | Export-only forever vs future external trainer | §13 |
| D-SIGN | When to set production_authorized / real codesign | §17, release docs |

---

## 10. Suggested first PR sequence (concrete)

1. **PR-A:** Orphan pyc purge (non-B1 clusters) + legacy-retirement updates + `scan_orphan_pyc` script.
2. **PR-B:** Fix `run_test_suite.py` + health version + product version authority.
3. **PR-C:** Compliance + admin route uniqueness + route uniqueness test.
4. **PR-D:** Legacy API prefix flag default off.
5. **PR-E:** B0 purge local_model **or** B1 restore (owner).
6. **PR-F:** Memory authority module + settings alignment.
7. **PR-G:** Split llm_gateway api package (behavior-preserving).
8. **PR-H:** Split electron main (behavior-preserving).
9. **PR-I:** Frontend copy + package.json deps.
10. **PR-J:** SDK rebuild 0.7.0 + delete provider pyc + license notice.
11. **PR-K:** CI coverage/a11y policy.
12. **PR-L:** (Later) release signing authority work.

---

## 11. Document history

| Version | Date | Notes |
|---|---|---|
| 1.0 | 2026-08-12 | Initial section-by-section 10/10 recommendations from slow audit |

---

## 12. Cross-links

| Document | Role |
|---|---|
| `docs/audits/DataLogicEngine_Slow_Section_Audit_Findings_2026-08-11.md` | Findings + orphan §18 |
| `docs/audits/ORPHAN_MODULE_DISPOSITION_WORKSHEET_2026-08-11.md` | Owner checkboxes for orphans |
| `docs/audits/DataLogicEngine_Phased_Implementation_Plan_2026-08-12.md` | Ordered PRs, AC, gates |
| `docs/RELEASE_READINESS_RECORD.md` | Go/No-Go authority |
| `CODEX_WORK_QUEUE_2026-08-10.md` | Prior decisions (defense_supervisor, etc.) |
| `config/legacy-retirement.json` | Formal retirement map |

**End of recommendations.**
