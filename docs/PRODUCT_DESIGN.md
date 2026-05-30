# DataLogicEngine Product Design

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-05-30 |
| Status | Active |
| Owner | Product Design and Frontend Engineering |
| Review cadence | Every 30 days |

## Purpose

Define the current UX architecture, route model, interaction patterns, design guardrails, and reviewer experience for DataLogicEngine.

This version aligns the product design with the current local-first Windows/Electron runtime, governed AI lifecycle, DMRF, Truth Engine, Trace Explorer, graph/knowledge surfaces, MCP governance, privacy controls, and release-readiness expectations.

## Audience

1. Product designers
2. Frontend engineers
3. QA and accessibility reviewers
4. Product and release managers
5. Technical judges and evaluators

## Related documents

1. `docs/PRODUCT_OVERVIEW.md`
2. `docs/USER_GUIDE.md`
3. `docs/ARCHITECTURE.md`
4. `docs/SECURITY.md`
5. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
6. `docs/diagrams/11_frontend_product_surface_and_trace_review_map.md`

---

## Product design thesis

DataLogicEngine should feel like an enterprise AI operations workspace, not a generic chatbot.

The product must make these differentiators visible:

1. local-first desktop runtime;
2. governed AI lifecycle;
3. traceability and evidence review;
4. knowledge graph context;
5. Truth Engine state;
6. MCP connector governance;
7. privacy and data controls;
8. admin and release-readiness posture.

A user should quickly understand:

```text
Ask a question
  -> get an answer
  -> inspect the trace
  -> review evidence/claims/personas
  -> inspect graph context
  -> export/delete data when needed
```

---

## Design principles

1. **Trace-first AI** — every important AI result should point toward trace/review evidence when available.
2. **Local-first clarity** — users must understand what is local, what is provider-backed, and what can leave the machine.
3. **Governed, not magical** — surface Truth Engine, DMRF, evidence, and policy decisions as understandable product concepts.
4. **Task-first navigation** — prioritize dashboard, chat, runs/traces, graph/knowledge, settings, and admin workflows.
5. **Progressive disclosure** — use tabs, side panels, empty states, and details panes instead of overwhelming first-time users.
6. **Role-aware operations** — admin/MCP/compliance features should be visible and protected according to role/runtime.
7. **Accessible by default** — keyboard navigation, labels, empty states, and readable themes are product requirements.
8. **No false certainty** — AI limitations, provider behavior, privacy, and release caveats should be visible where relevant.

---

## Information architecture

### Public and disclosure surfaces

| Route | Purpose |
|---|---|
| `/` | landing and product entry point. |
| `/about` | product and architecture narrative. |
| `/about/ai-limitations` | AI transparency and limitation disclosure. |
| `/about/cloud-services` | cloud/provider/data residency disclosure. |
| `/legal/privacy` | privacy policy and user rights. |
| `/login` | web mode authentication entry point. |
| `/register` | disabled in current local-first build; redirects to `/dashboard`. |

### Operator surfaces

| Route | Purpose |
|---|---|
| `/dashboard` | operational overview and quick actions. |
| `/chat` | governed AI interaction workspace. |
| `/projects`, `/projects/view` | session browsing and message history. |
| `/runs`, `/runs/view` | trace/run history, evidence review, export path. |
| `/graph` | knowledge graph exploration. |
| `/knowledge` | knowledge record review and graph-adjacent surfaces. |
| `/simulations` | simulation lifecycle monitoring. |
| `/truth-engine` | Truth Engine monitoring and system state. |
| `/mcp` | MCP ecosystem hub and integration UI. |
| `/settings`, `/settings/privacy` | provider, model, storage, privacy, theme, notifications, and preferences. |
| `/profile` | user profile and account context. |

### Admin surfaces

| Route | Purpose |
|---|---|
| `/admin` | role-gated admin dashboard. |
| `/admin/compliance` | compliance dashboard. |
| `/admin/mcp` | MCP status and governance. |
| `/admin/mcp/servers` | MCP server registry management. |

---

## Core user journeys

### First-time evaluator journey

1. Open app.
2. Land on dashboard.
3. Configure provider in Settings.
4. Send prompt in Chat.
5. Open Runs/Trace detail.
6. Inspect evidence/stages/personas/policy data.
7. Inspect Graph/Knowledge if data exists.
8. Review Privacy controls.
9. Review Truth Engine/MCP/Admin surfaces if permitted.

### Analyst journey

1. Start in Chat.
2. Ask domain question.
3. Use uploads/knowledge context where available.
4. Inspect trace when confidence or evidence matters.
5. Save or review session under Projects.
6. Export trace/data where needed.

### Admin/operator journey

1. Start in Dashboard/Admin.
2. Check provider, storage, MCP, and system health.
3. Review metrics/errors.
4. Inspect traces for high-risk results.
5. Manage privacy/export/delete or compliance workflows.

---

## Shell and layout system

1. `RootLayout` composes app-wide providers, sidebar, navigation, cloud disclosure, and routed content.
2. `AppSidebar` is the primary navigation model.
3. `NavBar` exposes top-level controls, theme, status, and user menu behavior.
4. `CloudDisclosureBanner` communicates provider/cloud behavior.
5. `AuthProvider` manages session and desktop local-auth behavior.
6. `ApiErrorBoundary` keeps API failures recoverable at the UI boundary.
7. `DesktopStatus` indicates local/desktop runtime state.

Relevant files:

- `frontend/app/layout.tsx`
- `frontend/components/layout/AppSidebar.tsx`
- `frontend/components/layout/NavBar.tsx`
- `frontend/contexts/AuthContext.tsx`
- `frontend/lib/runtime/policy.ts`

---

## Access and routing policy

1. Protected route policy is enforced in frontend runtime/proxy behavior.
2. Public routes include landing, auth, about, cloud-service disclosure, AI-limitations, and legal/privacy pages.
3. Desktop requests can bypass web login only when local/Electron/loopback conditions are met.
4. Web/browser requests without auth session should redirect to login.
5. Canonical API behavior should use `/api/v1/*` and JSON-native auth errors.
6. `/register` remains disabled by design in local-first mode.

---

## Trace review design requirement

Trace review is a core product differentiator.

Trace pages should help users answer:

1. What did the system do?
2. What evidence was used?
3. Which claims were made?
4. Which personas or roles contributed?
5. Which policy decisions occurred?
6. What was the confidence/risk/convergence state?
7. Can this run be exported or audited?

Design guardrail: AI answers should not be treated as isolated chat text when trace data exists.

---

## Local-first and privacy design requirement

The UI should make local-first behavior clear without falsely implying air-gapped operation.

Required clarity:

1. local storage status;
2. provider/cloud disclosure;
3. AI processing preferences;
4. export/delete controls;
5. connector behavior and scopes;
6. storage lifecycle actions;
7. privacy policy path.

Relevant routes:

- `/settings`
- `/settings/privacy`
- `/about/cloud-services`
- `/about/ai-limitations`
- `/legal/privacy`

---

## Performance and lazy-loading model

| Route/surface | Lazy-loaded unit | Benefit |
|---|---|---|
| `/chat` | chat workspace components | avoids loading heavy chat code before needed. |
| `/settings` | provider/storage/config panels | defers advanced settings modules. |
| `/mcp` | tab panels | reduces first-paint cost. |
| `/graph` | graph visualization package | avoids SSR failures and large initial JS cost. |
| global | route loading states | provides feedback during transitions. |

Design guardrail: heavy visualization and admin surfaces should not degrade first-run dashboard/chat experience.

---

## UX state model

1. Authentication state: `AuthContext` with desktop auto-login fallback logic.
2. Runtime mode: `frontend/lib/runtime/policy.ts`.
3. Theme state: theme provider/context.
4. API state: `frontend/lib/api/*` with session-aware requests.
5. Realtime/async state: websocket hooks and polling where applicable for chat/simulations/traces.
6. Sidebar state: persisted collapse/expand behavior.
7. Error state: API error boundary and page-level empty/error states.

---

## Accessibility baseline

Current accessibility expectations:

1. global skip link;
2. explicit labels for nav and panel toggles;
3. keyboard-accessible navigation;
4. loading and empty states;
5. readable dark and light themes;
6. automated accessibility checks;
7. manual screen-reader evidence before final production distribution.

Accessibility release caveat: manual NVDA or equivalent assistive-technology evidence remains required before final public release claims.

---

## Product validation

Use these commands for route and UX validation:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\test_frontend_route_policy.ps1 -FrontendPort 3000
cd frontend
npm run lint
npm run typecheck
npm test
npm run test:e2e -- tests/e2e/route-sidebar-smoke.spec.ts
npm run test:e2e:visual
cd ..
```

Additional release validation:

```powershell
python .\scripts\runtime_precheck.py --strict --skip-ports --allow-env-from-process
python .\scripts\verify_docs_references.py
```

---

## Known UX debt

UX debt and product backlog items are consolidated in the root `TODO.md`. This design guide documents the current UX model and validation approach and should not maintain a second backlog.

Known current caveats:

1. manual screen-reader evidence remains required;
2. `/register` is intentionally disabled in local-first mode;
3. some specialist surfaces depend on backend data/configuration state;
4. provider-backed features require configured provider credentials;
5. graph/vector/object-store views depend on local data services and ingestion state.

---

## Troubleshooting

1. Protected pages show unexpected redirects: verify auth cookies, desktop runtime mode, and loopback conditions.
2. Graph/heavy views stall: check browser console, backend API health, graph service status, and local data services.
3. Light mode appears unreadable: confirm latest frontend assets and clear browser cache.
4. Chat lacks provider response: verify provider key/model in Settings and provider test result.
5. Trace page empty: generate a run first and confirm backend trace API is reachable.
6. Settings storage panel missing values: validate local data services and absent-backend empty states.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Updated product design around current DMRF, Truth Engine, Trace Explorer, MCP, privacy, and local-first architecture.
3. Added product design thesis, core user journeys, trace review requirements, and local-first privacy requirements.
4. Added current shell/layout, state, accessibility, validation, and troubleshooting guidance.
