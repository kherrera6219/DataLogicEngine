# ADR-0004: SeaweedFS Replacement Qualification

## Metadata

| Field | Value |
|---|---|
| Status | Proposed - candidate qualification authorized, production decision not accepted |
| Date | 2026-07-13 |
| Decision owner | Kevin |
| Plan authority | Section 2.3 Replacement Control and Phase 3 CP3-A |
| Candidate | SeaweedFS 4.29 |

## Context

The active production architecture names MinIO as the app-owned object store.
MinIO Community can no longer satisfy the current support and distribution gate:
its repository is archived, community delivery is source-only, legacy binaries
are unmaintained, and supported proprietary use is directed to MinIO AIStor.

SeaweedFS 4.29 is an active Apache-2.0 S3-compatible candidate. Its immutable
candidate image is
`docker.io/chrislusf/seaweedfs@sha256:d47c7ee99fcb951351d7194915f4e3a5ea604a8e8871183d713907dec4fb9bf5`
with Linux amd64 manifest
`sha256:f16591b02e7a1d79dca57801405eec2c784711436edf65c0aa6394ef52800a3e`.

Kevin authorized qualification on 2026-07-13. This is not approval to use
SeaweedFS in production.

## Replacement Control gate

The candidate must pass all of the following before this ADR can be accepted:

1. caller and behavior inventory for every production object-store consumer;
2. contract parity for bucket creation, put/get/head/list/delete, content type,
   metadata, SHA-256 integrity, multipart upload, and presigned access;
3. durability across graceful restart, forced termination, application relaunch,
   and retained-data reinstall scenarios;
4. portable backup and clean-root restore with object, metadata, count, and hash
   parity, plus documented recovery failure behavior;
5. security qualification covering unique credentials, least privilege,
   anonymous/invalid-credential denial, loopback-only publication, rootless
   runtime, read-only container filesystem, dropped capabilities, bounded
   resources, telemetry policy, logging, vulnerability review, and data-at-rest
   limitations;
6. independent license, redistribution, notices, support-lifecycle, and
   vulnerability review for the exact artifact and delivery model;
7. versioned migration from the current object contract and a tested rollback
   that preserves content, keys, metadata, and hashes;
8. comparative crash, corruption, disk-full, port-conflict, backup-failure, and
   restore-failure tests on supported Windows 11 x64 hardware;
9. clean-machine installer/supervisor qualification using the exact approved
   Podman and SeaweedFS artifacts;
10. final ADR acceptance and explicit owner approval after the evidence is
    complete.

## Candidate-only controls

- Candidate containers, networks, volumes, secrets, ports, and labels use a
  qualification-specific installation identity and never adopt foreign state.
- Only the S3 endpoint may be published, and it must bind to `127.0.0.1`.
- Credentials are generated per run and supplied through a protected runtime
  secret, not a repository or plaintext production `.env` file.
- The production `ObjectStore` selection and persistent production data roots
  remain unchanged during qualification.
- A failed or incomplete gate rejects production selection; it does not permit a
  silent fallback or a partial architecture rename.

## Decision rule

Until every gate passes, this ADR remains proposed and MinIO remains the product-
specific target architecture. If every gate passes, update the architecture to
the capability requirement **app-owned S3-compatible object store**, set this
ADR to Accepted, name SeaweedFS as the selected implementation, link the complete
evidence bundle, and record final owner approval. If any gate cannot pass, set
this ADR to Rejected and retain or re-procure a supported MinIO implementation.

## Evidence

- `reports/production-readiness/2026/phase-03/cp3-a-version-license-audit.md`
- `reports/production-readiness/2026/phase-03/service-candidates.json`
- `reports/production-readiness/2026/phase-03/seaweedfs-replacement-qualification-windows.json`
- `reports/production-readiness/2026/phase-03/internal-data-plane-qualification.json`
- `reports/production-readiness/2026/phase-03/seaweedfs-qualification-summary.md`

The engineering runs passed S3 contract parity, concurrent operations,
graceful/forced restart durability, snapshot backup/clean restore, versioned
migration/rollback, invalid/anonymous access denial, required bucket use inside
the complete five-service profile, and cleanup.

The ADR remains Proposed because independent license/redistribution/support and
vulnerability review, TLS/data-at-rest disposition, exact Podman artifact
qualification, corruption/disk-full/backup-failure/restore-failure comparison,
clean signed-installer qualification, and final owner approval are still open.
No current evidence sets `production_authorized` or `production_selected` true.
