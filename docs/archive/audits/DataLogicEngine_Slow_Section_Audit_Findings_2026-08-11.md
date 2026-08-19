# DataLogicEngine — Slow Section-by-Section Audit Findings

| Field | Value |
|---|---|
| Document ID | DLE-AUDIT-SLOW-2026-08-11 |
| Title | Slow section audit findings (code-validated) |
| Product | DataLogicEngine Desktop |
| Product version observed | 4.3.0 |
| Audit date | 2026-08-11 |
| Methodology | Section-by-section, file/path inventory + critical-path source review |
| Scope | Local repository workshop tree (build machine), not a clean clone-only surface |
| Intent of this document | Input for **Codex** (or human planner) to produce a **phased update/remediation plan** |
| Status | Findings only — **no code changes** were made during this audit |
| Companion authority | `docs/RELEASE_READINESS_RECORD.md` (release_blocked / NO-GO), `README.md`, `config/release-*.json` |
| Recommendations (10/10 actions) | `docs/audits/DataLogicEngine_Slow_Audit_Recommendations_10of10_2026-08-12.md` |
| Phased implementation plan | `docs/audits/DataLogicEngine_Phased_Implementation_Plan_2026-08-12.md` |

---

## 1. Purpose for Codex

Codex: read this document fully before proposing work. Produce a **phased update plan** that:

1. Addresses findings by **severity and coupling**, not by random file order.
2. Does **not** widen scope into product redesign unless a finding requires it.
3. Respects product identity constraints in §2.
4. Distinguishes **ship blockers**, **architecture debt**, **hygiene**, and **optional product goals**.
5. Proposes **verification** (tests / contract / packaging smoke) per phase.
6. Leaves **local gitignored build materials** alone (see §4).
7. Updates docs only when code behavior changes (no new doc drift).

**Do not treat this file as a release authorization.** Production/public release remains **NO-GO** until release authority gates say otherwise.

---

## 2. Product identity (planning constraints)

Any remediation plan must preserve or explicitly renegotiate these product truths:

| Constraint | Meaning |
|---|---|
| Product type | **LLM middleware / overlay**, not primarily a chatbot |
| Frontend | **Control center** for operations setup; chat is a **reference probe** |
| Deployment | Always **one** high-end workstation / rack server / cloud VM (scale-up, not multi-tenant SaaS) |
| Security model | Host secures the machine; app should not add unnecessary external API attack surfaces |
| Core ambition | Local function: **API in (client → DLE) / API out**; no *required* outside APIs for core app function |
| Generative reality (current mainline) | **Cloud BYOK** (OpenAI + Google) on the main generative path; local-model acceleration is **not** first-class on main |
| Auth | Desktop Windows identity + install-secret HMAC loopback; web login/MFA/SSO removed |
| Release posture | `release_blocked` / candidate / unsigned for public distribution |
| Ownership | Self-funded hobby workshop; prioritize correctness and residual cleanup over startup packaging theater |

### Canonical request path (do not regress)

```
Client / Electron / SDK
  → API Gateway surface (/api/v1/gateway, OpenAI-compat /v1, client keys)
  → GovernedExecutionOrchestrator (L1–L10)
  → Provider (BYOK cloud on mainline) + retrieval/memory/trace
  → Response + TraceRun evidence
```

Thin SDKs must remain **transport clients**, not a second KA/DSQP/provider brain.

---

## 3. Methodology

### What was done

1. Slow **20-section** review of the live tree under `C:\software\DataLogicEngine`.
2. Inventory of packages, routes, frontend app surfaces, Electron packaging, SDKs, tests, reports, orphan bytecode, agent worktrees.
3. Read of critical source files (registration, auth, gateway, orchestrator, Electron main, SDK gateway/overlay, release trust policy, CI, etc.).
4. Scores are **engineering judgment from code**, not live re-execution of the full 2k+ test suite in this session.

### What was not done

- Full `pytest` green re-run of the entire suite in this audit session.
- Installer re-sign / production distribution qualification.
- Penetration test or formal threat-model exercise.
- Modification of application code.

### Code vs docs rule

When docs and code disagree, **code is truth**. This audit preferred source and registration paths over marketing language. Release/NO-GO docs were treated as intentional governance, not as proof of subsystem quality.

---

## 4. Non-findings (do not “fix” as product bugs)

| Item | Treatment |
|---|---|
| `API KEY/` folder with live test provider keys | **Local build-machine state**. Gitignored (`API KEY/`). Not a shipping defect. Do not delete as part of “security cleanup” without owner confirmation. |
| `certs/*.pfx` and password files | **Local dev codesign material**. Gitignored (`certs/`). Not a product defect in a workshop tree. |
| Large `dist/`, `frontend/dist*`, installer EXEs, databases, object-store blobs | Expected local build/runtime artifacts. |
| `.claude/worktrees/<agent-worktree>` (historical pattern) | Agent experiment trees; gitignored (`.claude/`). Source of experimental local-model work — not mainline product surface. |
| Release **NO-GO** / unsigned installer | **Intentional governance**, already encoded in `config/release-trust-policy.json`, `config/release-channel.json`, README, release readiness record. Plan may *prepare* gates; do not fake production_authorized. |

---

## 5. Overall scores (slow audit)

### Section scores

| # | Section | Score | Notes |
|---:|---|---:|---|
| 1 | Runtime / entry | 7.5 | Dual app factories; desktop runtime mature |
| 2 | Auth / desktop security | 6.5 | Strong desktop path; legacy residue / complexity |
| 3 | LLM Gateway | 7.0 | Real product boundary; cloud-only mainline |
| 4 | Governed execution L1–L10 | 8.0 | Core spine strength |
| 5 | DMRF / Truth | 6.5 | Integrated but Truth naming overshoots live path |
| 6 | Axes | 7.0 | Live compact vector + full coordinate library |
| 7 | DSQP | 7.5 | Canonical persona path on governed run |
| 8 | Knowledge Algorithms | 8.0 | Manifest + product workflow solid |
| 9 | Storage | 8.0 | Multi-store authority design strong |
| 10 | Ingestion / memory | 7.0 | Real local ingestion; memory systems fragmented |
| 11 | MCP | 7.5 | Policy/consent strong; large surface |
| 12 | Simulation | 7.5 | Bounded, separated from chat path |
| 13 | Training / dataset | 6.5 | Export/admission real; no in-app trainer |
| 14 | Tracing / audit | 8.0 | Trace SoR + signed export posture strong |
| 15 | Routes / API surface | 7.0 | Large dual-prefix surface; OpenAPI subset |
| 16 | Frontend control center | 7.5 | True control center; chat is probe |
| 17 | Electron / packaging | 7.5 | Security-conscious; ship blocked by policy |
| 18 | SDK | 7.5 | Thin-client design good; publish hygiene weaker |
| 19 | Tests / reports | 8.0 | Layered tests + evidence archive |
| 20 | Orphans / worktrees | 6.0 clean / 7.5 process | ~70 orphan pyc modules; formal retirement exists |

**Rough unweighted mean:** ~**7.2 / 10** as an engineering system in a local workshop repo.

### Verdict summary

| Lens | Score / posture |
|---|---|
| Craft / subsystem depth | **High** for solo AI-aided hobby |
| Architecture integrity (core path) | **Strong** with dual-path debt |
| Commercial / public ship readiness | **Blocked** (correctly) |
| Local data plane / control plane | **Strong** |
| Fully local generative (no outside API) | **Incomplete** on mainline |
| Verification culture | **Strong** |

**One-line product judgment:**
DataLogicEngine is a serious single-node governed LLM middleware + control center with desktop trust and evidence culture; not a toy; not yet a signed production release; generative airgap is incomplete on mainline.

---

## 6. Architecture snapshot (for plan authors)

### Runtime topology

- **Electron** spawns frozen `DataLogic_Backend.exe` (prod) or `python main.py` (dev).
- Backend: Flask app via `app.py` `create_app` (canonical) and legacy `backend/__init__.py` path still present.
- Data plane: app-owned stores (Postgres/SQLite desktop, Redis, Neo4j, Chroma, object store via Podman profile in packaged path).
- Generative providers on mainline: **OpenAI + Google BYOK only**.
- Virtual models: `dle-standard` (1 call), `dle-enhanced` (≤2), `dle-local-review` (0 provider calls).

### Major subsystems (all real in code)

- Governed execution L1–L10 + refinement workflow
- DMRF tier/axis routing
- DSQP personas (canonical under `backend/dsqp`)
- KA catalog/manifest + product plan/execute workflow
- Trace graph SoR + export integrity
- Local ingestion pipeline
- MCP connector policy surface
- Bounded simulation (refused on chat path)
- Dataset export / training admission (not full trainer)
- Thin Python (`ukg-sdk` 0.7.0 source) + TypeScript (`@datalogicengine/sdk` 0.1.0) clients

---

## 7. Finding registry

Severity legend:

| Severity | Meaning for planning |
|---|---|
| **S0** | Safety/integrity risk or high chance of wrong production behavior |
| **S1** | Ship/trust correctness, attack surface, or dual-path hazard |
| **S2** | Significant debt that confuses operators, audits, or future edits |
| **S3** | Hygiene, naming, polish, optional product goals |

Status: **Open** unless noted.

### 7.1 S0 / S1 — must address early in any remediation plan

#### F-001 — Dual compliance blueprints on same prefix family

| Field | Value |
|---|---|
| Severity | **S1** |
| Sections | 15 |
| Summary | `backend/regulatory_api.py` and `backend/routes/compliance_routes.py` both register under `/api/v1/compliance` (plus legacy names). Endpoint shadowing / ambiguous ownership risk. |
| Evidence | `app.py` `_register_application_routes`; `backend/routes/compliance_routes.py` `url_prefix='/api/v1/compliance'`; regulatory registration with same prefix family |
| Risk | Wrong handler wins; intermittent test/prod mismatch; security review confusion |
| Suggested direction | Single owner blueprint; other renamed/retired; contract tests for route uniqueness |
| Verify | Route inventory test; hit each documented compliance path; `tests/integration_routes/*` |

#### F-002 — Widespread legacy dual API prefixes

| Field | Value |
|---|---|
| Severity | **S1** |
| Sections | 15, 1 |
| Summary | Many blueprints register both `/api/v1/...` and legacy `/api/...` (truth, persona, pillar, ukg, ka, mcp, simulation, etc.). |
| Evidence | `app.py`, `backend/routes/__init__.py` dual `register_blueprint` calls |
| Risk | Doubled attack surface; docs/OpenAPI lag; clients pin unstable paths |
| Suggested direction | Compatibility flag default-off for new installs; deprecation window; OpenAPI only v1 |
| Verify | Contract tests; grep for dual registration; client SDK only uses v1 |

#### F-003 — Dual admin blueprints sharing `/api/v1/admin`

| Field | Value |
|---|---|
| Severity | **S1** |
| Sections | 15, 3 |
| Summary | `routes/admin_routes.py` (`admin_api`) and gateway `admin_bp` (`gateway_admin`) both use `url_prefix='/api/v1/admin'`. Works if paths never collide; fragile ownership. |
| Evidence | `backend/routes/admin_routes.py`; `backend/llm_gateway/api.py` `register_gateway_routes` |
| Risk | Future route collision; unclear authz ownership |
| Suggested direction | Namespace (`/admin/ops/*` vs `/admin/gateway/*`) or single admin package |
| Verify | Full `/api/v1/admin` route dump uniqueness test |

#### F-004 — Orphan bytecode for deleted security / multi-tenant stacks

| Field | Value |
|---|---|
| Severity | **S1** (hygiene with security confusion) |
| Sections | 2, 20 |
| Summary | ~70 orphan `.pyc` modules without `.py` under `backend/` + `core/`, including MFA, RBAC, honeypot, zero_trust, tenant_rls, defense_supervisor, etc. |
| Evidence | Historical `backend/security/__pycache__/` orphan cluster; scan listed in §8 |
| Risk | False confidence that features exist; accidental import of stale pyc; audit noise |
| Suggested direction | Purge orphan pyc; optional quarantine list in `legacy-retirement.json`; never reintroduce multi-tenant SaaS auth without explicit product decision |
| Verify | Script: every `.pyc` has matching `.py`; CI hygiene check optional |

#### F-005 — Local model acceleration hollow on mainline (pyc-only)

| Field | Value |
|---|---|
| Severity | **S1** if product claims airgap generative; **S2** if cloud-BYOK is accepted |
| Sections | 3, 17, 18, 20 |
| Summary | `backend/local_model_acceleration/` is **bytecode only** on main. Electron `local-model-status` hard-stubs `ollama_available: false` (“cloud-only product”). Full sources exist in gitignored worktree `.claude/worktrees/stupefied-ramanujan-516b57/...`. |
| Evidence | Orphan pyc list; `frontend/electron/main.ts` local-model-status handler; worktree path |
| Risk | Product messaging vs reality; half-restored imports; confused remediation |
| Suggested direction | **Decision gate first:** (A) accept cloud-BYOK generative + purge residue, or (B) restore first-class local generative from worktree with tests and Electron integration |
| Verify | If B: provider path tests, Electron status truth, no dual stack in SDK |

#### F-006 — Release trust gates correctly fail-closed (not a bug — planning input)

| Field | Value |
|---|---|
| Severity | **S1 ship gate** (do not weaken) |
| Sections | 17 |
| Summary | `config/release-trust-policy.json` has `production_authorized: false` and all update qualification gates false. Auto-update disabled unless policy allows + env flags. |
| Evidence | `config/release-trust-policy.json`; `frontend/electron/update-trust.ts`; `configureAutoUpdater` in `main.ts` |
| Risk | If someone flips gates without real signing/process, ship integrity fails |
| Suggested direction | Keep fail-closed. Separate phase for real signing, timestamping, publisher subjects, offline update story |
| Verify | Unit tests already on `update-trust`; packaging signature report remains honest |

#### F-007 — GraphQL GraphiQL enabled at registration

| Field | Value |
|---|---|
| Severity | **S1** in production profile |
| Sections | 15 |
| Summary | GraphQL registered with GraphiQL enabled (per app registration path). |
| Evidence | `app.py` / `backend/graphql_schema.py` registration logs and routes |
| Risk | Extra introspective surface on desktop loopback if not tightly auth-bound |
| Suggested direction | Disable GraphiQL outside dev; confirm auth on all mutations; or feature-flag GraphQL entirely for desktop product |
| Verify | Integration tests for unauth GraphQL; production config assertion |

### 7.2 S2 — architecture / product debt

#### F-008 — Dual application factories

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 1 |
| Summary | Canonical `create_app` vs legacy `create_legacy_app` / `backend/__init__.py` register different blueprint sets (e.g. `rest_api` on legacy). |
| Evidence | `app.py`, `backend/__init__.py` |
| Risk | Tests or scripts boot wrong surface |
| Suggested direction | Single entry; legacy behind explicit env or delete after inventory |
| Verify | Startup matrix test: only one factory in production desktop path |

#### F-009 — Unregistered API modules still in tree

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 15, 20 |
| Summary | `security_api.py`, `time_api.py` have routes but are not registered in canonical `app.py`; mounted in tests only. |
| Evidence | Grep registration in `app.py` (absent); `tests/integration_routes/test_uncovered_blueprints.py` |
| Risk | Dead code rot; false docs |
| Suggested direction | Register intentionally or move to archive/tests fixtures |
| Verify | Import graph / blueprint inventory script |

#### F-010 — Orphan storage route modules (pyc)

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 15, 20 |
| Summary | `storage_download_routes`, `storage_management_routes`, `storage_upload_routes` pyc without `.py`; live code is consolidated `storage_routes.py`. |
| Evidence | `backend/routes/__pycache__` |
| Suggested direction | Delete orphan pyc; confirm no imports |
| Verify | Import check + storage route tests |

#### F-011 — OpenAPI / Swagger drift

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 15 |
| Summary | `docs/openapi.yaml` stamped **3.5.2** while product is **4.3.0**. Documents ~67 paths vs ~300+ route decorators in app. Swagger UI points at `/static/swagger.json` which was not found as a main-tree static asset (only worktree copies observed). |
| Evidence | `docs/openapi.yaml`; `app.py` swagger registration |
| Risk | Integrators misled; dead `/api/docs` |
| Suggested direction | Version stamp alignment; keep OpenAPI as intentional **subset** (document that); ship real swagger artifact or remove UI registration |
| Verify | Contract tests already compare gateway baseline; extend inventory note |

#### F-012 — Health endpoint version hardcode

| Field | Value |
|---|---|
| Severity | **S3** (listed near API hygiene) |
| Sections | 15 |
| Summary | `api_routes` health returns `"version": "1.0.0"`. |
| Evidence | `backend/routes/api_routes.py` |
| Suggested direction | Use `product_version` / `config/product-versions.json` |
| Verify | Health contract test |

#### F-013 — Memory system fragmentation

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 10, 5, 14 |
| Summary | Multiple memory concepts: UnifiedMemoryService, TruthMemory, governed lifecycle/knowledge stores, graph memory. Hard to reason about “the” memory SoR. |
| Evidence | `backend/memory/`, truth_engine memory modules, governed_execution knowledge lifecycle |
| Risk | Double-write, incomplete recall, operator confusion |
| Suggested direction | Authority matrix doc + code comments; one write path for operator-visible memory |
| Verify | Memory route tests + trace memory projection tests |

#### F-014 — Dual persona / quad engines (non-live residue)

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 7, 20 |
| Summary | Canonical DSQP under `backend/dsqp`; additional `backend/quad_persona`, `core/persona/quad`, orphan persona pyc. |
| Evidence | Package trees + orphan scan |
| Suggested direction | Mark non-live as retired in `legacy-retirement.json`; remove dead imports |
| Verify | Governed path only imports DSQP; unit tests |

#### F-015 — God files

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 3, 4, 11, 15, 17 |
| Summary | Very large modules: `backend/llm_gateway/api.py`, `governed_execution/orchestrator.py`, `routes/mcp_routes.py`, `frontend/electron/main.ts` (~1.8k lines), `app.py`. |
| Risk | High merge conflict / review cost; accidental regressions |
| Suggested direction | Decompose after dual-path cleanup, not before (reduce moving targets) |
| Verify | Existing tests green per split PR |

#### F-016 — Training oversell risk

| Field | Value |
|---|---|
| Severity | **S2** (product honesty) |
| Sections | 13, 16 |
| Summary | Dataset export SFT/PRM from released TraceRuns is real; DPO blocked without rejects; **no in-app trainer**. UI exposes exporter under Settings. |
| Evidence | `backend/dataset_exporter/*`, `dataset_routes.py`, settings `DatasetExporterSettings` |
| Suggested direction | Keep naming as “dataset preparation / export”; never “train model in app” without trainer |
| Verify | Dataset route fail-closed tests; UI copy review |

#### F-017 — Truth Engine naming vs live path

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 5, 16 |
| Summary | Truth library language (AGI/quantum-ish) exceeds live behavior: L1/truth integration + gate + frontend telemetry over traces. Public TruthCore process routes through gateway (guarded by tests). |
| Evidence | `backend/truth_engine/*`, `tests/governed_execution/test_single_path.py`, `frontend/app/truth-engine/page.tsx` |
| Suggested direction | Soften user-facing claims; keep gateway single-path invariant |
| Verify | Keep single-path tests; UI copy audit |

#### F-018 — MCP surface size + orphan connectors

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 11, 20 |
| Summary | `mcp_routes.py` ~28 routes / ~70KB. Orphan jira/salesforce tool pyc. Production connectors need qualification flags. |
| Evidence | `backend/routes/mcp_routes.py`; mcp tools pyc |
| Suggested direction | Purge orphan connectors; keep consent/policy fail-closed |
| Verify | MCP phase11 tests |

#### F-019 — Simulation vs chat path discipline (preserve)

| Field | Value |
|---|---|
| Severity | **S2 preserve** |
| Sections | 12 |
| Summary | Simulation is bounded and refused on main chat path — good. Do not merge simulation provider into chat without budgets. |
| Evidence | Simulation contracts / gateway refusal patterns (prior sections) |
| Suggested direction | Keep separation; document in plan as invariant |
| Verify | Existing simulation + gateway tests |

#### F-020 — Stale SDK publish artifacts

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 18 |
| Summary | Python source/version is **0.7.0** but `sdk/UKG_Python_SDK/dist/` still has **0.3.1** wheel/sdist. Provider package is pyc-only (client-side providers removed). |
| Evidence | `pyproject.toml` version 0.7.0; dist filenames 0.3.1; `ukg_sdk/providers/__pycache__` only |
| Risk | Someone installs wrong wheel from tree |
| Suggested direction | Rebuild 0.7.0 artifacts or delete stale dist; purge provider pyc; document MIT SDK vs PolyForm app if intentional |
| Verify | SDK tests; version banner User-Agent |

#### F-021 — TypeScript SDK embeds huge KA manifest

| Field | Value |
|---|---|
| Severity | **S3** (perf/package size) / S2 if stale vs server |
| Sections | 18 |
| Summary | `ka-manifest.generated.ts` ~746KB inlined in package. |
| Suggested direction | Generate at build from server manifest; version pin check |
| Verify | Manifest hash parity test server vs SDK |

#### F-022 — Frontend dependency classification

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 16, 17 |
| Summary | Almost all Next/React deps under `devDependencies`; only `electron-updater` in `dependencies`. Works for electron-builder scripts; fragile for other install modes. |
| Evidence | `frontend/package.json` |
| Suggested direction | Reclassify runtime deps for the intended install path; document electron-only assumption |
| Verify | `npm ci` + electron:dist CI job |

#### F-023 — UI product-copy lag

| Field | Value |
|---|---|
| Severity | **S3** |
| Sections | 16 |
| Summary | Home still chat-forward; sidebar “Enterprise AI” for probe chat. |
| Evidence | `frontend/app/page.tsx`, `AppSidebar.tsx` |
| Suggested direction | Control-center-first copy |
| Verify | Snapshot / a11y unchanged |

#### F-024 — Replit auth hook still present

| Field | Value |
|---|---|
| Severity | **S3** |
| Sections | 15 |
| Summary | Env-gated Replit blueprint registration remains in `app.py`. |
| Suggested direction | Remove or quarantine for airgap desktop product |
| Verify | No import when flag false |

### 7.3 S2/S3 — test / CI / evidence

#### F-025 — CI runs pytest without coverage gate

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 19 |
| Summary | CI: `python -m pytest tests/ --no-cov`. Local `run_test_suite.py` has full coverage gate. |
| Evidence | `.github/workflows/ci.yml`; `run_test_suite.py` |
| Suggested direction | Optional phased: restore coverage threshold in CI once stable, or document intentional split |
| Verify | CI green; no flaky cov |

#### F-026 — Broken phased suite path `tests/resilience`

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 19 |
| Summary | `run_test_suite.py` Phase 4 targets `tests/resilience`, which **does not exist**. |
| Evidence | `run_test_suite.py` PHASES; `tests/` directory listing |
| Suggested direction | Remove target or restore package |
| Verify | `python run_test_suite.py` phase 4 |

#### F-027 — A11y CI soft-fail

| Field | Value |
|---|---|
| Severity | **S2** for compliance claims / **S3** otherwise |
| Sections | 19, 17 |
| Summary | Frontend a11y job uses `continue-on-error: true`. |
| Evidence | `.github/workflows/ci.yml` |
| Suggested direction | Harden when release claims accessibility; keep soft only if documented |
| Verify | a11y report artifacts |

#### F-028 — Dual e2e trees

| Field | Value |
|---|---|
| Severity | **S3** |
| Sections | 19 |
| Summary | Backend `tests/e2e` vs `tests/end_to_end` vs frontend Playwright e2e. |
| Suggested direction | Naming map in TESTING docs; no merge required unless confusing CI |
| Verify | Document only |

### 7.4 Desktop / packaging specifics

#### F-029 — Podman machine hard dependency at Electron ready

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 17 |
| Summary | Managed Podman machine `datalogicengine` required; app quit on failure. Correct fail-closed; rough first-run UX. |
| Evidence | `frontend/electron/main.ts` `ensureManagedPodmanMachineAvailable` |
| Suggested direction | Better first-run diagnostics UI; offline qualification profile if product needs it |
| Verify | Packaging smoke + manual first-run |

#### F-030 — Electron CSP allows `'unsafe-inline'`

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 17 |
| Summary | CSP injects unsafe-inline for script/style (common with static Next export). |
| Evidence | `main.ts` onHeadersReceived CSP |
| Suggested direction | Tighten when feasible (nonces/hashes); accept with residual risk note if not |
| Verify | App still loads; security checklist |

#### F-031 — Electron main process monolith

| Field | Value |
|---|---|
| Severity | **S3** (refactor after S1) |
| Sections | 17 |
| Summary | `main.ts` ~1791 lines mixing secrets, backend spawn, IPC, protocol, updates. |
| Suggested direction | Split modules after IPC/security freezes |
| Verify | Electron unit tests + e2e smoke |

### 7.5 Config / versioning drift

#### F-032 — Stale backend config version strings

| Field | Value |
|---|---|
| Severity | **S3** |
| Sections | 1 |
| Summary | Historical note: `backend/config.py` version drift vs product 4.3.0 (observed in earlier sections). |
| Suggested direction | Single authority `config/product-versions.json` |
| Verify | Product version endpoint / about UI |

#### F-033 — Pinecone still coded in vector store path

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 9 |
| Summary | Vector store still references Pinecone code paths while product story is local Chroma/object plane. |
| Evidence | Prior storage section review of `backend/storage/vector_store` |
| Suggested direction | Gate or remove cloud vector backends for desktop profile |
| Verify | Storage init tests; no unexpected network |

#### F-034 — Formal legacy retirement exists but incomplete vs pyc residue

| Field | Value |
|---|---|
| Severity | **S2** |
| Sections | 20 |
| Summary | `config/legacy-retirement.json` is good process; orphan pyc sets not fully reflected. |
| Suggested direction | Extend retirement inventory to orphan modules; automate check |
| Verify | Script vs JSON parity |

---

## 8. Orphan bytecode inventory (main tree)

Scan of `backend/` + `core/` for `.pyc` without matching `.py` (audit session). **~70 unique modules.** Categories:

### 8.1 Local model (high signal)

- `backend/local_model_acceleration::{config,keepalive,manager,ollama_client,paths,response_cache,safety}`

### 8.2 Security residue

- `backend/security::{active_defense,api_security,context_aware,data_classification,defense_supervisor,honeypot,mfa,rbac,sanitizer,security_monitoring,tenant_rls,token_manager,vulnerability_scanner,zero_trust}`

### 8.3 Routes / storage split

- `backend/routes::{storage_download_routes,storage_management_routes,storage_upload_routes}`

### 8.4 Models package split

- `backend/models::{gateway,knowledge,mcp,simulation,trace,truth,user}`

### 8.5 Gateway / MCP / middleware / services

- `backend/llm_gateway::{complexity_classifier,escalation_config,tier_availability}`
- `backend/mcp_server/tools::{jira,salesforce}`
- `backend/middleware::{asgi_security,input_sanitizer,request_hooks}`
- `backend/services::file_upload_service`
- `backend/simulation::simulation_engine`
- `backend/tracing::blueprint`
- `backend/api::ka_management`
- `backend::{admin,app_factory,decorators,email_service,enterprise_architecture,export_service,security_scan_api}`
- `backend/knowledge_algorithms::ka_50_knowledge_integrity_validator`
- `backend/truth_engine/truth_core::{persona_sufficiency,router}`

### 8.6 Core residue

- `core/axes::{axis14_provenance,axis15_object_type,axis16_validation_state,axis17_security,axis3_domain,axis5_honeycomb}`
- `core/knowledge_algorithm::resilience_router`
- `core/persona::{memory_system,persona_manager,persona_models,persona_system,quad_persona_engine}`
- `core/persona/quad::axis_role_mapper`
- `core/security::rag_sanitizer`
- `core/simulation::{coordinate_system,pov_engine_enterprise,query_analysis_system}`

**Planning rule:** Prefer **delete pyc + document** over resurrecting modules unless a product decision requires resurrection (especially local model).

---

## 9. Strengths to preserve (do not “fix” away)

Codex plan must **not** regress:

1. **Single governed answer path** — gateway → `GovernedExecutionOrchestrator` (see `tests/governed_execution/test_single_path.py`).
2. **Thin SDKs** — no second DSQP/KA/provider pipeline in clients.
3. **Desktop auth model** — Windows identity + HMAC install secret + CSRF; no reintroduction of multi-user SaaS auth by accident.
4. **Fail-closed auto-update** until trust policy is truly qualified.
5. **Release honesty** — `release_blocked` / NO-GO until evidence exists.
6. **Client keys do not expose provider credentials** (`provider_credentials_exposed: false`).
7. **Simulation budgets / chat separation**.
8. **Dataset exporter fail-closed** behaviors for incomplete training modes.
9. **Trace as system of record** for evidence/export.
10. **Control-center frontend IA** (settings/ops over chat-as-product).

---

## 10. Suggested phase skeleton for Codex plan

Codex should expand this into a full phased plan with PR-sized work units, owners, and tests. Suggested order:

### Phase A — Inventory freeze & hygiene (low risk)

- Orphan pyc purge script + delete known residue (F-004, F-010, F-020 providers pyc).
- Extend `legacy-retirement.json` (F-034).
- Fix `run_test_suite.py` missing `tests/resilience` (F-026).
- Health version from product-versions (F-012).
- Document OpenAPI subset version alignment (F-011 partial).

**Exit:** No orphan pyc in CI optional check; phased suite paths valid.

### Phase B — API surface consolidation (S1)

- Resolve dual compliance registration (F-001).
- Plan dual-prefix deprecation (F-002) with flag.
- Namespace dual admin (F-003).
- GraphQL GraphiQL policy (F-007).
- Unregistered API module disposition (F-009).

**Exit:** Route uniqueness tests; OpenAPI/gateway contract green; no silent shadowing.

### Phase C — Product decision: generative locality (fork)

**Decision record required:**

| Option | Work |
|---|---|
| **C0 Accept cloud-BYOK generative** | Purge local_model pyc; keep Electron stub; align all docs/UI cloud disclosure (already partially present) |
| **C1 Restore local generative** | Promote worktree `local_model_acceleration` to main with tests; wire Electron status truthfully; keep SDK thin (server owns local provider) |

Do not partially reintroduce local models without tests.

### Phase D — Memory & storage authority

- Memory authority matrix (F-013).
- Pinecone/cloud vector disposition for desktop profile (F-033).
- Confirm data-plane profiles vs release-channel (already partially gated).

### Phase E — Desktop packaging polish (not fake production sign-off)

- First-run Podman UX (F-029).
- CSP residual risk acceptance or tighten (F-030).
- Optional main.ts split (F-031) after IPC freeze.
- Keep update trust fail-closed (F-006).

### Phase F — SDK publish hygiene

- Rebuild/remove stale 0.3.1 artifacts (F-020).
- Manifest parity for TS SDK (F-021).
- License dual-notice if intentional.

### Phase G — Frontend control-center polish

- Copy/home/sidebar alignment (F-023).
- Dependency classification (F-022).
- Preserve settings as ops hub.

### Phase H — Test/CI hardening

- Decide coverage in CI (F-025).
- A11y gate policy (F-027).
- Keep windows packaging smoke.

### Phase I — Release authority only (out of engineering cleanup)

- Real codesign, trust gates, legal distribution, signed installer evidence.
- **Not** claimed complete by cleaning orphans.

---

## 11. Verification matrix (minimum)

| Area | Command / artifact |
|---|---|
| Backend unit/integration | `python -m pytest tests/ --no-cov` (CI parity) or `python run_test_suite.py` (local phased) |
| Contract | `tests/contract/` including gateway OpenAPI compatibility |
| Single path | `tests/governed_execution/test_single_path.py` |
| Security smoke | `tests/security/test_security_headers.py`, `test_request_limits.py` |
| Frontend | `cd frontend && npm run test && npm run typecheck` |
| Packaging | CI `windows-packaging-smoke` / local electron dist path |
| Release posture | `config/release-trust-policy.json` still fail-closed until authority says otherwise |
| Secrets hygiene | Confirm `API KEY/`, `certs/` remain gitignored; never commit |

---

## 12. Section-by-section finding index

| Section | Primary findings |
|---|---|
| 1 Runtime | F-008, F-032 |
| 2 Auth | F-004 (security pyc), preserve desktop auth |
| 3 Gateway | F-005, F-015, F-033-related provider locality |
| 4 Governed exec | Preserve spine; F-015 size |
| 5 DMRF/Truth | F-017 |
| 6 Axes | Core residue F-004 cluster |
| 7 DSQP | F-014 |
| 8 KAs | Preserve; F-021 TS manifest |
| 9 Storage | F-033, F-010 |
| 10 Ingestion/memory | F-013 |
| 11 MCP | F-018 |
| 12 Simulation | F-019 preserve |
| 13 Training | F-016 |
| 14 Tracing | Preserve strength |
| 15 Routes/API | F-001, F-002, F-003, F-007, F-009, F-011, F-012, F-024 |
| 16 Frontend | F-022, F-023 |
| 17 Electron | F-005, F-006, F-029, F-030, F-031 |
| 18 SDK | F-020, F-021 |
| 19 Tests | F-025, F-026, F-027, F-028 |
| 20 Orphans | F-004, F-005, F-010, F-034, §8 inventory |

---

## 13. Explicit exclusions for the remediation plan

Unless the product owner expands scope:

1. Multi-tenant SaaS redesign.
2. Reintroducing password/MFA/SSO web auth as default.
3. Claiming production release by flipping JSON gates without evidence.
4. Building a full in-app model trainer.
5. Rewriting the entire KA catalog.
6. “Cleaning” gitignored live keys/certs without owner request.
7. Merging simulation unbounded into chat.

---

## 14. Owner decisions required before coding

Codex should stop and ask if these are not already decided:

1. **Generative locality:** Accept cloud-BYOK (C0) vs restore local models (C1)?
2. **Legacy API prefixes:** Hard remove vs long deprecation flag?
3. **GraphQL:** Keep for power users or desktop-disable?
4. **SDK license dual (MIT client vs PolyForm app):** intentional?
5. **CI coverage:** enforce or keep local-only gate?

---

## 15. Final audit opinion (context for prioritization)

DataLogicEngine is a **serious single-node governed middleware + control center** with verification culture above typical solo AI-aided builds. Remaining work is mostly:

- **surface consolidation** (routes/admin/compliance),
- **residue purge** (orphan pyc / hollow local model),
- **honest product decision** on airgap generative,
- **publish/packaging hygiene**,
- and only later **true release signing authority**.

Do not “fix” the core by large speculative rewrites. Prefer phased, test-gated cleanup that preserves the governed single path.

---

## 16. Source references (high-value paths)

| Area | Paths |
|---|---|
| App entry | `app.py`, `main.py`, `wsgi.py`, `backend/__init__.py` |
| Route registration | `backend/routes/__init__.py`, `app.py` `_register_application_routes` |
| Gateway | `backend/llm_gateway/api.py`, `gateway.py`, `external_contract.py` |
| Governed path | `backend/governed_execution/orchestrator.py`, `ten_layers.py`, `refinement.py` |
| Auth | `backend/routes/auth_routes.py`, `backend/auth/*`, `backend/security/desktop_local_auth.py` |
| Electron | `frontend/electron/main.ts`, `preload.ts`, `update-trust.ts` |
| Release policy | `config/release-channel.json`, `config/release-trust-policy.json`, `config/product-versions.json` |
| Frontend shell | `frontend/components/layout/AppSidebar.tsx`, `frontend/app/settings/page.tsx` |
| SDK | `sdk/UKG_Python_SDK/`, `sdk/DataLogicEngine_TypeScript_SDK/` |
| Tests | `tests/`, `run_test_suite.py`, `.github/workflows/ci.yml` |
| Legacy map | `config/legacy-retirement.json` |
| Release status | `docs/RELEASE_READINESS_RECORD.md`, `README.md` |
| Orphan disposition (detailed worksheet) | `docs/audits/ORPHAN_MODULE_DISPOSITION_WORKSHEET_2026-08-11.md` |

---

## 17. Document history

| Version | Date | Notes |
|---|---|---|
| 1.0 | 2026-08-11 | Initial slow audit findings export for Codex phased plan |
| 1.1 | 2026-08-11 | Appended §18 orphan disposition notes for Codex validate + work |
| 1.2 | 2026-08-12 | Linked companion 10/10 recommendations document |
| 1.3 | 2026-08-12 | Linked phased implementation plan |

---

## 18. Orphan module disposition notes (Codex: validate and work)

> **Audience:** Codex (or implementer).
> **Task:** Validate the inventory, confirm zero live importers where claimed, then execute owner-approved dispositions (default = purge residue; wire only where owner chooses).
> **Companion worksheet:** `docs/audits/ORPHAN_MODULE_DISPOSITION_WORKSHEET_2026-08-11.md` (same content, checkbox form).
> **Related findings:** F-004, F-005, F-010, F-014, F-018, F-020, F-034.

### 18.1 Definition and scope

**Orphan** = `.pyc` bytecode on the main tree **without** a matching sibling `.py`.

| Metric | Value |
|---|---|
| Unique orphan modules (scan 2026-08-11) | **78** |
| Trees scanned | `backend/`, `core/`, `sdk/UKG_Python_SDK/ukg_sdk/` |
| Machine-readable local scan | `.codex_tmp/orphan_pyc_inventory.json` (workshop only; not product authority) |

These are almost always **intentionally deleted source with leftover bytecode**, not missing feature switches.

### 18.2 Disposition codes (for plan + PRs)

| Code | Meaning |
|---|---|
| **DELETE** | Not needed on current product; remove pyc (and empty dirs); do not restore |
| **HOLD** | Do not wire without explicit owner decision; prefer delete pyc and track as future feature if useful |
| **WIRE** | Restore **source** from worktree/git history and integrate into live path with tests |
| **SUPERSEDED** | Already replaced by a different live module; delete orphan pyc only |

**Codex rule:** Never “restore” from `.pyc` alone. Never reintroduce multi-tenant SaaS auth by accident. Preserve single governed path and thin SDKs (§9).

### 18.3 Product defaults that drive disposition

Align purge vs wire with current product identity (§2):

| Default | Implication for orphans |
|---|---|
| Single-owner desktop auth | MFA / RBAC / tenant_rls / multi-user email → **DELETE** |
| Live injection screening | gateway + `prompt_injection_shield` + `ai_guardrail` — **not** `defense_supervisor` |
| Models SoR | root `models.py` — historical split `backend/models/` bytecode → **SUPERSEDED → DELETE** |
| Canonical personas | `backend/dsqp` (+ live `core/persona/quad`) — old persona engines → **DELETE** |
| Generative on mainline | Cloud BYOK; Electron stubs local models — local_model stack is **decision fork** (§18.5) |
| Thin SDK | Client providers/handlers → **DELETE** |

### 18.4 Executive summary (recommended defaults)

| Bucket | Count (approx) | Recommendation |
|---|---:|---|
| Security multi-user / SaaS era | 14 | **DELETE** (several already product-decided) |
| Local model + gateway tier chain | 10 | **HOLD → owner decision B0/B1** (§18.5) |
| Consolidated routes / models / services | 15 | **SUPERSEDED → DELETE pyc** |
| Axes renames / old axis names | 6 | **SUPERSEDED → DELETE pyc** |
| Old persona engines | 6 | **SUPERSEDED → DELETE pyc** |
| MCP jira/salesforce | 2 | **DELETE** unless owner wants connectors now |
| Core simulation / KA / truth residue | ~8 | **DELETE** (live modules elsewhere) |
| SDK client providers + handlers | 8 | **DELETE** |
| Misc legacy backend modules | ~12 | **DELETE** |

**Nothing in the orphan list is required for the current live desktop path** as audited.
The only **strategic** wire-back candidate is **local model acceleration** (plus related tier modules) **if** the owner wants airgapped generative again.

If owner stance is cloud-BYOK generative + single-owner desktop + no Jira/SF now:

> **Wire nothing. Delete all 78 orphan pyc clusters after validation.**

### 18.5 Owner decision gate (Codex must not guess)

Codex must **stop and confirm** if not already marked by owner:

#### Decision B — Local generative

| Option | Meaning | Orphan action |
|---|---|---|
| **B0** Accept cloud-BYOK only (current mainline) | Airgap = data plane, not generative | **DELETE** entire §18.6.B cluster |
| **B1** Restore local generative | Server-owned Ollama/local path; SDK stays thin | **WIRE** from worktree + tests + truthful Electron status |

Source for B1 recovery (gitignored worktree archive, not product):

- `.claude/worktrees/stupefied-ramanujan-516b57/backend/local_model_acceleration/`
- Related gateway tier modules may exist in same worktree
- Electron today hard-stubs `local-model-status` → `ollama_available: false` (“cloud-only product”) in `frontend/electron/main.ts`

#### Decision C — Future compliance ideas only

| Modules | Guidance |
|---|---|
| `data_classification`, `vulnerability_scanner` | Prior audits “kept for future”; still unwired. Prefer **DELETE pyc** and open a **new feature** later — do not resurrect opaque bytecode |

#### Decision D — MCP enterprise connectors

| Modules | Guidance |
|---|---|
| `jira`, `salesforce` under `backend/mcp_server/tools` | CHANGELOG: removed from production connector set. **DELETE** unless owner explicitly wants them with consent/qualification |

### 18.6 Disposition by cluster (validate then act)

#### A. Security orphans (SaaS / multi-user era) — default DELETE

Live security today includes: `ai_guardrail`, `prompt_injection_shield`, `content_defense`, `desktop_local_auth`, `dpapi_store`, `encryption_manager`, `session_manager`, etc.

| Module | Dir | Prior notes | Default |
|---|---|---|---|
| `defense_supervisor` | `backend/security` | **DECIDED deprecate** in `CODEX_WORK_QUEUE_2026-08-10.md` D-2 / C-6. Live path uses gateway + shield/guardrail. Wiring = duplicate fail-open surface. | **DELETE** |
| `mfa` | `backend/security` | Web MFA removed with desktop single-owner auth | **DELETE** |
| `rbac` | `backend/security` | Multi-role SaaS | **DELETE** |
| `tenant_rls` | `backend/security` | Auth deprecation Phase D removed | **DELETE** |
| `honeypot` | `backend/security` | Prior: dead single-mode decoy | **DELETE** |
| `context_aware` | `backend/security` | Prior: dup of retired supervisor path | **DELETE** |
| `api_security` | `backend/security` | Prior: HMAC for retired enterprise gateway | **DELETE** |
| `security_monitoring` | `backend/security` | Prior: SIEM multi-user | **DELETE** |
| `zero_trust` | `backend/security` | Enterprise SaaS framing; unwired | **DELETE** |
| `token_manager` | `backend/security` | Legacy token surface | **DELETE** |
| `active_defense` | `backend/security` | Not on live path | **DELETE** |
| `sanitizer` | `backend/security` | Superseded by shield/middleware | **DELETE** |
| `data_classification` | `backend/security` | Future idea only | **HOLD idea / DELETE pyc** |
| `vulnerability_scanner` | `backend/security` | Future idea only | **HOLD idea / DELETE pyc** |

**Validate:** `tests/security/test_security_module_wiring.py`; grep zero production importers for each name excluding worktrees/dist.

#### B. Local generative stack — owner B0/B1 only

| Module | Dir | Default |
|---|---|---|
| `config`, `keepalive`, `manager`, `ollama_client`, `paths`, `response_cache`, `safety` | `backend/local_model_acceleration` | **HOLD / DECIDE** |
| `complexity_classifier`, `escalation_config`, `tier_availability` | `backend/llm_gateway` | **HOLD / DECIDE** |

Do **not** leave pyc as a half-feature after decision.

#### C. Routes / models / services — SUPERSEDED → DELETE

| Orphan | Replaced by / notes |
|---|---|
| `storage_download_routes`, `storage_management_routes`, `storage_upload_routes` | `backend/routes/storage_routes.py` |
| `backend/models/{gateway,knowledge,mcp,simulation,trace,truth,user}` | root `models.py` |
| `file_upload_service` | multimodal route hardening |
| `email_service` | multi-user; not desktop |
| `export_service` | route-level export |
| `admin`, `app_factory`, `decorators` | `app.py` + `backend/auth/api_decorators.py` + live admin routes |
| `enterprise_architecture`, `security_scan_api` | dead / unregistered |
| `ka_management` | `ka_routes` + KA controller |
| `blueprint` (`backend/tracing`) | `backend/tracing/api.py` |
| `asgi_security`, `input_sanitizer`, `request_hooks` | live middleware set |

#### D. MCP connectors — DELETE unless Decision D is WIRE

- `backend/mcp_server/tools/jira`
- `backend/mcp_server/tools/salesforce`

#### E. Axes old names — SUPERSEDED → DELETE (do not wire alongside live)

Live: `axis3_honeycomb`, `axis4_branch`, `axis14_acquisition_lifecycle`, `axis15_risk_threat`, `axis16_ethics_trust`, `axis17_frost_mode`, …

Orphans (old names): `axis3_domain`, `axis5_honeycomb`, `axis14_provenance`, `axis15_object_type`, `axis16_validation_state`, `axis17_security`

Wiring old names recreates dual axis definitions — **forbidden**.

#### F. Persona residue — DELETE

`quad_persona_engine`, `persona_manager`, `persona_system`, `persona_models`, `memory_system`, `axis_role_mapper` (unless a live import is proven — validate first).

Canonical: **`backend/dsqp`**.

#### G. Simulation / KA / truth residue — DELETE

| Module | Notes |
|---|---|
| `backend/simulation/simulation_engine` | Live: multi_agent_engine, jobs, contracts, … |
| `core/simulation/{coordinate_system,pov_engine_enterprise,query_analysis_system}` | Live sim/coordinate elsewhere |
| `core/knowledge_algorithm/resilience_router` | Residue |
| `backend/knowledge_algorithms/ka_50_knowledge_integrity_validator` | Old KA layout |
| `backend/truth_engine/truth_core/{persona_sufficiency,router}` | Unwired; gateway is authority |
| `core/security/rag_sanitizer` | Residue |

#### H. Python SDK thin-client residue — DELETE

`ukg_sdk/ka/handlers` and the entire historical Python SDK provider pyc tree
(`anthropic`, `azure_openai`, `base`, `google`, `local_slm`, `ollama`, `openai`).

Matches SDK v0.6+ “no second brain.” Remove empty `providers/` after purge. Rebuild/publish SDK artifacts separately if needed (see F-020).

### 18.7 Full orphan basename inventory (78)

**backend root:** admin, app_factory, decorators, email_service, enterprise_architecture, export_service, security_scan_api

**backend/api:** ka_management

**backend/knowledge_algorithms:** ka_50_knowledge_integrity_validator

**backend/llm_gateway:** complexity_classifier, escalation_config, tier_availability

**backend/local_model_acceleration:** config, keepalive, manager, ollama_client, paths, response_cache, safety

**backend/mcp_server/tools:** jira, salesforce

**backend/middleware:** asgi_security, input_sanitizer, request_hooks

**backend/models:** gateway, knowledge, mcp, simulation, trace, truth, user

**backend/routes:** storage_download_routes, storage_management_routes, storage_upload_routes

**backend/security:** active_defense, api_security, context_aware, data_classification, defense_supervisor, honeypot, mfa, rbac, sanitizer, security_monitoring, tenant_rls, token_manager, vulnerability_scanner, zero_trust

**backend/services:** file_upload_service

**backend/simulation:** simulation_engine

**backend/tracing:** blueprint

**backend/truth_engine/truth_core:** persona_sufficiency, router

**core/axes:** axis14_provenance, axis15_object_type, axis16_validation_state, axis17_security, axis3_domain, axis5_honeycomb

**core/knowledge_algorithm:** resilience_router

**core/persona:** memory_system, persona_manager, persona_models, persona_system, quad_persona_engine

**core/persona/quad:** axis_role_mapper

**core/security:** rag_sanitizer

**core/simulation:** coordinate_system, pov_engine_enterprise, query_analysis_system

**sdk:** ka/handlers; providers: anthropic, azure_openai, base, google, local_slm, ollama, openai

### 18.8 Source survival map (recovery only if WIRE)

| Cluster | Source available? | Location |
|---|---|---|
| local_model_acceleration + tier modules | Yes | `.claude/worktrees/stupefied-ramanujan-516b57/` |
| defense_supervisor | Yes in worktree | **Do not wire** — product decision deprecate |
| MFA / RBAC / zero_trust / tenant_rls / honeypot | Older worktrees | `dazzling-antonelli`, `strange-margulis-cc69c5` |
| Jira / Salesforce tools | Older worktrees | same |
| email_service / security_scan_api | Older worktrees | same |
| Axes old names | Not needed | Live renames on main |
| backend/models split | Not needed | root `models.py` |

Worktrees are **gitignored agent caches** — recovery archive only, not ship surface.

### 18.9 Codex work plan for this section

#### Step 1 — Validate inventory

1. Re-scan for pyc without sibling `.py` under `backend/`, `core/`, `sdk/UKG_Python_SDK/ukg_sdk/`.
2. Diff against §18.7; update count if drift.
3. For each **DELETE/SUPERSEDED** candidate, grep production imports **excluding** `.claude/worktrees`, `frontend/dist*`, `dist/`, `htmlcov*`.
4. Confirm live replacements still exist (especially axes renames, `models.py`, `storage_routes.py`, DSQP, live security modules).
5. Confirm `tests/security/test_security_module_wiring.py` still guards retired supervisor re-entry.

#### Step 2 — Obtain owner marks if missing

If B0/B1, compliance hold, or Jira/SF not marked in worksheet/chat, **ask before implementing WIRE**.

#### Step 3 — Execute purge (default path = B0 + DELETE all else)

1. Delete orphan `.pyc` only when no sibling `.py` exists.
2. Remove empty packages that contain only `__pycache__` residue (e.g. hollow `local_model_acceleration` after B0).
3. Extend `config/legacy-retirement.json` for major clusters:
   - security multi-user (mfa/rbac/tenant_rls/honeypot/defense_supervisor/…)
   - local_model_acceleration (if B0)
   - sdk providers
   - storage route split
   - axes old names
4. Optional: add a small test or script that fails CI if new orphan pyc appears without matching `.py`.
5. Do **not** touch gitignored `API KEY/`, `certs/`, or worktree trees unless owner requests.

#### Step 4 — If owner chooses B1 (local generative)

1. Restore **source** from worktree into main (not pyc).
2. Wire server-side only; keep SDK thin (no client provider brain).
3. Make Electron `local-model-status` truthful.
4. Add/repair unit + integration tests; no dual generative path that bypasses governed execution.
5. Update product/docs honesty (cloud disclosure may still apply for BYOK fallback).

#### Step 5 — Verification gates

| Gate | Action |
|---|---|
| Import graph | Zero imports of deleted module names on main |
| Security wiring | `pytest tests/security/test_security_module_wiring.py` |
| Single path | `pytest tests/governed_execution/test_single_path.py` |
| Targeted suite | security + gateway smoke + any touched packages |
| Optional full | `python -m pytest tests/ --no-cov` or phased runner (fix F-026 `tests/resilience` first) |
| Packaging | Do not reintroduce local-model into freeze unless B1 complete |

### 18.10 Safe cleanup rules (hard constraints)

1. Prefer **delete pyc + document** over resurrecting modules.
2. Do not wire `defense_supervisor` (decided).
3. Do not wire old axis names alongside live axis modules.
4. Do not reintroduce MFA/RBAC/tenant_rls as default desktop auth.
5. Do not put provider brains back into the Python/TS SDK.
6. Phase A hygiene in §10 should absorb the default purge; Phase C still owns B0/B1 product fork.

### 18.11 Practical bottom line for Codex

> Almost everything orphaned is **intentionally retired residue**.
> **Wire nothing** unless the owner explicitly selects **B1** (local generative) or **Jira/Salesforce connectors**.
> **Delete residue** for security multi-user, models/routes consolidation, old axes names, old personas, SDK providers, and MCP enterprise tools.
> Track `data_classification` / `vulnerability_scanner` as **future features**, not pyc resurrection.

---

**End of findings report.**
