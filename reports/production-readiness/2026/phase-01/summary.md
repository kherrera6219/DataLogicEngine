# Phase 1 Evidence Summary

## Status

| Field | Value |
|---|---|
| Phase | 1 - Trust boundary and public error closure |
| Started | 2026-07-13 |
| Completed | 2026-07-13 |
| Current checkpoint | CP1-A through CP1-F pass |
| Release posture | Phase 1 GO; overall production/public release remains NO-GO pending Phases 2-18 |

## Closure results

1. The live manifest classifies 424 Flask routes, 12 GraphQL operations, 19
   Electron IPC channels, 6 MCP JSON-RPC methods, 5 file capabilities, and 5
   network surfaces. No surface is unclassified and no mutation lacks
   authentication evidence.
2. The exhaustive anonymous-mutation runtime test covers 179 mutation rules;
   all fail closed before protected execution.
3. GraphQL uses the authenticated server principal, production introspection is
   controlled, depth/field limits are enforced, and errors are normalized.
4. MCP REST/JSON-RPC context is server-owned; caller identity/scope fields are
   rejected and missing scope fails closed.
5. The public-error static gate scans 353 Python files with zero findings.
   Sentinel response suites pass, and GitHub reports zero open CodeQL alerts.
6. The freshly built production renderer and Electron main/preload pass the
   security gate: sandbox/isolation/web security, exact sender origin, typed
   methods, argument/return validation, timeouts, cancellation, and navigation/
   window restrictions are present.
7. Backup and ingestion paths remain in Electron main behind single-use,
   five-minute capability tokens and a main-process-only purpose signature.
8. The desktop listener is loopback-only; unsafe Host/Origin/proxy combinations
   and non-loopback binds are rejected. Private gateway mode remains disabled
   until Phase 8.
9. Desktop, provider, and saved internal-service secrets are protected with
   safeStorage/DPAPI plus restrictive ACLs. Plaintext packaged `.env` secrets
   migrate into protected storage, logs redact credential patterns, wrong KEKs
   fail without destructive registry regeneration, and backups exclude secret,
   settings, `.env`, log, and key files.
10. `docs/THREAT_MODEL.md` and all seven Phase 1 source-of-truth references are
    updated.

## Validation summary

- Backend security and integration routes: **398 passed** (17 SQLAlchemy legacy warnings).
- Phase 3 API governance compatibility check: **6 passed**.
- Health/API contract checks: **14 passed, 1 optional dependency skip**.
- Frontend API unit suite: **81 passed**; focused settings suite: **13 passed**.
- Ruff, TypeScript, production Next export, Electron compile, mandatory gates,
  docs reference validation, and ACL application: **pass**.
- Frontend lint: **0 errors, 1 pre-existing warning**.
- Documentation validation: **0 errors, 46 pre-existing style warnings**.

Phase 1 is ready for its phase commit. Phase 2 must not weaken any Phase 1 trust
decision.
