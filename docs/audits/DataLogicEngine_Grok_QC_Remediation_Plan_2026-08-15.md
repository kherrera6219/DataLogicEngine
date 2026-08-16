# DataLogicEngine Grok Work QC Remediation Plan

| Field | Value |
|---|---|
| Date | 2026-08-15 |
| Status | QR-0 through QR-5 complete; QR-6 portable engineering subset complete; installed CP19-M acceptance retained |
| Scope | Local slow-audit remediation produced from Phases 1–7; no push or release authorization |
| Release authority | `PRODUCTION_COMPLETION_PLAN_2026.md` |
| Open-work authority | `TODO.md` |
| Session authority | `HANDOFF.md` |
| Source audit plan | `docs/audits/DataLogicEngine_Phased_Implementation_Plan_2026-08-12.md` |
| Release posture | **NO-GO**; no signing, publishing, or CP19-M acceptance from this tree |

## 1. Objective

Turn the useful portions of the local Grok implementation into a correct,
fully governed, qualification-ready source checkpoint without discarding sound
work or allowing incomplete audit claims to trigger a premature rebuild.

This plan is a remediation supplement. It does not replace the root production
program, authorize Phase 8, close CP19-M, or change production/public release
NO-GO.

## 2. Starting position

The QC review found substantial implementation value and broad backend/build
coverage, but the tree is not commit-ready because:

1. the new L1–L10 contract conflicts with the live ten-layer authority;
2. one frontend test is stale after an intentional product-honesty copy change;
3. one emitted truth-memory URL still targets the disabled legacy API prefix;
4. the OpenAPI product version and generated route index are stale;
5. KA manifest metadata exists server-side but automated client parity is not
   established;
6. frontend dependency classifications disagree with lockfile root metadata;
7. documentation reference, BOM, inventory, and truth gates are not green; and
8. the plan, TODO, and handoff overstate completion/commit status.

The preferred disposition is **targeted remediation**, not whole-tree rollback.

## 3. Execution rules

1. Preserve the current local patch before changing implementation files.
2. Treat newly appearing `_claude_*` files and `_claude_pytest.err` as concurrent,
   out-of-scope work until their owner and purpose are confirmed.
3. Do not stage, commit, rebuild, sign, publish, or push during QR-0 through QR-4.
4. Make each remediation batch independently reviewable and reversible.
5. Derive contracts from live authorities; do not create parallel descriptive
   authorities that can drift.
6. Generated evidence must be refreshed only after source and documentation
   inputs stabilize.
7. A passing source/build gate does not satisfy installed CP19-M acceptance.

## 4. Ordered remediation phases

### QR-0 — Preserve and classify the workshop tree

**Purpose:** prevent loss or accidental inclusion before edits begin.

**Actions**

- Record HEAD, origin parity, full status, tracked diff, and untracked inventory.
- Save a recoverable binary patch or equivalent local snapshot outside the
  intended commit set.
- Classify every untracked file as keep, regenerate, scratch helper, concurrent,
  or delete candidate.
- Exclude the one-shot `_phase5_package_splits.py` and
  `_phase5_restore_api_modules.py` helpers from the intended production commit.
- Confirm `backend/routes/mcp_routes.py` has no content delta if it remains
  reported as modified.

**Acceptance gate QR-0**

- [x] Recoverable pre-remediation snapshot exists.
- [x] Intended Grok scope is listed explicitly.
- [x] Concurrent and scratch artifacts cannot enter staging accidentally.
- [x] No implementation behavior changed during preservation.

**Rollback boundary:** restore the saved patch/snapshot; do not use a broad
destructive reset against the dirty workspace.

### QR-1 — Correct source-contract blockers

**Purpose:** remove known factual/runtime defects before wider cleanup.

#### QR-1A — Reconcile the ten-layer contract

- Compare `backend/governed_execution/layer_contracts.py` with
  `backend/governed_execution/ten_layers.py` and the orchestrator stage flow.
- Preferred fix: derive exposed layer names from `LAYER_STAGE_NAMES` and retain
  only additional read/write metadata that is demonstrably accurate.
- Alternative: remove the new file and its test, and keep Phase 5 contract
  extraction open.
- Replace shape-only assertions with equality/drift tests against the canonical
  layer-stage mapping.

**Acceptance**

- [x] There is one authoritative L1–L10 name mapping.
- [x] `provider_execution` remains correctly represented as a separate stage.
- [x] Trace persistence is not mislabeled as canonical L9.
- [x] A deliberate mapping mismatch causes a test failure.

#### QR-1B — Fix the truth-memory explainability URL

- Change the emitted URL in
  `backend/truth_engine/truth_gate/compliance.py` from the disabled legacy
  prefix to `/api/v1/truth/memory/explain/{session_id}`.
- Add a regression assertion covering the default legacy-off application.

**Acceptance**

- [x] Every emitted explainability URL targets the default v1 application.
- [x] No legacy `/api/truth/...` dependency is reintroduced.

#### QR-1C — Align the dataset exporter test

- Keep the honest export-only UI wording.
- Update the stale `DatasetExporterSettings` assertion to the approved copy.
- Confirm there are no other in-app trainer promises in active UI/docs.

**Acceptance**

- [x] The focused component test passes.
- [x] The UI consistently describes export/preparation rather than training.

#### QR-1D — Restore current product-version authority

- Change `docs/openapi.yaml` from the stale 4.3.0 audit baseline to current
  product version 4.4.0.
- Check all new audit-generated contract text for accidental 4.3.0 promotion;
  retain 4.3.0 only where clearly labeled historical observation.

**Acceptance gate QR-1**

- [x] Focused layer, truth, frontend, version, and route tests pass.
- [x] OpenAPI and current product-version authority agree.
- [x] No new compatibility aliases are introduced to hide failures.

**Rollback boundary:** revert only the failing QR-1 sub-batch; do not revert the
unrelated legacy-route, gateway, orphan, UI-honesty, or CI work.

### QR-2 — Complete integrity and dependency work

**Purpose:** close partial contract claims and make packaged dependency metadata
truthful.

#### QR-2A — Decide and implement KA manifest parity

Choose one documented outcome:

1. **Preferred:** add an automated Python/TypeScript/frontend or CI comparison
   of manifest version, capability count, and hash against the server endpoint;
   or
2. relabel the feature as a server manifest-integrity endpoint and remove
   claims that client/server parity is already enforced.

Strengthen the server test to validate the current 213-capability authority,
expected manifest version, and deterministic hash behavior without hardcoding a
second independent source of truth.

**Acceptance**

- [x] Documentation matches the implemented parity level.
- [x] Count/hash/version drift is automatically detectable.
- [x] All 213 canonical KA IDs remain preserved.

#### QR-2B — Regenerate frontend lock metadata

- Use the repository-governed Node/npm toolchain to regenerate
  `frontend/package-lock.json` after the production dependency move.
- Verify root dependency classification agrees with `frontend/package.json`.
- Run clean-install, lock, build, and packaging-resource checks.

**Acceptance gate QR-2**

- [x] Package manifest and lockfile root metadata agree.
- [x] Production-only dependency dry-run retains required runtime packages.
- [x] Frontend and Electron full builds pass from the refreshed lock.
- [x] KA integrity behavior and claims are aligned.

**Rollback boundary:** package manifest and lockfile changes revert together;
KA endpoint/client changes revert as a separate unit.

### QR-3 — Reconcile documentation and governance

**Purpose:** make active documentation accurately describe the corrected tree.

**Actions**

- Repair the two invalid wildcard source references in the slow-audit plan and
  findings document.
- Correct the orphan worksheet heading-level warning.
- Update the audit plan status:
  - Phase 5 = partial/deferred unless the major split acceptance criteria are
    actually completed;
  - Phases 1–7 = implemented with QC remediation complete only after QR-4;
  - engineering 9–10 re-review remains open until its explicit criterion passes.
- Correct `TODO.md`: do not say the work is committed until commit hashes exist.
- Correct `HANDOFF.md`: point the next session to this QC remediation plan and do
  not make rebuild the next action until QR-4 passes.
- Update `CHANGELOG.md` only with behavior that remains after remediation.
- Add every retained new active document to the appropriate authority,
  inventory, BOM, crosswalk, and documentation portal.
- Regenerate documentation inventories and the production contract index after
  the live route manifest is current.

**Required documentation gates**

```powershell
python scripts/generate_docs.py
python scripts/generate_documentation_contract_index.py
python scripts/verify_docs_references.py
python scripts/verify_documentation_bom.py
python scripts/verify_documentation_truth.py
```

**Acceptance gate QR-3**

- [x] Documentation references pass with no strict errors.
- [x] Documentation BOM passes with no inventory drift.
- [x] Documentation truth is 10/10.
- [x] The generated route count (350) matches the default live application.
- [x] OpenAPI, contract index, TODO, HANDOFF, and product authority agree on
  version, status, and next action.
- [x] Release remains NO-GO and CP19-M remains open.

**Rollback boundary:** generated documents revert and regenerate as one set;
hand-authored authority corrections remain a separate reviewable set.

### QR-4 — Full source qualification

**Purpose:** establish one post-remediation source certificate before any
commit/rebuild decision.

**Backend and governance**

```powershell
python -m pytest -q --no-cov tests
python scripts/scan_orphan_pyc.py --fail-on-orphan
python scripts/verify_route_uniqueness.py
python scripts/verify_docs_references.py
python scripts/verify_documentation_bom.py
python scripts/verify_documentation_truth.py
git diff --check
```

**Frontend**

```powershell
Set-Location frontend
npm test
npm run lint
npm run typecheck
npm run build
```

Run the existing Electron TypeScript build and Windows packaging-resource
verification using the repository's governed commands.

**SDKs**

- Run the complete Python SDK test suite from `sdk/UKG_Python_SDK`.
- Run `npm test` from `sdk/DataLogicEngine_TypeScript_SDK`.

**Acceptance gate QR-4**

- [x] All backend tests pass with only documented skips/warnings.
- [x] All frontend tests pass; no stale assertion remains.
- [x] Frontend lint, typecheck, Next build, and Electron build pass.
- [x] Python and TypeScript SDK suites pass.
- [x] Route collisions = 0 and legacy prefixes remain off by default.
- [x] Orphan count = 0 and blocked count = 0.
- [x] Documentation truth = 10/10.
- [x] Diff check and packaging-resource verification pass.
- [x] Counts and exact commands are recorded in TODO/HANDOFF.

**QR-4 certificate (2026-08-15):** backend 3,108 passed / 18 skipped;
frontend 435 passed; Python SDK 36 passed; TypeScript SDK 8 passed; frontend
lint/typecheck/Next/Electron builds passed; documentation truth 10/10; 350 live
routes with zero unclassified and zero unauthenticated mutations; route
collisions 0; orphan/blocked counts 0; packaging resources and diff check pass.

Any failed QR-4 check reopens the owning earlier phase. Do not waive a failed
gate by editing only its test or generated report.

### QR-5 — Commit-readiness review

**Purpose:** turn the validated workshop tree into auditable commits without
mixing scratch or concurrent artifacts.

**Recommended commit groups**

1. API/route and product-contract corrections.
2. Runtime/startup/layer/memory/DSQP contract work.
3. Frontend/Electron honesty, dependency, and path changes.
4. KA manifest/SDK parity work.
5. CI, route, orphan, and packaging governance.
6. Documentation, inventories, generated evidence, TODO, HANDOFF, and changelog.

Before each commit:

- inspect the exact staged file list and staged diff;
- confirm no `_claude_*`, `_phase5_*`, log, cache, build, or unrelated file is
  staged;
- rerun the focused tests for that commit group; and
- keep generated artifacts in the documentation/evidence commit with their
  source inputs.

**Acceptance gate QR-5**

- [x] Every retained file has an owner and purpose.
- [x] Scratch/concurrent artifacts are excluded or separately dispositioned.
- [x] Commit grouping preserves reviewability and rollback safety.
- [x] HANDOFF/TODO mention real commit hashes only after commits exist.
- [x] Local main is not pushed without an explicit owner instruction.

**QR-5 result (2026-08-15):** 75 tracked content-diff files and 33 intended
untracked implementation, test, documentation, tooling, or evidence files were
classified. The two one-shot Phase 5 rewrite/restore helpers were moved to the
recoverable QR-0 backup. No concurrent `_claude_*` artifacts remain in scope;
`backend/routes/mcp_routes.py` reports metadata-only modification with no
content diff. Local HEAD and `origin/main` remain equal at `d24273ff`.

### QR-6 — Handoff to CP19-M

QR-6 begins only after QR-1 through QR-5 are complete.

**Actions**

- Record exact final source commit(s), clean status, validation counts, product
  version, KA manifest authority, and generated evidence paths.
- Obtain owner authorization before any clean desktop rebuild.
- Build the exact source checkpoint and run packaging smoke/resource checks.
- Continue CP19-M only against the exact signed/timestamped artifact required by
  the root production plan.

**Acceptance gate QR-6**

- [x] Source checkpoint is clean, reproducible, and fully qualified.
- [x] Rebuild authorization is explicit (owner instruction, 2026-08-15).
- [ ] Installed evidence binds to the exact rebuilt artifact.
- [x] Production/public release remains NO-GO until every retained gate passes.

**QR-6 portable engineering result (2026-08-15):** the first rebuilt artifact
exposed a retained 4.3.0-to-4.4.0 runtime-lock incompatibility and proved the
old process-alive smoke was insufficient. Commit `16faaeb4` corrected the
upgrade-source contract and passed 34 focused lifecycle/migration tests. The
replacement artifact built from `e893d424` is 358,857,127 bytes with SHA-256
`54dfb496bc2c45a5d02656bdf3d9a02a571868889dc7a76b59ce4fc1ed44fc97`.
It is unsigned. Integrity, NSIS governance, resources, package-owned backend
readiness, `/health`, retained-identity advancement, and visible dashboard,
Trace Explorer, Diagnostics, and Algorithm Registry checks pass. Commit
`56bc4aa7` hardens the smoke to require and ownership-check `/ready`.

Per-machine installed acceptance, signing/timestamping, providers,
accessibility/NVDA, independent review, pilot, and soak gates remain open.
Evidence:
`reports/production-readiness/2026/phase-19/post-qc-rebuild/repaired-candidate-engineering-acceptance.md`.

**Local commit checkpoint:** `3054d5de` (source remediation), `6e2fdd5b`
(governance), `cbfacbdb` and `2d166456` (documentation/checkpoint), `16faaeb4`
(retained upgrade), `e893d424` (first-artifact blocker evidence), and `56bc4aa7`
(readiness-smoke hardening). These commits are local and unpushed. The final
evidence/handoff commit follows them. The exact rebuilt binary remains bound to
source commit `e893d424`, not to later evidence-only commits.

## 5. Keep, rework, and exclude disposition

### Keep after validation

- Legacy API prefixes off by default and route-uniqueness enforcement.
- Gateway administration namespace/client updates.
- Health product-version authority.
- Orphan scan/purge governance and zero-orphan outcome.
- Export-only/local-generation-disabled product honesty.
- Cloud-BYOK capability disclosure and simulation-model refusal.
- Startup/Electron path helpers and packaging-resource checks.
- DSQP seven-part contract test, memory authority work, and vector-profile
  fail-closed behavior where live tests confirm the claims.

### Rework before commit

- L1–L10 layer contract and its test.
- Truth-memory explainability URL.
- Dataset exporter test expectation.
- OpenAPI/product-version and generated route evidence.
- KA client parity claim/test depth.
- Frontend package-lock dependency classification.
- Audit-plan, TODO, HANDOFF, changelog, inventory, BOM, and truth status.

### Exclude unless separately reviewed

- One-shot Phase 5 rewrite/restore helpers.
- Concurrent `_claude_*` scripts and `_claude_pytest.err`.
- Temporary logs, caches, build products, and timestamp-only diagnostic output
  that is not required evidence.

## 6. Final definition of remediation complete

This QC remediation is complete only when all of the following are true:

- [x] QR-0 through QR-5 acceptance gates pass.
- [x] No known incorrect or competing runtime contract remains.
- [x] Backend, frontend, Electron, SDK, route, orphan, packaging, and docs gates
  are green in one post-remediation qualification run.
- [x] Documentation truth is 10/10 and current version/route evidence agrees.
- [x] Phase 5 and P1–P7 status language is evidence-based.
- [x] Intended changes are separated from scratch and concurrent work.
- [x] No rebuild, commit, push, or production-GO claim occurred prematurely.
- [x] The root production plan still controls CP19-M and release authorization.
