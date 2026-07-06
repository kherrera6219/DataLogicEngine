# DataLogicEngine Product Overview

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.8.0 |
| Last updated | 2026-07-06 |
| Status | Active |
| Owner | Product and Platform Engineering |
| Review cadence | Every 30 days |

## Purpose

Describe what DataLogicEngine is, what it does, which capabilities are currently usable, and how the product maps to the current DMRF, Truth Engine, local-first, trace, security, and governance architecture.

## Audience

1. Product and business stakeholders
2. Implementers and solution architects
3. Operators evaluating deployment fit
4. Contest judges and technical reviewers
5. Sponsors, employers, and enterprise evaluators

## What DataLogicEngine is

DataLogicEngine is a licensed, local-first Windows AI gateway and governed reasoning runtime.

It is intended to run on the user's own Windows system or on a user-controlled Windows VM. The user or organization brings their own AI provider accounts, API keys, connector credentials, storage location, and operating policy.

DataLogicEngine is not intended to be operated as a conventional multi-tenant SaaS where the project owner hosts customer data, manages customer API spend, or centrally secures customer workspaces.

It combines:

1. governed AI chat and reasoning workflows;
2. DMRF control-plane orchestration;
3. Truth Engine security, workflow, audit, and eventing;
4. 17-axis knowledge routing;
5. DSQP structured persona construction;
6. traceable run execution and review;
7. knowledge graph exploration;
8. local-first storage and memory systems;
9. MCP connector and tool governance;
10. desktop packaging and release-governance controls.

The product is not simply a chat wrapper around an LLM. Its core lifecycle is:

```text
application / chatbot / agent
  -> DataLogicEngine API gateway
  -> security/API envelope
  -> DMRF
  -> TruthGate
  -> tiering
  -> 17-axis routing
  -> DSQP
  -> TruthCore
  -> model/tool execution where required
  -> evidence/convergence
  -> memory/audit
  -> trace review/export
  -> API response
```

## Licensing and operating model

The intended commercial model is licensed software, not managed SaaS operations.

| Responsibility | Intended owner |
|---|---|
| Software license | DataLogicEngine vendor/project owner |
| Installation target | User/customer system or user-controlled Windows VM |
| AI provider account | User/customer |
| API keys and provider spend | User/customer |
| Local data, traces, memory, documents, exports | User/customer environment |
| Backups and retention | User/customer/operator |
| Provider terms, regional settings, and retention settings | User/customer/provider contract |
| Connector credentials and external service permissions | User/customer |
| Central hosting of customer data | Not the default product model |
| Central management of customer API bills | Not the default product model |

This model is designed to reduce vendor custody of customer data and avoid the vendor becoming the operator of customer API usage.

## Deployment modes

| Mode | Description | Status |
|---|---|---|
| Local-first desktop | Windows Electron runtime with loopback backend, desktop local-auth, local storage, and user-provided provider keys. | Primary target; current rebuild, installer, install smoke, and uninstall smoke validated |
| Windows VM gateway | Same Windows app stack running inside a user-controlled Windows VM as API-in/API-out middleware between applications/agents/chatbots and AI providers/tools. | Supported |
| Controlled web/cloud | Hosted deployment where explicitly configured by the operator. This is not the default managed SaaS model. | Conditional |

## Product surfaces

| Surface | Routes | Purpose |
|---|---|---|
| Dashboard | `/dashboard` | system overview and entry point. |
| Enterprise AI | `/chat` | governed AI interaction surface. |
| Trace Explorer | `/runs`, `/runs/view` | run review, evidence, stages, personas, trace details. |
| Graph / Knowledge | `/graph`, `/knowledge` | graph exploration, nodes, edges, coordinate context. |
| Projects | `/projects`, `/projects/view` | project/session organization. |
| Simulations | `/simulations` | scenario simulation and status tracking. |
| Truth Engine | `/truth-engine` | Truth Engine monitoring and review. |
| MCP Hub | `/mcp`, `/admin/mcp`, `/admin/mcp/servers` | connector/server registry and governance. |
| Admin | `/admin` | admin dashboard, providers, compliance, audit views (single-mode OS-level auth). |
| Settings | `/settings`, `/settings/privacy` | provider, model, storage, privacy, notifications, local config. |
| Public/legal | `/about`, `/about/*`, `/legal/privacy` | disclosures, limitations, privacy information. |

## Current capability status

| Area | Status | Notes |
|---|---|---|
| Chat and AI workflows | Live | backend-backed sessions, provider/model configuration, trace metadata where enabled. |
| DMRF control plane | Live | injection defense, TruthGate, tiering, axis routing, DSQP, TruthCore plan, evidence/convergence, memory/eventing. |
| Truth Engine | Live | TruthGate, TruthCore, TruthMemory, TruthLink modules and APIs. |
| 17-axis routing | Live | implemented under `core/axes/` and `backend/dmrf/router.py`. |
| DSQP personas | Live | deterministic/offline structured personas for axes 8-11. |
| Trace Explorer | Live | run detail review, stages, evidence, claims, personas, metrics, export path. |
| Knowledge graph | Live | graph and knowledge views, SQL/Neo4j/USKD model support. |
| Knowledge ingestion | Live | local ingestion APIs, text/binary support, manifests, optional Neo4j sync. |
| Settings/API gateway | Live | provider save/test, query playground, model/provider controls. |
| Storage operations | Live | local storage status and lifecycle controls. |
| Notifications | Live | user preferences loaded and persisted through user notification API. |
| Admin dashboard | Live | backend-backed admin data (system metrics, provider status, compliance). |
| MCP admin registry | Live | stats/list/add/delete flows (single authenticated owner). |
| Connector safety | Live | scope checks, SSRF/upstream guardrails, schema validation, telemetry. |
| Observability | Live | `/metrics`, route metrics, AI/connector latency signals, DMRF/Truth signals where enabled. |
| Data/integrity gates | Live | schema parity, runtime precheck, docs validation, lockfile/environment governance. |
| Trace export authenticity | Live | hashes, optional HMAC signature, optional encrypted export envelope. |
| Desktop local-auth | Live | loopback/Electron policy, install secret, nonce/HMAC, timestamp skew. |
| Installer packaging | Live | PyInstaller backend, Next.js static export, Electron shell, NSIS installer, root checksum/blockmap, packaging smoke, installer-mode install/uninstall smoke, and unsigned-local signature reporting. |
| Registration flow | Disabled by design | current local-first build redirects `/register` to `/dashboard`; reopen only if web self-registration becomes a requirement. |

## Current rebuild evidence

The latest local rebuild evidence on the current `main` line records:

1. PyInstaller backend rebuild completed before Electron packaging.
2. Root installer artifacts refreshed: `DataLogicEngine Setup Latest.exe`, `.sha256`, and `.blockmap`.
3. Installer integrity report passed with SHA-256 `a398c6cf1f92b1ff85b29231f58eb6d1ead96184304cf83ce61d5390ab54b496`.
4. NSIS governance passed.
5. Portable packaging smoke passed.
6. Installer-mode smoke passed with silent install exit code `0` and uninstall exit code `0`.
7. Local signature verification reports `NotSigned`, which is expected for unsigned workstation builds and remains a blocker for public signed production distribution.

Tracked evidence files: `reports/installer_integrity_report.json`, `reports/installer_signature_report.json`, and `reports/packaging_smoke_report.json`.

## Data and service model

Current data architecture includes:

1. SQLAlchemy database with SQLite/PostgreSQL paths.
2. Redis for cache/session/rate-limit/queue/stream behavior where enabled.
3. Neo4j graph store where configured.
4. USKD NetworkX RAM graph for reasoning traversal.
5. ChromaDB local vector store.
6. Local object store for deliverables, audit logs, simulations, graphs, eval data, and exports.
7. UnifiedMemory structured reasoning memory.
8. TruthMemory audit/explainability memory.

Local-first does not mean air-gapped. AI provider or MCP connector calls may transmit selected prompts/context/tool inputs depending on configuration.

The key operating distinction is that these calls are made using user/customer-controlled provider accounts and keys. Provider billing, retention, terms, and regional settings are governed by the user's provider account and contract.

## Security and governance model

Product-level security and governance include:

1. desktop local-auth for local/hybrid runtime;
2. CSRF/CORS/trusted-host/session/rate-limit controls;
3. DMRF injection defense;
4. TruthGate security/budget/compliance gate;
5. trace and audit records;
6. export integrity;
7. release checklist and CI governance;
8. packaging smoke and signing verification;
9. privacy/export/delete user controls;
10. operational runbooks.

## Known gaps

Known gaps and product backlog items are consolidated in the root `TODO.md`. This overview should not maintain a second planning list.

Current high-level caveats:

1. signed public Windows distribution requires trusted certificate workflow completion;
2. manual accessibility evidence remains required before final production distribution;
3. provider-backed flows require valid user/customer-configured provider credentials and network access;
4. API spend controls are user/customer/provider-account responsibilities, not centrally managed by the project owner;
5. backups, local data retention, and endpoint security are operator responsibilities in local-first and Windows VM modes.

## Validation commands

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
.venv\Scripts\python.exe .\scripts\verify_api_keys.py
powershell -ExecutionPolicy Bypass -File .\scripts\windows\test_frontend_route_policy.ps1 -FrontendPort 3000
.venv\Scripts\python.exe .\scripts\verify_local_data_stack.py
python .\scripts\runtime_precheck.py --strict --skip-ports --allow-env-from-process
python .\scripts\validate_schema_parity.py
python .\scripts\verify_docs_references.py
```

## Reviewer path

A product reviewer should inspect:

1. `docs/diagrams/12_end_to_end_request_lifecycle.md`
2. `docs/diagrams/11_frontend_product_surface_and_trace_review_map.md`
3. `docs/ARCHITECTURE.md`
4. `docs/USER_GUIDE.md`
5. `docs/SECURITY.md`
6. `docs/PRODUCTION_READINESS.md`
7. `frontend/app/layout.tsx`
8. `frontend/components/layout/AppSidebar.tsx`
9. `backend/dmrf/orchestrator.py`
10. `backend/truth_engine/api.py`

## Related documents

1. `docs/USER_GUIDE.md`
2. `docs/DEVELOPER_GUIDE.md`
3. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
4. `docs/ARCHITECTURE.md`
5. `docs/API.md`
6. `docs/SECURITY.md`
7. `docs/PRIVACY_POLICY.md`
8. `docs/PRODUCTION_READINESS.md`

## Change notes for v2.8.0

1. Updated document version/date for the post-rebuild documentation refresh.
2. Clarified that local-first desktop is the primary validated product target and now includes current installer, install-smoke, and uninstall-smoke evidence.
3. Added a rebuild evidence section with the current installer hash and tracked report locations.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Updated product description around DMRF, Truth Engine, 17-axis, DSQP, trace, memory, and local-first architecture.
3. Added deployment mode matrix and product surface table.
4. Updated capability status to reflect current architecture.
5. Added security/governance model and reviewer path.
6. Added current caveats aligned with production readiness and security docs.
7. Clarified licensed local-first/BYOK operating model and user/customer responsibility for provider spend, API keys, local data, backups, and retention.
