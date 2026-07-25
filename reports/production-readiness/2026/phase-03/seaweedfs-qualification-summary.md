# SeaweedFS Replacement Qualification Summary

## Decision

ADR-0010 defines the product requirement as **app-owned S3-compatible object
store** and selects SeaweedFS 4.40-dle.1 for rebuilt installed qualification.
Production provisioning and production approval remain false until the retained
installed and independent release gates pass.

## Exact selected implementation

| Field | Value |
|---|---|
| Upstream | SeaweedFS 4.40 |
| DataLogicEngine build | 4.40-dle.1 |
| Source revision | `875cd1f67ea25e8965a4f5ba1e6aaf501ba6b6fa` |
| Image digest | `sha256:52c010d8f866da9269d32ea98a0399a44922c36147c34e2adab9dcc340877f4b` |
| Image ID | `sha256:b41f8b293049bf79045ff9c8216a9dccf0ce99ee6a4e32d174c6b320659e2b3e` |
| Security dependency | gRPC-Go 1.82.1 |
| License | Apache-2.0 |
| Windows runtime | Podman client 6.0.1 / rootless machine server 5.8.5 |

The official 4.40 image embeds gRPC-Go 1.81.1, which is affected by
`GHSA-hrxh-6v49-42gf`. The selected app-owned image reproducibly rebuilds the
exact 4.40 source with the fixed 1.82.1 dependency.

## Passed engineering gates

- immutable image ID/digest, source revision, version, security-patch, and
  Apache-2.0 labels;
- exact-image vulnerability scan with zero High or Critical findings;
- loopback-only S3 publication and occupied-port fail-closed preflight;
- non-root execution, read-only root filesystem, zero capabilities,
  no-new-privileges, CPU/memory/PID budgets, and protected runtime credentials;
- anonymous, invalid-credential, and unauthorized bucket-creation denial;
- put/get/head/list/delete, metadata, integrity, multipart, and presigned GET;
- 32-object/eight-worker concurrent write/read/hash exercise;
- graceful restart and forced-termination read-back durability;
- 34-object portable backup and clean-data-root restore;
- rejection of tampered manifest, tampered blob, and missing blob before any
  restore write;
- disposable 512 MiB disk-full failure and sentinel recovery;
- local-to-candidate migration and candidate-to-local rollback;
- complete cleanup of disposable containers, volumes, network, and secret;
- engineering license/redistribution inventory; and
- Kevin's recorded implementation selection.

## Retained release gates

- signed clean-machine installer, relaunch, lifecycle, and upgrade/recovery;
- installed protected-volume and data-at-rest verification;
- independent security and license acceptance;
- exact signed-release SBOM/notices/malware/signature evidence; and
- final production GO decision.

## Evidence

- `seaweedfs-replacement-qualification-windows.json`
- `seaweedfs-4.40-dle.1-trivy.json`
- `seaweedfs-4.40-license-redistribution-review.md`
- `object-store-caller-contract-inventory.md`
- `cp3-a-version-license-audit.md`
- `risk-register.md`
- `rollback.md`
- `deploy/seaweedfs/Dockerfile`
- `deploy/internal-data-plane.candidate-lock.json`
- `docs/adr/ADR-0010-app-owned-s3-compatible-object-store.md`
