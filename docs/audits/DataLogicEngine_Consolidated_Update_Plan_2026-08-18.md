# DataLogicEngine Consolidated Update Plan

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-PLAN-CONSOLIDATED-2026-08-18 |
| Title | Consolidated update plan for the August 15–18 documentation set |
| Document version | v1.5.0 |
| Product version | 4.4.0 |
| Date | 2026-08-19 |
| Status | Active supporting review input; CU-2 desktop-chat hotfix has an exact-source portable rebuild while OpenAI/signing/fresh-installed rows remain blocked, CU-3/CU-4 are decision-gated, and CU-5 source/publication is partial |
| Audience | Product owner, maintainers, release reviewers, and the next execution session |
| Owner | Production Program Owner |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | `PRODUCTION_COMPLETION_PLAN_2026.md`, `TODO.md`, `HANDOFF.md`, live code, and reproducible evidence |
| Confidentiality | Public |
| Release posture | Production/public release remains **NO-GO** |

## 1. Purpose and authority

This plan consolidates the documentation, audit-remediation, coverage,
terminology, and rebuild material added between 2026-08-15 and 2026-08-18. It
replaces those planning inputs as the single active supporting update plan and
moves completed, superseded, or rejected source plans to `docs/archive/audits/`.

This document does not replace the root production program. Authority remains:

1. `PRODUCTION_COMPLETION_PLAN_2026.md` — sole release execution plan;
2. `TODO.md` — current open-work ledger;
3. `HANDOFF.md` — current checkpoint and exact next action;
4. this file — consolidated supporting implementation and documentation plan;
5. active canonical documents and artifact-bound evidence; and
6. `docs/archive/**` — historical reference only.

Installed behavior and reproducible production-path evidence outrank summaries.
No archived plan may authorize implementation, rebuilding, signing, or release.

## 2. Consolidated current state

### 2.1 Completed and retained

- Phase 19 CP19-A through CP19-L passed; all 213 canonical Knowledge
  Algorithms have individual qualification evidence.
- Slow-audit remediation Phases 1–4 and 6–7 passed post-QC source
  qualification. QR-0 through QR-5 are complete.
- Phase 5 delivered startup/layer contracts and Electron path helpers, but the
  major gateway, governed-execution, MCP, and Electron package decompositions
  were restored and remain partial/deferred.
- Independent coverage gates pass at 80.30% for `backend/`, 80.67% for
  `backend/security/`, 80.89% for `core/`, and 89.54% statements, 80.69%
  branches, 86.11% functions, and 91.36% lines for the frontend.
- The current portable engineering artifact is
  `DataLogicEngine Setup 4.4.0.exe`, 358,849,321 bytes, SHA-256
  `78800b84a670f6c5828894a26b6fc76d664fdf3f9e98876cb7d6fa11b15f49e3`,
  built from exact clean desktop-chat fix commit
  `e99119e222227eaf98940a9e34f0f587550ce2ca`. It passes integrity, NSIS,
  the 6,095-file payload, required-resource, and package-owned portable
  readiness checks; `/ready` completed in 25,138 ms with verified process
  ownership and clean shutdown.
- The scheduled full-history secret-scan finding is closed by scheduled run
  `32093054806`: 1,298 commits and 2,632,118,047 bytes scanned with zero
  verified and zero unverified secrets. Future candidate scans remain required.

### 2.2 Open and release-blocking

- CP19-M exact clean-source, signed, installed acceptance remains open.
- Google `gemini-3.7-flash` source-level live availability passes. OpenAI
  `gpt-5.6-sol` used High reasoning but is blocked on `quota_exhausted`; the
  two-provider source gate remains open.
- Signing/timestamping, elevated install/upgrade/repair/uninstall, retained-data
  lifecycle, Diagnostics service-role classification, installed Phase 9–13,
  accessibility/NVDA, protected-volume recovery, independent review, pilot,
  and 24/72-hour soak evidence remain open.
- The reviewed spec exports are published. Installed nested refinement-detail UI
  acceptance remains open, and the stale external analyses remain retrievable
  because their Google Docs are not writable by the connected app.
- Phase 5 structural decomposition requires an explicit owner disposition; it
  is not silently complete and is not a reason to invalidate the current
  CP19-M candidate line without a deliberate source-reopen decision.

Production/public release remains **NO-GO**.

## 3. Locked product and terminology boundaries

The following decisions remain controlling unless the product owner explicitly
reopens them:

| Gate | Locked boundary |
|---|---|
| Generative locality | Cloud BYOK only; do not reintroduce a local/Ollama/open-weights product path |
| API | Canonical `/api/v1/*`; legacy mirrors hard-off by default |
| GraphQL | Retained and authenticated; no GraphiQL in the product desktop |
| DSQP | Seven-part persona contract |
| Dataset/training | Dataset preparation/export only; no in-app trainer; DPO remains unavailable without real rejected-candidate provenance |
| MCP connectors | Jira and Salesforce orphan connectors remain retired |
| Signing/release | Owner-led only; no GO until CP19-M and every retained gate pass |
| Deployment | Single-owner, local-first Windows application; local-first does not mean air-gapped |

Terminology changes must describe implemented behavior. They must not create
new mathematical, compliance, certification, provider, deployment, or product
claims by renaming an existing component.

Specifically:

- do not call the product air-gapped while configured provider, connector,
  client, export, or telemetry egress exists;
- do not call sampled confidence a conformal prediction score or claim
  finite-sample coverage without a real conformal method, calibration evidence,
  tests, and reviewed documentation;
- do not reuse Common Criteria `EAL` terminology as a generic reasoning-depth
  label without standards/legal review and an exact code contract;
- do not advertise in-app fine-tuning or a complete DPO pipeline;
- do not add GDCH, Gemma, Med-Gemma, local open weights, or other unsupported
  providers without reopening the provider/product authority;
- do not introduce API aliases, schema aliases, database columns, or migrations
  solely to modernize copy; and
- use portable repository-relative Markdown links in active documentation.

## 4. Ordered consolidated execution

### CU-0 — Documentation consolidation and archive closure

**Status:** complete in this documentation change.

1. Preserve the full historical source documents under `docs/archive/audits/`.
2. Register this plan as the active supporting review input.
3. Update HANDOFF, TODO, CHANGELOG, the developer guide, and documentation
   portal to reference this plan.
4. Regenerate documentation authority, crosswalk, inventory, structure, and
   portal outputs.
5. Pass documentation reference, authority, BOM, truth, and diff-integrity
   gates.

### CU-1 — Current documentation truth repair

**Status:** complete in this documentation change.

1. Remove stale statements that the already-pushed August source checkpoints
   are wholly local and unpushed.
2. Mark the `5ec7af72...` and `1da8b8d6...` provider-refresh artifacts as
   superseded for current planning by the exact-source `650034ee...` rebuild.
3. Keep historical source/artifact statements in the archive or evidence tree,
   but prevent them from acting as the current handoff.
4. Keep the release decision **NO-GO**.

### CU-2 — CP19-M exact-artifact acceptance

**Status:** active; exact-source portable engineering rebuild is complete while
OpenAI, signing, installed, manual, and external acceptance remain open.

**2026-08-18 checkpoint:** focused provider/evidence contracts pass 26/26.
Google `gemini-3.7-flash` passes one bounded live call; OpenAI `gpt-5.6-sol`
uses `high` reasoning but is blocked on `quota_exhausted`. No credential or
response body was recorded. Exact-source rebuild/signing remains gated.
An owner-requested second Google call passed in 1,021.73 ms. The independent
full-history secret-scan finding is also closed; neither result closes OpenAI,
signing, or installed acceptance.
A fresh OpenAI retry reached the API with High reasoning and returned the same
`quota_exhausted` result in 2,224.49 ms without recording credentials or response
content.

**2026-08-18 exact-source checkpoint:** at the owner's direction, the work
advanced through independently safe packaging without waiving the failed
OpenAI row. Reviewed source/evidence commit
`c765ba03257e58e69a4cd4b80f92390c71346801` produced the unsigned
358,848,516-byte installer with SHA-256
`650034eeec76cbfc582ce81551f40d14e527aeea2707682bdf040d808062a591`.
Integrity, NSIS governance, the 6,096-file payload, required resources, and
strict package-owned portable `/ready` pass. Installed mode and signing were
not attempted; production/public release remains **NO-GO**.

**2026-08-19 desktop-chat checkpoint:** the installed app's Google provider
test succeeded, but desktop chat returned HTTP 422 before orchestration because
compatibility mode `chat` was compared directly with canonical virtual-model
mode `standard`. Commit `e99119e2...` normalizes supported desktop aliases
through the governed-mode contract and passes 14 focused contract/route tests.
Its exact-source `78800b84...` installer passes all static/package checks and
strict portable readiness described in Section 2.1. The stopped installed copy
was not modified; fresh installed Google chat acceptance remains open.

1. Run the bounded owner-authorized Google and OpenAI model tests without
   exposing or requiring re-entry of stored keys.
2. Commit the reviewed source and evidence. **Complete:** `c765ba03...`; latest
   desktop-chat fix checkpoint `e99119e2...`.
3. Rebuild from that exact clean commit. **Complete for current unsigned
   portable engineering acceptance:** `78800b84...`.
4. Sign and timestamp the resulting candidate.
5. Complete elevated installed lifecycle, retained-data, service-role,
   provider/corpus/human, accessibility, recovery, independent-review, pilot,
   and soak acceptance against that exact hash.
6. Bind CP16-G and CP17-E only to the exact signed artifact.

**Exit:** CP19-M and every retained installed/manual/external gate pass with
artifact-bound evidence. Until then, release remains **NO-GO**.

### CU-3 — Phase 5 structural residual disposition

**Status:** residual audit complete; owner disposition remains required. Do not
begin decomposition during CU-2 without an explicit source-reopen decision.

1. Decide whether the four major decompositions are required before release,
   deferred to post-release maintenance, or formally waived with residual risk.
2. If reopened, extract pure helpers first and preserve patch-visible module
   symbols used by tests.
3. Work one boundary at a time: gateway, governed orchestrator, MCP routes,
   then Electron main.
4. Require behavior/route/API parity, focused tests after every move, full
   applicable validation, and a new exact candidate rebuild.

**Exit:** all four splits pass their original acceptance criteria, or the owner
records a durable waiver and target phase. Partial helper extraction alone does
not close this phase.

The 2026-08-18 assessment measured 3,109-line gateway API, 2,681-line governed
orchestrator, 1,859-line MCP routes, and 1,808-line Electron main residuals. It
recommends a named post-release maintenance deferral because reopening the
source now would force a replacement artifact cycle without removing the current
quota/signing blockers. This recommendation is not a waiver.

### CU-4 — Evidence-based terminology modernization

**Status:** evidence inventory complete; adoption remains blocked on owner
approval after CU-2 unless explicitly reprioritized.

1. Inventory every candidate term across live code, UI, APIs, SDKs, active docs,
   generated contracts, tests, and archived history.
2. Classify each proposal as:
   - public-copy clarification with no contract change;
   - UI/SDK description change;
   - backward-compatible API/schema change requiring versioned contract work;
   - internal refactor requiring behavior-parity evidence; or
   - rejected because it overstates implementation or changes product scope.
3. For every mathematical or standards term, record the live implementation,
   exact measured property, authoritative source, reviewer, and prohibited
   claims before adoption.
4. Prefer plain factual terms such as uncertainty sampling, multi-hypothesis
   analysis, bounded planning, evidence validation, and multi-perspective review
   where those are what the code actually performs.
5. Preserve compatibility identifiers when renaming would break stored data,
   APIs, traces, SDKs, or evidence. Display aliases must not rewrite history.
6. Treat NIST, ISO/IEC, IEEE, EU, defense, healthcare, financial, and other
   compliance mappings as evidence-guided design crosswalks, not certification
   or approval claims.
7. Run documentation, API, SDK, frontend, migration, trace, and installed
   regression gates appropriate to the approved scope.

**Exit:** every adopted term maps to tested behavior, all standards claims have
reviewed sources and limitations, compatibility is preserved, and active docs
pass with zero errors or warnings.

The inventory rejects unsupported conformal-prediction, Common Criteria EAL,
air-gap, GDCH/local-open-weight, and complete DPO-training equivalences. It
records safe plain-language candidates but changes no compatibility identifier.

### CU-5 — External knowledge and installed trace-detail closure

**Status:** source trace detail and replacement publication complete; installed
acceptance and stale-document archive/de-rank remain open.

1. Publish the reviewed 213-row KA registry and axes 14–17 replacement export to
   the owner-controlled external project-knowledge system.
2. Archive or de-rank the superseded external analyses.
3. Expose named nested 12-step refinement receipt details in the installed Trace
   Explorer without creating a second trace authority.
4. Validate the UI through the CU-2 packaged visual/accessibility matrix.

The Trace Explorer now renders the existing
`dle.canonical-refinement-result.v1` receipt with named step details; focused
backend/frontend, lint, and type gates pass. Google Drive readback verifies the
published replacement files. The three stale Docs remain unchanged because the
connected app lacks file-scoped write access.

## 5. Recent-document disposition

### 5.1 Archived planning and audit inputs

The following originals are retained under `docs/archive/audits/` and are
historical only:

| Archived document | Consolidated disposition |
|---|---|
| `DataLogicEngine_Slow_Section_Audit_Findings_2026-08-11.md` | Findings resolved or transferred; baseline was product 4.3.0 |
| `DataLogicEngine_Slow_Audit_Recommendations_10of10_2026-08-12.md` | Completed recommendations transferred to current state; residual Phase 5 moved to CU-3 |
| `ORPHAN_MODULE_DISPOSITION_WORKSHEET_2026-08-11.md` | B0/delete decisions executed; no active owner worksheet remains |
| `DataLogicEngine_Phased_Implementation_Plan_2026-08-12.md` | Phases 1–4 and 6–7 complete; Phase 5 moved to CU-3; Phase 8 remains under release authority |
| `DataLogicEngine_Grok_QC_Remediation_Plan_2026-08-15.md` | QR-0 through QR-5 complete; QR-6 installed work transferred to CU-2/CP19-M |
| `DataLogicEngine_80_Percent_Coverage_Execution_Plan_2026-08-16.md` | Complete; measurements retained in active CI policy and canonical records |
| `PHASE5_GODFILE_SPLIT_NOTES.md` | Historical failed-split notes; safe pattern and residual transferred to CU-3 |
| `TERMINOLOGY_MODERNIZATION_PLAN_2026-08-18.md` | Superseded unapproved draft; corrected boundary and gated work transferred to CU-4 |

### 5.2 Retained active authority and policy records

These remain at their current paths because they describe live product
contracts rather than superseded planning:

- `docs/AUTH_SURFACE_MATRIX.md`;
- `docs/CI_QUALITY_POLICY.md`;
- `docs/DATASET_EXPORT_HANDOFF.md`;
- `docs/DESKTOP_CSP.md`;
- `docs/DMRF_TRUTH_BOUNDARY.md`;
- `docs/MEMORY_AUTHORITY.md`; and
- `sdk/LICENSE_NOTICE.md`.

### 5.3 Retained artifact-bound evidence

These remain under `reports/production-readiness/2026/phase-19/`:

- `post-qc-rebuild/first-rebuild-runtime-blocker.md`;
- `post-qc-rebuild/repaired-candidate-engineering-acceptance.md`; and
- `provider-refresh-rebuild/provider-refresh-rebuild-acceptance.md`.

They are evidence snapshots, not current execution plans. The provider-refresh
record's `5ec7af72...`, later `1da8b8d6...`, and prior exact-source
`650034ee...` artifacts are superseded for current planning by the desktop-chat
fix artifact `78800b84...` recorded in root authority.

## 6. Validation and stop conditions

Run the applicable documentation gates after any update to this plan or its
archive routing:

```powershell
python scripts/generate_docs.py
python scripts/generate_documentation_authority.py
python scripts/generate_documentation_portal.py
python scripts/generate_documentation_contract_index.py
python scripts/verify_docs_references.py
python scripts/verify_documentation_bom.py
python scripts/verify_doc_authority.py
python scripts/verify_documentation_truth.py
git diff --check
```

Stop and retain **NO-GO** if documentation overstates an installed, provider,
security, accessibility, signing, independent-review, or release result; if a
terminology change implies behavior not implemented; if an archived plan becomes
an active instruction; or if a source change invalidates the candidate without
a new exact rebuild and evidence binding.

## 7. Exact next action

Proceed with CU-2: install the exact-source `78800b84...` desktop-chat fix
artifact and repeat a normal Google chat to confirm governed session and
validation telemetry creation. Restore or replenish OpenAI quota and rerun the
bounded `gpt-5.6-sol` High-reasoning check without exposing stored keys. After
both source-level provider checks pass, obtain owner-authorized production
signing material and rebuild/sign/timestamp from the then-current exact commit,
then continue CP19-M installed acceptance against only that signed artifact
hash.
In parallel, grant the connected Google Drive app write access to the three
stale gap-analysis Docs or move them manually into the created archive folder.
