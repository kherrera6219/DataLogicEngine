# DataLogicEngine Audit Slice Findings and Corrections Report

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.1.0 |
| Last updated | 2026-07-06 |
| Prepared | 2026-07-06 |
| Audit window covered | 2026-07-04 through 2026-07-06 |
| Source branch | `main` |
| Source records | `TODO.md`, `HANDOFF.md`, focused tests, generated docs inventory |
| Scope | Documentation audit slice plus code audit slices 1 through 12 and selected CodeQL alert remediation |
| Status | Active audit summary |
| Folder review | Reviewed during `docs/audits` Markdown pass on 2026-07-06 |

## Executive summary

The audit sequence completed one documentation reconciliation slice, twelve code audit slices, approved scratch-output cleanup, and selected CodeQL alert remediation. The work moved from documentation/API truth alignment into progressively deeper runtime contract checks: provider configuration, desktop/session authentication, route decorator boundaries, KA route correctness, KA persistence and frontend consumers, Trace Explorer and export lifecycle, gateway trace persistence, gateway failure/offline replay trace lifecycle, frontend trace-link consumers, and fixed public error handling for reflected-output and exception-disclosure alerts.

At the end of slice 12, the active `TODO.md` and `HANDOFF.md` records identify no further trace production lifecycle slice. Future work should start from a new live docs/code audit scope rather than continuing the trace-lifecycle queue by assumption.

## Findings and corrections by slice

### Documentation audit slice - Active docs and API contract reconciliation

**Found**

- Active docs named an older Google model while live backend/frontend defaults used `gemini-3.1-pro-preview`.
- `docs/openapi.yaml` still documented removed auth routes and broken schema references.
- Duplicate stale API exports lived under `docs/api/`.
- README referenced a missing PNG architecture asset.
- Root scratch-output files were mixed into the working tree but were not maintained source docs.
- `COMMERCIAL_LICENSE.md` had placeholder contact text.

**Corrected**

- Updated active model references to `gemini-3.1-pro-preview`.
- Replaced `docs/openapi.yaml` with a current partial contract for desktop auth, gateway, Truth Engine, KA, settings, search, ingestion, trace, and health/readiness routes.
- Moved stale API exports into `docs/archive/api/` and indexed them as reference-only.
- Updated README asset references to the shipped SVG.
- Deleted approved scratch-output files; orphan scanner code candidates remain confirm-before-cut and were not removed.
- Replaced placeholder commercial-license contact text with repository discussion/issue entry paths.

### Code audit slice 1 - LLM provider/model configuration

**Found**

- `ApiOverlayConfig` still offered a retired Google model first.
- `/api/v1/gateway/keys` accepted arbitrary provider strings and could persist unsupported active defaults.
- LLM-path comments and docstrings still described older Google model names.

**Corrected**

- Reordered and trimmed Google overlay choices to current supported models.
- Normalized provider, key, and model input before writes and rejected unsupported providers.
- Updated touched comments/docstrings to current model constants or `gemini-3.1-pro-preview`.
- Added frontend and backend regressions for provider/model handling.

### Code audit slice 2 - Authentication/session/CSRF/settings authorization

**Found**

- `/api/v1/settings/ai` used page-style Flask-Login behavior instead of the desktop-aware JSON API decorator.
- Settings preference writes accepted non-canonical provider/model values.
- Strict CSRF origin/token behavior lacked focused server-side regressions.

**Corrected**

- Moved `/api/v1/settings/ai` to `api_session_login_required` and resolved the authenticated user through `g.auth_user`/`current_user`.
- Restricted AI preferences to `auto`, `openai`, and `google`; validated models against current defaults; cleared model preference when provider is `auto`.
- Added CSRF regressions for untrusted origins, missing tokens, and valid Electron `app://-` CSRF-token mutations.

### Code audit slice 3 - API route decorator consistency and API-key/session boundaries

**Found**

- Several JSON API route modules still used page-style `@login_required`, producing inconsistent unauthenticated behavior.
- MCP admin routes stacked raw Flask-Login ahead of `api_admin_required`, blocking valid ExternalAPIKey principals.
- MCP tool execution built scope context from `current_user`, making API-key principals invisible.
- LLM admin/provider/API-key/governance routes used raw Flask-Login and direct `current_user` writes.

**Corrected**

- Replaced scoped routes with `api_session_login_required` and tightened JSON `401` assertions.
- Removed the raw Flask-Login wrapper from MCP admin routes.
- Added `get_authenticated_principal()` and used it for MCP execution context.
- Moved LLM admin routes to the JSON/desktop-aware auth path and used the resolved principal for ownership fields.

### Code audit slice 4 - Dead KA route module and stale Flask page routes

**Found**

- `backend/api/ka_management.py` was an unregistered duplicate KA blueprint with raw Flask-Login usage.
- Synthetic tests targeted the dead KA route module rather than the live API.
- Flask still registered stale `/chat` and `/knowledge-graph` Jinja routes even though Electron/Next owns those UI surfaces.

**Corrected**

- Removed the dead KA module and its synthetic-only coverage.
- Added live route coverage for `/api/v1/ka`, legacy `/api/ka`, JSON auth failures, public KA health, and ExternalAPIKey access.
- Removed stale Flask page routes and added route-map coverage proving Flask no longer owns them.

### Code audit slice 5 - Live KA API behavior/data-contract correctness

**Found**

- KA execution/workflow routes used `current_user` directly even though API-key and signed desktop principals resolve through `g.auth_user`.
- High-stakes workflow and trace routes imported the TruthCore accessor from the wrong module, and async TruthCore calls were used synchronously.
- `docs/API.md` documented `data`/`context` execute payloads, but the route only accepted `input`.
- KA algorithm pagination and sparse registry metadata could break frontend expectations.
- Batch and layer endpoints were brittle for malformed bodies and non-numeric layer labels.
- Active API docs omitted multiple live KA endpoints.

**Corrected**

- Switched KA user resolution to the shared authenticated-principal helper.
- Used the real `backend.truth_engine.api.get_truth_core_engine()` accessor and bridged async TruthCore methods safely.
- Accepted documented `data`/`context` payloads while preserving `input` as preferred.
- Clamped pagination and added safe KA id/name/status fallbacks.
- Hardened batch/layer parsing and sorting.
- Expanded KA API documentation for batch, search, categories, layers, dependencies, stats, and health.

### Code audit slice 6 - KA execution persistence/history correctness

**Found**

- `/api/v1/ka/history` returned KA execution IDs as trace `run_id` values, creating links to nonexistent trace runs.
- KA history serialization was brittle for lowercase KA IDs, sparse metadata, malformed limits, and non-frontend statuses.
- `/api/v1/trace/ka-execution-feed?limit=bad` could raise.
- `UkgDatabaseManager.create_ka_execution()` wrote removed `KAExecution` columns, and `KAEngine.get_execution_history()` called a missing read method.
- API docs omitted KA history and trace KA execution feed endpoints.

**Corrected**

- Returned trace links only when persisted `run_id` or `trace_run_id` exists.
- Added safe limit clamping, KA id normalization, status mapping, name fallback, and risk-tier fallback.
- Hardened invalid limit handling for the trace KA execution feed.
- Rewrote the DB-manager writer for the current schema, preserved legacy session context in `input_data`, and added `get_ka_executions()`.
- Documented KA history and KA execution feed routes.

### Code audit slice 7 - KA execution frontend/desktop IPC consumers

**Found**

- `LiveTracePanel` returned before loading live progress or KA execution feed when no trace runs existed.
- KA feed types were duplicated across component and Electron declarations.
- Tool history assumed non-null timestamps, durations, status/name fields, and run IDs.
- Frontend tests did not cover the KA history page or no-trace-run live feed state.

**Corrected**

- Loaded runs, live progress, and KA feed independently; rendered KA activity even without a selected trace run.
- Added shared `KAExecutionFeed` types in `frontend/lib/api/types.ts` and reused them in Electron global declarations.
- Added nullable-safe history formatting and trace links only when `run_id` is truthy.
- Added focused frontend tests for nullable history rows, trace links, and zero-trace-run KA feed rendering.

### Code audit slice 8 - Trace run viewer/list/export frontend and API contracts

**Found**

- `GET /api/v1/trace/runs` accepted invalid or unbounded pagination.
- The frontend trace API wrapper interpolated raw run IDs and returned weak `unknown` shapes.
- `/runs` assumed every row had a string run ID and valid timestamp, and did not treat live `pass` status as success.
- `/runs/view` assumed complete bundle fields for timestamps, axes, persona drafts, scores, metrics, and stage indexes.
- Tests did not cover Trace Explorer nullability, encoded IDs, status vocabulary, or export failure fallback.

**Corrected**

- Clamped trace list pagination server-side and client-side.
- Encoded run IDs for trace subresources and added typed trace list/bundle/subresource responses.
- Added safe row rendering, visible load errors, encoded detail links, and disabled actions for malformed rows.
- Added robust bundle fallback rendering for nullable or malformed trace data.
- Added focused backend and frontend Trace Explorer contract regressions.

### Code audit slice 9 - Trace export persistence/history lifecycle

**Found**

- Trace export returned a protected document but never persisted a `TraceExport` history row.
- `TraceExport` lacked fields and a serializer used by export history/download APIs.
- Export download returned placeholder metadata instead of the protected export document.
- Non-object JSON bodies could raise during option parsing.

**Corrected**

- Persisted `TraceExport` rows with status, download URL, manifest hash, file size, options, signature/encryption flags, and protected payload.
- Added model fields, `to_dict()`, and migration `e7f8a9b0c1d2_harden_trace_export_records.py`.
- Streamed the stored protected export document on download, retaining metadata fallback for older rows.
- Treated non-object export option bodies as `{}` and added a regression.

### Code audit slice 10 - Gateway trace creation and DMRF/chat persistence

**Found**

- Successful direct gateway calls could return `run_id` and `audit_trail` links without creating the backing `TraceRun`.
- `_create_trace_run()` parsed anonymous user IDs and non-UUID session IDs too strictly, causing common desktop/API contexts to skip persistence.
- DMRF tier, FROST depth, and truth-engine mode did not flow into trace audit-bundle fields.
- Overlay trace creation could happen before final moderation, and repeated create attempts risked duplicate stages or stale data.

**Corrected**

- Created or upserted `TraceRun` rows before returning successful direct, quad, or UKG overlay responses.
- Added tolerant parsers for optional user/session/run identifiers.
- Persisted DMRF tier, FROST depth, truth-engine mode, gate decision, and DMRF snapshot metadata on trace rows.
- Made `_create_trace_run()` update existing rows and only create stages when none exist.

### Code audit slice 11 - Gateway failure, streaming, and offline replay trace lifecycle

**Found**

- Governance blocks, no-provider failures, provider exhaustion, DMRF blocks, and user-preference blocks returned `run_id` values without failed `TraceRun` rows.
- Failed `/api/v1/gateway/chat` responses exposed `run_id` but not `audit_trail`.
- `/api/v1/gateway/chat/stream` terminal/error events included only `run_id`.
- Offline replay stored run/provider/model on success but dropped trace metadata on failed replay attempts.

**Corrected**

- Converted `_error_response()` into an async trace-backed path that writes failed `TraceRun` rows and sanitized gateway-error metadata.
- Added `audit_trail` to rate-limit, queued-offline, and 503 gateway failure payloads.
- Added `audit_trail` to stream `done` and `error` events before SSE serialization.
- Added `audit_trail` to replay success/failure responses and persisted failed replay metadata back onto queue items.

### Code audit slice 12 - Frontend and desktop gateway trace-link consumers

**Found**

- `request()` reduced non-OK JSON responses to a message string, hiding failed-run `run_id` and `audit_trail` metadata from callers.
- `ChatInterface` preserved trace metadata only on direct and WebSocket success paths.
- The reusable `MessageBubble` rendered `ChatTracePanel`, but the active `ChatInterface` message loop used its own renderer and never mounted trace links.
- No separate frontend stream UI or desktop IPC offline-queue consumer was found beyond chat submission and trace/DMRF progress proxying.

**Corrected**

- `ApiError` now preserves the parsed payload while retaining normalized message and status fields.
- Added shared gateway trace-field extraction and applied it across direct, WebSocket, queued, 429, and fallback message construction.
- Rendered provider/model badges and `ChatTracePanel` in the active chat message loop when `runId` or `auditTrail` exists.
- Confirmed no additional desktop IPC code change was needed for gateway trace-link consumption.

### Post-slice CodeQL remediation - Reflected output and exception disclosure

**Found**

- KA route errors reflected attacker-controlled algorithm IDs and returned request-body validation errors through inconsistent tuple/string paths.
- KA, search, MCP, and trace export route handlers returned raw exception text in JSON responses.
- MCP console and dynamic-server error paths reflected request-controlled command/server names.
- Search routes parsed integer query parameters with direct `int(...)`, allowing malformed input to escape into exception handling.

**Corrected**

- Added fixed KA public error responses for invalid IDs, not-found results, malformed request bodies, route failures, and batch per-item failures.
- Added bounded search query-parameter parsing and generic route-level search errors.
- Hardened MCP route exception handling across the selected alert paths and adjacent same-class MCP disclosure sites.
- Replaced trace export `ValueError` response text with a stable public message while logging the detailed exception server-side.
- Added backend regressions proving malicious/secret exception strings are absent from KA, search, MCP, and trace export responses.

## Validation summary

The completed slices added or reran focused validation across backend route tests, integration tests, frontend Vitest suites, frontend typechecking, Ruff, ESLint, docs inventory generation, and docs reference validation. The final checkpoint records:

- Focused gateway/API/trace/DMRF pytest: 57 passed with workspace-local temp paths.
- Focused CodeQL remediation pytest for KA/search/MCP/trace export alert surfaces: 69 passed with workspace-local temp paths; 20 SQLAlchemy legacy-query warnings; known Neo4j driver teardown logging warning after successful exit.
- Focused frontend chat/API trace-consumer Vitest: 34 passed.
- Frontend typecheck: passed.
- Direct Ruff checks for touched gateway, trace, KA, auth, security-alert, and route files: passed.
- `scripts/generate_docs.py`: refreshed generated inventory artifacts.
- `scripts/verify_docs_references.py`: passed with 0 errors and 17 existing heading/style warnings.

## Remaining audit queue

The active trace production lifecycle queue is complete as of slice 12, and the selected CodeQL reflected-output/exception-disclosure alerts have been remediated. Remaining work before a complete rebuild is release validation rather than another trace slice: run the final rebuild/packaging path, confirm provider-configured staging, attach signed-artifact and accessibility evidence when available, and treat orphan scanner code candidates as confirm-before-cut cleanup if a separate cleanup pass is requested.

## Change notes for v1.1.0

1. Added active document metadata and folder-review status during the `docs/audits` Markdown pass.
2. Confirmed this file remains the active consolidated audit-slice findings report; older audit plans in this folder are historical/reference unless explicitly promoted.
