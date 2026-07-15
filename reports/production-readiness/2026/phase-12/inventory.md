# Phase 12 UI Workflow, Product Model, and Accessibility Inventory

Date: 2026-07-14
Status: engineering inventory complete; installed acceptance remains open
Plan authority: `PRODUCTION_COMPLETION_PLAN_2026.md`, Phase 12

## Current control inventory

The Phase 0 heuristic was replaced with a multiline-aware production-source scan
that excludes tests, stories, generated builds, and primitive UI definitions;
recognizes links, `asChild` targets, trigger wrappers, handlers, submit controls,
and literal/conditional disabled state; and records exact source locations.

Final engineering-checkpoint result:

- 27 pages;
- 194 production control instances;
- 191 wired or targeted controls;
- three truthfully, literally disabled controls;
- 17 controls with a literal or conditional disabled state;
- zero enabled controls without an obvious static action.

This is CP12-A source evidence only. A handler can still perform incomplete or
misleading work, so installed action-to-durable-effect testing remains required.

## Product-model decision

ADR-0009 selects the Session Library. The existing `/projects` paths are
compatibility routes over durable chat sessions; there is no independent Project
entity or workspace lifecycle. Unsupported file, note, message-action, and
project-status controls were removed. Future independent workspaces require a new
schema/API/ownership/migration decision.

## Workflow ledger

| Owner workflow | Current source boundary | Engineering state | Remaining proof/work |
|---|---|---|---|
| First launch and internal services | Electron status plus storage/service settings | Partial | Packaged first-run, repair, restart, recovery, and state-retention E2E |
| Provider key lifecycle | Protected OpenAI/Google save/test/replace/remove plus usage ledger | Source implemented | Installed provider and failure acceptance |
| External gateway | Listener/profile, client keys, scopes/limits, usage and examples | Source implemented; private mode gated | Same-host/private TLS/firewall/two-machine installed proof |
| Built-in chat | Governed send, attachment, mode, durable trace, timeout/cancel, plus encrypted offline queue review/export/replay/delete/clear | Source implemented | Installed reference-client and queue/store parity |
| Trace/run review | Lists, detail, stages, personas, evidence and export | Source implemented | Packaged real-service and visual/accessibility proof |
| Session Library | Durable session list/filter/detail under compatibility routes | Source implemented | Optional rename/archive/delete only after durable API design |
| Knowledge ingestion | Select, ingest, progress, cancel, retry, delete, consistency | Source implemented | Installed store-effect and failure/recovery proof |
| Knowledge Graph | Search, axis filter, node detail, provenance link and JSON export | Source implemented | Installed Neo4j/provenance/camera/visual proof |
| Algorithms | Category/search/detail/input/execute/history/limitations | Source implemented | Installed real-controller and accessibility proof |
| Simulations | Create/run/pause/resume/retry/cancel/results/artifacts | Source implemented | Installed provider/store/event/UI qualification |
| MCP | Register/review/consent/discover/call/cancel/stop/restart/revoke/remove | Source implemented | Deferred Phase 11 packaged containment/workflow qualification |
| Storage | Status, start/stop/restart, metrics and encrypted backup | Partial | Offline restore/recovery UI guidance and installed lifecycle proof |
| Privacy | Owner export and destructive delete controls | Source implemented | Installed multi-store deletion/export acceptance |
| Support bundle | Redacted command-line generator only | Open; Phase 13 dependency | Explicit owner UI, preview, output selection and redaction proof |
| Accessibility | All 27 routes pass axe; keyboard/app-readiness evidence passes 10 workflows | Automation pass | Packaged zoom/scaling, high contrast, reduced motion, visual and NVDA acceptance |

## First remediation slice

- Removed the unsupported Advanced Configuration panel and its fake confidence,
  persona, simulation-layer, jurisdiction, compliance, preset, and reset controls.
- Removed actionless chat export/clear, response regenerate/report/share, project
  upload/note/message actions, and optimistic status affordances.
- Added a real local validation-report JSON export.
- Replaced editable-looking profile fields with truthful read-only owner metadata.
- Removed the hardcoded dashboard `+12%` trend and non-actionable activity cues.
- Added backend-sourced dashboard and MCP analytics timestamps.
- Changed analytics failures from fabricated empty/zero success to explicit
  unavailable responses.
- Changed compliance records from `Active` to `Configured`; registry presence is
  not certification.
- Disabled unavailable voice input with an explicit reason.
- Added owner-visible encrypted offline queue review, redacted metadata export,
  policy/budget-enforced replay, single deletion, confirmed clear, timestamps,
  and explicit unavailable/progress/error states.
- Expanded axe automation to all 27 production routes and repaired the dashboard
  contrast findings; the automated app-readiness/keyboard suite now passes ten
  workflows, including the offline queue lifecycle.
- Hardened Windows MCP shutdown discovered by the full Phase 12 regression:
  descendant capture now occurs before connector stdin closes, job termination
  uses typed 64-bit native handles, and captured breakaway descendants are
  terminated explicitly.

## Engineering checkpoint boundary

CP12-A source evidence, CP12-B source semantics, CP12-D source contract parity,
and CP12-E browser automation pass at the engineering boundary. CP12-C remains
open until all primary workflows prove real installed service/store effects;
CP12-E still requires packaged visual/scaling/high-contrast checks; CP12-F manual
NVDA acceptance remains open. Those gates move forward unchanged and are not
represented as closed by component or route-mocked browser tests.
