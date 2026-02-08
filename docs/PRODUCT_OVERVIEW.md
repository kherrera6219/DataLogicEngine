# DataLogicEngine product overview

## Purpose

Explain what DataLogicEngine does, who it is for, and which capabilities are production-ready today.

## Audience

1. Business stakeholders evaluating product fit
2. End users and operators
3. Product managers and solution architects
4. Implementation partners

## Prerequisites

1. Internet access for cloud inference operations
2. At least one valid LLM provider API key
3. A running local or deployed DataLogicEngine environment

## Document control

1. Owner: Product and Platform Engineering
2. Last updated: 2026-02-08
3. Status: Active
4. Review cadence: Every 30 days

## Related documents

1. `docs/USER_GUIDE.md`
2. `docs/PRODUCT_DESIGN.md`
3. `docs/ARCHITECTURE.md`
4. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
5. `docs/API.md`

## What DataLogicEngine is

DataLogicEngine is an AI orchestration and knowledge operations application that combines:

1. Conversational AI workflows
2. Knowledge graph exploration
3. Traceable reasoning runs
4. Simulation orchestration
5. Policy-aware provider access and storage controls

The system is local-first on Windows and cloud-augmented for AI inference and optional managed data services.

## What the app does

1. Runs chat sessions through a gateway that can call multiple LLM providers and return trace metadata.
2. Organizes conversation history into project-style workspaces for recall, filtering, and review.
3. Visualizes knowledge nodes and relationships in a 3D graph explorer with node inspection.
4. Tracks simulation sessions and execution traces for operational visibility and auditability.
5. Exposes data-plane health for PostgreSQL, Redis, Neo4j, vector storage, and object storage.
6. Provides privacy controls to export and delete locally stored user data.

## Deployment modes

1. Web mode:
   Uses login/session authentication for protected routes.
2. Desktop mode:
   Uses Windows identity auto-login in loopback desktop runtime for no-login startup.

## Capability status by area

| Area | Primary routes | Current status | Notes |
|---|---|---|---|
| Conversational reasoning | `/chat`, `/projects`, `/projects/view` | Live | Uses gateway sessions and message APIs |
| Trace and run visibility | `/runs`, `/runs/view`, portions of `/dashboard` | Live | Uses trace and analytics endpoints |
| Simulation orchestration | `/simulations` | Live | Uses simulation APIs and websocket progress |
| Graph exploration | `/graph` | Live | Uses live nodes/edges with dynamic 3D render |
| Storage operations | `/settings` (Storage tab) | Live | Health and connection checks are backend-backed |
| API key management | `/settings` (API Gateway tab) | Mixed | Provider key save is live; model picker is partial UI |
| Admin console | `/admin` | Scaffold | Access control is live; much table data is static demo data |
| MCP operations | `/mcp`, `/admin/mcp`, `/admin/mcp/servers` | Mixed | Server registry pages are live; core hub/config pages are mostly demo data |
| Analytics and algorithms | `/analytics`, `/algorithms`, `/truth-engine`, `/knowledge` | Mixed | Combination of live calls and static placeholder datasets |
| Public disclosure and legal | `/about`, `/about/*`, `/legal/privacy` | Live | Informational pages for transparency and policy context |

## Data and service model

1. Default local runtime can use SQLite and in-memory fallbacks for fast startup.
2. Optional local data stack can include PostgreSQL, Redis, Neo4j, MinIO, and vector persistence.
3. AI inference requires cloud provider APIs and a configured key.

## Known limitations

1. Settings tabs `Notifications` and `AI Models` are placeholders in the current UI.
2. The register page presents UI fields but does not yet submit to the register API.
3. Several admin and MCP surfaces still show sample metrics while deeper integration is completed.
4. Some chat/project action buttons are UI placeholders and do not execute backend changes yet.

## Validation

Run the following checks after local startup:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
.venv\Scripts\python.exe .\scripts\verify_api_keys.py
powershell -ExecutionPolicy Bypass -File .\scripts\windows\test_frontend_route_policy.ps1 -FrontendPort 3000
.venv\Scripts\python.exe .\scripts\verify_local_data_stack.py
```

## Troubleshooting

1. Chat returns provider errors or `503`:
   Verify provider key validity and gateway provider configuration in `Settings > API Gateway`.
2. Protected routes always redirect to login in browser mode:
   Confirm backend auth session is established and cookies are present.
3. Desktop auto-login does not activate:
   Confirm desktop runtime, loopback access, and desktop header conditions are met.
