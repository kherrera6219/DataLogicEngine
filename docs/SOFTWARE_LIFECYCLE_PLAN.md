# DataLogicEngine software lifecycle and configuration-management plan

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ENG-005 |
| Title | Software lifecycle and configuration-management plan |
| Document version | v1.3.0 |
| Product version | 4.4.1 |
| Status | active |
| Audience | Product owner, engineering, quality, security, release, operations, and professional reviewers |
| Owner | Release Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Repository governance, production plan, CI/release workflows, locks, documentation authority, and evidence policy |
| Confidentiality | Public |
| Last reviewed | 2026-08-11 |
| Next-review trigger | Lifecycle, branch, review, toolchain, dependency, build, test, documentation, release, or maintenance-policy change |
| Requirements and evidence | Product requirements, active plan/TODO, CI workflows, exact locks, manifests, tests, and release records |

## Lifecycle objective

Deliver and maintain one truthful, secure, reproducible, supportable Windows
product from approved requirements through design, implementation, verification,
signed release, operation, incident response, update, and retirement. Schedule or
demonstration pressure does not waive an exit gate.

CP19-L and one clean unsigned rebuild/install checkpoint passed on 2026-08-10.
A newer August 11 engineering artifact has passed integrity but not installed-
mode acceptance. The lifecycle remains at CP19-M; signing, exact-artifact
acceptance, installed lifecycle/recovery, external review, pilot, and soak are
mandatory. A scheduled full-history secret-scan failure is also open pending
detector disposition and a clean rerun.

## Authoritative configuration

| Authority | Purpose |
|---|---|
| `docs/PRODUCT_REQUIREMENTS.md` | Approved product scope and acceptance requirements |
| `PRODUCTION_COMPLETION_PLAN_2026.md` | Sole active production completion program |
| `TODO.md` / `HANDOFF.md` | Current executable work and exact continuation point |
| `config/product-versions.json` | Product/Windows/contract version authority |
| `requirements.txt` / `requirements.lock` | Reviewed direct inputs and exact hash-locked Python release environment |
| `frontend/package-lock.json` | Exact Node/Electron dependency authority |
| `config/release-channel.json` | Candidate versus production promotion boundary |
| `config/release-trust-policy.json` | Signing/update/distribution trust decisions |
| `config/documentation-authority.json` | Canonical documents and source dispositions |
| Git commit/tag and release manifest | Immutable source and artifact identity |

Generated inventories, schemas, OpenAPI, SBOMs, attestations, and evidence are
derived outputs and identify their generation authority. Historical plans and
session records are not current requirements.

Retained Phase 18 work applies a stricter identity-migration rule to Knowledge
Algorithms.
Before changing a KA ID, name, purpose, or runtime mapping, CP18-A must classify
every historical/executable definition and preserve distinct capability through
an approved canonical ID or compatible alias. The approved KA manifest is
configuration authority after the crosswalk reported zero unclassified
capabilities and zero unresolved semantic collisions. CP19-L is complete;
signed release-candidate promotion remains paused at CP19-M exact-artifact
acceptance.

## Change lifecycle

1. Define or update the approved requirement, owner, acceptance evidence, risks,
   and affected UI/API/data/security/operations/documentation surfaces.
2. Record an ADR for a material architecture, product-boundary, replacement, or
   irreversible operational decision.
3. Add a failing test or other objective evidence that exposes the gap when
   feasible.
4. Implement the smallest coherent change while preserving trust boundaries and
   compatibility policy.
5. Run focused tests, cross-system tests, static/type/security checks, docs and
   schema/contract gates, and packaged/installed validation proportional to risk.
6. Update canonical documentation, TODO, handoff, changelog, generated
   inventories, and redacted phase evidence in the same checkpoint.
7. Review and commit only a coherent validated checkpoint; push and verify local
   branch parity with the protected GitHub branch.
8. Promote only after all phase/release gates and named authorities approve the
   exact artifact.

## Branch, review, and commit controls

`main` is the production integration authority and must remain protected by
required status checks and review/owner rules appropriate to the repository.
Changes identify their requirement/defect and validation. Secrets, generated
local runtime data, caches, unsigned release binaries, and unrelated developer
artifacts are excluded.

Commits are intentionally scoped and must not hide unrelated user work. Security,
auth, data migration/deletion, signing/update, provider/connector, and release
changes receive specialist review or explicit owner approval. Emergency changes
still require post-change evidence and do not self-authorize release.

## Verification pipeline

Required checks are selected from:

- Python Ruff, tests, coverage, exception/import/security sweeps;
- frontend ESLint, typecheck, unit, E2E, accessibility, visual, and build gates;
- API/route/schema/auth/SDK/streaming/compatibility contracts;
- migration, backup/restore, deletion, reconciliation, data-protection checks;
- exact dependency/version/workflow pins, SBOM, provenance, signature, malware,
  license, payload, and installer governance;
- documentation authority, references, requirements traceability, and generated
  inventory parity;
- clean packaged/installed normal, adversarial, failure, recovery, accessibility,
  performance/load/soak, human pilot, and independent-review evidence.

Passing source tests does not replace installed acceptance. Deferred installed
or manual evidence stays visible as a release blocker.

## Defect and vulnerability handling

Findings are severity-classified, reproducible, assigned an owner and due date,
linked to affected requirements and evidence, fixed or explicitly removed from
scope, regression-tested, and closed only against the corrected commit/artifact.
P0/P1 findings and unaccepted P2 findings block release. Dependabot alert 389
was fixed by removing the vulnerable ChromaDB Python SDK from both dependency
authorities and qualifying the restricted replacement client. The replacement
evidence remains bound to the release record.

Vulnerabilities use private disclosure, coordinated remediation, affected-version
analysis, secret/key rotation where needed, SBOM/advisory updates, and signed
replacement publication. Do not expose vulnerability details or secrets in
public issues before coordinated disclosure.

## Release lifecycle

1. Freeze approved requirements, source commit, versions, exact locks, workflows,
   documentation, and candidate release channel.
2. Produce isolated builds and compare them under the approved reproducibility
   rule; investigate nondeterminism rather than declaring equality.
3. Verify payload boundaries, manifests, SBOMs, provenance, malware/license/
   vulnerability state, legal redistribution authority, and publisher identity.
4. Sign and timestamp the canonical installer and every required executable.
5. Complete clean install/repair/upgrade/rollback/uninstall, Windows, providers,
   five services, gateway/MCP, failure/recovery, accessibility, pilot, and soak.
6. Bind the release record to commit, tag, installer hash/signature, manifests,
   evidence, limitations, and owner go/no-go approval.
7. Publish only approved artifacts and documentation; candidate mode and
   environment variables cannot authorize production.

Automatic update remains disabled until signed metadata, publisher, downgrade/
replay/interruption/rollback, staged activation, and offline gates pass.

## Documentation lifecycle

Canonical documents use controlled IDs, version, product binding, status,
audience, owner, approver, authority, classification, review date/trigger, and
requirements/evidence. Status uses the controlled vocabulary and never converts
planned or qualification-only work into current production behavior.

The Phase 16 crosswalk preserves every source as authoritative input, generated
replacement, merge route, or historical/archive record. CP16-F authorized and
completed the controlled archive only after target content, evidence retention,
inbound links, technical review, and per-source hashes passed. The baseline and
closure reports preserve that proof. Future moves require a new reviewed closure;
the prior authorization is not a standing permission. Phase 17 locks the final set.

## Maintenance and retirement

Monitor vulnerabilities, provider/model support, dependencies, Windows support,
service artifacts, certificate/update authority, performance/resource trends,
backup/restore drills, data retention/deletion, incidents, and customer feedback.
Each maintenance release repeats impact-appropriate gates and updates the change
log and release record.

Retirement defines end-of-support dates, migration/export, provider/connector key
revocation, update/feed shutdown, data retention/deletion, archive/evidence
preservation, and public disclosure. Unsupported versions do not silently remain
eligible for production support.

## Current status

Product 4.4.1 inherits engineering checkpoints through Phase 15, completed CP16-F
documentation replacement, and completed CP17-A through CP17-D consolidation.
CP17-E remains an exact signed clean-installed walkthrough. The unsigned
candidate, differing independent build hashes, installed/manual/independent
gates, legal/signing decisions, and installed/independent acceptance of the
selected object store keep production/public release at **NO-GO**. Alert 389 is
fixed.
