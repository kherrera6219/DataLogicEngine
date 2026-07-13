# DataLogicEngine Production TODO

## Document status

| Field | Value |
|---|---|
| Last updated | 2026-07-13 |
| Status | Canonical open-work ledger |
| Active plan | `PRODUCTION_COMPLETION_PLAN_2026.md` v1.2.0 |
| Completed phase | Phase 0 - committed checkpoint pending |
| Next phase | Phase 1 - Trust boundary and public error closure |
| Release decision | Production/public release: **NO-GO** |
| Historical backlog | `docs/archive/session-history/TODO_through_2026-07-12.md` |

This file contains current open work only. Detailed requirements, stop
conditions, and exit gates remain authoritative in the active root plan.

## Phase 0 closure

CP0-A through CP0-G passed on 2026-07-13. Evidence is stored under
`reports/production-readiness/2026/phase-00/`. The baseline truthfully records a
healthy isolated five-service Podman profile and a failing unsigned 0.1.1
installer that does not provision or register the production application.

The owner-approved contract is:

- app-managed immutable OCI containers through rootless Podman Machine/WSL2;
- Windows 11 x64 Home, Pro, or Enterprise on a supported build;
- minimum 4 CPU cores, 16 GB RAM, and 50 GB free local NTFS disk;
- recommended 8 CPU cores, 32 GB RAM, and 100 GB free local NTFS disk;
- offline-capable installation and signed owner-initiated updates with rollback;
- Kevin as Phase 0 owner/acceptance authority; and
- mandatory independent reviews retained as pre-release blockers.

## Phase 1 objective

Close all P0 authentication, authorization, IPC, MCP, file-capability,
exception-disclosure, credential-storage, and local-network boundary defects.

## Phase 1 work packages

- [ ] Generate a live route manifest with an explicit public-health,
      authenticated-read, authenticated-mutation, external-client,
      owner/admin, desktop-only, or internal-only classification for every route.
- [ ] Apply canonical JSON API authentication to every active and legacy route.
- [ ] Require owner/admin authorization for governance, service lifecycle,
      destructive storage, policy, MCP configuration, backup, restore, and
      sensitive export operations.
- [ ] Separate public health fields from authenticated diagnostics.
- [ ] Secure GraphQL principal context, introspection, complexity, depth, and
      error normalization.
- [ ] Make MCP REST/JSON-RPC execution context server-owned and reject
      caller-supplied identity, tenant, role, and scope.
- [ ] Replace generic Electron preload access with typed approved capabilities.
- [ ] Validate IPC sender, arguments, path scope, return schema, timeout, and
      cancellation for every channel.
- [ ] Enforce Electron sandbox, isolation, navigation, window, and HTTPS external
      origin allowlists.
- [ ] Keep administration and internal-service interfaces loopback/private and
      reject untrusted Host, Origin, listener, and address-only trust.
- [ ] Rotate and DPAPI-protect the desktop install/HMAC secret with expiry,
      replay, nonce, and recovery rules.
- [ ] Complete CSRF protection for cookie/session paths and signed desktop calls.
- [ ] Replace public exception strings with stable codes, safe messages, and
      correlation IDs; retain details only in redacted local logs.
- [ ] Add repository-wide sentinel tests for JSON, GraphQL, SSE, WebSocket,
      export metadata, and UI error sinks.
- [ ] Replace renderer-supplied ingestion paths with expiring picker capability
      tokens bound to owner-selected paths.
- [ ] DPAPI-wrap provider/internal-service credentials, apply restrictive ACLs,
      and prove no plaintext mirror exists in settings, logs, crashes, or backups.
- [ ] Create the complete local-first threat model required by Phase 1.

## Phase 1 mandatory gates

- [ ] `scripts/verify_route_manifest.py --fail-unclassified`
- [ ] `scripts/verify_public_error_contracts.py`
- [ ] `scripts/verify_electron_security.py`
- [ ] `scripts/verify_secret_storage.py`

## Phase 1 checkpoints

| Checkpoint | Required result | Status |
|---|---|---|
| CP1-A | Route, GraphQL, IPC, MCP, file, and network inventories have no unclassified entry | Open |
| CP1-B | Every mutation denies anonymous or under-authorized callers | Open |
| CP1-C | Exception-sentinel and CodeQL checks are clear | Open |
| CP1-D | Packaged Electron checklist and IPC schema tests pass | Open |
| CP1-E | DPAPI, rotation, ACL, log-redaction, and backup-exclusion checks pass | Open |
| CP1-F | Gateway clients cannot reach owner/admin/internal capabilities or secrets | Open |

## Phase ledger

| Phase | Result | Status |
|---:|---|---|
| 0 | Scope, baseline, and authority lock | **Complete 2026-07-13** |
| 1 | Trust boundary and public error closure | **Next** |
| 2 | Runtime factory, startup, and capability state | Blocked by Phase 1 |
| 3 | Full internal service delivery and supervision | Blocked by prior phases |
| 4 | Data contracts, migrations, backup, and recovery | Blocked by prior phases |
| 5 | Canonical governed reasoning path | Blocked by prior phases |
| 6 | Evidence, confidence, convergence, TruthCore, and KA validity | Blocked by prior phases |
| 7 | Provider execution, latency, privacy, streaming, and offline behavior | Blocked by prior phases |
| 8 | External API Gateway and LLM middleware productization | Blocked by prior phases |
| 9 | Ingestion, retrieval, graph, and memory completion | Blocked by prior phases |
| 10 | Simulation completion | Blocked by prior phases |
| 11 | MCP and connector completion | Blocked by prior phases |
| 12 | UI workflow, project model, and accessibility completion | Blocked by prior phases |
| 13 | Observability, diagnostics, compliance semantics, and support | Blocked by prior phases |
| 14 | Packaging, signing, updates, dependencies, and supply chain | Blocked by prior phases |
| 15 | System qualification and release candidate | Blocked by prior phases |
| 16 | Production documentation replacement and professional review dossier | Blocked by prior phases |
| 17 | Documentation consolidation and release lock | Blocked by prior phases |
| 18 | Production launch and maintenance | Blocked by prior phases |

## Release blockers retained across phases

- [ ] Zero open P0/P1 findings; every P2 fixed, removed, or owner-accepted with
      an expiration.
- [ ] One causal governed request path shared by built-in chat and approved clients.
- [ ] Full required data plane installed, supervised, secured, migrated, backed
      up, restored, and truthfully reported.
- [ ] Every mutation, IPC, GraphQL, MCP, and file capability protected.
- [ ] Every enabled UI control performs its stated real-backend action.
- [ ] Ten legal/distribution authority actions resolved before release.
- [ ] Independent architecture, security, API, usability/accessibility, and
      operations reviews completed.
- [ ] Signed, timestamped, reproducible Windows artifacts and verified updates.
- [ ] Installed-system accessibility, security, failure, recovery, performance,
      soak, and human-acceptance evidence.

## Exact next action

Commit the completed Phase 0 checkpoint, then start Phase 1 by generating the
live route manifest and adding failing anonymous-mutation and public-exception
sentinel tests. Do not begin Phase 2 work.
