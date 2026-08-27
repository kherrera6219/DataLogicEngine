# Installed Governed Chat Repair Plan

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-PLAN-CHAT-QC-2026-08-26 |
| Document version | v1.0.0 |
| Product version | 4.4.3 |
| Date | 2026-08-26 |
| Status | Active supporting implementation plan; not release authority |
| Owner | Production Program Owner |
| Approver | Kevin Herrera, Product Owner |
| Evidence run | `0779492c-c054-4630-b321-b2e13be7b4ef` |
| Release posture | Production/public release remains **NO-GO** |

## 1. Purpose and authority

This plan converts the installed governed-chat findings recorded in `TODO.md`
into an implementation sequence grounded in the current frontend, backend,
persistence, and test code. It covers session durability, answer completeness,
confidence and mode truthfulness, live trace presentation, refinement and
analyst visibility, Trace & Review analytics, the Knowledge Base workspace,
and installed acceptance.

This is a supporting plan. It does not replace, reopen, or weaken:

1. `PRODUCTION_COMPLETION_PLAN_2026.md`, the release execution authority;
2. `TODO.md`, the open-work ledger;
3. `HANDOFF.md`, the current checkpoint;
4. `docs/compliance/REMEDIATION_PLAN.md`, the compliance work orders; or
5. any human gate, CP19-M installed-evidence row, or release requirement.

CP19-D through CP19-G remain implemented. The work below repairs product
binding, presentation, durability, and acceptance around those capabilities.
The current 4.4.3 release status remains `release_blocked`.

## 2. Fixed boundaries

Every implementation task must preserve these boundaries:

- No new provider, telemetry, update-check, crash-reporting, or other outbound
  destination is authorized.
- Safe public execution summaries are required; private chain-of-thought, full
  prompts, credentials, personal data, and unbounded internal JSON must not be
  displayed, persisted for display, or exported.
- A refinement cycle is conditional. The UI must explain why it was not used;
  it must not execute twelve steps merely to populate the display.
- A continuation after a provider output limit is a separate, user-authorized,
  budgeted provider attempt. It must never happen silently.
- Profile coverage is not answer confidence. Provider success is not evidence
  confidence. Missing measurements must remain missing and explained.
- The four analyst contributions remain deterministic governed findings unless
  the owner separately approves additional provider calls and their latency,
  cost, privacy, and public contract.
- Current authentication and principal ownership must not be broadened.
- No test, validation gate, or safety control may be skipped or weakened.
- The standing major-update rule is applied once, at the final integrated
  rebuild boundary. This planning change does not change the product version.

## 3. Reproduced findings and confirmed causes

### 3.1 Chat durability and response truth

| Finding | Confirmed code cause | Primary code |
|---|---|---|
| First conversation disappears from Recent Sessions | A new chat generates a client UUID only when the user presses New Chat. The initial page send can omit `session_id`; the backend saves messages only when an ID is present. Session creation is an incidental side effect of message persistence, and the UI does not adopt a server-created ID after the response. | `frontend/components/Chat/ChatInterface.tsx`; `frontend/lib/api/chat.ts`; `backend/llm_gateway/api.py`; `backend/llm_gateway/gateway.py`; `backend/governed_execution/orchestrator.py`; `models.py` |
| An answer can end mid-sentence yet appear successful | Provider adapters discard finish, incomplete, block, and safety metadata. The gateway propagates text and usage only, and the OpenAI-compatible response hard-codes `finish_reason` as `stop`. The prompt has no typed response-depth target. The observed 107-token output therefore cannot be distinguished from a completed response. | `backend/llm_gateway/providers/base.py`; `backend/llm_gateway/providers/google.py`; `backend/llm_gateway/providers/openai.py`; `backend/llm_gateway/gateway.py`; `backend/llm_gateway/api.py`; `backend/governed_execution/prompt.py` |
| Confidence is absent or misleading | The response already carries confidence fields, but the chat ignores them. Live Trace renders missing values as `--`, while persona `coverage_score` values are displayed as if they were persona-answer confidence. | `frontend/components/Chat/ChatInterface.tsx`; `frontend/components/Chat/ChatTracePanel.tsx`; `frontend/components/Chat/LiveTracePanel.tsx`; `backend/tracing/api.py`; `backend/governed_execution/trace_persistence.py`; `models.py` |
| Standard answers are marked Enhanced | Both live and direct response paths hard-code `isEnhanced: true`; history normalization also treats any assistant message without the legacy boolean as enhanced. The governed response does not return its normalized mode. | `frontend/components/Chat/ChatInterface.tsx`; `frontend/components/Chat/types.ts`; `frontend/lib/api/types.ts`; `backend/llm_gateway/api.py`; `models.py` |

### 3.2 Trace, refinement, and analyst presentation

| Finding | Confirmed code cause | Primary code |
|---|---|---|
| Live stages are not reliably shown | The backend emits `stage_name`, `input`, `output`, and top-level `duration_ms`; the socket client expects `name`, `inputs`, `outputs`, and nested timing. Governed Chat uses the synchronous endpoint, learns the run ID after completion, and does not subscribe to `useTraceStream` during the run. | `backend/governed_execution/orchestrator.py`; `backend/websocket.py`; `backend/llm_gateway/gateway.py`; `frontend/lib/socket.ts`; `frontend/hooks/useTraceStream.ts`; `frontend/components/Chat/ChatInterface.tsx` |
| The trace names steps but does not explain work | The orchestrator persists useful structured stage records, but the chat surfaces reduce them to labels, status, and duration. The run-detail page can show raw JSON instead of a bounded user-facing explanation. | `backend/governed_execution/orchestrator.py`; `backend/governed_execution/trace_persistence.py`; `frontend/components/Chat/TraceVisualizer.tsx`; `frontend/components/Chat/ChatTracePanel.tsx`; `frontend/app/runs/view/page.tsx` |
| No explanation appears when refinement is absent | Refinement is disabled for Standard mode by default and conditional in Enhanced mode. No typed disposition is persisted when no `refinement_1` stage exists, so the UI renders nothing. The observed run had zero permitted cycles and unmeasured confidence; it was not a high-confidence skip. | `backend/governed_execution/orchestrator.py`; `backend/governed_execution/contracts.py`; `backend/knowledge_algorithms/refinement_workflow.py`; `frontend/app/runs/view/page.tsx` |
| The twelve refinement steps do not stream | `CanonicalRefinementWorkflow.execute` creates the complete receipt internally and returns it after the loop. The orchestrator emits only the parent refinement stage, with no per-step callback or event. | `backend/knowledge_algorithms/refinement_workflow.py`; `backend/governed_execution/orchestrator.py`; `backend/governed_execution/trace_persistence.py` |
| Analyst cards do not show distinct findings | Layer 4 produces actual persona findings and constraints, but trace persistence stores the generic profile description as `draft_text` and profile coverage as `confidence`. The current UI therefore cannot show the governed contribution that affected synthesis. | `backend/governed_execution/orchestrator.py`; `backend/governed_execution/trace_persistence.py`; `frontend/components/Chat/LiveTracePanel.tsx`; `frontend/app/runs/view/page.tsx`; `models.py` |
| Trace Explorer is compressed and controls are inert | Fourteen labels are placed in a fixed horizontal row with narrow label widths; fixed chat sidebars further shrink the center. Tree/Timeline are badges and View Details is a non-interactive span. | `frontend/components/Chat/TraceVisualizer.tsx`; `frontend/components/Chat/ChatInterface.tsx`; `frontend/components/Chat/ChatTracePanel.tsx` |

### 3.3 Analytics and Knowledge Base connectivity

| Finding | Confirmed code cause | Primary code |
|---|---|---|
| Trace & Review Analytics is not trace analytics | The page is under Trace & Review but calls only `api.knowledge.pillars()` and renders 17-axis pillar definitions. It never queries `TraceRun`, stages, evidence, providers, tokens, personas, or refinement. | `frontend/app/analytics/page.tsx`; `frontend/lib/api/knowledge.ts`; `frontend/components/layout/AppSidebar.tsx` |
| Trace failure can look like an empty dataset | The trace list converts database or schema exceptions into HTTP 200 with an empty run list. Bundle construction can similarly return a successful-looking empty bundle. A consumer cannot distinguish no data from unavailable data. | `backend/tracing/api.py`; `frontend/lib/api/trace.ts` |
| Knowledge Base is a partial read-only view | The page shows pillar definitions and visible graph-node counts only. Durable ingestion history, file/revision state, parser and defense results, object/vector/graph materialization, retrieval linkage, reconciliation, and deletion state exist in ingestion APIs and the Settings ingestion component but are not represented here. | `frontend/app/knowledge/page.tsx`; `frontend/lib/api/knowledge.ts`; `frontend/lib/api/ingestion.ts`; `frontend/components/Settings/KnowledgeIngestionSettings.tsx`; `backend/routes/ingestion_routes.py`; `backend/routes/api_routes.py`; `models.py` |
| Page-specific acceptance is absent | Analytics and Knowledge Base have error-boundary coverage and API unit tests, but no page tests for real loading, empty, unavailable, populated, principal-scoped, lifecycle, or retrieval-linked states. | `frontend/app/app-surfaces.test.tsx`; `frontend/tests/unit/lib/api/knowledge.test.ts`; `frontend/tests/unit/lib/api/ingestion.test.ts`; `frontend/components/settings/KnowledgeIngestionSettings.test.tsx` |

## 4. Target product contracts

### 4.1 Durable chat transaction

The first send must use this ordered contract:

1. Create or resolve one principal-owned chat session.
2. Return and retain its authoritative `session_id` and normalized governed
   mode before provider execution begins.
3. Correlate the chat session, request ID, governed run, trace run, and both
   transcript rows.
4. Persist the user message before provider execution.
5. Persist the released assistant message and completion metadata atomically
   enough that a successful UI result cannot silently omit history.
6. Refresh and select the same session in Recent Sessions.
7. Make create/send/retry/replay idempotent without duplicate sessions or
   messages.

Persistence failures must be typed and observable. Existing catch-and-log
behavior in `_save_chat_message` must not remain the success path.

### 4.2 Provider completion and answer-depth contract

The internal provider response must preserve a typed completion disposition:

- `complete`;
- `length_limited`;
- `safety_blocked`;
- `provider_incomplete`; or
- `failed`.

It must also retain the provider-native reason in a bounded diagnostic field,
usage, model, and response identifier. Google and OpenAI adapters must map
their native metadata to this shared type. The gateway, governed result,
trace, persistence, and UI must preserve it without claiming `stop` when it is
unknown.

The prompt builder must select an explicit response-depth profile from the
request's breadth and intent. This controls expected structure and coverage;
it does not authorize an extra provider call. A `length_limited` result must be
shown as incomplete and offer a clearly budgeted continuation action.

### 4.3 Confidence display contract

Every confidence surface must use one shared display model:

- measurement status;
- numeric value only when measured;
- formula/version identifier;
- missing or failed reason;
- missing components; and
- plain-language explanation of what the value measures.

The visible name of the canonical score remains decision-gated by CR-D1. This
plan does not rename it or calibrate its thresholds; CR-F3 retains calibration
authority. Profile coverage, evidence support, policy results, and analyst
finding status must be labeled separately.

### 4.4 Public trace presentation contract

One typed presentation contract must feed chat live updates, final chat trace,
run detail, analytics, and export. Each event or persisted stage presentation
must include:

- run ID, stable stage ID, layer/step index, and monotonic event sequence;
- stage name, purpose, state, start/end time, and duration;
- bounded authorized-input and evidence summary;
- selected and executed KA identifiers;
- material findings, decisions, reasons, checks, warnings, and output summary;
- refinement disposition and step data when applicable; and
- redaction and presentation-schema versions.

The public narrative must be generated deterministically from governed stage
records. It must not make a provider call or expose private reasoning. A
central allowlist, size bound, redactor, and sensitive-value canary test must
protect every transport and export path.

The live transport must provide the run ID before meaningful stage events are
lost, normalize field names once, order by event sequence, resume from the last
seen sequence, and backfill from the persisted bundle after reconnect.

### 4.5 Refinement disposition and receipt contract

Every run must persist exactly one of:

- `not_enabled` — the selected mode allowed no refinement cycle;
- `not_needed` — convergence was measured and policy did not select refine;
- `not_measured` — the required convergence/confidence input was unavailable;
- `executed` — the canonical workflow ran and produced a receipt;
- `blocked` — policy or a safety gate prevented execution; or
- `failed` — an invoked workflow failed.

The reason and governing inputs are mandatory. When invoked, the canonical
twelve-step workflow remains the single authority, but it gains an in-process
progress callback that emits started/completed/skipped/blocked/failed events
for each step. The final persisted receipt must reconcile all twelve ordered
steps and any post-rewrite Layer 6 through Layer 10 pass.

### 4.6 Analyst contribution contract

The four analyst panels must show the actual deterministic findings,
objections, constraints, evidence references, measurement status, and
synthesis influence produced by the governed persona stage. Generic persona
descriptions and profile coverage must not be presented as answers or answer
confidence.

This plan does not authorize four additional provider responses. If the desired
product becomes full separately generated prose answers, implementation pauses
for the owner to approve the call budget, latency, data exposure, persistence,
and public field names.

### 4.7 Trace analytics contract

The Analytics page must describe what its navigation promises: current-
principal trace/run analytics. It must derive only from persisted trace
authority and expose a bounded time range with:

- run counts and status/disposition counts;
- provider/model and actual governed-mode distribution;
- latency and token usage with explicit unavailable values;
- confidence-measurement status and values only where measured;
- evidence, KA, and persona contribution counts;
- refinement disposition and executed-step counts; and
- links to the exact contributing runs.

No fabricated zero may replace an unavailable query or missing measurement.
The API must return distinct loading, empty, unavailable, and populated states
and preserve principal scope. Reusing the generic dashboard overview or the
pillar list does not satisfy this contract.

### 4.8 Knowledge workspace contract

Knowledge Base must become the read/operate workspace for authoritative local
knowledge state while Knowledge Graph remains the relationship visualization.
It must reuse the existing ingestion authority and expose:

- sources, jobs, files, and source revisions;
- acquisition, parsing, defense, and rejection status;
- object, normalized-object, vector, and graph materialization state;
- chunks, pending materializations, errors, repair/retry/delete state;
- last retrieval time and trace linkage; and
- cross-store consistency with an explicit unavailable reason.

Existing Settings ingestion controls should be extracted or reused rather than
duplicated. Source selection remains desktop-capability based. Page access and
all list/detail operations require explicit authorization tests before broader
visibility is accepted.

## 5. Ordered implementation work packages

Each TODO ID remains independently attributable and should receive its own
focused commit and evidence. Do not combine unrelated fixes merely because
they touch the same component.

### WP-1 — CHAT-QC-01: durable session and transcript

**Changes**

1. Add an explicit create/ensure-session operation with principal ownership,
   normalized mode, and idempotency.
2. Await that operation before the first send; immediately select the returned
   session and join its run/session transport as applicable.
3. Return the authoritative session/run correlation to the desktop client.
4. Replace silent transcript-write failure with a typed result and define the
   release behavior when user or assistant persistence fails.
5. Remove state updates performed during render and reconcile the selected
   session after navigation/relaunch.

**Likely files**

`frontend/components/Chat/ChatInterface.tsx`, `frontend/lib/api/chat.ts`,
`frontend/components/Chat/types.ts`, `frontend/lib/api/types.ts`,
`backend/llm_gateway/api.py`, `backend/llm_gateway/gateway.py`,
`backend/governed_execution/orchestrator.py`, `models.py`, and a migration if
the durable correlation cannot be represented safely by the current schema.

**Gates**

Backend session ownership/idempotency tests; frontend first-send, refresh,
reopen, retry, and replay tests; installed navigation/relaunch proof.

### WP-2 — CHAT-QC-02: provider completion and answer breadth

**Changes**

1. Introduce the internal typed completion disposition.
2. Map Google candidate finish/block metadata and OpenAI response status,
   incomplete details, and output metadata.
3. Propagate completion through gateway, governed result, trace, transcript,
   and rendering; remove hard-coded success finish reasons.
4. Add deterministic response-depth selection and complete-answer prompt
   requirements without a second provider call.
5. Add a visible, user-authorized continuation action for length-limited
   responses.

**Likely files**

`backend/llm_gateway/providers/base.py`,
`backend/llm_gateway/providers/google.py`,
`backend/llm_gateway/providers/openai.py`, `backend/llm_gateway/gateway.py`,
`backend/llm_gateway/api.py`, `backend/governed_execution/contracts.py`,
`backend/governed_execution/prompt.py`, trace persistence, frontend API types,
and chat rendering.

**Gates**

Provider fixture tests for every disposition; no false `stop`; persistence/UI
parity; bounded live Google test using the installed acceptance prompt after
source tests pass.

### WP-3 — CHAT-QC-03 and CHAT-QC-04: confidence and mode truth

**Changes**

1. Add the shared confidence display model and preserve reasons for unmeasured
   or failed measurement.
2. Remove persona coverage from confidence surfaces or label it only as
   profile coverage.
3. Return, persist, and render the normalized governed mode and provider-call
   budget; retire the assistant-role `is_enhanced` inference.
4. Migrate or compatibly read legacy transcript rows without rewriting their
   historical meaning.

**Likely files**

`backend/governed_execution/contracts.py`, trace persistence,
`backend/llm_gateway/api.py`, `models.py`, `frontend/lib/api/types.ts`,
`frontend/components/Chat/types.ts`, `ChatInterface.tsx`,
`ChatTracePanel.tsx`, `LiveTracePanel.tsx`, and run-detail/export rendering.

**Gates**

Measured, unmeasured, insufficient-evidence, and validation-failed fixtures;
Standard/Enhanced/history fixtures; no threshold or metric rename without the
CR-D1 human decision.

### WP-4 — TRACE-QC-01 and TRACE-QC-02: one safe live trace

**Changes**

1. Define one backend/frontend public trace presentation schema.
2. Align current event field names, add stable IDs and sequence numbers, and
   provide early run correlation.
3. Use one live subscription path from Governed Chat and reconcile it with the
   persisted bundle after completion or reconnect.
4. Generate bounded stage narratives from allowlisted structured records.
5. Replace successful-looking empty trace responses on internal failure with a
   typed unavailable result and preserve an explicit empty state only for a
   genuinely empty query.

**Likely files**

`backend/governed_execution/orchestrator.py`, a central public-trace presenter,
`backend/websocket.py`, `backend/tracing/api.py`,
`backend/governed_execution/trace_persistence.py`, `frontend/lib/socket.ts`,
`frontend/hooks/useTraceStream.ts`, `frontend/lib/api/trace.ts`, and the three
chat/run-detail trace renderers.

**Gates**

Schema contract tests; stage ordering, reconnect, duplicate, and backfill
tests; redaction/canary/size tests; failure-is-not-empty tests; zero additional
provider calls.

### WP-5 — TRACE-QC-03 and TRACE-QC-04: refinement accounting

**Changes**

1. Calculate and persist a disposition on every run.
2. Render the disposition card even when no refinement stage exists.
3. Add a progress callback to the canonical workflow without creating a
   second receipt authority.
4. Stream and persist all twelve step states, then reconcile the final receipt
   and post-rewrite Layer 6 through Layer 10 pass.

**Likely files**

`backend/knowledge_algorithms/refinement_workflow.py`,
`backend/governed_execution/contracts.py`,
`backend/governed_execution/orchestrator.py`, trace persistence/API types,
`frontend/components/Chat/ChatTracePanel.tsx`, and
`frontend/app/runs/view/page.tsx`.

**Gates**

Standard `not_enabled`, measured `not_needed`, `not_measured`, Enhanced
executed, blocked-step, failed-step, and completed-rewrite fixtures; every
invoked receipt accounts for twelve ordered steps.

### WP-6 — TRACE-QC-05: analyst findings and synthesis influence

**Changes**

1. Persist each analyst's actual governed finding bundle and evidence links.
2. Record how the synthesis used, reconciled, or rejected each contribution.
3. Replace generic profile prose and misleading 100% labels with the actual
   finding and its measurement status.
4. Keep a clear visual boundary between analyst contributions and the released
   combined answer.

**Likely files**

Layer 4/5 governed contracts and orchestrator code, trace persistence and
models, trace API types, `LiveTracePanel.tsx`, `ChatTracePanel.tsx`, and
`frontend/app/runs/view/page.tsx`.

**Gates**

Four distinct fixture contributions; trace linkage; synthesis-influence
assertions; no analyst card represented as a provider-generated answer unless
that work actually occurred.

### WP-7 — DATA-QC-01: principal-scoped trace analytics

**Changes**

1. Replace the pillar query on `/analytics` with a bounded, principal-scoped
   aggregate over persisted trace authority.
2. Provide time/status/mode/provider filters and exact run drill-down links.
3. Render loading, empty, unavailable, partial, and populated states.
4. Keep missing confidence, token, evidence, and refinement values explicit.
5. Remove fail-soft empty-list/bundle behavior from the analytics dependency.

**Likely files**

`frontend/app/analytics/page.tsx`, a typed frontend trace-analytics client,
`backend/tracing/api.py` or a dedicated trace-analytics service, trace models,
and page/API tests.

**Gates**

Principal isolation; owner visibility where explicitly authorized; range and
filter bounds; observed-run fixture; unavailable-not-zero; empty-not-error;
run-detail links.

### WP-8 — DATA-QC-02: authoritative Knowledge Base workspace

**Changes**

1. Reframe `/knowledge` as source/revision/materialization/retrieval status and
   keep `/graph` for relationship browsing.
2. Reuse the existing ingestion controls and APIs rather than duplicating job
   logic.
3. Add source and file detail views with bounded content-free status fields,
   retrieval trace links, consistency state, and authorized lifecycle actions.
4. Make unavailable object/vector/graph services explicit.
5. Verify authorization and principal filtering before accepting source lists
   or detail views.

**Likely files**

`frontend/app/knowledge/page.tsx`, extracted ingestion components,
`frontend/lib/api/knowledge.ts`, `frontend/lib/api/ingestion.ts`,
`backend/routes/ingestion_routes.py`, `backend/routes/api_routes.py`, and
ingestion/graph tests.

**Gates**

Queued through completed/failed/cancelled/superseded lifecycle fixtures;
cross-store consistency and unavailable fixtures; retrieval-to-trace link;
delete reconciliation; authorization and bounded-detail tests.

### WP-9 — TRACE-QC-06: responsive, accessible Trace Explorer

**Changes**

1. Move the explorer out of the composer and give it a resizable/collapsible
   product pane or full run-detail surface.
2. Replace badges/spans with actual tabs, buttons, accordions, and keyboard
   navigation.
3. Use responsive list/tree/timeline views with scrolling or virtualization;
   never compress fourteen stages plus twelve refinement steps into one fixed
   row.
4. Preserve focus, live-region restraint, readable names, and detail state
   across live/final reconciliation.

**Gates**

Component and browser tests at supported viewport/scaling combinations;
keyboard-only operation; focus order; contrast; screen-reader labels. Final
NVDA/Section 508 conformance evidence remains under CP19-M and CR-G12.

### WP-10 — CHAT-QC-05 and CHAT-QC-06: integrated acceptance

**Source gates**

1. Run focused backend governed-session/provider/trace/refinement/persona/
   analytics/ingestion tests.
2. Run focused frontend API/component/page/socket tests and browser flows.
3. Run the full Windows suite with zero collection errors, frontend build,
   lint/type checks, documentation gates, and diff integrity.
4. Confirm no new outbound destination, dependency, or silent fallback.

**Installed gate**

Once all source tasks are green and the change set is declared the next major
update, increment the product version from 4.4.3 to 4.4.4, rebuild from the
exact clean commit, record artifact hashes, and execute installed acceptance
for:

- first-session persistence through navigation and relaunch;
- complete Google answer or explicit typed limit state;
- actual Standard/Enhanced mode and provider-attempt budget;
- measured/unmeasured confidence explanations;
- live safe stage narrative and persisted-trace reconciliation;
- separate analyst findings and combined answer;
- truthful refinement disposition and all twelve steps when invoked;
- trace analytics and Knowledge Base populated/unavailable/lifecycle states;
- supported scaling, keyboard, contrast, and NVDA; and
- install/repair/upgrade/uninstall and retained-data rows still open in CP19-M.

The exact installed artifact, source commit, database state, provider/model,
request/run/session IDs, and evidence paths must be recorded. A portable or
source-only pass cannot close installed acceptance.

## 6. Human decisions and stop conditions

Implementation pauses for the owner before any of these changes:

1. **External response contract:** adding or renaming fields on an external-
   facing gateway schema rather than a desktop-internal contract.
2. **Analyst provider calls:** generating four separate provider prose answers
   instead of showing deterministic governed findings.
3. **Public metric name:** selecting a replacement public name for the current
   confidence metric; CR-D1 owns that decision.
4. **New dependency or destination:** any package addition or outbound service.
5. **Authorization discovery:** a test shows a source, session, trace, or
   analytics record is visible outside its intended principal scope.
6. **Test retirement or behavior change outside scope:** a required fix would
   weaken a gate, delete a test, or change unrelated business behavior.

## 7. Recommended dependency order

```text
CHAT-QC-01 durable session
    -> CHAT-QC-04 actual mode
    -> TRACE-QC-01 run correlation and live transport

CHAT-QC-02 completion contract
    -> trace/UI completion presentation
    -> installed answer-completeness proof

CHAT-QC-03 confidence display
    -> TRACE-QC-03 refinement disposition

TRACE-QC-01
    -> TRACE-QC-02 safe stage narrative
    -> TRACE-QC-04 twelve-step streaming
    -> TRACE-QC-05 analyst contribution display
    -> DATA-QC-01 trace analytics

DATA-QC-02 knowledge workspace
    -> retrieval-to-trace installed proof

All functional/data tasks
    -> TRACE-QC-06 accessible layout
    -> CHAT-QC-05 integrated source regression
    -> version 4.4.4 exact-source rebuild
    -> CHAT-QC-06 installed acceptance
```

The first implementation slice should be CHAT-QC-01. It removes the durable
identity gap needed by history, live run correlation, trace drill-down, and
installed acceptance. CHAT-QC-02 can be prepared independently after its
internal completion-disposition names are fixed.

## 8. Completion definition

This plan is complete only when every linked TODO item is checked with
artifact-bound evidence, the current handoff points to the next true release
blocker, documentation is synchronized, and the exact rebuilt installed app
passes the retained CP19-M rows. Passing source tests or making the UI appear
populated is not sufficient.
