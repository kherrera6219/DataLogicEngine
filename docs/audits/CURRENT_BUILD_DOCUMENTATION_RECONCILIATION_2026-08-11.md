# DataLogicEngine current-build documentation reconciliation

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-AUDIT-012 |
| Title | Current-build documentation reconciliation |
| Document version | v1.1.0 |
| Product version | 4.3.0 |
| Status | active supporting review |
| Audience | Product owner, engineering, quality, release reviewers, and documentation maintainers |
| Owner | Documentation Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Current source, generated contracts, build reports, GitHub workflows, canonical documents, and retained installed evidence |
| Confidentiality | Public |
| Last reviewed | 2026-08-11 |
| Next-review trigger | Runtime code, build artifact, installed result, documentation authority, security result, or release decision change |
| Requirements and evidence | `config/product-versions.json`, `reports/installer_integrity_report.json`, `reports/packaging_smoke_report.json`, canonical docs, and documentation gates |

## Purpose and boundary

This review reconciles every tracked current file under `docs/` with the current
DataLogicEngine 4.3.0 source and build state. It distinguishes current authority,
generated contracts, immutable evaluation inputs, current supporting reviews,
and historical records.

At review start, `docs/` contained 207 tracked files: 43 current files and 164
files under `docs/archive/`. Archived files are intentionally not rewritten;
their dates, counts, findings, and decisions are historical evidence. Current
documents must identify archives as reference-only and must not use them as live
product authority.

## Current build truth

| Subject | Current evidence |
|---|---|
| Product | DataLogicEngine Desktop 4.3.0; Windows file version 4.3.0.0; pre-production channel |
| Source used for latest local build | `e0ebb6e137ff267567b31faf933291b356a275d0` |
| Current local installer | `DataLogicEngine Setup 4.3.0.exe` |
| Size | 283,874,927 bytes |
| SHA-256 | `734f92ff00e20b1b6c76cea41032264a34b8fa8eaa1a3c804ec185848b219e25` |
| Integrity | Pass; checksum and block map present |
| Signature | Not signed |
| Portable smoke | Not run by owner direction |
| Installed-mode smoke | Not run; no install/uninstall success evidence |
| Last installed qualification artifact | Separate August 10 artifact: 283,890,413 bytes; SHA-256 `1b7bb3202f1ac320d266f1203e12956c152040c42ba015f405ca33c2425a018e` |
| Installed evidence | Bound only to the August 10 hash: per-machine Program Files launch, `/ready`, five app-owned services, retained-data adoption, authentication, Diagnostics, and representative KA smoke |
| Release decision | **NO-GO**; CP19-M and retained signing, provider, installed, accessibility, recovery, external, pilot, and soak gates remain open |

The current local build and the last installed qualification artifact are
different evidence subjects. No installed, provider, accessibility, recovery,
privacy, performance, or soak result transfers between them.

## Current source and CI truth

The latest pushed runtime-equivalent CI records:

- 3,091 main-suite backend tests passed and 26 skipped;
- 23 contract tests passed and one skipped;
- five local-mode parity tests and six focused security tests passed;
- 435 frontend unit tests passed;
- five accessibility, 15 app-readiness, and 31 visual/browser checks passed;
- lint, typecheck, frontend build, Windows packaging smoke, governance, Docker
  build, deployment, and the push-triggered security workflow passed.

A later scheduled full-history TruffleHog scan failed on Lob-shaped identifiers
in historical/generated KA evidence and a test identifier. Repository search
found no current Lob integration or explicitly named Lob credential. This is not
treated as proof of exposure or as a clean result: detector disposition and a
successful scheduled rerun remain required.

## Findings corrected

1. Current documents conflated the August 11 local build with the August 10
   installed qualification artifact. They now name both subjects explicitly.
2. The documentation portal contained hard-coded, stale build and test claims.
   Its generator now reads the current installer and packaging reports.
3. The generated contract index omitted the actual local artifact identity. It
   now includes source commit, size, hash, signature, and installed-smoke state.
4. `DOCS_VERSION.json` pointed to archived superseded documents. Its policy,
   coverage, and baseline pointers now reference canonical authorities.
5. The Developer Guide repeated architecture documents in its required reading
   list and did not identify the current build boundary. Both are corrected.
6. The July 12 design audit looked current despite describing superseded code.
   It now carries a prominent historical-baseline notice.
7. The architecture overview omitted ChromaDB and described a generic browser
   client. It now shows the approved-client and five-service boundary.
8. Current security and release records did not include the later scheduled
   secret-scan failure. It is now retained as an open gate.

## Current document disposition

| Path or group | Disposition in this reconciliation |
|---|---|
| `docs/README.md` | Regenerated current portal and artifact boundary |
| Product/user canonical docs | Versions/review dates advanced; current-build versus installed-artifact language reconciled |
| Engineering canonical docs | Versions/review dates advanced; architecture, workflow, lifecycle, and security state reconciled |
| Assurance/external canonical docs | Versions/review dates advanced; exact-artifact evidence, CI counts, open scan, and retained gates reconciled |
| `docs/adr/README.md` | Index reviewed; ADR-0010 remains current and production approval remains withheld |
| `docs/adr/ADR-0010-app-owned-s3-compatible-object-store.md` | Accepted decision retained unchanged; no superseding decision found |
| `docs/audits/DataLogicEngine_Design_vs_Implementation_Audit_2026-07-12.md` | Preserved as historical baseline with current-use notice |
| `docs/audits/UKG_Spec_vs_App_Findings_2026-08-10.md` | Historical disposition retained; version advanced after current-build review |
| `docs/contracts/gateway-v1-compatibility.json` | Checked against live/OpenAPI compatibility; unchanged |
| `docs/openapi.yaml` | Checked against the live gateway compatibility gate; unchanged |
| `docs/evaluation/golden_corpus_v1.json` | Repository-authored immutable corpus reviewed; unchanged |
| `docs/evaluation/provider_model_matrix_v1.json` | Review version advanced and blockers rebound to the exact current artifact |
| `docs/spec-exports/*` | Regenerated from current KA, axis, and OpenAPI authorities |
| `docs/assets/readme/architecture-overview.svg` | Client and five-service labels corrected |
| `docs/DOCS_VERSION.json` | Global document baseline and canonical pointers updated |
| `docs/DOCUMENTATION_BOM.md` | Regenerated from documentation authority |
| `docs/DOCUMENTATION_CROSSWALK.md` | Regenerated from documentation authority and replacement state |
| `docs/generated/PRODUCTION_CONTRACT_INDEX.md` | Regenerated from live routes, product/provider/service authorities, and build reports |
| `docs/FILE_INVENTORY.csv` | Regenerated from the tracked repository |
| `docs/GENERATED_STRUCTURE.md` | Regenerated from the tracked repository |
| `docs/archive/**` | Preserved unchanged as historical/reference evidence |

## Validation required for closure

The reconciliation closes only when all of the following pass:

```powershell
python scripts/generate_documentation_authority.py
python scripts/generate_documentation_portal.py
python scripts/generate_documentation_contract_index.py
python scripts/generate_spec_exports.py
python scripts/generate_docs.py
python scripts/verify_documentation_truth.py --write-generated
python scripts/verify_product_user_docs.py
python scripts/verify_engineering_assurance_docs.py
python scripts/verify_docs_references.py
python scripts/verify_requirements_traceability.py
python scripts/verify_product_versions.py
python scripts/check_gateway_openapi_compatibility.py
```

The scheduled secret-scan finding remains outside documentation closure and
inside the production security/release gate until independently dispositioned
and rerun successfully.
