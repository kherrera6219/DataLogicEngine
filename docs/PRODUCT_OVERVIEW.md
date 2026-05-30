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

## Current Capability Status (May 22, 2026)

| Area | Routes | Status | Notes |
|---|---|---|---|
| Chat and session workflows | `/chat`, `/projects`, `/projects/view` | Live | Session list/detail are backend-backed |
| Run and trace visibility | `/runs`, `/runs/view`, `/dashboard` | Live | Live telemetry with empty-state fallbacks |
| Simulations | `/simulations` | Live | Run orchestration and status tracking |
| Knowledge graph | `/graph` | Live | Interactive graph and node inspection |
| Settings: API gateway | `/settings` (`API Gateway`) | Live | Save key, provider test, query playground |
| Settings: AI model controls | `/settings` (`AI Models`) | Live | Provider/model selection + save/test |
| Settings: storage operations | `/settings` (`Storage`) | Live | Health, local lifecycle, auto-start preference, and internal storage config persistence are wired; local port fields are display/edit UI only until a broader local-service config flow is needed |
| Settings: notifications | `/settings` (`Notifications`) | Live | Per-user preferences are loaded and persisted through `/api/v1/user/notifications`; delivery-channel integrations are not separately validated here |
| Knowledge ingestion | `/api/v1/ingestion/*`, `/settings` (`Knowledge`) | Live | Supports text and binary (PDF/DOCX) async ingestion with optional Neo4j sync and manifest-backed history |
| Admin dashboard | `/admin` | Live | Role-gated, backend-backed stats/user data |
| MCP admin registry | `/admin/mcp`, `/admin/mcp/servers` | Live | Stats, list, add, and delete flows are wired for admin users |
| Connector scope enforcement | MCP tool execution paths | Live | Runtime scope checks added with user/tenant context propagation |
| Connector safety controls | API gateway/service discovery | Live | SSRF outbound validation + allowlist guardrails enforced |
| Connector OAuth + contracts | Jira/Salesforce MCP tools | Live | Managed OAuth token lifecycle + runtime request/response contract validation |
| Connector observability | `/metrics`, analytics MCP stats | Live | Connector latency/error telemetry exported with p95/p99 SLO violation gauges |
| AI latency observability | `/metrics` | Live | Gateway latency percentiles (`p50`/`p95`/`p99`) plus p95/p99 SLO violation gauges |
| Data/integrity release gates | CI + deploy workflows | Live | Schema parity, installer checksum, deterministic startup precheck, and crash-reporting probe checks required in pipeline |
| Snapshot + trace integrity | FROST + tracing services | Live | Snapshot and audit bundle hash/HMAC verification enforced |
| Trace export authenticity | Trace export API | Live | Signed export manifests and optional encrypted payload envelopes |
| Tenant DB isolation | Postgres-backed APIs | Live | Request-scoped tenant context + RLS policy bootstrap controls available |
| Vault-backed secret enforcement | Runtime bootstrap | Live | Production runtime enforces secure secret sources (file/DPAPI/JSON/keyring) |
| Immutable audit replication | Audit logger | Live | Hash-chain immutable replica stream + verification controls active |
| Installer code signing | Release + governance workflows | Live | Signature verification plus certificate rotation/revocation drill workflows |
| Crash reporting hardening | Global Flask error handlers + `/metrics` | Live | Fallback crash IDs and provider telemetry/probe hooks active |
| Diagnostic tooling | Support bundle generator | Live | Sanitized support bundle script available for incident triage |
| Public info/legal pages | `/about`, `/about/*`, `/legal/privacy` | Live | Informational pages available |
| Registration flow | `/register` | Disabled by design | Current local-first build redirects `/register` to `/dashboard`; reopen only if web self-registration becomes a product requirement |

## Data and Service Model

1. Default local runtime supports SQLite and in-memory fallbacks.
2. Optional local services support PostgreSQL, Redis, Neo4j, vector DB, and object storage.
3. AI inference requires at least one valid provider API key and internet access.

## Known Gaps

Known gaps and product backlog items are consolidated in the root `TODO.md`. This overview describes current capability status and should not maintain a second planning list.

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
2. Last updated: 2026-05-23
3. Status: Active
4. Review cadence: Every 30 days
