# ADR-0010: App-Owned S3-Compatible Object Store

## Document metadata

| Field | Value |
|---|---|
| Status | Accepted for rebuilt installed qualification; production approval withheld |
| Date | 2026-07-24 |
| Owner | Kevin |
| Supersedes | Historical Proposed ADR-0004 |
| Capability | App-owned S3-compatible object store |
| Selected implementation | SeaweedFS 4.40-dle.1 |

## Context

The product requires locally owned S3-compatible object storage for source
objects, evidence, trace exports, simulation artifacts, deliverables, gateway
results, backups, and support bundles. The earlier plan named MinIO as the
product requirement. That coupled the architecture to an implementation whose
current community distribution and support posture did not pass the project
gate.

Kevin authorized SeaweedFS qualification with a fail-closed condition: the
architecture could change only after contract parity, durability,
backup/restore, security, licensing, migration/rollback, Windows deployment,
and owner-decision evidence passed.

## Decision

1. The product requirement is the capability **app-owned S3-compatible object
   store**, not a particular vendor product.
2. SeaweedFS `4.40-dle.1` is selected as the implementation to package and
   exercise through rebuilt installed and signed-release qualification.
3. The selected image is a DataLogicEngine-owned, reproducible build of the
   exact SeaweedFS 4.40 source revision with `google.golang.org/grpc` upgraded
   from 1.81.1 to the upstream-fixed 1.82.1 for
   `GHSA-hrxh-6v49-42gf`.
4. Production provisioning and production approval remain false. The selected
   implementation does not become an approved production object store until
   the deferred clean-installed, protected-volume, independent
   security/license, signing, recovery, and release gates pass.
5. Callers depend on the existing app-owned S3 contract. Product-specific
   SeaweedFS APIs are not permitted in application business logic.

## Qualification basis

The exact selected image passed:

- S3 put/get/head/list/delete, multipart upload, and presigned retrieval;
- bounded concurrent reads and writes;
- graceful restart and forced-termination durability;
- portable backup, clean-root restore, corrupt/incomplete snapshot rejection,
  and zero restore writes from invalid evidence;
- local-to-S3 migration and S3-to-local rollback;
- occupied-port fail-closed behavior and disposable disk-full recovery;
- loopback-only publication, non-root execution, read-only root filesystem,
  dropped capabilities, no-new-privileges, bounded resources, protected
  credentials, anonymous denial, invalid-credential denial, and least
  privilege; and
- an exact-image Trivy scan with zero High or Critical findings.

The engineering Apache-2.0 redistribution inventory is complete. The separate
installed-release gates remain explicit rather than being treated as evidence
from this source/lab qualification.

## Consequences

- Architecture, requirements, UI copy, support guidance, and tests must name
  the capability except where the selected SeaweedFS implementation or
  historical MinIO decision is specifically relevant.
- The release pipeline must build or import only the locked image and verify
  image ID, manifest digest, archive hash, source revision, dependency patch,
  license record, and vulnerability report.
- Future SeaweedFS/base-image changes require the complete Replacement Control
  regression and a new or superseding ADR.
- A failure in any installed-release gate prevents production authorization
  but does not silently fall back to filesystem storage.

## Evidence

- `deploy/internal-data-plane.candidate-lock.json`
- `deploy/seaweedfs/Dockerfile`
- `reports/production-readiness/2026/phase-03/seaweedfs-replacement-qualification-windows.json`
- `reports/production-readiness/2026/phase-03/seaweedfs-4.40-dle.1-trivy.json`
- `reports/production-readiness/2026/phase-03/seaweedfs-4.40-license-redistribution-review.md`
- `reports/production-readiness/2026/phase-03/object-store-caller-contract-inventory.md`
- `reports/production-readiness/2026/phase-03/rollback.md`
