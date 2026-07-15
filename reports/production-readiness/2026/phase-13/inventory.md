# Phase 13 live inventory

Date: 2026-07-14 (America/Los_Angeles)

Status: implementation entry inventory; production/public release remains
**NO-GO**.

## Scope inspected

1. Flask request lifecycle, runtime lifecycle, health/readiness/capability and
   metrics routes.
2. Backend JSON logging, audit/security logs, crash capture, log rotation, and
   redaction helpers.
3. Electron runtime logging, signed loopback fetches, renderer client errors,
   and Next request IDs.
4. Provider, MCP, DMRF, ingestion, simulation, and cross-store correlation and
   metrics call sites.
5. Support-bundle generation and operational runbooks.
6. Compliance routes, exports, registry data, and the owner-facing compliance
   page.
7. Production Python broad exception handling. The heuristic inventory finds
   1,113 broad-catch sites across 320 files and six module-level
   `logging.basicConfig` calls. These counts are an audit queue, not a claim that
   every site is defective; process/task boundaries may retain documented broad
   catches.

## Existing foundations

| Area | Live implementation |
|---|---|
| Backend logs | `backend/logging_config.py` provides JSON output, PII/secret pattern redaction, and bounded rotating app/security/audit files. |
| Correlation | Flask accepts/creates `X-Correlation-ID` and `X-Request-ID`; JSON logs include the request ID; readiness/capability responses and governed trace persistence retain correlation in selected paths. |
| Metrics | Authenticated `/metrics` exposes process/request/route latency and status, readiness, AI/provider latency, connector latency, DMRF, SLO, and crash counters. |
| Diagnostics | Authenticated health and capability contracts exist at `/api/v1/system/diagnostics/health` and `/api/v1/system/capabilities`. |
| Crash capture | Backend fallback crash IDs work without an external provider; Sentry integration exists when configured. |
| Desktop logs | Electron writes a local bounded runtime log and redacts common secret formats. |
| Compliance UI | The owner page labels registry entries as `Configured` and states that presence is not certification. |
| Runbooks | `docs/OPERATIONAL_RUNBOOKS.md` defines severity, global handling, support capture, and 22 incident procedures. |

## Gaps found

### Correlation and structured events

1. Caller-provided correlation headers are not syntax/length validated before
   being echoed, logged, and persisted.
2. Renderer API calls and Electron loopback requests do not consistently create
   and propagate one correlation ID. The Next proxy creates a separate page
   request ID, while several job/store paths substitute entity IDs.
3. The JSON log contract does not guarantee schema version, component, event,
   severity, safe error code, duration, state transition, or redaction class on
   every record.
4. Electron logs are plain text and truncate the only file at its size limit;
   they do not retain bounded rotated generations or structured event fields.

### Error and capability truth

1. The exception hierarchy covers a small API-oriented subset, while provider,
   persistence, migration, tool, timeout, cancellation, corruption, and runtime
   errors use separate local conventions.
2. The broad-catch inventory is too large for unreviewed mechanical replacement.
   Critical request, provider, storage, simulation, MCP, and worker boundaries
   need an allowlisted fail-closed/fail-soft matrix and a gate against regression.
3. Six production modules configure root logging themselves and can conflict
   with the application-owned logging configuration.

### External telemetry and client errors

1. Backend Sentry activation currently follows `SENTRY_DSN` alone; there is no
   separate explicit opt-in flag even though external telemetry must be disabled
   by default.
2. Renderer client errors use a global Sentry object when present without a
   product opt-in check; the console fallback can contain raw error/context
   strings.

### Support bundles

1. Bundle creation is explicit and size-bounded, but it copies recent logs and
   reports byte-for-byte. Existing source logging redaction is not proof that
   every copied file is safe.
2. Redis and other URL-shaped environment values can retain credentials; HTTP
   probe headers are copied without an allowlist.
3. There is no preview-only manifest, deterministic canary redaction suite,
   per-file manifest hash, archive hash sidecar, or optional encryption path.
4. The generic reports copy can include user-selected exports or content-bearing
   evidence and is not an approved support-bundle contract.

### Diagnostics, compliance, and operations

1. Authenticated diagnostic JSON exists, but there is no dedicated owner page,
   redacted event review, support-bundle preview/export workflow, or bounded safe
   repair action surface.
2. Compliance registry records do not yet resolve each displayed result to a
   typed claim class, versioned check, execution time, scope, result, and evidence
   link.
3. Runbooks do not yet have dedicated full-disk, high-memory, failed-update,
   data-deletion-failure, support-bundle-redaction, or soak-growth incidents.
4. The 24-hour stress and 72-hour idle/normal-use soak profiles and bounded-growth
   evaluators do not exist.

## First implementation order

1. Validate and propagate correlation IDs; define the structured event schema.
2. Require explicit external-telemetry opt-in and sanitize renderer fallback
   reporting.
3. Replace generic support collection with previewable, allowlisted, fully
   redacted, hashed bundle contents and canary tests.
4. Extend authenticated diagnostics and add the owner-facing diagnostics page.
5. Add the error/fail-semantics inventory gate, compliance evidence resolver,
   missing runbooks, and soak profiles.

Installed multi-process reconstruction, packaged diagnostics/repair, real
support export, failure injection, and 24/72-hour soak evidence remain later
Phase 13 acceptance gates.

## Engineering checkpoint resolution update

The source checkpoint completed the first implementation order:

1. caller correlation IDs are bounded and validated; renderer/Electron requests
   originate IDs; Flask binds request and background-task context; governed trace
   persistence retains the active correlation ID;
2. backend and Electron logs emit `dle.log.v1` JSON with canonical nullable error,
   duration, and state-transition fields; Electron logs now rotate through four
   backups instead of truncating the active file;
3. backend and renderer external telemetry require separate explicit opt-in and
   apply redaction before provider/console capture;
4. authenticated diagnostics plus preview/confirm/export UI/API contracts are
   implemented, and support archives are allowlisted, re-redacted, hashed,
   retained, and optionally encrypted;
5. all required typed error categories and a critical-boundary fail-semantics map
   exist. The AST inventory now records 1,104 broad/bare catches in 321 files and
   prevents growth beyond this legacy queue; module-level `logging.basicConfig`
   calls are zero;
6. the former simulated circular dependency check is now a real AST graph gate.
   It truthfully reports four existing cycles, retained as open technical debt;
7. compliance outputs are self-assessment/control-map evidence, empty evidence is
   `not_measured`, false framework coverage scores and compliant-by-default paths
   are removed, and source records/check versions/times/scope/results/evidence
   references are required;
8. full-disk, resource-growth, failed-update, deletion, support-redaction,
   unexpected-egress, and soak-degradation runbooks plus versioned stress24 and
   idle72 evaluators are implemented.

The short stress-profile observation validates resource collection and bounds but
is explicitly `engineering_observation_only`. It does not satisfy CP13-E.
