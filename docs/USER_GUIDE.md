# DataLogicEngine User Guide

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.9.0 |
| Last updated | 2026-07-13 |
| Status | Active |
| Owner | Product Operations |
| Review cadence | Every 30 days |

## Purpose

Provide task-focused instructions for day-to-day use of DataLogicEngine by analysts, operators, admins, pilot users, and technical evaluators.

This guide reflects the current local-first product: dashboard, chat, projects, traces, graph/knowledge, simulations, Truth Engine, MCP, settings, privacy, and admin workflows.

## Audience

1. Analysts and operators
2. The single owner/operator (single-mode admin)
3. Pilot users validating workflows
4. Technical judges and reviewers
5. Sponsors or employers reviewing the product experience

## Prerequisites

1. Running local desktop or the Windows VM qualification profile.
2. Internet access for cloud provider inference.
3. At least one configured OpenAI or Google/Gemini API key for provider-backed chat/reasoning.
4. Local storage services running when testing graph/vector/object/data features.

## Mode behavior

| Mode | Behavior |
|---|---|
| Desktop/local-first | App opens directly into the internal dashboard using desktop local-auth behavior. |
| Windows VM qualification | Same app stack inside a controlled VM with app-owned local services; this is a validation profile, not a public web service. |

Public web/cloud SaaS, web login, and self-service registration are outside the
active production-completion scope. The single owner is authenticated through
the local desktop trust boundary.

## Primary navigation

| Route | Use |
|---|---|
| `/dashboard` | Operational overview and quick actions. |
| `/chat` | Governed AI conversation and uploads. |
| `/projects` | Session/workspace list. |
| `/projects/view?id=<session_id>` | Session detail timeline. |
| `/simulations` | Simulation runs and scenario status. |
| `/runs` | Trace/run history. |
| `/runs/view?id=<run_id>` | Trace detail, evidence, stages, and export path. |
| `/graph` | Knowledge graph exploration. |
| `/knowledge` | Knowledge records and graph-related review. |
| `/truth-engine` | Truth Engine status and monitoring. |
| `/mcp` | MCP connector hub where enabled. |
| `/settings` | API, storage, AI model, preferences, and local configuration. |
| `/settings/privacy` | Export/delete profile data and manage privacy controls. |
| `/admin` | Admin telemetry/provider/compliance views (single owner; no user management). |
| `/admin/mcp/servers` | MCP server registry management. |
| `/legal/privacy` | Privacy policy surface. |

## First-run workflow

1. Launch the desktop app or local stack.
2. Open `/dashboard`.
3. Open `/settings`.
4. Configure at least one provider under API Gateway or AI Models.
5. Test the provider connection.
6. Open `/chat` and run a simple prompt.
7. Open `/runs` and inspect the trace/run record.
8. Open `/settings/privacy` and confirm export/delete controls are visible.
9. Open `/graph` or `/knowledge` if graph/knowledge data is available.

## Core workflows

### 1. Configure provider access

1. Open `/settings`.
2. Select `API Gateway` or `AI Models`.
3. Choose provider and model.
4. Enter API key.
5. Select `Save Key` or `Save Model`.
6. Select `Test Connection` or `Test Model`.
7. Read the exact state: `not configured`, `stored`, `validating`, `available`,
   `limited`, `invalid`, or `unavailable`. A saved key is only `stored` until a
   bounded live test proves availability.
8. If the test fails, use the specific reason: invalid key, unauthorized/invalid
   model, quota/rate/billing, network/outage, or timeout.

**Choose a cloud model:** the app uses one user-selected cloud model. In **Settings → AI/Model**, pick **OpenAI** (`gpt-5.5`) or **Google** (`gemini-3.1-pro-preview`) and save its API key. Every request is then served by that model. An API key and internet connection are required for reasoning.

### 2. Start governed AI chat

1. Open `/chat`.
2. Enter a prompt.
3. Attach supported files where available.
4. Send the request.
5. Review the external-data-category and current budget disclosure. If the
   80-percent warning threshold is crossed, confirm before resubmitting; a hard
   ceiling cannot be bypassed from the app.
6. Use **Cancel request** to cancel an active client request. The request keeps
   one stable request/trace identity and finalizes as cancelled.
7. Review the answer.
8. Follow run/session links to inspect trace details.

Behind the scenes, governed requests pass through the single `governed.v1`
path. The trace shows real sources/evidence, claims, citations, validators,
TruthCore/KA work, policy decisions, and convergence state that executed.

If the trace shows **Evidence support: Not measured**, one or more required
source-quality, provenance, freshness, claim-support, or validator inputs was
unavailable. This is not an error to hide and is never replaced with a default
percentage. A percentage, when present, is evidence-support coverage with a
formula explanation; it is not a promise that the answer is correct.

An **Abstained** result means required claims remained unsupported or
contradicted after the one allowed enhanced refinement. Provide a newer or more
authoritative source and retry. The Algorithms page labels production-enabled,
experimental, presentation-only, and placeholder entries and states each
guarantee and limitation.

### 3. Review sessions and projects

1. Open `/projects`.
2. Search by title, session ID, or visible metadata.
3. Open `/projects/view?id=<session_id>`.
4. Review messages, run references, and session timeline.

### 4. Review traces and evidence

1. Open `/runs`.
2. Select a run.
3. Open `/runs/view?id=<run_id>`.
4. Review available stages, evidence, claims, personas, policy decisions, metrics, and artifacts.
5. Export trace data where enabled.

Trace review is one of the main ways to understand why the system answered the way it did.

### 5. Explore graph and knowledge data

1. Open `/graph`.
2. Inspect available nodes and relationships.
3. Open `/knowledge` where available for knowledge records.
4. Use graph context to validate reasoning inputs, evidence, or project knowledge.

Graph/knowledge features may depend on local SQL, Neo4j, ChromaDB, object-store, or ingestion state.

### 6. Run simulations

1. Open `/simulations`.
2. Create or select a scenario.
3. Run the simulation.
4. Review status and results.
5. Open trace/run details where links are available.

### 7. Use Truth Engine monitoring

1. Open `/truth-engine`.
2. Review Truth Engine status where enabled.
3. Inspect health, budget, gate, memory, or link/event information where exposed by the current build.

### 8. Manage MCP connectors

1. Open `/mcp` or `/admin/mcp/servers`.
2. Review registered servers.
3. Add or remove servers where permitted.
4. Validate scopes and tool contract behavior.
5. Review connector health/latency signals where available.

MCP connector behavior depends on configured scopes, credentials, external service availability, and admin policy.

### 9. Run storage checks and lifecycle actions

1. Open `/settings`.
2. Select `Storage`.
3. Use `Refresh` for current health.
4. Use `Test Connection` per service.
5. Use `Start All` / `Stop All` for local data services where available.
6. Use auto-start toggle for local launch behavior.

### 10. Use privacy tools

1. Open `/settings/privacy`.
2. Use `Export My Data` for JSON export where enabled.
3. Use delete action with confirmation for local data removal.
4. Review AI processing/history preferences where available.
5. Review notification preferences where available.

### 11. Review provider usage and offline replay

1. Open `/settings` and select the API Gateway/provider panel.
2. Review session/day/month call and token limits, remaining allowance, and
   pricing status. `Unknown` means no trusted price metadata is configured; it
   never means free.
3. Review recent content-free egress categories and provider attempts.
4. Export the redacted ledger when owner review evidence is needed.
5. Reset it only through the explicit owner confirmation flow.
6. If replay is enabled, review or delete queued items. Only network,
   provider-outage, and timeout failures are eligible. A message is shown as
   queued only after encrypted durable storage succeeds.

The current SSE route delivers the fully governed response in buffered chunks;
it is not presented as native token streaming. Native governed streaming is a
Phase 8 qualification item.

## Understanding local-first privacy

Local-first means application data is stored locally by default in desktop/VM mode. It does not mean data never leaves the machine.

Data may leave the machine when:

1. cloud AI providers are configured;
2. MCP connectors or external APIs are configured;
3. users export/share trace bundles or data archives;
4. web/cloud deployment is used;
5. logs/reports are manually shared for support.

Review `docs/PRIVACY_POLICY.md` for details.

## Validation checklist

1. Dashboard loads without route errors.
2. Provider test succeeds after key setup.
3. Chat returns provider response after key setup.
4. Projects list and detail pages show session data.
5. Runs and trace detail pages render successfully.
6. Storage status panel returns service state.
7. Privacy page shows export/delete controls.
8. Graph/knowledge pages render expected empty or populated states.
9. Admin route loads for the single owner.
10. MCP admin route loads where enabled.

## Known limitations

1. Manual NVDA accessibility evidence remains open in `TODO.md`; automated WCAG, keyboard navigation, failure-mode, and export/delete evidence is tracked under `reports/app-readiness/`.
2. `/register` redirects to `/dashboard` in the current local-first build.
3. Release builds require trusted production code-signing evidence before public distribution.
4. Provider-backed features require valid provider credentials and network access.
5. Some graph/vector/object-store features require local data services to be started or initialized.

## Change notes for v2.9.0

1. Added exact provider states, preflight budget/egress disclosure, request
   cancellation, owner usage-ledger controls, transient-only replay, and truthful
   buffered-delivery guidance.

## Change notes for v2.7.0

1. Updated prerequisites to remove stale local/offline-provider wording.
2. Clarified that the current user-facing provider choices are OpenAI and Google/Gemini.

## Troubleshooting

### API/provider test fails

1. Re-save key.
2. Confirm provider/model selection.
3. Check for `invalid_api_key`, `rate_limited`, `invalid_model`, or `network_error`.
4. Confirm internet access.
5. Try a different configured provider/model.

### Chat says no active providers found

1. Open Settings -> AI Providers or AI Models.
2. Confirm at least one provider is saved and active.
3. Confirm the running desktop/backend is using the same local database.
4. Set provider key in `.env` as fallback.
5. Restart local stack or desktop app.

### Desktop shows login unexpectedly

1. Verify the app is running in desktop/local mode.
2. Confirm loopback backend is reachable.
3. Confirm desktop local-auth path is active.
4. Restart the app.
5. See `docs/WINDOWS_11_LOCAL_RUNBOOK.md` for desktop-auth troubleshooting.

### Storage offline

1. Open Settings -> Storage.
2. Start local services.
3. Refresh status.
4. Run local data stack validation.
5. Check local permissions and antivirus/file locks.

### Trace page is empty

1. Run a chat or simulation first.
2. Open `/runs`.
3. Confirm run ID exists.
4. Confirm backend trace API is reachable.
5. Confirm user/session permissions.

### Route redirects incorrectly in web mode

1. Re-authenticate.
2. Verify session cookie state.
3. Confirm canonical `/api/v1/*` endpoints return JSON auth errors.
4. Check deployment mode configuration.

## Related documents

1. `docs/PRODUCT_OVERVIEW.md`
2. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
3. `docs/PRIVACY_POLICY.md`
4. `docs/API.md`
5. `docs/ARCHITECTURE.md`
6. `docs/SECURITY.md`
7. `docs/OPERATIONAL_RUNBOOKS.md`

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Updated user workflow for local-first desktop, Windows VM, and web/cloud modes.
3. Added first-run evaluator workflow.
4. Added Truth Engine, trace review, graph/knowledge, MCP, privacy, and storage workflows.
5. Added local-first privacy explanation and expanded troubleshooting.
