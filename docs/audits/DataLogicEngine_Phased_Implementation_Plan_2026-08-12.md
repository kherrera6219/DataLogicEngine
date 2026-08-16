# DataLogicEngine — Phased Implementation Plan (Audit Remediation → 10/10)

| Field | Value |
|---|---|
| Document ID | DLE-PLAN-IMPL-2026-08-12 |
| Title | Phased implementation plan from slow audit |
| Date | 2026-08-12 |
| Product baseline | DataLogicEngine Desktop 4.3.0 |
| Current product | DataLogicEngine Desktop 4.4.0 |
| Status | Phases 1–4 and 6–7 implemented and post-QC qualified; **Phase 5 partial/deferred** |
| Inputs | Findings v1.2 · Recommendations 10/10 · Orphan worksheet |
| Audience | Owner + Codex / implementers |

---

## 1. Purpose

Turn the slow-audit **findings** and **10/10 recommendations** into an ordered sequence of **phases, PRs, and tickets** with:

- Dependencies
- Acceptance criteria
- Verification commands
- Finding IDs closed
- Explicit **owner decision gates**

**Do not** treat completion of engineering phases as public/production release.
The root `PRODUCTION_COMPLETION_PLAN_2026.md` remains the sole release execution
authority; `docs/RELEASE_READINESS_RECORD.md` records the current decision.

---

## 2. Source documents

| Doc | Path |
|---|---|
| Findings | `docs/audits/DataLogicEngine_Slow_Section_Audit_Findings_2026-08-11.md` |
| Recommendations | `docs/audits/DataLogicEngine_Slow_Audit_Recommendations_10of10_2026-08-12.md` |
| Orphan worksheet | `docs/audits/ORPHAN_MODULE_DISPOSITION_WORKSHEET_2026-08-11.md` |
| Release authority | `docs/RELEASE_READINESS_RECORD.md` |
| Prior decisions | `CODEX_WORK_QUEUE_2026-08-10.md` |
| Retirement map | `config/legacy-retirement.json` |

---

## 3. Global rules for every PR

1. **Preserve invariants:** gateway → governed execution → trace; thin SDKs; desktop single-owner auth; fail-closed updates; simulation off chat path.
2. **One logical change per PR** (or tightly coupled pair).
3. **Tests first or with** the change; no green-by-skip.
4. **Docs only when code behavior changes.**
5. **Never commit** gitignored `API KEY/`, `certs/`, or secrets.
6. **Never wire** `defense_supervisor` (decided deprecate).
7. Prefer **delete orphan pyc** over resurrecting bytecode.
8. After each phase: update this plan’s checklist status (or a short `reports/` note).

### Standard verification (run what applies)

```text
# Backend (CI parity)
python -m pytest tests/ --no-cov -q

# Always after auth/gateway/spine changes
python -m pytest -q --no-cov tests/governed_execution/test_single_path.py tests/security/test_security_module_wiring.py

# Contract when API changes
python -m pytest -q --no-cov tests/contract/

# Frontend when UI/Electron changes
cd frontend && npm run typecheck && npm run test
```

---

## 4. Owner decision gates (Phase 0 — before implementation)

Complete these **before** Phase 3 (generative) and before any WIRE of orphans.

| Gate ID | Decision | Options | Default if owner silent | Blocks |
|---|---|---|---|---|
| **G-GEN** | Generative locality | **B0** cloud-BYOK only · **B1** restore local generative | **B0** (matches mainline Electron stub) | PR-P3-* |
| **G-API** | Legacy `/api/*` prefixes | **Hard-off default** · long deprecation | Hard-off default for new installs | PR-P2-03 |
| **G-GQL** | GraphQL | **Keep + auth, GraphiQL dev-only** · remove | Keep + harden | PR-P2-04 |
| **G-DSQP** | Persona contract | Keep **5-part** · expand **7-part** (IP) | Keep 5-part | PR-P6-05 / DSQP work |
| **G-TRAIN** | Training product | **Export-only** · future external trainer | Export-only | PR-P4-TRAIN |
| **G-MCP-CONN** | Jira/Salesforce | **Delete** · wire | Delete | orphan purge |
| **G-SIGN** | When to production-sign | Later only with evidence | Stay fail-closed | Phase 8 |

### 4.1 LOCKED owner decisions (2026-08-12)

**Status: Phase 0 complete for implementation.** Owner confirmed all suggested answers except DSQP.

| Gate ID | **LOCKED decision** | Notes for implementers |
|---|---|---|
| **G-GEN** | **B0 — cloud BYOK only** | Purge local_model residue in Phase 3 B0 track. Do not restore Ollama path. |
| **G-API** | **Hard-off default** for legacy `/api/*` mirrors | Only `/api/v1` (+ intentional OpenAI `/v1`) unless `DLE_LEGACY_API_PREFIXES=1`. |
| **G-GQL** | **Keep + harden** | Auth required; GraphiQL **dev-only**, not production desktop. |
| **G-DSQP** | **7-part persona required** | **Override of prior 5-part default.** Implement Traits + Related Roles (or equivalent 7-part contract). Align code, tests, and product/IP-facing docs. See §4.2. |
| **G-TRAIN** | **Export-only** | Dataset preparation/export; no in-app trainer. Honest UI/docs. |
| **G-MCP-CONN** | **Delete** Jira/Salesforce orphans | Do not wire; purge pyc/residue in Phase 1. |
| **G-SIGN** | **Not now** | Stay release_blocked / fail-closed auto-update. Skip Phase 8 until owner reopens. |

### 4.2 G-DSQP = 7-part — implementation implications

Current mainline DSQP is documented/audited as a **5-component** construction chain. Owner requires the **7-part** persona contract.

Codex / implementers must:

1. Inventory live components in `backend/dsqp/dsqp_chain.py` and persona construction services.
2. Define the **exact 7 parts** (canonical names) in one contract module/test — e.g. existing 5 plus **Traits** and **Related Roles** (per prior work-queue D-1), unless product docs name different seventh fields.
3. Implement missing components end-to-end on the **live** path only (`backend/dsqp`, governed L4/L5 as applicable). Do **not** revive orphan `core/persona/*` engines.
4. Update tests to **assert component count == 7** and payload shape.
5. Update any patent/technical disclosure crosswalk docs **in-repo** that still claim 5-part, so code and disclosure match.
6. Treat this as a **first-class Phase 4/6 workstream**, not a drive-by: recommend dedicated PRs (see PR-P4-DSQP / PR-P6-05 below).

**Risk:** IP/docs mismatch if code goes to 7 while external disclosure still says 5 — close both in the same phase.

### Phase 0 deliverable

| Ticket | Title | Owner | Done when |
|---|---|---|---|
| **T-0.1** | Record G-* decisions in this file §4 table or orphan worksheet | Owner | **DONE 2026-08-12** (§4.1) |
| **T-0.2** | Codex reads findings + recs + this plan; no code yet | Codex | Kickoff note |

**Phase 0 exit:** Gates G-GEN, G-API, G-GQL, G-MCP-CONN, G-TRAIN, **G-DSQP**, G-SIGN recorded — **met**.
---

## 5. Phase map overview

```text
P0 Decisions
  → P1 Hygiene & orphans (safe)
  → P2 API surface uniqueness
  → P3 Generative locality (B0 or B1)
  → P4 Authority planes (memory, storage, training honesty, truth naming)
  → P5 Refactors (gateway, orchestrator, MCP, electron)
  → P6 Product polish (frontend, SDK publish)
  → P7 CI / packaging UX
  → P8 Release authority (optional, owner-led)
```

| Phase | Name | Risk | Est. effort* | Primary sections lifted |
|---:|---|---|---|---|
| 0 | Decisions | None | 1 session | — |
| 1 | Hygiene & orphans | Low | S–M | 2, 6, 7, 18, 19, 20 |
| 2 | API uniqueness | Medium | M | 1, 15, 2 |
| 3 | Generative locality | Medium–High | S (B0) / L (B1) | 3, 16, 17, 18 |
| 4 | Authority & honesty | Medium | M | 5, 9, 10, 13, 14 |
| 5 | Structural refactors | Medium | L | 3, 4, 11, 17 |
| 6 | Polish & SDK | Low–Med | M | 8, 12, 16, 18 |
| 7 | CI & packaging UX | Low–Med | M | 17, 19 |
| 8 | Release authority | High process | L | 17, release |

\*S = small (1 PR), M = medium (2–4 PRs), L = large (multi-PR).

---

## 6. Phase 1 — Hygiene & orphans

**Goal:** Zero (or decision-scoped) orphan pyc; suite runner fixed; retirement map updated; no behavior change to live path.

**Depends on:** P0 for G-MCP-CONN (jira/sf); G-GEN only if Phase 1 would touch local_model — **default: leave local_model cluster for P3**.

### PR-P1-01 — Orphan pyc purge (safe clusters)

| Field | Content |
|---|---|
| **Title** | purge: remove retired orphan bytecode (security, models, routes, axes, personas, sdk providers) |
| **Findings** | F-004, F-010, F-014, F-018, F-020, F-034 |
| **Recs** | R2-1, R6-1, R7-1, R8-1, R9-2, R11-2, R12-1, R18-1, R20-1 |
| **Scope** | Delete pyc without sibling `.py` in clusters: security multi-user, storage routes, backend/models split, axes old names, persona engines, mcp jira/sf (if G-MCP-CONN=delete), simulation residue, truth_core orphans, SDK providers/handlers, misc backend dead modules |
| **Out of scope** | The removed historical local-model acceleration tree and gateway tier pyc (`complexity_classifier`, `escalation_config`, `tier_availability`) unless G-GEN=B0 already and owner wants them in this PR |
| **Touches** | `__pycache__` dirs only + empty package dirs; `config/legacy-retirement.json` |
| **Tests** | `tests/security/test_security_module_wiring.py`; import smoke; optional new scan |
| **AC** | No production imports of deleted names; suite green for security wiring; retirement JSON lists major clusters |

### PR-P1-02 — Orphan scan tooling + test guard

| Field | Content |
|---|---|
| **Title** | test: add orphan pyc scanner and unit guard |
| **Findings** | F-034, §18 |
| **Recs** | R19-5, R20-3 |
| **New files** | `scripts/scan_orphan_pyc.py`, `tests/unit/test_no_orphan_pyc.py` |
| **AC** | Scanner exits non-zero on orphans (allowlist empty or documented); test fails if new orphans appear under `backend/`, `core/`, SDK |

### PR-P1-03 — Fix phased test runner

| Field | Content |
|---|---|
| **Title** | fix: run_test_suite Phase 4 invalid tests/resilience path |
| **Findings** | F-026 |
| **Recs** | R19-1 |
| **Touches** | `run_test_suite.py` — remove missing path or add stub package with one skip test + README why |
| **AC** | `python run_test_suite.py` does not fail on missing directory before tests run |

### PR-P1-04 — Product version / health authority (small)

| Field | Content |
|---|---|
| **Title** | fix: health and runtime version from product-versions.json |
| **Findings** | F-012, F-032 |
| **Recs** | R1-3, R15-8 |
| **Touches** | `backend/routes/api_routes.py`, `backend/product_version.py`, any stale `backend/config.py` version string |
| **AC** | `/api/v1/health` (or documented health) reports product version **4.3.0** (or current product-versions) |

### Phase 1 exit checklist

- [x] PR-P1-01 merged (workshop)
- [x] PR-P1-02 merged (workshop)
- [x] PR-P1-03 merged (workshop)
- [x] PR-P1-04 merged (workshop)
- [x] Orphan scan clean for purged clusters
- [x] Single-path + security wiring tests green

**Sections progress:** 20↑, 19↑, 2↑, 6↑, 18↑
**Status:** complete 2026-08-12

---

## 7. Phase 2 — API surface uniqueness

**Goal:** No route shadowing; clear admin namespaces; legacy prefixes controlled; GraphQL hardened.

**Depends on:** Phase 1 (cleaner tree); G-API, G-GQL.

### PR-P2-01 — Single compliance blueprint owner

| Field | Content |
|---|---|
| **Title** | fix: resolve dual /api/v1/compliance registration |
| **Findings** | F-001 |
| **Recs** | R15-1 |
| **Touches** | `app.py`, `backend/regulatory_api.py`, `backend/routes/compliance_routes.py` |
| **Approach** | Pick one owner; re-prefix or merge the other (`/api/v1/regulatory/*` vs `/api/v1/compliance/*`); update frontend if any |
| **New/tests** | Route uniqueness assertion for compliance paths |
| **AC** | Flask map has unique endpoints; integration compliance tests pass |

### PR-P2-02 — Namespace admin surfaces

| Field | Content |
|---|---|
| **Title** | fix: separate ops admin vs gateway admin routes |
| **Findings** | F-003 |
| **Recs** | R3-5, R15-3 |
| **Touches** | `backend/routes/admin_routes.py`, `backend/llm_gateway/api.py`, `frontend/lib/api/gateway.ts`, any admin callers |
| **Approach** | e.g. ops remain `/api/v1/admin/*` (cache/health); gateway moves to `/api/v1/admin/gateway/*` **or** document exclusive path partition + uniqueness test |
| **AC** | No path collisions; frontend gateway admin calls updated; gateway admin tests green |

### PR-P2-03 — Legacy API prefix flag

| Field | Content |
|---|---|
| **Title** | feat: gate legacy /api/* blueprint mirrors behind flag (default off) |
| **Findings** | F-002 |
| **Recs** | R15-2 |
| **Depends** | G-API |
| **Touches** | `app.py`, `backend/routes/__init__.py`, env example docs |
| **AC** | Default desktop/prod: only `/api/v1` (plus intentional OpenAI `/v1`); legacy on only when `DLE_LEGACY_API_PREFIXES=1`; contract tests use v1 |

### PR-P2-04 — GraphQL / Swagger / unregistered APIs

| Field | Content |
|---|---|
| **Title** | fix: GraphQL GraphiQL policy; swagger asset or remove; dispose dead API modules |
| **Findings** | F-007, F-009, F-011 |
| **Recs** | R15-4, R15-5, R15-6 |
| **Depends** | G-GQL |
| **Touches** | `graphql_schema.py`, swagger registration, `security_api.py`/`time_api.py` disposition, `docs/openapi.yaml` version stamp |
| **AC** | GraphiQL off when not dev; OpenAPI version aligned with product; dead modules archived or registered intentionally |

### PR-P2-05 — Route uniqueness CI script

| Field | Content |
|---|---|
| **Title** | test: route uniqueness verifier in CI/contract |
| **Findings** | F-001..F-003 |
| **Recs** | R15-7, R19-6 |
| **New files** | `scripts/verify_route_uniqueness.py`, contract test wrapper |
| **AC** | Script fails on duplicate rule+methods; wired in CI or contract suite |

### PR-P2-06 — Single app factory default path

| Field | Content |
|---|---|
| **Title** | refactor: deprecate legacy create_legacy_app on default boot |
| **Findings** | F-008 |
| **Recs** | R1-1, R1-2, R1-5 |
| **Touches** | `main.py`, `wsgi.py`, `backend/__init__.py`, `app.py` (Replit) |
| **AC** | Default entry only `create_app`; legacy requires explicit env; Replit off for desktop product |

### Phase 2 exit checklist

**Status:** complete 2026-08-12 (G-API hard-off default live).

- [x] All PR-P2-0x merged (P2-06 can trail slightly)
- [x] Route uniqueness green
- [x] OpenAPI/gateway contract green
- [x] No dual compliance/admin collisions

**Sections progress:** 15→~10, 1↑

---

## 8. Phase 3 — Generative locality

**Goal:** Execute **G-GEN** completely (no hollow half-state).

**Depends on:** P0 G-GEN; Phase 1 preferably done.

### Track B0 (default) — cloud BYOK only

#### PR-P3-B0-01 — Remove local model residue

| Field | Content |
|---|---|
| **Title** | chore: remove local_model_acceleration and unused tier pyc (cloud-BYOK generative) |
| **Findings** | F-005 |
| **Recs** | R3-1, R3-2, R20-1 (B0) |
| **Touches** | delete hollow package/pyc; gateway tier orphans; `legacy-retirement.json`; capabilities message |
| **AC** | Orphan scan clean for this cluster; capabilities advertise cloud_byok; Electron stub consistent |

#### PR-P3-B0-02 — Honesty in UI/capabilities

| Field | Content |
|---|---|
| **Title** | docs/ui: generative locality cloud_byok explicit in capabilities and settings |
| **Recs** | R3-6, R16-5 |
| **Touches** | gateway capabilities, CloudDisclosureBanner, AiModelSettings if needed |
| **AC** | Operator cannot believe Ollama is live when it is not |

### Track B1 — restore local generative

#### PR-P3-B1-01 — Restore server-side local model package

| Field | Content |
|---|---|
| **Title** | feat: restore local_model_acceleration from worktree (server-owned) |
| **Source** | `.claude/worktrees/stupefied-ramanujan-516b57/backend/local_model_acceleration/` (+ tests) |
| **Recs** | R3-1, R3-3 |
| **AC** | Source on main; unit tests; no SDK provider brain |

#### PR-P3-B1-02 — Wire into gateway / virtual models / Electron

| Field | Content |
|---|---|
| **Title** | feat: local generative path in gateway + truthful desktop status |
| **Touches** | gateway providers/active_model, virtual models, Electron local-model-status, preload |
| **AC** | End-to-end local answer on configured machine; status IPC truthful; governed path preserved |

#### PR-P3-B1-03 — Contract & docs

| Field | Content |
|---|---|
| **Title** | docs/contract: generative_locality hybrid/local in OpenAPI and product docs |
| **AC** | Claims match code |

### Phase 3 exit checklist

**Status:** complete 2026-08-12 — **B0** track only.

- [x] Exactly one track complete (B0 **or** B1)
- [x] No pyc-only local model half-state
- [x] Single-path tests green

**Sections progress:** 3↑, 17↑, 16↑

---

## 9. Phase 4 — Authority planes & product honesty

**Goal:** One memory authority story; desktop storage purity; Truth/training naming honest; light trace polish.

**Depends on:** Phase 2 preferred; Phase 3 done for locality claims.

### PR-P4-01 — Memory authority

| Field | Content |
|---|---|
| **Title** | feat: memory authority module + align memory routes/settings |
| **Findings** | F-013 |
| **Recs** | R10-1..R10-5 |
| **New files** | `backend/memory/authority.py`, `docs/MEMORY_AUTHORITY.md` |
| **Touches** | `memory_routes.py`, UnifiedMemoryService, settings MemoryManagement, optional truth memory proxy |
| **AC** | Documented single operator write path; tests for review/export/compact; settings match API |

### PR-P4-02 — Desktop storage purity (Pinecone / cloud vector)

| Field | Content |
|---|---|
| **Title** | fix: disable non-desktop vector backends on desktop profile |
| **Findings** | F-033 |
| **Recs** | R9-1, R9-3, R9-4 |
| **Touches** | `vector_store.py`, storage health, profile tests |
| **AC** | Desktop/qualification profile cannot init Pinecone path; health lists components |

### PR-P4-03 — Truth naming & boundary

| Field | Content |
|---|---|
| **Title** | docs/ui: DMRF vs Truth boundary; retire experimental dead adapters |
| **Findings** | F-017 |
| **Recs** | R5-1..R5-5 |
| **New files** | `docs/DMRF_TRUTH_BOUNDARY.md` (or ADR) |
| **Touches** | truth-engine page copy, unused truth adapters quarantine |
| **AC** | UI does not claim private AGI workflow; single-path tests still pass |

### PR-P4-04 — Training / dataset honesty

| Field | Content |
|---|---|
| **Title** | fix: dataset export product naming and DPO fail-closed OpenAPI |
| **Findings** | F-016 |
| **Recs** | R13-1..R13-3, R13-5 |
| **Depends** | G-TRAIN=export-only (default) |
| **New files** | `docs/DATASET_EXPORT_HANDOFF.md` |
| **Touches** | DatasetExporterSettings, dataset_routes, openapi tags/descriptions |
| **AC** | No “train in app” copy; export path documented |

### PR-P4-05 — Auth surface matrix (doc + tests)

| Field | Content |
|---|---|
| **Title** | docs/test: auth surface matrix for session/desktop/client-key |
| **Recs** | R2-3, R2-4 |
| **New files** | `docs/AUTH_SURFACE_MATRIX.md` |
| **AC** | Matrix matches decorators; wiring tests extended if needed |

### PR-P4-06 — Trace export UX / feed consistency (optional mid-size)

| Field | Content |
|---|---|
| **Title** | feat: unify trace live feeds + export verify affordance in runs UI |
| **Recs** | R14-1, R14-2 |
| **Touches** | `tracing/api.py`, `frontend/app/runs/*` |
| **AC** | Export download + integrity metadata visible; feeds consistent |

### Phase 4 exit checklist

**Status:** complete 2026-08-12 (includes G-DSQP 7-part freeze).

- [x] Memory authority landed
- [x] Desktop vector purity landed
- [x] Truth + training honesty landed
- [x] Auth matrix doc exists

**Sections progress:** 10↑, 9↑, 5↑, 13↑, 2↑, 14↑

---

## 10. Phase 5 — Structural refactors (behavior-preserving)

**Goal:** Decompose god files without changing external contracts.

**Depends on:** Phases 1–2 (stable routes); Phase 3 done so provider surface stable.

### PR-P5-01 — Split LLM gateway API package

| Field | Content |
|---|---|
| **Title** | refactor: split backend/llm_gateway/api.py into api package |
| **Findings** | F-015 |
| **Recs** | R3-4 |
| **Approach** | Move routes to `chat.py`, `runs.py`, `admin_*.py`, `openai_compat.py`; `register_gateway_routes` unchanged externally |
| **AC** | Same URL rules; gateway tests green; file sizes reviewable (~≤400 LOC target) |

### PR-P5-02 — Governed execution stages extraction

| Field | Content |
|---|---|
| **Title** | refactor: extract orchestrator stages + layer_contracts |
| **Recs** | R4-1, R4-2, R4-4 |
| **New files** | `backend/governed_execution/stages/*.py`, `layer_contracts.py` |
| **AC** | Fixture/comparison tests for governed path; single-path green; no API change |

### PR-P5-03 — Split MCP routes package

| Field | Content |
|---|---|
| **Title** | refactor: split mcp_routes.py into package |
| **Recs** | R11-1, R11-3 |
| **AC** | Same routes; phase11 MCP tests green |

### PR-P5-04 — Split Electron main process

| Field | Content |
|---|---|
| **Title** | refactor: split frontend/electron/main.ts into modules |
| **Recs** | R17-1 |
| **New files** | `frontend/electron/main/{secrets,backend,ipc,protocol,updater,window}.ts` (names flexible) |
| **AC** | electron unit tests green; desktop smoke; no auth regression |

### PR-P5-05 — Startup contract module

| Field | Content |
|---|---|
| **Title** | refactor: extract startup_contract from app/runtime boot |
| **Recs** | R1-4 |
| **New files** | `backend/runtime/startup_contract.py` |
| **AC** | Desktop/prod startup order testable; precheck still passes |

### Phase 5 exit checklist

**Status:** **partial/deferred** — targeted contracts and Electron helpers
landed, but the full gateway/api/mcp package splits were **reverted** after
mock.patch breakage (see `PHASE5_GODFILE_SPLIT_NOTES.md`). The phase is not
complete against its original decomposition goal.

- [x] Targeted structural helpers landed (startup/layer contracts, Electron paths)
- [ ] Four major package splits — deferred/restored; monolithes retained
- [x] No intentional unversioned API contract breaks
- [x] Full relevant test slices green after restore

**Sections progress:** 3↑, 4↑, 11↑, 17↑, 1↑

---

## 11. Phase 6 — Product polish & SDK

**Goal:** Control-center framing; SDK publishable; sim/KA polish.

**Depends on:** Phase 3 (locality messaging); Phase 2 (API stable).

### PR-P6-01 — Frontend control-center copy & deps

| Field | Content |
|---|---|
| **Title** | ui: control-center-first home/sidebar; fix dependency classification |
| **Findings** | F-022, F-023 |
| **Recs** | R16-1..R16-4 |
| **Touches** | `app/page.tsx`, `AppSidebar.tsx`, `package.json` |
| **AC** | Chat framed as probe; npm story documented or deps fixed; vitest green |

### PR-P6-02 — SDK publish hygiene

| Field | Content |
|---|---|
| **Title** | release: rebuild ukg-sdk 0.7.0 artifacts; license notice; drop stale 0.3.1 |
| **Findings** | F-020, F-021 |
| **Recs** | R18-2..R18-5 |
| **New files** | `sdk/LICENSE_NOTICE.md` |
| **AC** | Only 0.7.0 artifacts; SDK tests green; no provider packages |

### PR-P6-03 — KA manifest parity (server ↔ clients)

| Field | Content |
|---|---|
| **Title** | feat: manifest version/hash endpoint + client check |
| **Recs** | R8-2, R8-3 |
| **Touches** | ka routes, TS SDK generate-or-hash, algorithms page |
| **AC** | Mismatch detectable; optional CI check |

### PR-P6-04 — Simulation isolation UI + invariant test

| Field | Content |
|---|---|
| **Title** | test/ui: simulation budgets visible; chat isolation hard test |
| **Recs** | R12-2, R12-3 |
| **AC** | Chat cannot use simulation provider; UI shows budgets |

### PR-P4-DSQP — Expand DSQP to 7-part persona (REQUIRED — G-DSQP locked)

| Field | Content |
|---|---|
| **Title** | feat: DSQP 7-part persona contract (Traits + Related Roles + existing five) |
| **Findings** | F-014; owner gate G-DSQP |
| **Recs** | R7-2, R7-3; prior work-queue D-1 |
| **Depends** | G-DSQP = **7-part** (locked). Prefer after Phase 1 hygiene; can run parallel to mid Phase 4. |
| **Touches** | `backend/dsqp/dsqp_chain.py`, `dsqp_orchestrator.py`, persona construction / ten_layers L4–L5 as needed, KA consumers of DSQP profile, tests under `tests/` DSQP/persona, in-repo disclosure/docs that state component count |
| **Out of scope** | Restoring orphan `core/persona` pyc engines; changing gateway single-path |
| **AC** | Live profile always exposes **7** named components; unit/integration tests assert count and required keys; governed path still single; docs/IP crosswalk in-repo match 7-part; no second persona engine on live path |

### PR-P6-05 — DSQP single authority freeze (after 7-part landed)

| Field | Content |
|---|---|
| **Title** | chore: retire non-DSQP persona engines; freeze component count test at 7 |
| **Findings** | F-014 |
| **Recs** | R7-2, R7-3 |
| **Depends** | **PR-P4-DSQP** merged; G-DSQP = 7-part |
| **AC** | One construction path; tests assert **exactly 7** components; legacy engines retired in `legacy-retirement.json` |

### Phase 6 exit checklist

**Status:** implemented 2026-08-12; post-QC qualification passed 2026-08-15.

- [x] Frontend identity / honesty copy landed
- [x] SDK 0.7.0 clean
- [x] KA server/TypeScript/Python manifest parity check exists
- [x] Simulation isolation / bounds note proven

**Sections progress:** 16↑, 18↑, 8↑, 12↑, 7↑

---

## 12. Phase 7 — CI, packaging UX, quality gates

**Goal:** CI matches quality bar; desktop first-run less brutal; optional CSP note.

**Depends on:** Phase 5 electron split helpful but not required for all tickets.

### PR-P7-01 — CI coverage / a11y policy

| Field | Content |
|---|---|
| **Title** | ci: document or enforce coverage; a11y gate policy |
| **Findings** | F-025, F-027 |
| **Recs** | R19-2, R19-3 |
| **Touches** | `.github/workflows/ci.yml`, testing docs |
| **AC** | Policy explicit; if fail_under set, threshold realistic and green |

### PR-P7-02 — Podman first-run UX

| Field | Content |
|---|---|
| **Title** | ux: actionable first-run when Podman machine missing |
| **Findings** | F-029 |
| **Recs** | R17-2 |
| **Touches** | Electron main/backend bootstrap; optional UI message |
| **AC** | User sees recovery steps; not only opaque quit (or documented intentional fail-closed with link) |

### PR-P7-03 — CSP residual risk note + optional tighten

| Field | Content |
|---|---|
| **Title** | security: CSP documentation and best-effort tighten |
| **Findings** | F-030 |
| **Recs** | R17-3 |
| **AC** | Residual risk written; no app break |

### PR-P7-04 — Wire orphan scan into CI (optional job)

| Field | Content |
|---|---|
| **Title** | ci: orphan pyc scan job |
| **Recs** | R20-3 |
| **AC** | Main branch cannot reintroduce orphans silently |

### PR-P7-05 — Packaging smoke assertions

| Field | Content |
|---|---|
| **Title** | ci: packaging smoke asserts backend + policies + release JSON |
| **Recs** | R17-6 |
| **AC** | windows-packaging-smoke checks required resources exist |

### Phase 7 exit checklist

**Status:** implemented 2026-08-12; post-QC qualification passed 2026-08-15.

- [x] CI policy clear (`docs/CI_QUALITY_POLICY.md`)
- [x] First-run UX improved (Podman recovery messaging)
- [x] Orphan CI guard on
- [x] Packaging smoke stronger (resource verify)

**Sections progress:** 19→~10, 17↑, 20→10

---

## 13. Phase 8 — Release authority (owner-led, optional)

**Goal:** Real production candidate when **and only when** evidence exists.

**Do not start** to “get a higher audit score.” Start when owner intends distribution.

| Ticket | Title | Notes |
|---|---|---|
| **T-8.1** | Production codesign identity + hardware/managed signing | Outside pure app code |
| **T-8.2** | Fill `release-trust-policy.json` gates only with proof | Never flip true without evidence |
| **T-8.3** | Signed installer + sha + signature report | `reports/installer_signature_report.json` |
| **T-8.4** | Update feed URL + staged rollout plan | Auto-update enable path |
| **T-8.5** | Update `RELEASE_READINESS_RECORD.md` go/no-go | Owner approves |
| **T-8.6** | Accessibility hard-gate if claiming a11y | Ties P7 |

**Phase 8 exit:** Signed artifact + readiness record **GO** only if all gates true.

---

## 14. Master PR / ticket index

| ID | Phase | Title (short) | Priority | Depends |
|---|---:|---|---|---|
| T-0.1 | 0 | Record owner gates | P0 | — |
| PR-P1-01 | 1 | Orphan pyc purge (safe) | P0 | T-0.1 (MCP) |
| PR-P1-02 | 1 | Orphan scanner + test | P0 | PR-P1-01 |
| PR-P1-03 | 1 | Fix run_test_suite path | P0 | — |
| PR-P1-04 | 1 | Health/product version | P1 | — |
| PR-P2-01 | 2 | Compliance single owner | P0 | P1 |
| PR-P2-02 | 2 | Admin namespace | P0 | P1 |
| PR-P2-03 | 2 | Legacy prefix flag | P0 | G-API |
| PR-P2-04 | 2 | GraphQL/Swagger/dead APIs | P1 | G-GQL |
| PR-P2-05 | 2 | Route uniqueness script | P0 | P2-01/02 |
| PR-P2-06 | 2 | Single app factory | P1 | — |
| PR-P3-B0-* / B1-* | 3 | Generative locality | P0 | G-GEN, P1 |
| PR-P4-01 | 4 | Memory authority | P0 | — |
| PR-P4-02 | 4 | Storage purity | P0 | — |
| PR-P4-03 | 4 | Truth boundary | P1 | — |
| PR-P4-04 | 4 | Dataset honesty | P1 | G-TRAIN |
| PR-P4-05 | 4 | Auth matrix | P1 | P1 |
| PR-P4-06 | 4 | Trace UX | P2 | — |
| PR-P4-DSQP | 4 | DSQP 7-part persona (REQUIRED) | **P0** | G-DSQP locked |
| PR-P5-01 | 5 | Gateway API split | P1 | P2, P3 |
| PR-P5-02 | 5 | Orchestrator stages | P1 | — |
| PR-P5-03 | 5 | MCP routes split | P1 | P1 |
| PR-P5-04 | 5 | Electron main split | P1 | — |
| PR-P5-05 | 5 | Startup contract | P2 | — |
| PR-P6-01 | 6 | Frontend identity | P1 | P3 |
| PR-P6-02 | 6 | SDK 0.7.0 publish | P1 | P1 |
| PR-P6-03 | 6 | KA manifest parity | P2 | — |
| PR-P6-04 | 6 | Simulation isolation | P1 | — |
| PR-P6-05 | 6 | DSQP freeze | P2 | G-DSQP |
| PR-P7-01 | 7 | CI coverage/a11y | P1 | — |
| PR-P7-02 | 7 | Podman first-run UX | P1 | P5-04 optional |
| PR-P7-03 | 7 | CSP note/tighten | P2 | — |
| PR-P7-04 | 7 | Orphan CI job | P1 | P1-02 |
| PR-P7-05 | 7 | Packaging smoke asserts | P1 | — |
| T-8.* | 8 | Signing / GO | P3 | Owner intent |

---

## 15. Suggested calendar (hobby-realistic)

Not a commitment — ordering only:

| Sprint | Focus | PRs |
|---|---|---|
| Sprint 1 | P0 + P1 | T-0.1, P1-01..04 |
| Sprint 2 | P2 core | P2-01, 02, 05, 03 |
| Sprint 3 | P2 tail + P3 | P2-04, 06, P3-B0 or B1 |
| Sprint 4 | P4 | P4-01..05 |
| Sprint 5–6 | P5 | P5-01..04 |
| Sprint 7 | P6 | P6-01..04 |
| Sprint 8 | P7 | P7-01..05 |
| Later | P8 | Only if shipping |

Parallelization notes:

- P1-03 and P1-04 parallel to P1-01
- P4-02 parallel to P4-01
- P5-03 parallel to P5-01 after P2
- P6-02 can start after P1 SDK purge

---

## 16. Risk register (plan-level)

| Risk | Mitigation |
|---|---|
| Refactor breaks gateway contract | Contract tests first; no intentional breaks in P5 |
| B1 local model half-wired | Forbidden; complete track or stay B0 |
| Legacy clients on `/api/*` | G-API deprecation window only if needed |
| Admin path rename breaks UI | Update `frontend/lib/api/gateway.ts` in same PR as P2-02 |
| Orphan purge deletes “still needed” | Grep importers; worktree recovery; don’t delete live `.py` |
| Phase 8 pressure to fake gates | Keep fail-closed; readiness record NO-GO until real |

---

## 17. Progress tracking template

Copy into HANDOFF or a living `reports/audit-remediation-progress.md`:

```markdown
## Audit remediation progress
- Phase 0: [x] locked 2026-08-12
- Phase 1: [x] P1-01 [x] P1-02 [x] P1-03 [x] P1-04
- Phase 2: [x] P2-01 … P2-06 (route uniqueness + legacy hard-off)
- Phase 3: track B0 [x] complete
- Phase 4: [x] memory/auth/DSQP7/vector purity/honesty
- Phase 5: [x] contracts + electron helpers; full godfile splits deferred
- Phase 6: [x] SDK 0.7.0 + KA manifest integrity
- Phase 7: [x] CI orphan/route + packaging resource verify
- Phase 8: [ ] not started (owner/signing)
```

---

## 18. Codex execution instructions

When asked to implement:

1. Read this plan + findings §9 preserve list + recommendations for the PR.
2. Confirm required gates for that PR.
3. Work **one PR ID** at a time on a branch `codex/p{N}-{slug}`.
4. Implement only that PR’s scope.
5. Run listed AC verification.
6. Summarize: files changed, findings closed, residual risks.
7. Do not start Phase 8 without explicit owner request.
8. Do not widen into unrelated refactors.

### First implementation command (recommended start)

```text
Implement PR-P1-03 and PR-P1-04 (small fixes), then PR-P1-01 orphan purge
per docs/audits/DataLogicEngine_Phased_Implementation_Plan_2026-08-12.md
assuming G-GEN=B0 and G-MCP-CONN=delete unless owner said otherwise.
```

---

## 19. Definition of plan complete (engineering)

Engineering remediation plan is **complete** only after the supplemental QC
plan at
`docs/audits/DataLogicEngine_Grok_QC_Remediation_Plan_2026-08-15.md` passes:

- [ ] Phases 1–7 acceptance criteria met (Phase 5 remains partial/deferred)
- [x] Orphan scan = 0 on workshop tree for purged clusters
- [x] Route uniqueness green
- [x] G-GEN track fully executed (**B0**)
- [ ] Section scores re-reviewable as 9–10 band per recommendations exit criteria
- [x] Release still honest (Phase 8 separate)

---

## 20. Document history

| Version | Date | Notes |
|---|---|---|
| 1.0 | 2026-08-12 | Initial phased PR/ticket plan from findings + recommendations |
| 1.1 | 2026-08-12 | Locked §4.1 owner gates; G-DSQP = 7-part required; added PR-P4-DSQP |
| 1.2 | 2026-08-12 | Phases 1–7 implemented in workshop tree (Phase 8 still owner/signing) |
| 1.3 | 2026-08-12 | Exit checklists marked complete; HANDOFF/TODO/CHANGELOG synced; tests aligned to v1-default |
| 1.4 | 2026-08-15 | QC corrected Phase 5 and overall completion status; linked ordered remediation plan |

---

## 21. Cross-links

| Document | Role |
|---|---|
| Findings | Problem statements + F-IDs + orphan §18 |
| Recommendations | Section 10/10 actions |
| **This plan** | Order, PRs, AC, gates |
| Orphan worksheet | Owner checkboxes for wire/delete |

**End of phased implementation plan.**
