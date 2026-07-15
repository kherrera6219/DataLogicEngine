# DataLogicEngine third-party software, SBOM, licensing, redistribution, and notices index

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ASR-007 |
| Title | SBOM, licensing, redistribution, and notices index |
| Document version | v1.0.0 |
| Product version | 4.3.0 |
| Status | release_blocked |
| Audience | Release/legal/security engineering, procurement, operators, independent reviewers, and release authority |
| Owner | Release Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Exact dependency locks, service candidate lock, SBOMs, release manifest, ownership/legal registers, and review evidence |
| Confidentiality | Public |
| Last reviewed | 2026-07-15 |
| Next-review trigger | Dependency/service/artifact, license, notice, vulnerability, provider/model, asset, redistribution, region, or release change |
| Requirements and evidence | Product requirement DLE-QR-002/004/006, exact locks, SBOMs, manifests, scans, legal actions, and approved notice bundle |

## Current disposition

This index is an engineering inventory, not legal advice, redistribution
approval, a complete notice bundle, or a SLSA conformance claim. Product 4.3.0
remains release-blocked: ten legal/distribution actions, final exact-artifact
SBOM/notices reconciliation, publisher/signing, vulnerability/malware scans,
service redistribution, object-store selection, export/region review, and owner/
independent approvals remain open.

## Dependency authorities

| Ecosystem | Reviewed input | Exact release authority | Build/runtime boundary |
|---|---|---|---|
| Python | `requirements.txt` (81 direct pins at Phase 14) | `requirements.lock` (315 hash-locked packages at Phase 14) | CPython 3.11; hashes required; no implicit `pyproject` runtime authority |
| Node/Electron | `frontend/package.json` | `frontend/package-lock.json` v3 via `npm ci` | Node major 24; Electron 43.1.1, Chromium 150.0.7871.114, embedded Node 24.18.0 |
| Internal services | `deploy/internal-data-plane.candidate-lock.json` | Exact image/runtime digests and platform selection | Engineering candidates only until redistribution/security/license approval |
| Product/contracts | `config/product-versions.json` | Product 4.3.0, Windows 4.3.0.0, versioned public/gateway/governed/data contracts | Must match installer, binaries, UI/API/support, SDKs, manifests, and evidence |

Package-manager license metadata is a discovery input, not authoritative legal
permission. Exact source/license texts, notices, exceptions, linking/distribution
terms, modifications, trademarks, patents, export restrictions, and asset/data/
model terms require review.

## SBOM and inventory set

The exact release candidate shall include machine-readable SBOMs and content
inventories for:

- frozen Python/backend components;
- frontend production dependencies and Electron/Chromium/embedded Node;
- installer/portable payload, native binaries, DLLs, executables, and helper tools;
- app-owned PostgreSQL, Redis, Neo4j, ChromaDB, MinIO/object-store implementation,
  Podman/WSL2/runtime layers, and any JRE/native transitive components;
- Python/TypeScript SDK packages, examples/templates, fonts, icons, images,
  schemas, test/evaluation data shipped to users, and other redistributable assets;
- build/signing/SBOM/provenance tools where required by the release evidence.

Current Phase 14 evidence includes service and software SBOM inputs, exact locks,
content inventories, a release manifest, dependency/version/workflow verifiers,
and an attestation-verification path. Regenerate all of them from the clean final
signed candidate; prior/different-hash candidate data is not final evidence.

## Material runtime components

The current engineering manifest identifies CPython 3.11, PyInstaller 6.18.0,
Electron 43.1.1, electron-builder 26.8.1, Next.js 16.2.7, PostgreSQL 18.4,
Redis 8.8.0, Neo4j, the Chroma Rust service 1.5.9, Podman 5.8.2, and the qualification object-
store candidate set. Exact image versions/digests and license fields are recorded
in the service candidate lock and release manifest.

Redis is recorded as an AGPL-3.0 selection from a tri-license and explicitly
requires redistribution review. Podman redistribution review is pending. Every
service currently has `production_approved=false` in the engineering manifest.
These fields intentionally prevent inventory from becoming approval.

MinIO remains the required production object store. SeaweedFS is qualification-
only and may be selected only after Replacement Control, licensing/
redistribution, migration/rollback, Windows delivery, and owner approval pass.

## Providers, models, connectors, and content

OpenAI and Google are external service providers controlled by the owner's
accounts; their APIs/models are not shipped software. Their terms, model names,
regions, retention, acceptable use, branding, output/data rights, and changes are
recorded separately and must not be represented as endorsement.

MCP connectors and client applications are owner-installed/integrated software,
not automatically part of the DataLogicEngine distribution. Each connector's
executable, dependencies, license, scopes, credentials, and external-service
terms remain the owner's responsibility unless explicitly included in a signed
distribution record.

Repository sample data, evaluation corpora, documentation excerpts, generated
assets, fonts, icons, diagrams, and screenshots require provenance and license/
permission review before shipping. Synthetic does not automatically mean
unrestricted.

## Vulnerability and maintenance state

SBOM components are scanned with the approved dependency, code, container, and
malware tools. Findings bind package/version/digest, affected path/reachability,
severity, advisory, mitigation, owner, expiration, correction, and exact-artifact
retest. An unavailable upstream fix does not close a finding.

Dependabot alert 389 (`GHSA-f4j7-r4q5-qw2c` / `CVE-2026-45829`) affected the
ChromaDB Python SDK. The SDK has been removed from direct and locked transitive
dependencies and replaced by a restricted loopback-only, caller-vector-only HTTP
client. The digest-pinned Rust service remains. Focused adversarial tests, live
five-service compatibility/restart qualification, and an isolated dependency
audit with zero vulnerabilities pass; GitHub closure awaits manifest rescan.

The 2026-07-15 lock refresh includes Flask async support plus Pillow 12.3.0,
Starlette 1.3.1, and Transformers 5.13.0. The post-replacement lock contains 290
packages and no Chroma Python SDK. An isolated audit examined 266 applicable
dependencies and found zero vulnerabilities. Installed exact-artifact review,
legal approval, and release authorization remain separate gates.

## Notice and redistribution approval gate

Before release, the owner shall:

1. regenerate all SBOMs/content inventories from the exact clean signed artifact;
2. reconcile every package, native/service component, asset, corpus, SDK, and
   installer file with authoritative license text and required notices;
3. resolve missing/ambiguous/custom/copyleft/font/icon/model/provider/sample-data
   terms and record modifications/source-offer obligations where applicable;
4. complete all ten release-blocking legal/distribution actions and intended-
   region export review;
5. complete malware, vulnerability, signature, provenance, and service
   redistribution/security reviews;
6. approve one versioned notice bundle bound to commit, installer hash/signature,
   SBOM hashes, manifests, attestations, scan results, and release decision;
7. publish required notices/source offers with the artifact and retain the
   reviewed evidence for the maintenance period.

`verify_release_ownership.py --require-release-ready` and the final legal/
distribution review must pass. Until then, this document remains
`release_blocked`, and production/public distribution is **NO-GO**.
