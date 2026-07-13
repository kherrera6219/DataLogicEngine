# Phase 3 Evidence Summary

## Status

| Field | Value |
|---|---|
| Phase | 3 - Full internal service delivery and supervision |
| Started | 2026-07-13 |
| Engineering checkpoint completed | 2026-07-13 |
| Checkpoint result | Qualification implementation GO; installed production exit gate deferred |
| Release posture | Production/public release remains **NO-GO** |

## Closure results

1. The Phase 2 supervisor now owns one installation-specific, immutable,
   rootless Podman profile for PostgreSQL, Redis, Neo4j, ChromaDB, and an
   object-store candidate. It never pulls at runtime, adopts foreign resources,
   or treats an occupied port as proof of ownership.
2. Candidate artifacts are locked by Windows package hash plus OCI index and
   Linux amd64 digests. Production construction fails closed while any artifact
   or final provisioning authority remains unapproved.
3. Per-install service credentials are generated with a cryptographic RNG,
   protected by the DPAPI/ACL credential vault, delivered through Podman
   secrets, and excluded from repository and production `.env` authority.
4. All service ports are installation-derived and loopback-only. Containers use
   an internal network, read-only root filesystem, dropped capabilities,
   no-new-privileges, non-root service identities, and CPU/memory/PID limits.
5. PostgreSQL is injected as the production SQLAlchemy authority with SCRAM,
   separate migration/application roles, real transactions, and no production
   SQLite fallback. Redis uses an authenticated application ACL, protected mode,
   AOF/RDB persistence, no-eviction policy, and real key/stream operations.
6. Neo4j and Chroma are supervised services with authenticated graph and HTTP
   vector probes. Their live contracts persist graph and vector records across
   complete service restarts.
7. The object abstraction selects the supervisor-owned S3 endpoint in the
   managed profile. Required audit, simulation, and DSQP artifact writes fail
   closed when object storage is required; the local filesystem remains limited
   to development/bootstrap behavior.
8. The Storage UI now presents a read-only internal-data-plane model and removes
   cloud database credentials and uncontrolled internal port/path editing.
   Health and actions use supervisor identity/state rather than directory or
   socket assumptions.
9. A live Windows qualification run started all five immutable services,
   exercised PostgreSQL transaction/rollback, Redis idempotency/streams, Neo4j
   graph writes, Chroma vector read/query, and six S3 buckets, then proved
   restart durability and complete qualification-resource cleanup.
10. SeaweedFS 4.29 passed the exercised S3 contract, concurrency, restart/kill
    durability, backup/restore, migration/rollback, access-control, and container
    hardening checks. It remains a candidate only: ADR-0004 is Proposed,
    production authorization is false, and the architecture still names MinIO.

## Validation summary

- Live internal data-plane qualification: **passed**, including all five
  services, restart durability, truthful identities, and full cleanup.
- Backend: **1,814 passed, 18 skipped, 21 warnings**.
- Frontend: **81 files / 402 tests passed**.
- Ruff, frontend lint, TypeScript, and Next.js production build: **passed**.
- Documentation reference validation and diff/whitespace validation are recorded
  in the phase commit checks.

## Deferred production exit evidence

The following are intentionally not claimed as passed and remain release
blockers for their owning later phases or the final rebuilt candidate:

- exact locked Podman 5.8.2 clean-machine deployment (the lab client/server were
  5.8.3/5.8.5);
- signed installer provisioning, app relaunch, repair, uninstall, upgrade, and
  supported prior-version migration on a clean Windows 11 x64 machine;
- coordinated five-store backup/restore, corruption, disk-full, partial backup,
  and recovery orchestration owned by Phase 4 and system qualification;
- independent redistribution/license/notices, security, TLS, vulnerability,
  data-at-rest, and support-lifecycle review;
- final object-store replacement acceptance and explicit production approval.

Phase 4 may begin from this engineering checkpoint. No deferred item is converted
to PASS, and the final release remains NO-GO.
