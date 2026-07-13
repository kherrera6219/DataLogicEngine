# CP3-A Version, Support, and License Audit

## Status

| Field | Value |
|---|---|
| Phase/checkpoint | Phase 3 / CP3-A |
| Captured | 2026-07-13 |
| Result | Engineering candidates locked; production approval blocked by independent review and final object-store decision |
| Provisioning changes | Qualification-only profile implemented; no production provisioning or persistent user-data migration |

## Recommended candidate locks

| Component | Candidate | Immutable index digest | Windows x64 / Linux amd64 artifact | License posture | Support posture |
|---|---|---|---|---|---|
| Podman | 5.8.2 Windows x64 MSI | n/a | `sha256:eda54f26f9695d198d9a679fa45ae24ba35b78444f432b5fe0c122c5a3624c57` | Apache-2.0; notices/redistribution review still required | Current official security release; includes the Windows CVE-2026-33414 fix |
| PostgreSQL | `postgres:18.4-alpine3.22` | `sha256:774521500f4c22761b25a6bdb772a0a3c2e8dd32468210bdad9231c5752ea398` | `sha256:56ba71bf54060de15a6b2df1a18081b8f6c5bf61255b7ed6f1ef10ee868eaff0` | PostgreSQL License | Current 18.x minor; major supported through 2030-11-14 |
| Redis | `redis:8.8.0-trixie` | `sha256:2838d5524559494f6f1cd66e97e76b200d64a633a8614200620755ed395daf32` | `sha256:c904002d182255b6db3cbe3a1e8ce6c187d15390c39500b59fc07181aabff7bf` | Select AGPLv3 from the Redis 8 tri-license; independent review required for distributed commercial product | Current official image/release line; exact patch update policy still required |
| Neo4j Community | `neo4j:5.26.28-trixie` | `sha256:4bae36aff76271e27fd6a6ed0835413f86a284cd179cfb1cb7d188f5f7533aca` | `sha256:32e6325c6f2160747d68601b6e1a38e556deca66524cf95cf0e6c1ee29b1596b` | GPLv3; independent distribution review and source/notices procedure required | 5.26 LTS line supported through 2028-06-06; preferable to monthly 2026.x for this product |
| ChromaDB | `chromadb/chroma:1.5.9` | `sha256:1e0b73a187a28757c572acba508c46f48c9e8b0acaf5c20e6d95cdedce1acdf6` | `sha256:abcce7c335e2dab9f11ef629296f7309b09cb19ae4b34da32ac7e34ff5773140` | Apache-2.0 | Current stable release found; fast-moving community project with no LTS commitment found |
| Object store candidate | SeaweedFS 4.29 | `sha256:d47c7ee99fcb951351d7194915f4e3a5ea604a8e8871183d713907dec4fb9bf5` | `sha256:f16591b02e7a1d79dca57801405eec2c784711436edf65c0aa6394ef52800a3e` | Apache-2.0 declaration; independent review pending | Engineering qualification passed; production selection not approved |

The index digest is the multi-platform OCI identity. The amd64 manifest is also
recorded because the approved product target is Windows 11 x64 running Linux
containers in a rootless Podman Machine.

## Blocking MinIO finding

The Phase 0 ADR and active plan require MinIO. Current official MinIO evidence
now says:

1. the community repository was archived on 2026-04-25 and is read-only;
2. community distribution is source-only; precompiled legacy releases are not
   maintained;
3. community MinIO is AGPLv3 and provides no warranty, maintenance, or support;
4. proprietary/commercial deployments are directed to MinIO AIStor commercial
   licensing and support.

Therefore `minio/minio:latest` must be removed, but it cannot honestly be
replaced with another community MinIO image/digest while CP3-A requires a
supported production service.

## Owner authorization and remaining decision

Kevin authorized the recommended SeaweedFS qualification path on 2026-07-13.
The qualification profile and contract evidence are implemented. This did not
approve a production replacement or change the MinIO-specific architecture.

Remaining production decision path:

1. complete every ADR-0004 Replacement Control gate and the independent reviews;
2. if every gate passes, obtain explicit owner production approval and only then
   amend the product requirement from MinIO to an app-owned S3-compatible object
   store;
3. retain the existing S3 `ObjectStore` contract so application callers are not
   vendor-specific;
4. run the complete object operation, integrity, lifecycle, backup/restore,
   crash, and installed-app qualification matrix before acceptance.

Candidate SeaweedFS identities:

- index: `sha256:d47c7ee99fcb951351d7194915f4e3a5ea604a8e8871183d713907dec4fb9bf5`
- linux/amd64: `sha256:f16591b02e7a1d79dca57801405eec2c784711436edf65c0aa6394ef52800a3e`

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
- Podman 5.8.2 artifacts/security fix: https://github.com/containers/podman/releases/tag/v5.8.2
- SeaweedFS 4.29 release: https://github.com/seaweedfs/seaweedfs/releases/tag/4.29
- SeaweedFS Apache-2.0 repository: https://github.com/seaweedfs/seaweedfs

This is an engineering license inventory, not legal advice or a legal
conclusion. The Phase 0 legal/distribution register still requires independent
review and final owner approval. `deploy/internal-data-plane.candidate-lock.json`
therefore retains `production_provisioning_authorized: false`.
