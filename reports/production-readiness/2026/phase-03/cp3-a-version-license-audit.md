# CP3-A Version, Support, and License Audit

## Status

| Field | Value |
|---|---|
| Phase/checkpoint | Phase 3 / CP3-A |
| Captured | 2026-07-24 |
| Result | Exact object-store implementation selected for rebuilt installed qualification; production approval remains blocked by installed and independent release gates |
| Provisioning changes | Qualification-only profile implemented; no production provisioning or persistent user-data migration |

## Recommended candidate locks

| Component | Candidate | Immutable index digest | Windows x64 / Linux amd64 artifact | License posture | Support posture |
|---|---|---|---|---|---|
| Podman | 6.0.1 Windows x64 | n/a | MSI `sha256:3b65848f2d9ae652a15c35f2496a9ece2e07f28746fa651415d519ae7c5902ad`; portable remote zip `sha256:127d02930ac25c80088817502e833916cd3ee1ed1e771dbd42a4ce81b2e0d415` | Apache-2.0; notices/redistribution review still required | Exact signed MSI and official portable client verified; portable client passed the Windows engineering matrix against documented WSL machine server 5.8.5 |
| PostgreSQL | `postgres:18.4-alpine3.22` | `sha256:774521500f4c22761b25a6bdb772a0a3c2e8dd32468210bdad9231c5752ea398` | `sha256:56ba71bf54060de15a6b2df1a18081b8f6c5bf61255b7ed6f1ef10ee868eaff0` | PostgreSQL License | Current 18.x minor; major supported through 2030-11-14 |
| Redis | `redis:8.8.0-trixie` | `sha256:2838d5524559494f6f1cd66e97e76b200d64a633a8614200620755ed395daf32` | `sha256:c904002d182255b6db3cbe3a1e8ce6c187d15390c39500b59fc07181aabff7bf` | Select AGPLv3 from the Redis 8 tri-license; independent review required for distributed commercial product | Current official image/release line; exact patch update policy still required |
| Neo4j Community | `neo4j:5.26.28-trixie` | `sha256:4bae36aff76271e27fd6a6ed0835413f86a284cd179cfb1cb7d188f5f7533aca` | `sha256:32e6325c6f2160747d68601b6e1a38e556deca66524cf95cf0e6c1ee29b1596b` | GPLv3; independent distribution review and source/notices procedure required | 5.26 LTS line supported through 2028-06-06; preferable to monthly 2026.x for this product |
| ChromaDB | `chromadb/chroma:1.5.9` | `sha256:1e0b73a187a28757c572acba508c46f48c9e8b0acaf5c20e6d95cdedce1acdf6` | `sha256:abcce7c335e2dab9f11ef629296f7309b09cb19ae4b34da32ac7e34ff5773140` | Apache-2.0 | Current stable release found; fast-moving community project with no LTS commitment found |
| App-owned S3-compatible object store | SeaweedFS 4.40-dle.1 | Local image `sha256:52c010d8f866da9269d32ea98a0399a44922c36147c34e2adab9dcc340877f4b` | OCI archive `sha256:1f48d45b87554b6008bc086b101f58887ba360a214e928ccc23a216f804bdfbc`; upstream Windows zip `sha256:6713c300fe8bcc807bbdd73fe9e6753e96cb08905568102e0b842c686cfa8f3e` | Apache-2.0 engineering inventory passed; independent legal acceptance pending | Selected by ADR-0010 for rebuilt installed qualification; production approval remains false |

The index digest is the multi-platform OCI identity. The amd64 manifest is also
recorded because the approved product target is Windows 11 x64 running Linux
containers in a rootless Podman Machine.

## Historical MinIO finding and resulting capability decision

The Phase 0 ADR and active plan require MinIO. Current official MinIO evidence
now says:

1. the community repository was archived on 2026-04-25 and is read-only;
2. community distribution is source-only; precompiled legacy releases are not
   maintained;
3. community MinIO is AGPLv3 and provides no warranty, maintenance, or support;
4. proprietary/commercial deployments are directed to MinIO AIStor commercial
   licensing and support.

Therefore `minio/minio:latest` cannot be a supported release dependency. The
Replacement Control program retained the application S3 contract, qualified an
alternative, and replaced the vendor-specific product requirement with the
capability requirement **app-owned S3-compatible object store**.

## Owner authorization and remaining decision

Kevin authorized qualification and selection under Replacement Control. Every
engineering gate passed for the exact rebuilt image: contract parity,
concurrency, restart/kill durability, backup/restore, corrupt-backup rejection,
failure/recovery, disk-full recovery, security, license inventory,
migration/rollback, observability, Windows runtime, and explicit owner
selection. ADR-0010 supersedes the historical Proposed ADR-0004, changes the
architecture to the capability requirement, and selects SeaweedFS
`4.40-dle.1` for rebuilt installed qualification.

Selected SeaweedFS identities:

- image: `sha256:52c010d8f866da9269d32ea98a0399a44922c36147c34e2adab9dcc340877f4b`
- image ID: `sha256:b41f8b293049bf79045ff9c8216a9dccf0ce99ee6a4e32d174c6b320659e2b3e`
- OCI archive: `sha256:1f48d45b87554b6008bc086b101f58887ba360a214e928ccc23a216f804bdfbc`
- source revision: `875cd1f67ea25e8965a4f5ba1e6aaf501ba6b6fa`

Production authorization remains false. The remaining path is to package this
exact image in the rebuilt signed application and pass clean-machine delivery,
protected-volume/coordinated recovery, installed workflow, independent
security/license, signing, accessibility, soak, pilot, and final owner release
acceptance. The S3 `ObjectStore` contract remains vendor-neutral and local
filesystem storage cannot act as a production fallback.

Alternative path: procure/approve MinIO AIStor commercial licensing and support,
then record the vendor-provided immutable artifact, redistribution authority,
offline delivery terms, and SLA before implementation.

## Current client compatibility gaps

- Direct clients are now pinned for the engineering profile: ChromaDB 1.5.9,
  Neo4j 6.2.0, Redis 8.0.1, Boto3 1.43.45, and psycopg2-binary 2.9.12.
  Their live five-service compatibility gate passed; final wheel/image/legal
  lock remains part of release qualification.
- Current Compose uses default credentials, host-wide ports, broad tags, Docker
  restart ownership, no Chroma service, and no service health checks. It is a
  development artifact, not the Phase 3 production profile.

## Primary evidence

- PostgreSQL support/version policy: https://www.postgresql.org/support/versioning/
- PostgreSQL May 2026 security releases: https://www.postgresql.org/about/news/postgresql-184-1710-1614-1518-and-1423-released-3297/
- Redis license matrix: https://redis.io/legal/licenses/
- Redis official image: https://hub.docker.com/_/redis
- Neo4j 5.26 LTS support table: https://neo4j.com/developer/kb/neo4j-supported-versions/
- Neo4j Community GPLv3: https://neo4j.com/legal-terms/
- Neo4j official image: https://hub.docker.com/_/neo4j
- Chroma 1.5.9 release and Apache-2.0 repository: https://github.com/chroma-core/chroma
- MinIO archived source-only AGPL repository: https://github.com/minio/minio
- MinIO license status command: https://min.io/docs/minio/linux/reference/minio-mc/mc-license-info.html
- Podman 6.0.1 release: https://github.com/containers/podman/releases/tag/v6.0.1
- SeaweedFS 4.40 release: https://github.com/seaweedfs/seaweedfs/releases/tag/4.40
- gRPC-Go security advisory fixed by the DataLogicEngine rebuild: https://github.com/grpc/grpc-go/security/advisories/GHSA-hrxh-6v49-42gf
- SeaweedFS Apache-2.0 repository: https://github.com/seaweedfs/seaweedfs

This is an engineering license inventory, not legal advice or a legal
conclusion. The exact upstream license and modification inventory is recorded in
`seaweedfs-4.40-license-redistribution-review.md`; independent legal acceptance
remains a release gate. `deploy/internal-data-plane.candidate-lock.json`
therefore retains `production_provisioning_authorized: false` and the selected
object-store entry retains `production_approved: false`.
