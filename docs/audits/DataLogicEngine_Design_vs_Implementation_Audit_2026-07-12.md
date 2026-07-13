# DataLogicEngine Design vs. Implementation Audit

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.0.0 |
| Review date | 2026-07-12 |
| Status | Active production-readiness audit |
| Scope | Repository-wide design, implementation, integration, security-boundary, desktop-runtime, and test review |
| Source-of-truth baseline | Root active documents, `docs/README.md`, active architecture/product/operations documents, and root `TODO.md` |
| Historical material | `docs/archive/**` and whitepapers were treated as supporting context, not current implementation authority |

## Executive verdict

**DataLogicEngine is a substantial working prototype and engineering platform, but it is not yet complete as the product described by the active documentation and is not ready for a production or public release.**

The desktop shell, Flask API, signed Electron request authentication, provider-key storage, chat sessions, Google/OpenAI invocation, trace persistence, local ingestion, knowledge-algorithm registry, MCP framework, and large automated test suite are real. The central product claim, however, is not yet true end to end: normal chat does not execute the documented DMRF -> TruthCore -> evidence/convergence -> provider/tool -> validation/refinement -> memory/trace lifecycle.

The installed chat path currently performs DMRF gating/routing and DSQP persona construction, records a TruthCore *plan*, then runs a much thinner SDK overlay. That overlay executes a small KA subset and sends the original query to one cloud model. Retrieved RAG context, DSQP persona outputs, the TruthCore workflow plan, claims, evidence, and convergence decision are not incorporated into the final model prompt or used to validate the answer. Several resulting trace values therefore describe planned or synthetic governance activity rather than the causal path that produced the answer.

Two conclusions follow:

1. The application can be used today as a local desktop AI client with experimental governance telemetry.
2. It must not yet be represented as a production-grade governed reasoning engine whose answers have passed the documented evidence, persona, convergence, refinement, and TruthCore controls.

## Release recommendation

| Release target | Decision | Reason |
|---|---|---|
| Developer/local evaluation | Conditional go | Core UI, provider calls, persistence, ingestion, and tests work; limitations must remain explicit. |
| Internal pilot with non-sensitive data | Conditional go after P0 security closure | Requires authenticated route closure, telemetry labeling, provider-call controls, and a constrained acceptance plan. |
| Production/public release | **No-go** | The governed data path is incomplete, network-facing mutations have authentication gaps, storage/runtime claims do not match the installer, several UI controls are nonfunctional, and trusted signing/migration evidence remains open. |

## Review method and coverage

This review used five evidence layers:

1. Read the root active documentation and all active/reference material under `docs/`, applying the authority hierarchy in `docs/README.md`.
2. Inventoried the complete tracked repository and statically scanned all authored code/configuration areas.
3. Deep-traced active execution paths for startup, desktop authentication, chat, providers, DMRF, DSQP, TruthCore, KAs, tracing, retrieval, storage, knowledge/graph, ingestion, simulations, MCP, compliance, frontend workflows, Electron IPC, packaging, and migrations.
4. Compared frontend API calls and controls with backend routes and runtime behavior.
5. Ran the repository's backend, frontend, environment, runtime, and documentation checks.

Repository scale at review time:

| Measure | Count |
|---|---:|
| Tracked files | 1,634 |
| Tracked code/config files | 1,304 |
| Python files | 797 |
| TSX files | 208 |
| TypeScript files | 58 |
| Test-related files | 283 |
| Backend route declarations found | 303 |
| Knowledge Algorithm registry entries | 125 |
| Versioned migration files | 11 |

Generated installer/package contents and third-party dependency internals were inventoried and sampled for packaging truth, but were not treated as authored source requiring line-by-line design review. All tracked Python files parsed successfully during the static inventory.

## Intended architecture

The active documents describe this governed lifecycle:

```text
Electron/Next UI
  -> Flask API security boundary
  -> DMRF InjectionDefense
  -> TruthGate
  -> tier classification
  -> 17-axis routing
  -> DSQP personas (axes 8-11)
  -> TruthCore workflow execution
  -> local retrieval / graph / memory context
  -> configured provider or governed MCP tool
  -> evidence and claim validation
  -> convergence / refinement decision
  -> TruthMemory, artifacts, audit, and TruthLink
  -> trace review and export
```

Primary design references:

- `docs/WORKFLOW.md:49-62`
- `docs/DATA_FLOW_DIAGRAMS.md:88-114`
- `docs/DECISION_LOGIC.md:287-329`
- `docs/PRODUCT_DESIGN.md:68-75`
- `docs/ARCHITECTURE.md:169-190`

## Actual normal-chat architecture

The active implementation is closer to this:

```text
Electron/Next chat
  -> signed/session-authenticated Flask gateway
  -> DMRF InjectionDefense and TruthGate
  -> heuristic tier and fixed 17-axis route
  -> four DSQP persona-construction calls (cloud-assisted by default)
  -> record TruthCore workflow step names only
  -> compute freshness from one optional timestamp
  -> compute a one-time should-refine flag
  -> SDK overlay
       -> KA-061, KA-004, KA-005, KA-113
       -> optional KA-001
       -> one provider call using coordinate + tier + original query
       -> KA-056 explanation template
  -> persist trace/telemetry and answer
```

The key implementation evidence is:

- DMRF requests only workflow step names from TruthCore: `backend/dmrf/truth_integration/core_adapter.py:10-17`.
- DMRF records the plan, scores one synthetic freshness input, and evaluates convergence once at iteration zero: `backend/dmrf/orchestrator.py:101-143`.
- The SDK overlay's final prompt contains coordinate, tier, and the original query, but not RAG context, DSQP output, evidence, claims, or the TruthCore plan: `SDK/UKG_Python_SDK/ukg_sdk/overlay.py:139-180`.
- The overlay returns the provider text immediately after one explanation-template KA: `SDK/UKG_Python_SDK/ukg_sdk/overlay.py:180-197`.

## Capability matrix

| Area | Designed idea | What is built | Assessment |
|---|---|---|---|
| Desktop shell | Local-first Windows Electron product | Electron shell, static Next export, PyInstaller backend, NSIS packaging, signed loopback requests | Substantial and functional |
| Identity/security | Single-owner desktop trust plus protected API | Strong signed desktop request path and CSRF/session controls where decorators are applied | Partial; route coverage has critical gaps |
| Provider access | One selected OpenAI or Google model | DB-first encrypted keys, environment fallback, provider test, retries/circuit behavior | Functional with async/timeout and catalog drift |
| Governed chat | DMRF + TruthCore + evidence/convergence around model output | DMRF telemetry plus thin SDK overlay and one final model call | Major design gap |
| DMRF | Control plane for gate, route, evidence, convergence, persistence | Gate/router/personas/telemetry implemented; TruthCore execution and refinement loop absent | Partial |
| DSQP | Personas influence reasoning and validation | Four structured personas generated; generally stored in trace but not used in final answer | Implemented but disconnected |
| TruthCore | Execute tier-specific L1-L10 workflow | Large standalone engine and API exist; normal chat receives only its planned step names | Substantial isolated subsystem, not integrated |
| Knowledge Algorithms | 125 governed algorithms | All 125 registry targets exist; depth ranges from useful deterministic utilities to templates/heuristics | Broad but uneven |
| Evidence/claims | Answer grounded in retrieved evidence and validated claims | Tables and trace schemas exist; normal answer path usually creates no causal evidence/claim records | Mostly telemetry/schema |
| RAG | Local knowledge and memory affect answers | Retrieval and ingestion work; retrieved chat context is passed in metadata but omitted from final prompt | Implemented but disconnected from normal answer |
| Trace Explorer | Explain how an answer was produced | Run/stage/persona/axis persistence and exports are real | Functional, but some semantics are synthetic |
| Storage | App-owned SQL, graph, vector, cache, object, and memory stores | Packaged default is SQLite + local files/Chroma; Redis/PostgreSQL/Neo4j binaries are not bundled | Partial; UI/docs overstate installed runtime |
| Knowledge graph | SQL/Neo4j/USKD graph reasoning | SQL-backed nodes and in-memory USKD fallback work; Neo4j is optional and absent from installer | Partial |
| Ingestion | Local PDF/DOCX/text ingestion into graph/vector stores | Authenticated sync/async ingestion, chunking, hashing, manifests, SQL nodes, optional Chroma/Neo4j | Functional with operational limits |
| Simulations | FROST multi-layer, observable simulations | User route runs a separate multi-agent debate engine through repeated gateway calls | Different implementation than product language |
| MCP | Governed connector/tool ecosystem | JSON-RPC router, registry, scopes, stdio client, UI, metrics, and config exist | Partial; key default tools/resources are placeholders |
| Compliance | Evidence-backed controls and reporting | Standards hierarchy, audit export, report generator, and multiple heuristic compliance engines | Partial; UI/status wording can overclaim |
| Frontend workflows | Complete operational desktop UI | Main navigation and many data surfaces work | Several visible controls are no-ops or misleading |
| Updates/releases | Trusted install/update lifecycle | Rebuild and NSIS flow work | Unsigned; update signature verification disabled |

## Findings

### P0-1: Normal chat does not execute the documented governed reasoning lifecycle

The DMRF adapter instantiates `TruthCoreEngine` but calls only `get_workflow_steps()`. It never creates or processes a TruthCore session. The SDK overlay then executes a small KA sequence and sends a minimal prompt to the model.

Evidence:

- `backend/dmrf/truth_integration/core_adapter.py:10-17`
- `backend/dmrf/orchestrator.py:117-131`
- `backend/llm_gateway/gateway.py:747-811`
- `SDK/UKG_Python_SDK/ukg_sdk/overlay.py:107-180`
- `backend/truth_engine/truth_core/engine.py:290-324`

Impact:

- Trace stages can imply TruthCore, evidence, convergence, and persona governance that did not influence the answer.
- Product documentation and UI labels overstate the causal guarantees of a response.
- The primary differentiator of the product is not yet delivered on the primary user path.

Required correction:

Create one canonical governed orchestrator. It must execute TruthCore, inject retrieval/persona context before the provider call, validate claims/evidence after the call, run bounded refinement when required, and persist only stages that actually executed.

### P0-2: Active unauthenticated mutation routes bypass the intended API boundary

The active application registers legacy Truth Engine, pillar, method, and GraphQL endpoints without an authentication decorator. At least 17 mutation handlers are affected:

- Truth Engine: session creation/processing, gate evaluation/reset, artifact storage, and link publication in `backend/truth_engine/api.py:203-205`, `245-247`, `288-290`, `316-318`, `349-351`, and `396-398`.
- Pillars: create pillar/sublevel/mapping, analyze text, expand, and export in `backend/pillar_api.py:51-53`, `85-87`, `151-153`, `188-190`, `207-209`, and `229-231`.
- Methods: cross-sector/cross-pillar processing, method creation, and hierarchy creation in `backend/methods_api.py:99-100`, `141-142`, `183-184`, and `232-233`.
- GraphQL mutation endpoint: `backend/graphql_schema.py:239-258` and `301-303`.

`require_truth_engine` initializes the subsystem but does not authenticate the caller. This remains a production blocker even if the desktop normally binds to loopback because the documented Windows VM/API gateway mode is network-facing and any local process can reach loopback.

Required correction:

Apply the canonical session/API-key decorators to every active route, require admin authorization for state-changing governance operations, add route-inventory tests that fail on unclassified mutations, and remove or explicitly isolate legacy aliases.

### P0-3: GraphQL and several compliance routes still expose exception text

GraphQL returns raw mutation exceptions and execution errors to callers (`backend/graphql_schema.py:256-258`, `286-292`). Compliance reads also include `str(e)` in public JSON (`backend/routes/compliance_routes.py:55-60`, `161-167`, `184-190`).

This conflicts with the repository's recent CodeQL exception-disclosure hardening and can expose paths, database messages, provider details, or internal types.

Required correction:

Normalize all public errors, retain detailed exceptions only in structured server logs, and add a repository-wide response-sink regression test rather than repairing alerts one file at a time.

### P1-1: DMRF evidence and convergence are synthetic and do not control execution

`EvidenceModel` receives only `evidence_observed_at`; no evidence item, claim, source, provenance, or quality signal is scored. Missing timestamps become age zero and therefore perfect freshness (`backend/dmrf/evidence_model.py:19-44`). Convergence is evaluated once with router confidence at iteration zero, and its `should_refine` result is recorded but not acted on (`backend/dmrf/orchestrator.py:120-131`).

Trace persistence also substitutes `0.85` when no confidence exists (`backend/llm_gateway/gateway.py:1922-1932`). Dashboard and Truth Engine summaries can then present this value as if it were measured confidence.

Required correction:

Define an evidence/claim schema that is populated from retrieval and provider output, calculate confidence from explicit validators, execute the bounded refinement decision, and use `null/not measured` rather than a plausible default.

### P1-2: DSQP adds cloud cost and latency but usually does not affect the answer

DSQP runs axes 8-11 concurrently (`backend/dsqp/dsqp_orchestrator.py:32-59`). Cloud assistance is enabled by default and performs one selected-provider request per axis (`backend/dsqp/dsqp_answer_generator.py:81-129`). The resulting personas are attached to trace metadata, but the SDK overlay's final prompt does not include them (`SDK/UKG_Python_SDK/ukg_sdk/overlay.py:150-180`).

A normal enhanced chat can therefore perform four DSQP provider calls, an optional defense-supervisor call, and the final answer call while only the last response affects the answer. This explains observed 45-second latency and creates avoidable provider spend and data disclosure.

Required correction:

Use deterministic DSQP construction by default, or incorporate validated persona contributions into the actual prompt/decision. Record exact provider-call count, latency, and cost per run. Do not label cloud-generated metadata as `LOCAL_MODEL` (`backend/dsqp/dsqp_chain.py:179-201`).

### P1-3: Retrieved local knowledge is not used by normal chat

The gateway retrieves document and prior-chat context and places it into `meta.rag_context` (`backend/llm_gateway/gateway.py:747-792`). The overlay ignores that field when creating the final prompt (`SDK/UKG_Python_SDK/ukg_sdk/overlay.py:169-180`).

Additional retrieval risks:

- Embedding providers can produce incompatible dimensions across OpenAI, Google, local sentence-transformer, and mock modes in `backend/services/rag_service.py`.
- RAG key selection reads environment keys rather than the encrypted provider record used by chat.
- A local sentence-transformer fallback may download or load a local model despite current user-facing documentation saying inference uses only OpenAI or Google.

Required correction:

Make retrieval an explicit step in the canonical orchestrator, maintain dimension/version metadata per collection, rebuild incompatible collections safely, use the active encrypted provider configuration, and disclose any embedding-provider data movement independently of answer-model selection.

### P1-4: Async provider methods perform blocking synchronous network calls

Both primary provider adapters expose `async def complete()` but call synchronous SDK clients directly:

- Google: `SDK/UKG_Python_SDK/ukg_sdk/providers/google.py:36-82`
- OpenAI: `SDK/UKG_Python_SDK/ukg_sdk/providers/openai.py:46-87`

The gateway wraps the coroutine in `asyncio.wait_for()` (`backend/llm_gateway/gateway.py:821-824`), but a synchronous call that blocks the event-loop thread cannot be reliably interrupted by that timeout. Google has no explicit client timeout in this adapter. OpenAI retries can further multiply latency.

The streaming API is also simulated: it waits for the complete response and then emits 256-character slices (`backend/llm_gateway/gateway.py:1099-1136`).

Required correction:

Use the providers' async clients or run sync SDK calls in a bounded worker, apply one end-to-end deadline across DSQP/defense/final calls, support cancellation, and label the current endpoint as buffered chunking until native streaming is implemented.

### P1-5: Packaged storage behavior does not match the storage UI or active documents

The installer bundles the backend, scripts, and policies, but no PostgreSQL, Redis, or Neo4j binaries (`frontend/electron-builder.yml:7-23`). Electron configures the packaged backend to use SQLite (`frontend/electron/main.ts:737-757`). The lifecycle manager silently skips absent database directories and returns no result (`backend/storage/database_manager.py:231-245`), while the API always returns “Database startup initiated” (`backend/routes/storage_routes.py:590-603`).

Other concrete defects:

- `get_db_manager()` returns a new manager on every call, so a stop request usually has no process handles for services started by a previous instance (`backend/storage/database_manager.py:247-277`; `backend/routes/storage_routes.py:704-717`).
- The UI requires PostgreSQL, Redis, Neo4j, vector, and object-store health even though packaged desktop SQL is SQLite.
- Electron reports `managed` if the backend health endpoint says only SQL is okay, and also returns `managed` on fetch failure (`frontend/electron/main.ts:845-873`).
- Local port/path fields are uncontrolled `defaultValue` inputs and are not persisted (`frontend/components/settings/DatabaseSettings.tsx:574-587`).
- Cloud credentials are stored in plaintext runtime `settings.json` and no connection manager consumes `cloud_config` after save (`backend/routes/storage_routes.py:661-701`).
- Desktop backup includes SQLite, Chroma, object, and memory data but omits Neo4j (`backend/routes/storage_routes.py:138-174`).

Required correction:

Choose and document one desktop data-plane contract. If SQLite/Chroma/files are the default, make the UI and readiness checks reflect it. Treat Redis/Neo4j/PostgreSQL as explicit optional profiles. Use one process-lifetime lifecycle manager, return per-service outcomes, encrypt or remove dead cloud configuration, and implement backup/restore parity for every enabled store.

### P1-6: Desktop schema evolution is not migration-safe

The packaged backend sets `AUTO_CREATE_SCHEMA=true` (`frontend/electron/main.ts:749-753`). `db.create_all()` creates missing tables but does not migrate existing tables (`app.py:638-672`). The only desktop upgrade helper adds a fixed set of TraceRun columns (`backend/desktop/schema_upgrade.py:8-42`). The uninstaller intentionally retains AppData (`frontend/electron-builder.yml:30-40`), so old schemas survive reinstall.

Required correction:

Run a versioned, transactional SQLite migration chain before backend readiness. Back up the database, record schema version, test upgrades from every supported installed version, and provide rollback/recovery instructions.

### P1-7: User-facing simulations are a different and potentially very expensive system

The simulation page invokes `backend/simulation/multi_agent_engine.py`, not the large FROST implementation under `core/simulation`. Standard mode performs three debate calls plus synthesis, with an additional context call in the surrounding flow. Every call sets `run_ukg_pipeline=True` (`backend/simulation/multi_agent_engine.py:145-165`, `222-250`). Because each gateway call can itself run four DSQP calls plus defense/final inference, one simulation can generate roughly 25-30 provider requests.

The route blocks synchronously, increments one step, marks the simulation completed, and emits no simulation-progress websocket events (`backend/routes/simulation_routes.py:127-174`). The frontend nevertheless subscribes for live progress (`frontend/app/simulations/page.tsx:29-53`). Confidence is derived from debate-turn count, not evidence (`backend/simulation/multi_agent_engine.py:240-253`).

Required correction:

Select one simulation architecture, prevent recursive full-pipeline calls, define a provider-call budget, persist stepwise progress, emit the events the UI consumes, and derive confidence from validators rather than text/turn counts.

### P1-8: Visible governance and workflow controls are nonfunctional

Examples confirmed in active UI source:

- Advanced confidence threshold, reasoning-layer switches, context buttons, Save Preset, and Reset have no state/action wiring: `frontend/components/Chat/AdvancedControls.tsx:34-120`.
- Chat Export, Clear All, Settings, and status controls have no actions: `frontend/components/Chat/ChatInterface.tsx:445-469`.
- Validation Report and Share buttons have no actions: `frontend/components/Chat/DetailedResponseView.tsx:167-174`.
- Global Settings “Save Changes” has no action: `frontend/app/settings/page.tsx:145-154`.
- Project Upload, New Note, message Download/Delete/More have no actions: `frontend/components/projects/ProjectDetail.tsx:93-100`, `151-161`.
- Graph “View Full Details” has no action and the selected node is labeled “Compliance Passed” with a hardcoded NIST statement: `frontend/app/graph/page.tsx:322-334`.
- Dashboard shows a hardcoded `+12%` request trend: `frontend/app/dashboard/page.tsx:143-184`.

Required correction:

Remove or disable controls until implemented, then add end-to-end tests that assert the backend receives and enforces each governance setting. No control should imply a saved policy or completed compliance check based only on presentation state.

### P1-9: Readiness can be green while important subsystems are unavailable

Application readiness blocks only on SQL connectivity and the session secret (`app.py:999-1057`). Redis latency, Chroma counts, object-store state, memory state, graph availability, provider configuration, and trace persistence do not affect readiness. Electron waits on this weak health signal before opening the app and can independently return a healthy-looking managed state when its health fetch fails.

Required correction:

Publish separate liveness, core readiness, and feature-capability status. The UI should show which workflows are available and why, without treating optional stores as core blockers or treating failed checks as managed.

### P1-10: MCP scope enforcement can be bypassed on the JSON-RPC path

The authenticated REST tool-call route builds server-side execution context and fails closed (`backend/routes/mcp_routes.py:420-454`). The generic `/mcp/rpc` route passes the caller payload directly to `MCPRouter` (`backend/routes/mcp_routes.py:141-151`). The router accepts caller-supplied `params.context`, and the registry explicitly uses `permissive_on_missing_context=True` (`backend/mcp_server/registry.py:103-120`).

Default MCP resources/tools also contain scaffold behavior: hardcoded pillars, “algorithm execution” string formatting, and unavailable responses rather than real graph/KA execution (`core/mcp/mcp_manager.py:257-370`). MCP sampling returns a deterministic echo when no provider is injected (`backend/mcp_server/sampling.py`).

Required correction:

Build execution context from authenticated server state for every transport, reject caller-controlled identity/scope context, fail closed on missing scope context, and label or remove placeholder tools/resources.

### P2-1: Knowledge Algorithm breadth is real, but semantic depth is uneven

The registry contains 125 entries and every configured target exists. This is a real implementation asset. However, many KAs are thin deterministic keyword classifiers, templates, plan generators, or metadata calculators whose names imply stronger cognitive/analytical capability than they deliver.

Examples observed:

- KA-009 can treat an empty evidence set as valid/neutral rather than proving support.
- KA-012 returns templated persona prose and uses random confidence.
- KA-018 computes provenance trust from configured base values and chain length, not independent source verification.
- KA-056 narrates a decision log; it does not explain model internals.
- KA-008, KA-012, and KA-028 include random behavior that weakens deterministic replay.

The broad KA suite mainly proves importability and dictionary-shaped output; selected targeted tests provide stronger checks but do not establish scientific validity for every named algorithm.

Required correction:

Classify KAs as production validator, deterministic heuristic, experimental method, or placeholder. Define evidence-backed acceptance tests per category, remove random outputs from governed paths, and show users which KAs actually executed and what guarantees each provides.

### P2-2: TruthCore is substantial but internally contains scaffold/default behavior

The standalone TruthCore engine includes tier workflows, memory, graph context, personas, L6-L10 services, and refinement (`backend/truth_engine/truth_core/engine.py`). It is more than a stub. Its active behavior still has important limitations:

- `simulation_engine` is accepted and stored but not used (`backend/truth_engine/truth_core/engine.py:111-116`).
- Routing profiles retain unsupported `codestral` and `grok-4-fast` model names (`backend/truth_engine/truth_core/engine.py:35-59`).
- Several services default plausible confidence values such as 0.9 or 0.95 (`backend/truth_engine/truth_core/engine.py:671-676`, `699-726`).
- Final output is the last successful step, which can be a structural safety result rather than a provider-grounded answer (`backend/truth_engine/truth_core/engine.py:659-678`).
- The refinement controller often preserves content because most KAs do not return `refined_content`; its DRL convergence hashes the answer into a numeric vector rather than validating external truth (`backend/truth_engine/truth_core/refinement_orchestrator.py:102-150`).

Required correction:

Define TruthCore's exact input/output contract, remove stale model routing, require explicit validator outputs, and integrate it with the one canonical provider/retrieval path before calling the workflow production-ready.

### P2-3: Chat's offline queue hides non-network failures

All non-429 errors are queued or presented as potentially queued, including authentication, validation, policy, persistence, and internal server defects (`frontend/components/Chat/ChatInterface.tsx:232-278`; `backend/llm_gateway/api.py:336-374`). This previously made a provider-selection defect look like provider unavailability.

Required correction:

Queue only classified transient network/provider errors. Surface authentication, policy, validation, schema, and internal errors distinctly and preserve the public-safe correlation ID for diagnosis.

### P2-4: Startup is side-effect-heavy and ordered incorrectly

`app.py` creates and configures the global application at import time, registers optional subsystems with fail-soft imports, initializes Chroma/object storage and the graph, and only then starts optional local database processes (`app.py:90-125`, `683-800`, `803-981`). `create_app()` returns the existing global app rather than constructing an isolated instance (`app.py:1297-1317`).

Required correction:

Move to a real app factory with explicit startup phases: configuration -> schema migration -> required services -> stores/graph -> routes -> readiness. Record optional feature failures in capability state rather than only logs.

### P2-5: Provider and deployment contracts are internally inconsistent

Active user docs expose only OpenAI and Google, but the gateway still creates Azure and Anthropic adapters and defaults unknown providers to OpenAI-compatible (`backend/llm_gateway/gateway.py:1138-1206`). The Google SDK adapter still defaults to `gemini-2.5-pro` when called without an explicit model (`SDK/UKG_Python_SDK/ukg_sdk/providers/google.py:21-34`). Electron still probes Ollama on port 11434 (`frontend/electron/main.ts:976-990`).

The root Python package is version `0.1.0`, the frontend is `0.1.1`, active docs are `v2.14.x`, and the UI/installer uses separate product-version language. `pyproject.toml` is only a partial dependency declaration while `requirements.txt` is authoritative.

Required correction:

Remove unsupported provider/runtime branches or formally restore them to product scope, centralize model/version metadata, and define one authoritative dependency/package version strategy.

### P2-6: Local ingestion works but has bounded governance

Strengths include authentication, file-size/type controls, deterministic hashes, chunk manifests, SQL persistence, optional vector indexing, and optional Neo4j sync (`backend/routes/ingestion_routes.py`; `backend/ingestion/local_ingestion.py`). Limitations:

- Desktop mode accepts any local path by design (`backend/routes/ingestion_routes.py:18-31`), so a compromised renderer has broad read reach under the user's account.
- Prompt-injection scrubbing is a short regex list, not the DMRF defense path (`backend/ingestion/local_ingestion.py:24-34`, `301-314`).
- Async state is process-memory only and disappears on restart (`backend/ingestion/local_ingestion.py:32-34`, `342-418`).
- SQL rows can commit even when vector indexing fails, creating partial corpus state.

Required correction:

Use an Electron file/folder picker capability token, run ingested content through the canonical defense policy, persist jobs and per-chunk indexing state, and provide retry/reconciliation controls.

### P2-7: Compliance status is not equivalent to certification or verified conformance

Compliance managers and reports are useful internal control/evidence tools, but several scores are heuristic or derive from available logs and confidence values. The frontend labels every returned standard “Active” and describes “live monitoring” (`frontend/app/admin/compliance/page.tsx`), while the graph shows hardcoded passed status for a selected node.

Required correction:

Label outputs as control checks, mappings, or self-assessment evidence. Require source records for pass/fail status and avoid NIST/SOC 2/HIPAA conformance language unless the exact control evidence exists.

### P2-8: Exception-heavy fail-soft behavior reduces diagnostic and test certainty

The tracked Python inventory found more than one thousand broad `except Exception` handlers. Some are appropriate at process or optional-integration boundaries, but many silently convert implementation errors into skipped features, empty results, fabricated defaults, or “unavailable” states. This is a major reason tests can pass while the integrated product path is degraded.

The repository also contains a circular-dependency checker that prints a success result without performing a real dependency analysis (`scripts/check_circular_deps.py`).

Required correction:

Define fail-closed versus fail-soft boundaries, replace broad catches in core logic with typed failures, emit structured capability state, and ensure every release check performs the analysis its name claims.

## What is already strong

The following should be retained and built upon:

1. **Desktop request security:** Electron signs loopback requests, the backend validates desktop signatures, and session mutations include CSRF/origin protections where canonical decorators are used.
2. **Provider credential storage:** Provider keys are Fernet-encrypted in SQL and the UI distinguishes saved keys from provider validation.
3. **Local data primitives:** SQLite, Chroma, filesystem object storage, structured memory, SQL knowledge nodes, and USKD in-memory graph fallback provide a viable default desktop data plane.
4. **Trace schema and review surfaces:** Runs, stages, axes, KAs, personas, policies, evidence, claims, metrics, and exports have substantial persistence and UI support.
5. **Ingestion:** Local document ingestion has meaningful extraction, chunking, hashing, deduplication, manifest, and indexing behavior.
6. **KAs:** All 125 registry entries resolve to code, and selected KAs have focused semantic tests.
7. **Testing:** The repository has broad backend/frontend unit, integration, contract, security, and packaging coverage.
8. **Documentation governance:** Active/archive separation, role-based navigation, release caveats, and canonical TODO ownership are well established.

## Validation evidence

Commands run from the live checkout on 2026-07-12:

| Check | Result |
|---|---|
| Backend full test suite | **Passed:** 1,699 passed, 18 skipped, 23 warnings in 231.15 seconds |
| Frontend Vitest suite | **Passed:** 80 files, 401 tests |
| Frontend TypeScript check | **Passed** |
| Frontend ESLint | **Passed with one test-file warning** |
| Strict runtime precheck | **Passed:** 0 blockers, 0 actions, 3 warnings |
| Environment parity | **Failed locally:** repository expects Python 3.11; active shell used Python 3.13. Node/npm and parity files passed |
| Documentation reference validation before this report | **Passed:** 0 errors, 47 style warnings |
| Tracked Python parse inventory | **Passed:** 797 files, 0 syntax failures |

Interpretation: the codebase is syntactically healthy and its existing test contracts pass. The largest findings are architecture/integration and product-truth gaps that current mocked and subsystem tests do not assert.

## Why tests did not catch the central gaps

1. Many frontend tests mock API responses and prove rendering or error-state behavior, not backend execution.
2. DMRF, DSQP, TruthCore, SDK overlay, RAG, simulation, and provider tests are largely subsystem tests; few assert one installed-app causal trace.
3. KA bulk tests emphasize importability and response shape.
4. Readiness tests encode the current SQL-only blocker policy.
5. UI tests do not fail when a rendered button has no action.
6. Passing trace tests prove persistence/shape, not that every persisted stage changed or validated the answer.

## Production completion plan

### Slice 0: Correct the trust boundary

1. Authenticate and authorize every active and legacy mutation route.
2. Protect GraphQL and build server-owned MCP execution context.
3. Eliminate public exception text.
4. Add a route manifest gate: every route must declare public, authenticated, admin, desktop-only, or internal.

Exit criteria: no unclassified mutation route; anonymous mutation tests fail closed; CodeQL exception-disclosure scan is clear.

### Slice 1: Establish one canonical governed request path

1. Replace the plan-only TruthCore adapter with actual workflow execution.
2. Define one request/result contract for DMRF, TruthCore, provider/tool execution, evidence, claims, convergence, memory, and trace.
3. Remove duplicate SDK/TruthCore reasoning branches or make one a thin library used by the other.
4. Persist stage start/end/result only for executed stages.

Exit criteria: an end-to-end test proves that changing retrieved evidence, DSQP persona input, or a TruthGate decision changes or blocks the final answer and is visible in the trace.

### Slice 2: Make evidence, confidence, and refinement real

1. Feed retrieved sources into the model with stable source IDs.
2. Extract claims and validate source support/provenance/freshness.
3. Replace default confidence with measured components or `not measured`.
4. Execute bounded refinement and prove convergence changes output or terminates safely.

Exit criteria: no fabricated 0.85/0.95 defaults on user-facing runs; unsupported claims are identified; refine/finalize behavior has deterministic tests.

### Slice 3: Control provider latency, cost, and privacy

1. Move provider calls off the event-loop thread or use async clients.
2. Apply one end-to-end request deadline and cancellation path.
3. Make DSQP deterministic by default or make its contributions causal.
4. Record every provider/embedding/tool call, token count, latency, and disclosed fields.
5. Implement native streaming or label buffered responses accurately.

Exit criteria: simple chat normally performs one answer call plus only explicitly enabled governance calls; p95 latency and maximum call-count budgets are enforced.

### Slice 4: Align storage and desktop lifecycle

1. Declare SQLite/Chroma/files/memory as the packaged default profile.
2. Make Redis/Neo4j/PostgreSQL optional installable profiles or bundle them intentionally.
3. Repair lifecycle manager ownership and per-service start/stop results.
4. Remove or encrypt/integrate cloud configuration.
5. Implement versioned desktop migrations and complete backup/restore.
6. Separate liveness, core readiness, and feature capability.

Exit criteria: a clean machine install reports only services that exist, upgrade tests preserve old data, start/stop is truthful, and restore drills pass.

### Slice 5: Correct simulations, MCP, and compliance semantics

1. Select the authoritative simulation engine and prevent recursive governed-pipeline calls.
2. Implement persisted asynchronous progress/events and provider-call budgets.
3. Replace MCP placeholder tools/resources with real, scoped operations.
4. Tie compliance status to explicit evidence and remove hardcoded pass language.

Exit criteria: each surface has real backend behavior, cost/security boundaries, and an installed-app acceptance test.

### Slice 6: Finish the user workflows

1. Inventory every interactive control.
2. Implement, disable with a clear state, or remove every no-op control.
3. Separate projects from chat-session aliases or rename the feature accurately.
4. Replace static dashboard trends and status badges with sourced data.
5. Add browser/Electron tests for provider setup, chat, trace, ingestion, graph, storage, simulation, MCP, export, backup, and recovery.

Exit criteria: no enabled control is actionless; all primary workflows pass against the packaged backend without mocked APIs.

### Slice 7: Lock the release

1. Unify product/package/document versions and dependency authority.
2. Remove stale providers, Ollama probes, Replit auth, and unsupported model metadata.
3. Replace false/static release checks with real analysis.
4. Complete trusted code signing and enable update signature verification.
5. Run clean-install, upgrade, uninstall/reinstall, offline, provider-failure, backup/restore, accessibility, and security acceptance.
6. Update active documents from evidence after the implementation is stable.

Exit criteria: signed artifact, complete release evidence, clean CI/security scans, production checklist approval, and no open P0/P1 findings.

## Definition of finished

DataLogicEngine can reasonably be called complete for production when all of the following are true:

1. The installed app executes the same governed path shown in active architecture documents.
2. Every trace statement is causally tied to executed code and measured inputs.
3. Every network/API mutation is authenticated and authorized.
4. Evidence, confidence, convergence, compliance, and validation labels are evidence-backed.
5. Provider/tool call count, latency, cost, timeout, privacy, and failure behavior are bounded and observable.
6. The installer contains or accurately declares every required runtime service.
7. Existing user data upgrades through versioned migrations and can be backed up/restored.
8. Every enabled UI control performs its stated action.
9. Packaged-app end-to-end tests cover all primary user journeys without mocked backend responses.
10. Trusted signing, update verification, accessibility evidence, security scans, rollback, and release approvals are complete.

## Final assessment

The codebase should not be discarded or rebuilt from zero. It contains enough working infrastructure to finish the intended product. The highest-leverage action is to reduce architectural duplication and make one governed chat path real, measurable, and testable. Once that path is authoritative, storage, simulation, MCP, compliance, UI, packaging, and documentation can align around observable behavior rather than parallel implementations and planned telemetry.

Until then, the accurate product description is:

> A local-first Windows AI workspace with working OpenAI/Google chat, local data and ingestion, experimental DMRF/DSQP/Truth Engine components, trace persistence, and governance-oriented tooling that is still being integrated into one production-grade reasoning lifecycle.
