# SLSA Level 3 Supply-Chain Roadmap

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.9.0 |
| Last updated | 2026-07-14 |
| Status | Planning / Partial Implementation |
| Owner | Security Engineering + Release Engineering |
| Review cadence | Every 60 days |

## Purpose

Document DataLogicEngine's current software supply-chain controls and the roadmap toward SLSA Level 3-style build integrity.

This document is **not** a formal SLSA Level 3 attestation. It separates current repository evidence from target-state controls so reviewers can distinguish implemented protections from planned improvements.

## Scope

Covered artifacts:

1. source repository changes;
2. GitHub Actions CI and release workflows;
3. Windows desktop installer artifacts;
4. backend/frontend build outputs;
5. Docker/container build paths where applicable;
6. release evidence and verification reports.

## Current evidence

| Control area | Current evidence |
|---|---|
| Version-controlled build definitions | `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`, `.github/workflows/release-installer-signing.yml`, `frontend/build_installer.ps1`, `scripts/windows/` |
| CI validation | backend tests, frontend validation, contract/parity/security tests, governance checks, Docker build where applicable. |
| Runtime/release prechecks | `scripts/runtime_precheck.py`, `scripts/verify_release_governance.py`, `scripts/verify_environment_parity.py`, `scripts/verify_lockfiles.py` |
| Windows packaging governance | `scripts/windows/verify_nsis_governance.ps1`, `scripts/windows/run_packaging_smoke.ps1` |
| Installer integrity/signature verification | `scripts/verify_installer_integrity.py`, `scripts/windows/verify_installer_signature.ps1` |
| Version/dependency authority | `config/product-versions.json`, `config/dependency-authority.json`, `requirements.lock`, `scripts/verify_product_versions.py` |
| Immutable workflow inputs | `scripts/verify_workflow_pins.py`; 71 external references pinned to commits |
| SBOM and release inventory | backend/frontend/service/installer CycloneDX generators, normalized content inventory, `scripts/generate_release_manifest.py` |
| Provenance verification | pinned `actions/attest`, GitHub attestation generation, and `gh attestation verify` release gate |
| Documentation governance | `scripts/verify_docs_references.py`, versioned active docs, release checklist. |

## Target SLSA Level 3-style capabilities

| Capability | Current status | Target state |
|---|---|---|
| Build defined as code | Implemented | All production artifacts built only from version-controlled workflows/scripts. |
| Hosted/isolated build service | Partial | Production releases should use hosted CI/release runners, not developer laptops. |
| Ephemeral build environment | Partial | Prefer clean hosted runners or equivalent isolated builders for release artifacts. |
| Authenticated provenance | Workflow implemented; final evidence pending | Generate and verify GitHub attestations for the exact final artifacts. |
| Non-falsifiable provenance | Partial | GitHub OIDC attestation path is gated; archive/independent final verification remains required. |
| Artifact signing | Fail-closed structure; authority pending | Approve publisher and managed/hardware signing boundary, then verify every executable. |
| Policy enforcement | Source release gates implemented | Installed promotion remains blocked until trust, legal, artifact, and qualification gates pass. |

## Required production release policy

Production release artifacts should be built by controlled workflows, not manually assembled on a developer workstation.

Required evidence before claiming production supply-chain integrity:

1. exact commit SHA;
2. workflow run URL/ID;
3. build logs retained;
4. artifact checksums;
5. signature verification report where signing is required;
6. installer integrity report for Windows artifacts;
7. portable packaging smoke report;
8. installer-mode install/uninstall smoke report where the release scope includes install behavior evidence;
9. release checklist approval;
10. known waivers documented.

## Claims that require verification before use

Do not claim the following unless current workflow artifacts prove them:

1. SLSA Level 3 compliance achieved;
2. Sigstore/cosign signing completed;
3. provenance uploaded to Rekor;
4. `provenance.intoto.jsonl` generated for every artifact;
5. Kubernetes/admission-controller enforcement active;
6. SBOM generated and attached to every release;
7. all release artifacts are built only in hosted ephemeral builders.

These are valid target-state goals, but they must not be represented as implemented without evidence.

## Roadmap

1. Approve the production publisher and managed/hardware signing boundary.
2. Build the canonical 4.3.0 release candidate from a clean tagged commit.
3. Generate final backend/frontend/service/JRE/installer SBOMs and notices.
4. Sign every applicable executable and verify publisher/timestamp/revocation.
5. Generate and verify final GitHub artifact and SBOM attestations.
6. Complete license, vulnerability, AV, alert 389, and legal/distribution review.
7. Prove two-build normalized-content repeatability and run installed qualification.
8. Archive the complete release dossier and approval together.

## Reviewer verification path

A supply-chain reviewer should inspect:

1. `.github/workflows/ci.yml`
2. `.github/workflows/deploy.yml`
3. `.github/workflows/release-installer-signing.yml`
4. `docs/RELEASE_CHECKLIST.md`
5. `docs/SDLC_SSDF_MAPPING.md`
6. `docs/PRODUCTION_READINESS.md`
7. `scripts/verify_release_governance.py`
8. `scripts/verify_lockfiles.py`
9. `scripts/verify_environment_parity.py`
10. `scripts/verify_installer_integrity.py`
11. `scripts/windows/verify_nsis_governance.ps1`
12. `scripts/windows/verify_installer_signature.ps1`
13. `scripts/windows/run_packaging_smoke.ps1`

## Change notes for v2.8.0

1. Added NSIS governance to the supply-chain reviewer path alongside installer integrity, signing verification, and packaging smoke.

## Change notes for v2.7.0

1. Added installer-mode install/uninstall smoke evidence to the production release evidence list.
2. Updated metadata for the July 2026 desktop rebuild documentation review.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Corrected the document from a direct SLSA claim to a current-state/target-state roadmap.
3. Added current evidence table.
4. Added explicit caveats for Sigstore, Rekor, provenance, SBOM, and admission-controller claims.
5. Added reviewer verification path and production release evidence requirements.
