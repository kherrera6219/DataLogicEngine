# Phase 13 critical failure semantics

Date: 2026-07-14 (America/Los_Angeles)

Status: source regression contract; installed injection matrix remains open.

The executable authority is
`backend/utils/exceptions.py::CRITICAL_BOUNDARY_FAILURE_SEMANTICS`. This record
explains the intended behavior without treating the legacy broad-catch inventory
as resolved.

| Boundary | Behavior | Required terminal state | Rationale |
|---|---|---|---|
| Authentication and authorization | Fail closed | Request rejected | Identity or permission uncertainty cannot grant access. |
| Policy and safety gates | Fail closed | Request blocked | Missing/failed policy cannot release work or content. |
| Configuration and migration | Fail closed | Capability unavailable | Invalid configuration/schema cannot report readiness. |
| Durable mutation and artifact write | Fail closed | Failed or partial | A failed write cannot be reported committed/materialized. |
| Provider and tool execution | Fail closed | Typed terminal failure | No upstream/tool error may become fabricated output. |
| Corruption and integrity | Fail closed | Quarantine/recovery required | Unverified data cannot be released as trusted. |
| Optional external telemetry | Fail soft | Telemetry unavailable | Opt-in telemetry cannot interrupt local work. |
| Diagnostics and support export | Fail soft | Support operation failed | Failure is explicit while the local runtime remains usable. |
| Metrics observation | Fail soft | Metrics degraded | Metrics are non-authoritative and cannot change work results. |
| Process/task outer boundary | Fail closed | Internal defect recorded | Unknown defects may be caught only to preserve safe terminal state. |

Typed categories cover authentication, authorization, policy, validation,
configuration, migration, service, provider, tool, timeout, cancellation,
persistence, corruption, and internal defects. Safe metadata exposes category,
code, behavior, retryability, and optional capability without exception text,
paths, credentials, provider bodies, prompts, or documents.

The AST regression gate scans 532 production Python files and currently records
1,104 broad/bare catches in 321 files with zero module-level root-logging
configuration. These sites remain a deliberate audit queue. The gate fails if
the queue grows, a module reintroduces `logging.basicConfig`, a required typed
category disappears, or production source no longer parses.
