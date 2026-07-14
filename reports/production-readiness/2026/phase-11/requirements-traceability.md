# Phase 11 Requirements Traceability

Date: 2026-07-14

| Plan requirement | Implemented authority | Primary evidence |
|---|---|---|
| Supported transport/lifecycle | MCP `2025-11-25`, local stdio only, explicit lifecycle | ADR-0008; policy, protocol, manager, routes |
| Server-owned context and fail-closed scope | Authenticated principal and persisted consent/scopes | route, router, and scope tests |
| Command/capability validation | Exact executable/args/cwd/env/file/network/limit policy and fingerprint | policy and malicious-fixture tests |
| Credential protection | DPAPI credential store and renderer-safe serialization | credential tests and server model contract |
| Child isolation and bounds | Durable runtime loop, bounded client, Job Object, cancellation | stdio fixture and client/manager tests |
| Remove placeholder production behavior | Fake/default web, sampling, UKG, KA, graph, and simulation paths removed | source inventory and regression tests |
| Durable data authorities | PostgreSQL consent/lifecycle/execution; Redis live mirror; object result reference | migration, schema/data inventory, route tests |
| Health/discovery/restart/cancel/version | Durable status and explicit owner API/UI controls | backend and frontend focused tests |
| Governed results | Untrusted envelope, redaction, injection/privacy/evidence/trace fields | policy and route result tests |
| Hostile fixtures | Malformed, oversized, delayed, cancellation, and child-spawn stdio servers | `tests/fixtures/mcp` and `tests/mcp` |

Items requiring a rebuilt installed environment are listed in
`deferred-gates.md`; they are not represented as passed by this traceability map.
