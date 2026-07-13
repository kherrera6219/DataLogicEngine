# Product Acceptance Charter

## Authority and status

| Field | Value |
|---|---|
| Product owner and acceptance authority | Kevin - DataLogicEngine owner |
| Product boundary | `PRODUCTION_COMPLETION_PLAN_2026.md` v1.2.0 sections 2.1-2.6 |
| Status | Phase 0 contract owner-approved 2026-07-13; measurable outcomes await assigned phases |
| Release posture | NO-GO until every required outcome has accepted installed-system evidence |

## Supported user and clients

The supported operator is one Windows owner operating DataLogicEngine locally.
Approved clients are the signed Electron desktop, its built-in reference chat,
same-host applications using the versioned gateway, and private Windows clients
only after the dedicated gateway profile is qualified. OpenAI and Google are
optional outbound model providers; they do not host the application or its data
plane.

## Primary jobs and measurable outcomes

1. Install, start, repair, upgrade, back up, restore, diagnose, and uninstall the
   application without losing retained user data.
2. Configure and validate OpenAI or Google credentials without exposing them to
   clients, logs, evidence, or build artifacts.
3. Submit a request from built-in chat or an approved external client and obtain
   a response through the same governed causal lifecycle.
4. Ingest local content, retrieve it semantically, traverse its graph provenance,
   inspect runs and evidence, and export integrity-verifiable artifacts.
5. Administer the five app-owned internal services and see truthful health and
   capability state without silent production fallbacks.
6. Operate simulations and MCP connectors only when their real production
   contracts, scopes, and evidence are complete.

Each job passes only with the numeric budget and installed-system evidence
assigned by the requirements traceability matrix and its target phase. A green
UI state, mock, skipped test, or fail-soft substitute is not acceptance.

## Explicit exclusions

Cloud SaaS, multi-tenant operation, public-internet gateway exposure, hosted
application databases, Kubernetes, mobile, macOS/Linux packaging, public
registration/SSO, unsupported model providers, and unsubstantiated compliance or
market-novelty claims are excluded from this completion program.

## Acceptance rule

Kevin is the Phase 0 owner and acceptance authority. Independent architecture, security,
API, usability/accessibility, and operations reviewers must still be named and
their reviews completed before production release; those assignments are
release-blocking in `responsibility-approval.json` until filled.
