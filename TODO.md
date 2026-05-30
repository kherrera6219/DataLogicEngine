# DataLogicEngine TODO

**Last updated:** 2026-05-29
**Status:** Canonical planning source

This is the canonical active TODO list for repository release readiness and operational work. `UKG_DataLogicEngine_Master_Completion_Plan_v1.txt` is the current phased execution plan for the broader UKG/DataLogicEngine completion roadmap; keep release go/no-go items mirrored here when they affect the current shipping branch.

## Unified Backlog

Review date: 2026-05-23

No standalone `ROADMAP.md` file exists in the repository. The only roadmap-style source found during the May 22 review was `docs/archive/historical-documents/MVP Plan_ Universal Knowledge Graph (UKG) System.pdf`; actionable current and future work is consolidated below.

### Production Code Review Remediation

Source report: `reports/production-code-review-2026-05-23.md`

Validation status: Production code-review remediation phases 1 through 4 are complete as of 2026-05-23.

Master completion plan status: Phase 1 / A is complete for the local-first desktop target as of 2026-05-25. Phase 2 / DB-N local implementation and Phase B / Axis Alignment are also complete. NVDA screen-reader pass, trusted production signing, final CI/security/code-owner/rollback/DR release evidence remain production/public release gates, not local-first blockers. Phase 2 live Neo4j is configured locally through ignored `.env`, seeded, and verified; SQL graph-node parity still depends on initializing the local SQL graph tables.

CI/security update, 2026-05-28: dependency-alert remediation and backend CI regression fixes are pushed to `main` in `edbf0127`. Local validation passed `python -m pytest -q` (`1717 passed, 21 skipped`), targeted ruff/py_compile checks, and the commit hook's ruff/frontend lint/frontend typecheck. GitHub Security Scan passed on `edbf0127`; CI/CD and Deploy were rerunning on that head when this document was updated.

| Item | Code validation | Status |
| --- | --- | --- |
| API gateway authentication | `backend/api_gateway/api_gateway.py` validates signed JWT bearer tokens, required expiration, optional issuer/audience, and optional roles. | Done |
| Migration-first deployment | `scripts/deploy.py` runs `python -m flask db upgrade` through Flask-Migrate/Alembic. | Done |
| Trusted proxy and host validation | `app.py` gates `ProxyFix` behind `TRUST_PROXY_HEADERS=true`, enforces `TRUSTED_HOSTS`, and no longer trusts raw `X-Forwarded-Proto` for HTTPS redirects. | Done |
| Multimodal upload hardening | `backend/routes/multimodal_routes.py` validates route-specific size, extension, content signatures, sanitized filenames, inferred MIME types, and normalized public errors before processing. | Done |
| Security scan API protection | `backend/security_scan_api.py` requires admin authentication on scan/compliance endpoints and normalizes public 500 errors. | Done |
| Legacy fallback secrets | `backend/__init__.py` keeps deterministic defaults under pytest only and fails fast outside tests when secrets are missing. | Done |
| Shell-based static copy | `scripts/deploy.py` copies static build artifacts with `pathlib`/`shutil` and no shell invocation. | Done |
| Strict runtime precheck | `python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process` passes with no blockers and no action items. | Done |
| Phase 1 gateway/model contract drift | `ChatSession.to_dict()` exists; API key expiration is modeled/enforced; gateway-created `TraceRun` rows set `user_id`; SDK version has a single `0.4.0` assignment. | Done |
| Phase 1 provider-backed staging | `scripts/validate_phase1_provider_staging.py` runs a live-provider Tier 2 gateway request with `IS_DESKTOP_APP=true` and verifies the audit footer plus a SQLite `TruthAuditEvent` row. | Done |
| Phase 1 installer smoke | `scripts/windows/run_packaging_smoke.ps1 -Mode installer` verifies packaged portable launch plus silent installer/uninstaller behavior; Electron source sets desktop mode and the per-user SQLite database path. | Done |
| Phase 1 local-first closure | `reports/release-readiness/local-first-phase1-completion-2026-05-25.md` separates completed local-first desktop gates from production/public release evidence gates. | Done |
| Phase 2 USKD memory graph implementation | `backend/storage/uskd_memory_graph.py`, `scripts/sync_nodes_to_neo4j.py`, `GraphStore` cached traversal helpers, TruthCore graph context bootstrap, Layer 2 live graph preference, L10 Lane B authorized graph commit, and `backend.spec` NetworkX hidden import are implemented and locally validated. | Done |
| Phase B axis alignment | Axes 14-17 now use the canonical Acquisition Lifecycle, Risk & Threat Context, Ethics/Trust/Criticality, and FROST-Mode Selector definitions across coordinate system, axis managers, SDK resolver, TraceRun, and tests. | Done |
| Phase 4 / DB-C Chroma wiring | `knowledge_nodes` collection naming is aligned; `scripts/index_knowledge_nodes.py` indexes SQL nodes; startup can background-index empty local desktop collections; `/health` and Electron IPC expose Chroma counts; L3/L8/L9/L10 use DB-C retrieval/indexing; persona_profiles cache path and sentence-transformers packaging are in place. | Done |
| Phase 5 / DB-R Redis TruthCache persistence | TruthCache supports Redis HSET/HGET persistence with memory fallback; TruthMemoryManager auto-selects Redis when `USE_REDIS=true`; GraphStore subgraph and RAG embedding caches can use Redis; `/health` and Electron IPC expose `redis_ping_ms`. | Done |
| Phase C Integration Bridge + LocalSLM | Gateway quad mode reaches `PodOrchestrator` and records pod status; TruthCore L5 constructs 7-part personas for axes 8-11 and uses pod expansion; KA-038, PersonaEnhancer, DRL refinement, JSON-safe weights, desktop LocalSLM fallback, and `quadAnalysisStatus` IPC are wired. | Done |
| Phase DB-P SQL historical reasoning calibration | L8 calibrates confidence thresholds from 90-day TraceRun history by risk domain; TruthSession stores local deterministic input embeddings; L9 returns `db_similar_sessions` historical drift baselines; KA execution timing is persisted and KA-036 reads p95 latency from the last 100 executions. | Done |

Remaining phase validation update: 2026-05-26

Next priority update: 2026-05-29. Phase H, KI local-first text-corpus ingestion, TV / Trace Viewer Wiring, the first KI productization slice, and hardened KI end-to-end validation evidence are implemented, validated, and pushed. The next local implementation priority is the remaining KI productization backlog: richer PDF/DOCX/binary extractors, standard corpus loaders, optional async background queue semantics, and optional SQL -> Neo4j sync evidence after ingestion. Production release evidence and manual store/release tasks can run in parallel, but they should not block KI productization unless the target is immediate public distribution.

| Remaining phase | Live-code validation | Status |
| --- | --- | --- |
| Phase D / DSQP | `docs/ip/dsqp_technical_disclosure.md`, `backend/dsqp/`, local templates, DSQP chain/registry/orchestrator/validator, PersonaConstructionService DSQP fallback, TruthCore L5 context wiring, KA-012 DSQP profiles, SDK `DSQPClient`, PyInstaller template datas, Electron DSQP IPC, desktop persona cards, DSQP benchmark/report, and provider-backed `dsqp_chain` audit evidence are implemented. | Done for D-1..D-12 code/test/evidence scope; broader production packaging smoke remains under release evidence. |
| Phase E / L10 KA suite | `backend/knowledge_algorithms/l10/l10_ka_001..007` modules expose `.run` callables; `ka_registry.yaml` points at importable functions; KA-116 delegates entropy scoring to L10-KA-001; KA-014, KA-023, KA-002, and KA-022 have deterministic depth implementations; L10 modules are included in PyInstaller collection and covered by focused tests. | Done for E-0..E-14 code/test scope; broader production packaging smoke remains under release evidence. |
| DB-O / Object store + blockchain | `TruthAuditEvent` now has queryable object-store and anchor fields; `TruthMemoryCommitService` writes audit bundles to `audit_logs`, records object references, computes Merkle roots, and anchors Tier 3+ runs through BlockchainAdapter with local simulated anchors when no node/key is configured. `FROSTService` persists snapshots to `simulation_artifacts`, `DSQPChain` persists persona artifacts to `deliverables/dsqp`, and `/health` plus Electron `get-db-status` expose object-store bucket counts and byte totals. | Done for DB-O local-first desktop/VM scope. |
| DB-M / StructuredMemoryGraph | `backend/memory/unified_memory_service.py` wraps `StructuredMemoryGraph` with deterministic local embeddings, layer/persona namespacing, JSON persistence under `databases/memory/memory_graph.json`, recall/consolidation APIs, FROST branch checkpoints, and runtime stats. TruthCore recalls and writes memory for L1-L10 workflow steps, L10 Lane B records release-authorized knowledge into StructuredMemoryGraph, and `/health` plus Electron `get-db-status` expose memory counts/timestamps. | Done for DB-M local-first desktop/VM scope. |
| Phase F / DMRF | `backend/dmrf/` now contains the Python control-plane foundation: orchestrator/result models, 17-axis router, tier classifier, convergence/evidence policy, injection defense, TruthGate/TruthCore/TruthMemory/TruthLink adapters, Redis Streams publishing against the app-managed Redis service with in-memory fallback, FROST snapshots, DSQP persona construction, MLflow/local JSONL tracking, gateway `USE_DMRF` flag, Prometheus metrics, `dmrf-status` API/IPC, validation script, and focused integration tests. | Done for Phase F Python control-plane scope on the internal Windows app database model. Desktop and VM are treated as identical Windows app deployments; no external database source is required. Optional Rust F2 is not required unless VM profiling later shows a Python bottleneck. |
| Phase G / Enterprise integrations | G-A desktop-compatible scope is implemented: TruthMemory local MLflow/JSONL tracking, Rego policy file plus OPA subprocess/Python fallback evaluation in TruthGate, W3C PROV-JSON in TruthAuditEvent data, active MCP `sampling/createMessage`, MCP resource subscriptions with SSE stream route, and SDK v0.5.0 metadata with offline `DSQPClient` plus bundled taxonomy data. G-B optional VM enhancements are now implemented with TruthLink Redis Streams fallback, TruthMemory local retention archives, opt-in TruthGate enhanced screening, and ADR-0002 for PQ-gRPC research/no-go on desktop dependency. | Done for Phase G local-first desktop/VM scope. |
| Phase H / Desktop experience | H-1..H-15 local-first desktop scope is implemented: app-owned JRE setup/priority and installer resources; provider/local-model network status; signed Electron IPC for live reasoning progress and KA execution feed; trace panel active KA/persona confidence/FROST enrichment; detailed storage metrics; one-click backup archive; durable desktop offline queue/replay; DSQP and gateway LocalSLM audit metadata; backend health-gated splash startup and three-attempt restart recovery; PyInstaller desktop module inclusion; reproducible cold-start/packaging evidence in `reports/phase_h_desktop_evidence.json`. | Done for Phase H local-first desktop/VM scope. |
| KI / Knowledge ingestion | KI local-first scope is implemented: `backend/ingestion/` ingests supported local text files into chunk-level SQL `KnowledgeGraphNode` rows, scrubs prompt-injection markers, writes manifests, indexes chunks through existing `RAGService`/Chroma `knowledge_nodes`, exposes `POST /api/v1/ingestion/local`, adds `scripts/ingest_local_corpus.py`, surfaces citation metadata in RAG and TruthCore deep-research output, and records reproducible sample-corpus evidence in `reports/ki_ingestion_evidence.json`. KI productization slice 1 adds `/api/v1/ingestion/supported`, `/api/v1/ingestion/history`, and a Settings -> Knowledge UI for local path ingestion and manifest-backed history. The evidence script now validates extraction/scrubbing, chunking, SQL persistence/metadata, Chroma handoff, citation normalization, source-rendered context, and manifest output end to end. Richer PDF/DOCX/binary extractors, standard corpus loaders, async queue semantics, and SQL -> Neo4j sync evidence remain next enhancements. | Done for KI local-first text-corpus ingestion scope, productization slice 1, and end-to-end validation evidence; partly done for rich corpus/product workflow scope. |
| TV / Trace Viewer Wiring | `UKG_TraceViewer_Wiring_Plan_v3_1.docx` was reviewed against live code and completed locally. Gateway chat responses now expose structured trace links, `/api/v1/trace/runs/<run_id>/bundle` returns an aggregate bundle, chat messages show a lazy inline trace panel, trace-specific Socket.IO run rooms/events exist, trace serializers expose viewer aliases, and `/runs/view` consumes the same bundle contract. | Completed with local evidence in `reports/trace_viewer_wiring_evidence.json`; focused backend/frontend tests, typecheck, ruff, and docs reference validation pass. Browser smoke reached the local Next app but authenticated page rendering still requires backend/auth running on `127.0.0.1:5000`. |

### Next Work Queue

1. [x] KI-1: build the local-first knowledge ingestion package.
   - Evidence: `backend/ingestion/local_ingestion.py` discovers supported local text files, extracts/scrubs text, chunks through `RAGService`, creates chunk-level SQL `KnowledgeGraphNode` rows, dedupes by chunk hash, indexes Chroma `knowledge_nodes`, and writes JSON manifests.
   - Validation: `python -m pytest -q --no-cov tests\unit\test_ki_local_ingestion.py tests\unit\test_phase4_dbc.py::test_index_knowledge_nodes_indexes_sql_node_like_objects`.
2. [x] KI-2: add document ingestion CLI and API entrypoints.
   - Evidence: `scripts/ingest_local_corpus.py` runs ingestion under Flask app context; `POST /api/v1/ingestion/local` is registered through `routes/__init__.py` and path-scoped outside desktop mode.
   - Validation: route tests cover allowed local ingestion and path rejection outside `DATALOGIC_INGESTION_ROOT`.
3. [x] KI-3: connect ingestion evidence to trace/audit surfaces.
   - Evidence: `RAGService.search_documents()` now returns normalized `citation` objects from source metadata; `get_context_for_query(include_sources=True)` renders source/chunk labels; TruthCore deep-research output includes `citations` alongside RAG evidence.
   - Validation: focused RAG/TruthCore tests verify citation metadata from ingested corpus search results.
4. [x] KI-4: release evidence refresh after KI.
   - Evidence: `scripts/verify_ki_ingestion.py` creates a disposable sample corpus/database, ingests it, verifies SQL node creation, verifies indexing handoff, verifies search citation metadata, and writes `reports/ki_ingestion_evidence.json`.
   - Validation: KI tests, ruff, py_compile, docs reference validation, and the KI evidence script passed.
5. [x] KI-5: add Settings knowledge ingestion controls and manifest-backed history.
   - Evidence: `GET /api/v1/ingestion/supported`, `GET /api/v1/ingestion/history`, `frontend/components/settings/KnowledgeIngestionSettings.tsx`, and Settings -> Knowledge tab are implemented.
   - Validation: `python -m pytest -q --no-cov tests\unit\test_ki_local_ingestion.py`; `npm --prefix frontend test -- tests/unit/lib/api/ingestion.test.ts components/settings/KnowledgeIngestionSettings.test.tsx`; frontend typecheck passed.
6. [x] KI-6a: harden end-to-end KI ingestion validation evidence.
   - Evidence: `scripts/verify_ki_ingestion.py` now writes explicit checks for text extraction/scrubbing, chunking, SQL persistence and metadata, Chroma handoff, citation metadata, source-rendered context, and manifest output to `reports/ki_ingestion_evidence.json`.
   - Validation: `python scripts\verify_ki_ingestion.py`; `python -m ruff check scripts\verify_ki_ingestion.py`.
7. [x] KI-6b: add richer PDF/DOCX/binary extractors and standard corpus loaders.
   - Evidence: `LocalKnowledgeIngestionService` now supports `.pdf` and `.docx` files by delegating to the existing `DocumentProcessor` (pypdf + python-docx). Binary extensions are routed through `_extract_via_document_processor()` while text files continue through the existing UTF-8 fallback path. `SUPPORTED_EXTENSIONS` is the new union set; `SUPPORTED_TEXT_EXTENSIONS` is preserved for backward compatibility. `/api/v1/ingestion/supported` now returns `.pdf` and `.docx` in the extensions list.
   - Validation: `python -m pytest tests/unit/test_ki_local_ingestion.py` — all 14 tests pass including `test_pdf_file_ingestion_uses_document_processor`, `test_docx_file_ingestion_uses_document_processor`, `test_unsupported_binary_files_are_rejected`, `test_pdf_without_processor_rejects_gracefully`. Ruff clean.
8. [x] KI-7: add optional async/background ingestion queue semantics and SQL -> Neo4j sync evidence after ingestion.
   - Evidence: `ingest_path_async()` runs ingestion in a background `threading.Thread` with Flask app context, tracks status via a module-level dict, and optionally calls `scripts.sync_nodes_to_neo4j.sync()` post-ingestion. New routes: `POST /api/v1/ingestion/local/async` (returns 202 with `ingestion_id`), `GET /api/v1/ingestion/status/<ingestion_id>`. Frontend `KnowledgeIngestionSettings` adds async mode toggle with 2s polling and Neo4j sync toggle.
   - Validation: `test_async_ingestion_returns_id_and_completes`, `test_async_ingestion_status_route`, `test_async_route_starts_and_returns_202`, `test_neo4j_sync_called_on_async_with_flag` — all pass. Ruff clean.

### Trace Viewer Wiring Phased Update Plan

Source plan: `UKG_TraceViewer_Wiring_Plan_v3_1.docx` reviewed 2026-05-29 against live code.

Live-code baseline:

- Existing: `backend/tracing/api.py` exposes run, stage, evidence, claim, axis, persona, KA, policy, memory, metrics, export, replay, span, and log routes under `/api/v1/trace/runs*`.
- Existing: `frontend/lib/api/trace.ts`, `frontend/app/runs/page.tsx`, `frontend/app/runs/view/page.tsx`, `frontend/components/Chat/LiveTracePanel.tsx`, `frontend/components/Chat/MessageBubble.tsx`, and `frontend/components/Chat/ChatInterface.tsx`.
- Existing: `backend/websocket.py` initializes Socket.IO and supports generic room join/leave plus chat/simulation events.
- Gap: the DOCX assumes direct `/api/v1/trace/{run_id}` endpoints, but current live routes use `/api/v1/trace/runs/{run_id}` and related subroutes.
- Gap: `/api/v1/gateway/chat` currently returns `run_id` but not a structured `audit_trail` object with `complete_trace_url` and `download_url`.
- Gap: `MessageBubble` does not render an inline lazy-loaded trace panel for a specific assistant response.
- Gap: live WebSocket trace streaming needs trace-specific room join and `trace_stage_update` emissions after `TraceStage` writes.

| Phase | Scope | Local exit gate | Status |
| --- | --- | --- | --- |
| TV-0: Contract verification | Capture local Tier 2/Tier 3 gateway responses and trace route payloads; document exact live shapes for chat response, run detail, stages, evidence, personas, KAs, axes, and export. | A fixture report records current JSON contracts and mismatches from the DOCX assumptions. | Done: `scripts/verify_trace_viewer_wiring.py` writes `reports/trace_viewer_wiring_evidence.json` with gateway `audit_trail` links and aggregate bundle keys. |
| TV-1: Backend response and bundle contract | Add `audit_trail` to `/api/v1/gateway/chat`; add or document a single aggregate trace bundle shape that wraps run, stages, evidence, claims, personas, KAs, axes, policy, memory, and metrics; keep `/api/v1/trace/runs/*` canonical unless aliases are deliberately added. | Focused backend tests prove chat response contains `audit_trail.complete_trace_url`, `download_url`, and trace bundle data resolves for a generated/local fixture run. | Done: gateway chat includes `audit_trail`; `/api/v1/trace/runs/<run_id>/bundle` returns the aggregate contract; UUID route parsing and backend contract tests pass. |
| TV-2: Frontend trace types and API client | Expand `frontend/lib/api/trace.ts` and add typed trace interfaces for run bundle, stages, evidence, personas, KA invocations, axes, and export. | Frontend unit tests prove each API function unwraps the backend response shape and handles missing optional sections. | Done: `TraceBundle`, evidence, KA, persona, axis, stage, metrics, and audit-trail types are wired through `frontend/lib/api/trace.ts`; focused API tests pass. |
| TV-3: Inline chat trace panel | Thread `runId`/`auditTrail` through `ChatInterface` into `MessageBubble`; build an inline lazy-loaded TracePanel with summary, coordinate, FROST stages, personas, evidence, KA feed, refinement, and export affordance using the current design system. | Assistant messages with a trace run show a compact trace control; expanding it fetches the bundle only once and renders useful panels. | Done: `ChatInterface` threads `auditTrail`, `MessageBubble` renders `ChatTracePanel`, and the panel lazy-loads bundle data, streams live updates, links details, and exports traces. |
| TV-4: Runs explorer completion | Align `/runs` list/detail pages with the same typed trace bundle and add missing detail panels rather than relying on shallow run metadata. | `/runs` list and detail page render seeded/local trace fixture data, handle empty/error states, and pass frontend typecheck. | Done: `/runs/view` now consumes the aggregate bundle and renders stages, evidence, personas, KA feed, policy/memory counts, coordinates, metrics, and export. |
| TV-5: Evidence and persona depth | Validate or add serializer fields for evidence tier, source provenance, KA invoked, claims supported, persona positions, debate log, synthesis weights, and conflicts. | Backend tests prove evidence/persona APIs expose the fields used by the frontend panels without leaking unauthorized runs. | Done: `TraceEvidence`, `TracePersona`, `TraceStage`, and `TraceKAInvocation` serializers expose the viewer aliases used by frontend panels; backend contract tests validate them. |
| TV-6: Real-time trace streaming | Add trace-specific `join_run_room`/leave handling and emit `trace_stage_update` after `TraceStage` creation/update; add frontend hook for run-scoped live updates and a live badge. | WebSocket unit tests prove join + emit behavior; frontend tests prove streamed stage updates merge into panel state. | Done: trace run room join/leave, `trace_stage_update` emission, gateway stage emission, frontend `useTraceStream`, and socket tests are implemented. |
| TV-7: Validation and docs | Add trace viewer contract tests, frontend component tests, update API docs/TODO/master plan, and record local evidence. | Focused pytest, frontend unit/typecheck, docs reference validation, and trace viewer evidence report pass locally. | Done: pytest, Vitest, typecheck, ruff, docs validation, and evidence generation pass. Browser smoke was limited by auth/backend not running. |

### CI And Security Evidence

Latest update: 2026-05-28

- Security/dependency remediation: frontend `tmp` transitive dependency is pinned through npm overrides, Python lockfile `idna` is updated, `npm --prefix frontend audit --audit-level=moderate` reports zero vulnerabilities, and GitHub Dependabot open-alert query returns no open alerts.
- Deploy/CI remediation: strict runtime precheck accepts explicit in-memory SQLite for disposable CI/runtime checks; KA-116 bulk-contract input coercion accepts scalar claims; TruthGate OPA policy respects Axis 14 threshold overrides; DRL convergence no longer overwrites a recovered refinement confidence when refinement steps fail; expanded persona pod outputs expose lane-level pod summaries; SQLite DMRF audit tests disable foreign-key checks while dropping cyclic test tables.
- Validation: `python -m pytest -q` passed with `1717 passed, 21 skipped`; targeted ruff and py_compile checks passed; commit hook ran repository ruff plus frontend lint and typecheck successfully.
- GitHub status at documentation update: Security Scan passed for `edbf0127`; CI/CD Pipeline and Deploy were rerunning on `edbf0127`.

Phased update plan:

| Phase | Scope | TODO items | Exit gate |
| --- | --- | --- | --- |
| Phase 1: Stop production blockers | Fix gateway authentication and migration-first deployment; remove shell-based static copy while touching deploy flow. | 1, 2, 7 | Done: `python -m pytest -q --no-cov tests/unit/test_api_gateway_auth.py tests/unit/test_deploy_phase1.py`; `python -m ruff check backend/api_gateway/api_gateway.py scripts/deploy.py tests/unit/test_api_gateway_auth.py tests/unit/test_deploy_phase1.py`. |
| Phase 2: Harden request perimeter | Add trusted proxy/host validation and harden active multimodal upload routes. | 3, 4 | Done: `python -m pytest -q --no-cov tests/unit/test_phase2_request_perimeter.py`; `python -m ruff check app.py backend/routes/multimodal_routes.py tests/unit/test_phase2_request_perimeter.py`. |
| Phase 3: Remove latent unsafe surfaces | Protect or remove security scan API and remove insecure legacy factory defaults. | 5, 6 | Done: `python -m pytest -q --no-cov tests/integration_routes/test_uncovered_blueprints.py::test_security_scan_api_requires_admin tests/integration_routes/test_uncovered_blueprints.py::test_security_scan_api_endpoints tests/integration_routes/test_uncovered_blueprints.py::test_security_scan_api_error_paths tests/unit/test_models.py::test_create_legacy_app tests/unit/test_models.py::test_create_legacy_app_requires_secrets_outside_pytest`; `python -m ruff check backend/security_scan_api.py backend/__init__.py tests/integration_routes/test_uncovered_blueprints.py tests/unit/test_models.py`. |
| Phase 4: Release evidence refresh | Re-run strict runtime precheck after schema initialization and refresh release evidence/docs. | 8 | Done: `python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process`; `python scripts/verify_docs_references.py`. |

Priority order:

1. [x] Replace API gateway placeholder authentication with real token validation.
   - Evidence: `backend/api_gateway/api_gateway.py` now rejects unsigned placeholder tokens and validates signed JWT bearer tokens in `verify_token`.
   - Acceptance: JWT validation checks signature, expiration, optional issuer, optional audience, and optional authorization roles; negative tests cover missing, malformed, wrong-audience, and insufficient-role tokens.
2. [x] Replace production deployment `db.create_all()` behavior with migration-first deployment.
   - Evidence: `scripts/deploy.py` now runs `python -m flask db upgrade` in `run_database_migrations`.
   - Acceptance: production deploys run the migration system and fail when the migration command fails; `create_all()` remains reserved for disposable local/test bootstrap paths outside this deployment script.
3. [x] Add trusted proxy and host validation controls.
   - Evidence: `app.py` now gates proxy header trust behind `TRUST_PROXY_HEADERS=true`, validates request hosts against `TRUSTED_HOSTS`, and redirects HTTPS without trusting raw forwarded headers.
   - Acceptance: proxy header trust is environment-gated, trusted host/canonical-origin validation is enforced, and tests cover direct-backend requests with spoofed `Host`, `X-Forwarded-Host`, and `X-Forwarded-Proto`.
4. [x] Harden active multimodal upload routes.
   - Evidence: registered `/api/v1/multimodal/*` routes now validate uploads before processing and normalize public errors.
   - Acceptance: upload routes enforce per-route limits before processing, validate file type from content signatures, sanitize filenames, normalize public errors, and include abuse/rate-limit tests.
5. [x] Protect or remove the security scan API before any production registration.
   - Evidence: `backend/security_scan_api.py` now requires administrator authentication on scan/compliance endpoints.
   - Acceptance: endpoints require administrator auth if retained, unauthenticated/unauthorized tests assert `401`/`403`, and public errors do not expose internal exception details.
6. [x] Remove insecure fallback secrets from the legacy Flask app factory.
   - Evidence: `backend/__init__.py` now limits fallback secrets to pytest and raises outside tests when required secrets are missing.
   - Acceptance: defaults are pytest-only; non-test startup fails when required secrets are missing, or the factory is moved under test utilities.
7. [x] Replace shell-based static file copy in `scripts/deploy.py`.
   - Evidence: static collection now uses `pathlib` and `shutil`.
   - Acceptance: static collection no longer uses `cp -r`, `shell=True`, or shell glob behavior.
8. [x] Clear the strict runtime precheck action item and update release evidence.
   - Evidence: strict precheck now detects the Flask SQLite instance database path and passes with no action items.
   - Acceptance: ran the documented local schema initialization path, reran `python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process`, and updated release-readiness evidence with the passing output.

### Release Readiness

- [x] Finalize the in-app feature list used by `frontend/public/manifest.json`, `README.md`, and About pages. Current copy is conservative and aligned; manifest shortcuts now point to dashboard, chat, privacy controls, and provider settings.
- [x] Add or document keyboard navigation coverage across primary pages and modal/dialog workflows on the packaged Windows app.
- [ ] Production/public release only: execute NVDA screen reader compatibility checks on Windows using `reports/app-readiness/nvda-manual-checklist.md`.
- [ ] Production/public release only: provision a trusted production code-signing certificate in GitHub secrets and run `.github/workflows/release-installer-signing.yml` to produce signed release artifacts with signature reports.
- [ ] Production/public release only: prepare release checklist evidence: changelog entry, governance command output, CI/security scan review, artifact signing evidence, code-owner approval, rollback plan, and disaster recovery review. Local-first Phase 1 closure is documented in `reports/release-readiness/local-first-phase1-completion-2026-05-25.md`.

### Product And UX

- [x] Decide whether `/register` remaining disabled is the intended local-first behavior or whether web self-registration should be reopened as a future web-mode feature. Decision: keep disabled for the current local-first desktop build; reopen only as a future web-mode product requirement.
- [x] Audit MCP and admin screens for live-data versus static metric placeholders and update any placeholder controls before release. Evidence: `reports/app-readiness/ui-placeholder-audit.md`.
- [x] Verify toolbar actions route by route and either wire, hide, or document placeholder-only actions. The graph toolbar now routes search/help/settings/history/profile actions and hides unsupported export/notification controls.
- [x] Add public architecture assets under `docs/assets/readme/` for the external README.
- [ ] Keep screenshots refreshed when primary UI changes.

### API, Contracts, And Documentation

- [ ] Tighten public API contracts, reduce legacy route aliases, and improve generated OpenAPI coverage.
- [x] Keep generated inventory docs (`docs/FILE_INVENTORY.csv`, `docs/GENERATED_STRUCTURE.md`) refreshed after repository cleanup/refactors.
- [ ] Expand CI docs enforcement to include markdown linting for active files.
- [ ] Keep vendor guidance baseline (`docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md`) reviewed at least monthly.
- [ ] Expand deployment reference material for Windows VM installation and the internal portable PostgreSQL, Redis, Neo4j, ChromaDB, object-store, and SQLite fallback stack.

### Runtime, Testing, And Operations

- [ ] Validate the simulation engine in a provider-backed staging environment.
- [ ] Expand comprehensive integration tests beyond current targeted route and readiness evidence.
- [ ] Configure production firewall rules and network security groups.
- [ ] Set up or document the production security incident response team.
- [x] Configure local desktop backup creation evidence for Phase H. Restore-drill automation remains a production operations item.
- [ ] Set up continuous security scanning review evidence for release.
- [ ] Set up performance benchmarking evidence.
- [ ] Configure compliance reporting automation.
- [ ] Document production blue-green deployment, disaster recovery, read-replica, and rollback procedures where applicable.
- [ ] Configure user analytics, usage tracking, A/B testing, feature flags, and chaos testing only if they remain product requirements for the target deployment.

### MCP And Connector Roadmap

- [x] Reconcile `docs/MCP_INTEGRATION.md` future items against implemented connector/OAuth/metrics work and close stale entries.
- [ ] Add MCP sampling support for LLM completions if still required.
- [ ] Add advanced MCP resource subscriptions and real-time update notifications.
- [ ] Add external/remote MCP server connection management.
- [ ] Add dynamic MCP plugin discovery and loading.
- [ ] Validate production connector operation against real external systems.

### Long-Term Research And Platform Roadmap

- [ ] Evaluate mobile applications only if mobile becomes a product requirement; historical research is retained in `docs/archive/research/REACT_NATIVE_RESEARCH.md`.
- [ ] Evaluate local SLM/model serving for L1/L2 tasks.
- [ ] Add multi-language/i18n support if required by target users.
- [ ] Expand richer user-facing trace and compliance overlay UX.
- [ ] Validate production-scale enterprise ingestion and vector-store workflows.
- [x] Phase 4 / DB-C: align RAG `knowledge_nodes` collection naming, add `scripts/index_knowledge_nodes.py`, wire startup empty-index detection, connect Chroma retrieval to TruthCore L3/L8/L9/L10, add local/offline embedding packaging, and expose Chroma collection counts through health/IPC.
- [x] Phase 5 / DB-R: implement Redis-backed TruthCache persistence, Redis subgraph cache, Redis embedding cache, TruthMemoryManager Redis selection, and Redis ping latency in health/IPC.
- [x] Phase C: wire quad-persona `PodOrchestrator`, L5 7-part persona construction, dynamic weighted synthesis, DRL convergence, desktop LocalSLM fallback, and quad analysis IPC status.
- [x] Phase DB-P: implement SQL historical reasoning calibration with TraceRun threshold history, TruthSession input embeddings, L9 DB similarity baselines, KAExecution timing persistence, and KA-036 p95 latency estimation.
- [x] Phase D prerequisite: write the DSQP technical disclosure before implementing the DSQP Protocol code.
- [x] Phase D first slice: write DSQP technical disclosure, implement offline deterministic DSQP chain/registry/orchestrator/validator, wire PersonaConstructionService and KA-012 to DSQP, expose SDK `DSQPClient`, and include templates in PyInstaller datas.
- [x] Phase E first slice: repair L10 registry/import shape, add executable L10-KA-001..007 modules, and route KA-116 entropy scoring through L10-KA-001.
- [x] Phase D follow-up: expose DSQP persona profiles through backend/Electron IPC, render desktop persona cards, and add deterministic 18-question DSQP benchmark report.
- [x] Phase E follow-up: complete E-9..E-14 with KA-014 domain calibration, KA-023 domain lambdas, KA-002 deterministic 3-branch BFS decomposition, KA-022 six-dimensional Axis 15 risk schema, PyInstaller L10 collection, and focused tests.
- [x] Phase D live evidence: provider-backed end-to-end flow confirmed `dsqp_chain` appears in persisted audit events via `reports/dsqp_provider_audit_report.json`.
- [x] Phase F first slice: implement DMRF Python control-plane package with 17-axis routing, tier classification, convergence/evidence policy, injection defense, DSQP/FROST wiring, Truth subsystem adapters, optional gateway flag, desktop status IPC, and focused tests.
- [x] Phase F completion: add DMRF Redis Streams-compatible TruthLink publishing, MLflow/local tracking, Prometheus metrics, SQLite audit persistence evidence, standalone validation report, and Rust F2 no-build decision based on current Python timing.
- [x] Cross-phase VM/database correction: audit previous DB-N/DB-C/DB-R/DB-O/Phase F/G/H planning and storage runtime paths for external-database assumptions; enforce internal app-owned database selection in `ConnectionManager`, `VectorStore`, and `ObjectStore`; update deployment/security/architecture docs to define Windows VM as the same Windows app stack.
- [x] DB-O first slice: add TruthAuditEvent object-store/blockchain fields, write TruthMemory audit bundles to `audit_logs`, compute Merkle roots, and anchor Tier 3+ audit events with local simulated blockchain receipts when no node/key is configured.
- [x] DB-O completion: persist FROST snapshots to `simulation_artifacts`, DSQP construction outputs to `deliverables/dsqp`, and object-store bucket counts/byte totals through `/health` and Electron `get-db-status`.
- [x] DB-M completion: add `UnifiedMemoryService`, persist StructuredMemoryGraph to `databases/memory/memory_graph.json`, wire TruthCore L1-L10 memory recall/consolidation, L10 Lane B memory commits, FROST memory checkpoints, and memory stats through `/health` plus Electron `get-db-status`.
- [x] Phase G-A completion: add local TruthMemory MLflow/JSONL tracking, TruthGate OPA/Rego policy evaluation fallback, W3C PROV-JSON audit records, active MCP sampling and resource subscription SSE, and SDK v0.5.0 offline DSQP/coordinate resolver packaging.
- [x] Phase G-B completion: add optional TruthLink Redis Streams XADD/XREAD, TruthMemory 7-year local archive routing, opt-in TruthGate enhanced model screening fallback, and ADR-0002 documenting PQ-gRPC as VM-only research with no desktop dependency.
- [x] Phase H first slice: add Eclipse Temurin JRE 17 setup/bundling path, prioritize `databases/jre` for Neo4j, add backend network status + Electron IPC/local model status, gate desktop window creation on `/health`, and restart backend up to three times on unexpected exit.
- [x] Phase H completion: implement desktop offline queue/replay, LocalSLM audit metadata, dedicated live reasoning/KA IPC feeds, trace panel active KA/persona confidence/FROST enrichment, detailed settings database metrics, one-click backup flow, PyInstaller desktop-module inclusion, and reproducible cold-start/packaging evidence.
- [ ] Validate production alerting evidence for `/health`, `/live`, `/ready`, `/metrics`, Sentry, and admin dashboards.
- [ ] Harden multi-tenant operations, cost controls, recursive persona evaluation, dynamic persona expansion, human feedback loops, automated axis learning, quantum-ready node research, and policy-as-code governance for larger deployments.

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
| Authenticated WCAG 2.1 A/AA route evidence | `frontend/scripts/run-a11y-ci.mjs`, `reports/app-readiness/a11y-ci-report.json` |
| Failure-mode/export-delete Playwright evidence | `frontend/tests/e2e/app-readiness-evidence.spec.ts`, `reports/app-readiness/playwright-app-readiness-report.json` |
| Keyboard navigation evidence | `frontend/tests/e2e/keyboard-navigation-evidence.spec.ts`, `reports/app-readiness/keyboard-navigation-report.json` |
| NVDA manual screen reader checklist | `reports/app-readiness/nvda-manual-checklist.md` |
| UI placeholder audit | `reports/app-readiness/ui-placeholder-audit.md` |
| Local release evidence | `reports/release-readiness/local-release-evidence-2026-05-23.md` |
| Conservative copy/disclosure pass | `frontend/public/manifest.json`, `frontend/app/about/page.tsx`, `frontend/app/about/ai-limitations/page.tsx`, `frontend/app/about/cloud-services/page.tsx`, `frontend/app/legal/privacy/page.tsx`, `frontend/components/Chat/ChatInterface.tsx`, `frontend/components/settings/AiModelSettings.tsx`, `frontend/components/CloudDisclosureBanner.tsx`, `docs/PRIVACY_POLICY.md` |

## Documentation Cleanup Policy

- Keep current planning in this file only.
- Keep release go/no-go criteria in `docs/RELEASE_CHECKLIST.md`.
- Keep active documentation discoverable from `README.md` and `docs/README.md`.
- Do not add new `PROJECT.md`, `ROADMAP.md`, `current_plan.md`, assessment TODOs, or archived planning summaries without first folding actionable items into this file.
