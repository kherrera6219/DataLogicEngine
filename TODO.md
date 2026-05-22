# DataLogicEngine TODO

**Last updated:** 2026-05-22
**Status:** Canonical planning source

This is the only active TODO list for the repository. Keep open work here instead of adding separate project plans, roadmap files, assessment TODOs, or notes documents.

## Current Priority

### Application Readiness

#### Product Copy and Disclosures

- [x] Replace overbroad product claims in app-facing copy with conservative, verifiable wording.
- [x] Align AI provider names across `README.md`, `docs/PRIVACY_POLICY.md`, `frontend/app/about/ai-limitations/page.tsx`, and `frontend/app/about/cloud-services/page.tsx`.
- [x] Explicitly disclose cloud AI processing and internet requirement anywhere AI settings or chat entry points are shown.
- [ ] Finalize the in-app feature list used by `frontend/public/manifest.json`, `README.md`, and About pages. Current copy is conservative and aligned, but the manifest shortcuts/features still need a product-owner pass before release.
- [x] Finalize privacy practices wording in the app and docs so export/delete/history/AI-processing controls match actual behavior.

Baseline app description:

```text
DataLogicEngine is a local-first, cloud-augmented knowledge graph workspace for governed AI reasoning. It helps users organize enterprise knowledge, run traceable AI-assisted analysis, inspect provider/model usage, and manage privacy controls.

Internet access is required for AI reasoning features. Prompts and related context may be sent to configured third-party AI providers such as OpenAI, Anthropic, Google, or Microsoft Azure OpenAI. AI-generated responses may contain errors and should be verified before use in critical decisions.
```

#### App Assets and Manifest

- [x] Capture 5-10 screenshots from the actual app UI for docs, manifest, and release verification.
- [x] Add screenshots to `frontend/public/manifest.json` if publishing as a web/PWA surface.
- [x] Create missing PWA icon assets referenced by `frontend/public/manifest.json`.
- [x] Prepare in-app and documentation banner images where useful.

#### Windows Installer

- [x] Rebuild the Electron/NSIS installer after current app updates.
- [x] Verify installer configuration for assisted install location selection, progress, completion behavior, and desktop/start menu shortcuts.
- [x] Verify Windows Apps registry metadata lists `DataLogicEngine Desktop` with publisher `Kevin Herrera`, install location, and uninstall command.
- [x] Verify normal Windows uninstall removes application binaries and keeps app data by default.
- [x] Create a local dev certificate helper for development validation.
- [ ] Create and document a trusted production code-signing certificate path.

Completed asset work:

- `frontend/public/icons/icon-192.png` and `frontend/public/icons/icon-512.png` are generated from the existing app icon.
- `frontend/public/screenshots/` contains six 1440x900 route captures from the running app: dashboard, chat, settings/privacy, cloud services, graph, and settings/provider controls.
- `frontend/public/brand/datalogicengine-banner-1600x900.png` provides a reusable documentation/banner asset based on the existing app icon.

#### Manual Validation

- [ ] Add repeatable WCAG 2.1 AA accessibility evidence for primary app routes.
- [ ] Add or document keyboard navigation coverage across primary pages.
- [ ] Add or document screen reader compatibility checks with NVDA on Windows.
- [ ] Add cloud outage graceful-degradation test coverage.
- [ ] Add auth failure end-to-end test coverage.
- [ ] Add rate-limit user experience test coverage.
- [ ] Add AI provider failure-mode test coverage.
- [ ] Add data export and delete end-to-end test coverage.

## Validated Gap Review

Review date: 2026-05-22

No standalone `ROADMAP.md` file exists in the repository. The only roadmap-style source found during the May 22 review was `docs/archive/historical-documents/MVP Plan_ Universal Knowledge Graph (UKG) System.pdf`; actionable current work from that historical plan is tracked in this file instead of creating a second roadmap.

| TODO area | Code validation | Current status |
| --- | --- | --- |
| App-facing product copy | Baseline copy exists in this file; app-facing claims were revised to conservative local-first/cloud-augmented wording in manifest, About, AI limitations, cloud-services, chat, and settings surfaces on 2026-05-21. | Implemented; keep future copy changes aligned with baseline wording. |
| Third-party AI services list | Provider disclosures exist in `README.md`, `docs/PRIVACY_POLICY.md`, `frontend/app/about/ai-limitations/page.tsx`, and `frontend/app/about/cloud-services/page.tsx`, using OpenAI, Anthropic, Google Gemini / Vertex AI, and Microsoft Azure OpenAI. | Implemented; keep provider labels consistent when adding new providers. |
| Screenshots | `frontend/public/manifest.json` contains six real screenshot entries and `frontend/public/screenshots/` contains dashboard, chat, privacy, cloud-services, graph, and provider-settings captures. | Implemented; keep screenshots refreshed when primary UI changes. |
| PWA icons | `frontend/public/manifest.json` references `/icons/icon-192.png` and `/icons/icon-512.png`; both files exist under `frontend/public/icons/`. | Implemented. |
| App/banner images | `frontend/public/brand/datalogicengine-banner-1600x900.png` exists for documentation/banner reuse. | Implemented. |
| Windows installer publisher | Rebuilt installer metadata now reports company/publisher as `Kevin Herrera`, product as `DataLogicEngine Desktop`; Windows Apps registry metadata includes display name, publisher, install location, and uninstall command; local dev signature status is `Valid` for `CN=Kevin Herrera`. | Partially ready; release still needs a trusted production certificate configured and documented. |
| Automated accessibility support | `frontend/package.json` includes `test:a11y:ci`; `frontend/scripts/run-a11y-ci.mjs` scans public/static routes with axe WCAG A/AA tags. | Partially ready; authenticated primary-route coverage and manual WCAG evidence are still required. |
| Keyboard/navigation route coverage | `frontend/tests/e2e/route-sidebar-smoke.spec.ts` covers route load and sidebar toggles. | Partially ready; manual keyboard pass still required. |
| AI transparency labels | `frontend/components/Chat/MessageBubble.tsx` labels AI-generated output and shows provider/model metadata. | Implemented; add regression coverage where missing. |
| User data controls | `routes/user_data_routes.py` includes export/delete endpoints, and `frontend/app/settings/privacy/page.tsx` exists. | Implemented; end-to-end manual validation still required. |
| AI processing controls | `frontend/components/settings/AiModelSettings.tsx` includes AI processing and chat history preferences. | Implemented; end-to-end manual validation still required. |

## MVP Roadmap Document Validation

Source reviewed: `docs/archive/historical-documents/MVP Plan_ Universal Knowledge Graph (UKG) System.pdf`

| MVP / roadmap item | Current validation | Status |
| --- | --- | --- |
| 13-axis coordinate MVP | Current architecture and code have evolved to a 17-axis coordinate model (`core/coordinate_system.py`, `docs/ARCHITECTURE.md`, `docs/DECISION_LOGIC.md`). | Superseded and implemented as 17-axis. |
| Pillar and sector classification | Pillars, sectors, domains, coordinates, and knowledge-node APIs are documented and implemented across backend models/routes and architecture docs. | Implemented; keep API coverage current. |
| Basic simulation engine with traceability | Truth Engine, trace routes, `TraceRun` fields, Tier 2 audit footer, and `TruthAuditEvent` hash-chain receipt are implemented. | Implemented; broader staging/provider evidence still required. |
| Regulatory and compliance reasoning | Regulatory/compliance axes, TruthGate checks, compliance routes, and audit metadata are implemented. | Implemented; conflict/failure-mode evidence still required. |
| Quad-persona reasoning | Persona axes, persona routes, and multi-persona reasoning docs/code exist. | Implemented foundation; recursive debate and dynamic persona expansion remain future work. |
| Node/honeycomb graph navigation | Graph, knowledge-node, edge, and related UI/API surfaces exist. | Implemented foundation; keep graph UX and OpenAPI coverage improving. |
| Compliance overlays and coordinate trace UI | AI labels, provider/model metadata, audit footer, and trace-oriented backend support exist. | Partially implemented; richer user-facing trace/overlay UX remains open. |
| External API / enterprise connector extension | MCP server management, tool/resource/prompt routes, scope enforcement, and connector infrastructure exist. | Implemented foundation; production connector validation remains open. |
| Enterprise data ingestion and vector store | PostgreSQL, Neo4j, Redis, ChromaDB, object storage, and local setup/QC are implemented. | Implemented for local QC; production-scale ingestion validation remains open. |
| Real-time monitoring/dashboard | `/health`, `/live`, `/ready`, `/metrics`, Sentry configuration, admin routes, and dashboard surfaces exist. | Implemented foundation; production alerting evidence remains open. |
| Testing and evaluation report | Automated commands and partial a11y route scan exist. | Partially implemented; app-readiness evidence and manual accessibility/failure-mode report remain open. |
| Post-MVP recursive debate, dynamic PoV expansion, automated axis learning, quantum-ready nodes, feedback loops, enterprise scaling | Architecture and simulation modules include foundations for advanced reasoning and operations. | Future work; not release blockers for the current local-first application readiness pass. |

## Phased Completion Plan

### Phase 1: App Copy and Disclosures

Goal: Make every in-app and repo-facing statement conservative, specific, and consistent with actual behavior.

- Finalize app description from the baseline description.
- Replace overbroad wording in app surfaces and manifest metadata with conservative wording.
- Reconcile third-party AI provider names across `README.md`, `docs/PRIVACY_POLICY.md`, `frontend/app/about/ai-limitations/page.tsx`, and `frontend/app/about/cloud-services/page.tsx`.
- Ensure chat, AI settings, privacy settings, and cloud disclosure pages clearly state when internet/cloud AI processing is used.
- Ensure privacy wording matches implemented export, delete, chat-history, and AI-processing controls.

Exit criteria:

- Manifest description, README description, About pages, AI limitations page, cloud services page, and privacy policy use consistent provider and data-handling wording.
- No app-facing copy promises guaranteed accuracy, certification, zero retention, or enterprise agreements unless backed by repo evidence.

### Phase 2: App Assets and PWA Manifest

Goal: Make referenced app assets real and keep generated visual assets usable by the app/docs.

- Capture 5-10 screenshots from real app routes: dashboard, chat with AI label, settings/privacy, cloud services disclosure, graph/knowledge view, and provider/model settings.
- Create `frontend/public/icons/icon-192.png` and `frontend/public/icons/icon-512.png`.
- Generate reusable app/documentation banner images from the approved brand asset if needed.
- Update `frontend/public/manifest.json` with real screenshot entries if publishing the web/PWA surface.
- Verify assets render in the packaged Electron build and web build.

Exit criteria:

- Manifest icon references resolve on disk.
- Screenshots and banners are committed in a documented asset path.
- `npm run build` and `npm run test:e2e:visual` pass or have documented environment blockers.

### Phase 3: Automated Regression Evidence

Goal: Convert existing smoke coverage into repeatable application-readiness evidence.

- Expand `test:a11y:ci` routes to include `/dashboard`, `/chat`, `/settings`, `/settings/privacy`, `/about/cloud-services`, and `/about/ai-limitations` once authenticated/local fixture routing is stable.
- Add or update Playwright coverage for auth failure, cloud/provider failure, rate-limit UX, export flow, and delete flow.
- Save test command output and screenshots under `reports/app-readiness/`.
- Confirm no not-found, hydration, or accessibility regressions on primary pages.

Exit criteria:

- Frontend lint, typecheck, unit tests, route smoke, visual smoke, and a11y scans pass.
- Backend route tests cover user export/delete and AI preference APIs.
- App-readiness report links to exact commands and generated artifacts.

### Phase 4: Manual Accessibility and Failure-Mode Audit

Goal: Complete the manual checks that automation cannot prove.

- Perform WCAG 2.1 AA manual audit on the packaged/local app build.
- Keyboard-test all primary pages and modal/dialog workflows.
- Confirm screen reader compatibility with NVDA on Windows at minimum.
- Test cloud outage, AI provider failure, auth failure, rate-limit behavior, data export, and data deletion end to end.
- Record findings, fixes, screenshots, and pass/fail evidence in `reports/app-readiness/`.

Exit criteria:

- Every item under Manual Validation is checked off with evidence.
- Any blocking issue has either a fix committed or a documented application risk decision.

### Phase 5: Release Readiness Cleanup

Goal: Leave the application in a release-ready state with no stale TODOs.

- Rebuild and validate the normal Windows installer/uninstaller path.
- Sign installer artifacts with a real trusted certificate before release; use the dev certificate generator only for local validation.
- Run final packaged installer smoke test.
- Verify `frontend/public/manifest.json`, docs, and app pages agree with implemented behavior.
- Archive app-readiness evidence in `reports/app-readiness/`.
- Update `TODO.md` checkboxes based on completed code and verification work.

Exit criteria:

- Application readiness evidence is complete.
- `TODO.md` contains only unresolved repo-actionable work.

## Completed Local Stack QC (Phase 6 — 2026-05-15)

All five internal databases have been wired, seeded, and mutually validated in local QC mode. No cloud or external dependencies required.

| Check | Status |
| --- | --- |
| PostgreSQL migrations current | Done — `flask db current` resolves to head; `correlation_id` and `estimated_cost_usd` columns added via `d1e2f3a4b5c6` migration |
| All tracked tables exist | Done — 64 models fully migrated |
| TraceRun AuditBundle columns added | Done — `layers_executed`, `refinement_cycles`, `regulatory_pass`, `security_pass`, `truthgate_decision`, `token_cost`, `latency_ms`, `evidence_pack_hash`, `coordinate17_id` |
| Redis live | Done — Redis on port 6379 responds; session and rate-limit storage functional |
| Neo4j pillar seed | Done — `scripts/seed_neo4j.py` seeds pillar taxonomy + `HONEYCOMB_BRIDGE` crosswalk edges |
| ChromaDB collections initialized | Done — `knowledge_nodes`, `persona_profiles`, `citation_cache`, `audit_evidence` collections created at startup |
| Object storage buckets initialized | Done — `audit_logs`, `simulation_artifacts`, `deliverables`, `graphs`, `eval_data` buckets pre-created at startup |
| End-to-end Tier 2 gateway query | Done — 200 OK with `[UKG Audit Trace]` footer in response body |
| TruthAuditEvent hash-chain receipt | Done — `TruthAuditEvent` row written with valid `hash_chain` and `previous_hash` after each Tier 2+ run |
| F-CONF-01 confidence formula | Done — `TraceRun.confidence` set by `ConfidenceCalculator` (evidence × KA × persona × gate weighting), not raw LLM output |
| Circular import fixes | Done — `core/axes/axis1_knowledge.py`, `axis12_location.py`, `axis13_time.py` migrated to `from extensions import db` |
| `db.session.flush()` before FK child rows | Done — `TraceStage.run_id` now populated correctly after `TraceRun` flush |
| Audit footer coordinate guard | Done — `_audit_footer` coerces non-dict `coordinate` to `{}` before attribute access |
| TruthAuditEvent session_id FK | Done — `TruthMemoryCommitService` passes `session_id=None` (nullable column; no `truth_sessions` row in this flow) |
| Local database setup script | Done — `scripts/setup_local_databases.py` installs PostgreSQL 16, Redis, and Neo4j binaries |
| GraphStore schema constraints | Done — `ensure_schema()` creates `Pillar` and `KnowledgeNode` uniqueness constraints and code/axis indexes on connect |
| Vector store collection init | Done — `initialize_collections()` called at startup via `app.py` |
| Object storage bucket pre-creation | Done — called at startup via `app.py` |

## Completed Application-Readiness Work

| Area | Evidence |
| --- | --- |
| Privacy policy drafted | `docs/PRIVACY_POLICY.md` |
| Privacy policy published in-app | `frontend/app/legal/privacy/page.tsx` |
| AI limitations page | `frontend/app/about/ai-limitations/page.tsx` |
| Cloud services page | `frontend/app/about/cloud-services/page.tsx` |
| Cloud disclosure banner | `frontend/components/CloudDisclosureBanner.tsx` |
| AI output labels | `frontend/components/Chat/MessageBubble.tsx` |
| Provider/model shown per response | `frontend/components/Chat/MessageBubble.tsx` |
| User data export endpoint | `routes/user_data_routes.py` |
| User data deletion endpoint | `routes/user_data_routes.py` |
| Privacy controls page | `frontend/app/settings/privacy/page.tsx` |
| Privacy links in settings and footer | `frontend/app/settings/page.tsx`, `frontend/app/layout.tsx` |
| AI processing toggle | `frontend/components/settings/AiModelSettings.tsx` |
| Chat history opt-out toggle | `frontend/components/settings/AiModelSettings.tsx` |
| Automated accessibility audit command | `frontend/package.json` (`test:a11y:ci`) |
| Conservative copy/disclosure pass | `frontend/public/manifest.json`, `frontend/app/about/page.tsx`, `frontend/app/about/ai-limitations/page.tsx`, `frontend/app/about/cloud-services/page.tsx`, `frontend/app/legal/privacy/page.tsx`, `frontend/components/Chat/ChatInterface.tsx`, `frontend/components/settings/AiModelSettings.tsx`, `frontend/components/CloudDisclosureBanner.tsx`, `docs/PRIVACY_POLICY.md` |

## Documentation Cleanup Policy

- Keep current planning in this file only.
- Keep release go/no-go criteria in `docs/RELEASE_CHECKLIST.md`.
- Keep active documentation discoverable from `README.md` and `docs/README.md`.
- Do not add new `PROJECT.md`, `ROADMAP.md`, `current_plan.md`, assessment TODOs, or archived planning summaries without first folding actionable items into this file.
