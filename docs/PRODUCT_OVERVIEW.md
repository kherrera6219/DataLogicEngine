# DataLogicEngine Product Overview

## Purpose

Describe what DataLogicEngine does, which capabilities are currently production-usable, and where work is still in progress.

## Audience

1. Product and business stakeholders
2. Implementers and solution architects
3. Operators evaluating deployment fit

## What DataLogicEngine Is

DataLogicEngine is a local-first AI orchestration application that combines:

1. Chat-driven AI workflows
2. Traceable run execution and review
3. Knowledge graph exploration
4. Simulation workflows
5. Provider and storage operations controls

## Deployment Modes

1. Web mode: browser UX with login/session authentication.
2. Desktop mode: Windows Electron runtime with no-login boot to the internal dashboard.

## Current Capability Status (February 16, 2026)

| Area | Routes | Status | Notes |
|---|---|---|---|
| Chat and session workflows | `/chat`, `/projects`, `/projects/view` | Live | Session list/detail are backend-backed |
| Run and trace visibility | `/runs`, `/runs/view`, `/dashboard` | Live | Live telemetry with empty-state fallbacks |
| Simulations | `/simulations` | Live | Run orchestration and status tracking |
| Knowledge graph | `/graph` | Live | Interactive graph and node inspection |
| Settings: API gateway | `/settings` (`API Gateway`) | Live | Save key, provider test, query playground |
| Settings: AI model controls | `/settings` (`AI Models`) | Live | Provider/model selection + save/test |
| Settings: storage operations | `/settings` (`Storage`) | Mixed | Health + local lifecycle live; cloud config persistence still partial |
| Settings: notifications | `/settings` (`Notifications`) | Partial | Placeholder UI only |
| Admin dashboard | `/admin` | Live | Role-gated, backend-backed stats/user data |
| MCP admin registry | `/admin/mcp`, `/admin/mcp/servers` | Mixed | Stats/list/delete live; add server flow pending |
| Connector scope enforcement | MCP tool execution paths | Live | Runtime scope checks added with user/tenant context propagation |
| Connector safety controls | API gateway/service discovery | Live | SSRF outbound validation + allowlist guardrails enforced |
| Connector observability | `/metrics`, analytics MCP stats | Live | Connector latency/error telemetry exported |
| Data/integrity release gates | CI + deploy workflows | Live | Schema parity and installer checksum verification required in pipeline |
| Public info/legal pages | `/about`, `/about/*`, `/legal/privacy` | Live | Informational pages available |
| Registration flow | `/register` | Partial | UI present, submit flow not wired |

## Data and Service Model

1. Default local runtime supports SQLite and in-memory fallbacks.
2. Optional local services support PostgreSQL, Redis, Neo4j, vector DB, and object storage.
3. AI inference requires at least one valid provider API key and internet access.

## Known Gaps

1. `Settings > Notifications` is not implemented.
2. `Settings > Storage > Cloud Config` form is not fully persisted.
3. MCP admin add-server actions are not yet enabled.
4. Register form does not submit to backend registration API.
5. Connector OAuth lifecycle framework and API contract validation are not fully generalized yet (Phase 2 workstream).
6. Support-bundle diagnostic generator is not yet complete (Phase 2 workstream).

## Validation Commands

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
.venv\Scripts\python.exe .\scripts\verify_api_keys.py
powershell -ExecutionPolicy Bypass -File .\scripts\windows\test_frontend_route_policy.ps1 -FrontendPort 3000
.venv\Scripts\python.exe .\scripts\verify_local_data_stack.py
```

## Related Documents

1. `docs/USER_GUIDE.md`
2. `docs/DEVELOPER_GUIDE.md`
3. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
4. `docs/ARCHITECTURE.md`
5. `docs/API.md`

## Document Control

1. Owner: Product and Platform Engineering
2. Last updated: 2026-02-16
3. Status: Active
4. Review cadence: Every 30 days
