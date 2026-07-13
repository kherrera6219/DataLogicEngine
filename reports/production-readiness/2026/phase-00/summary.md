# Phase 0 Evidence Summary

## Status

| Field | Value |
|---|---|
| Phase | 0 - Scope, baseline, and authority lock |
| Started | 2026-07-12 |
| Active plan | `PRODUCTION_COMPLETION_PLAN_2026.md` v1.2.0 |
| Evidence baseline | `docs/audits/DataLogicEngine_Design_vs_Implementation_Audit_2026-07-12.md` |
| Completed | 2026-07-13 |
| Current checkpoint | CP0-A through CP0-G complete |
| Release posture | Production/public release NO-GO |

## Approved scope

The owner directed that the July 12 production completion plan is the path ahead
and instructed work to begin. That directive approves the plan authority and the
product boundary recorded in CP0-A:

- local-first, single-owner Windows 11 x64 product;
- API gateway as the primary integration surface;
- Electron desktop as the full control, administration, audit, observability,
  support, and validation application;
- built-in chat as the reference client for the canonical governed path;
- required app-owned PostgreSQL, Redis, Neo4j, ChromaDB, and MinIO services;
- optional OpenAI and Google model access;
- no cloud SaaS, multi-tenant operation, Kubernetes, mobile, macOS/Linux desktop,
  public registration, or public-internet gateway in this program.

## Completed work

1. Archived superseded plans and prior long-form TODO/HANDOFF.
2. Replaced root TODO/HANDOFF with current-state controls.
3. Created the Phase 0 evidence structure.
4. Began product/version, runtime-surface, UI-control, and service-consumer inventories.
5. Accepted ADR-0003: app-managed pinned OCI containers through rootless Podman Machine/WSL2.
6. Captured the current-host, toolchain, Compose, installer, and git baseline.
7. Created and structurally verified 20 requirements and 783 inventoried feature dispositions.
8. Recorded the owner-approved Windows contract, responsibility matrix, and legal/distribution register.
9. Passed strict Python 3.11 parity, lockfile, source-generator, and verified-secret checks.
10. Recorded Kevin's approval of the Windows, hardware, offline-install, update, and acceptance contracts.
11. Installed Podman 5.8.3 and created a rootless WSL2 reference machine at the approved minimum allocation.
12. Proved all five required candidate services healthy and recorded retrieved image digests.
13. Captured the unsigned 0.1.1 installer's failure to register/provision the application without fabricating installed-app metrics.

## Known baseline defects

- Current Compose omits ChromaDB.
- MinIO uses `latest`; PostgreSQL, Redis, and Neo4j use broad tags.
- The Windows installer does not deliver the required five-service profile.
- Root, frontend, SDK, and documentation versions are not unified.
- Existing checks validate the current implementation, not the approved profile.
- Mandatory independent reviews and ten legal/distribution actions remain later release blockers owned by Kevin.

## Exit condition

**Passed 2026-07-13.** CP0-A through CP0-G have reproducible evidence and owner
approval. Phase 1 is authorized; production/public release remains NO-GO.
