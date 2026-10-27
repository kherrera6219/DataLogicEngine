# Owner-approved CI and governed-chat repair — 2026-10-26

## Authority and scope

Kevin approved this fast-track work outside the compliance phase order: resolve
the current Python and NPM dependency scans, replace the LlamaIndex dependency,
audit the new PyJWT finding, and update Governed Chat presentation. This does not
close CR-A0, disposition Phase A, or approve production release.

Work identifiers: **OWNER-CI-01** (dependencies, chunking, CI compatibility),
**OWNER-CHAT-01** (chat presentation and response breadth), and
**OWNER-DOC-01** (this checkpoint). Scope is the dependency manifests/locks and
authority, RAG chunking and ingestion revision handling, associated verification
scripts/tests, CI workflows, and the affected chat components/prompt selector.
Code fixes and root `tests/` changes are committed separately as required by
`tests/AGENTS.override.md`.

Kevin explicitly retained the current Standard-mode release behavior when no
governed evidence is found. Standard still permits one provider attempt;
Enhanced permits at most two attempts and one conditional refinement cycle.
No new provider call, network destination, or telemetry is introduced. Chunker
revision data uses the existing extensible ingestion metadata.

## Verified causes

- September security and backend jobs both stopped at the NLTK audit, before
  pytest. The October 26 PR #93 audit instead reported 93 Python advisories in
  18 packages and 26 vulnerable NPM packages.
- PR #93 frontend tests/build passed until Playwright browser installation:
  `ubuntu-latest` selected Ubuntu 26.04, unsupported by the locked Playwright
  1.60.0. The browser job now uses Ubuntu 24.04.
- Run `9d38570b-a558-4338-9f1d-fb2a2717fd0e` executed all L1–L10 stages once.
  Standard mode disabled refinement; L9 finalized 39 insufficient claims with
  zero governed sources/citations. The provider reported `STOP`, 1,606 output
  tokens. The chat's empty metrics view incorrectly implied no validation ran.

## Implemented source changes

- Refresh exact Python pins and the universal hash lock. Remove LlamaIndex and
  its NLTK dependency; refresh existing NPM dependencies and Electron 43.8.3.
  The accessibility runner uses Playwright and the already-used `axe-core`
  package directly, so the unused CLI/ChromeDriver dependency chain is removed.
- Remove the now-unnecessary historical pip-audit ignore list from both jobs.
- Use a deterministic local sentence chunker. Its units are words/punctuation,
  with long words split into bounded pieces; they are not provider-token counts.
  The configured chunk size now applies consistently on every installation.
  No optional-import fallback changes behavior silently.
- Record the chunker/config revision in ingestion metadata and chunk identity.
  Re-ingesting identical source bytes under a new chunker queues old chunks for
  deletion and creates distinct replacement IDs. Repeating the same revision
  deduplicates. Supersession begins only after parsing and content checks succeed.
  Existing stored knowledge is not automatically rewritten by this source change.
- PyJWT call-site audit found Flask-JWT-Extended uses fresh option dictionaries
  for unverified inspection and verified decoding. The new PyJWT 2.15.1 lock
  passes the actual audit; regression tests also verify option preservation,
  expired-token rejection, and wrong-audience rejection. No authentication
  monkey patch or advisory suppression is needed.
- Show the Standard refinement limitation beside the answer, make Enhanced's
  conditional budget visible before sending, and direct users to saved trace
  details when chat metrics are absent. A mechanism question such as “how does
  cold fusion work” requests comprehensive breadth within the same call budget.

## Verification checkpoint

- Clean Windows CPython 3.11 environment installed from the hash lock.
- Focused Python regressions: **50 passed**, zero setup/collection errors.
- Fresh Python audit: **zero known vulnerabilities**, no ignore arguments.
- Fresh NPM audit/install: **zero vulnerabilities**.
- Lockfile governance, frontend type checking, frontend production build, and
  Electron TypeScript compilation passed.
- Frontend: **506 tests passed**; coverage statements 89.65%, branches 80.36%,
  functions 86.68%, lines 91.49%. Frontend lint has zero warnings.
- Initial full Windows run: 3,370 passed, 19 skipped, three failures, zero
  setup/collection errors. A raw-file SHA differed under Windows CRLF checkout;
  the generator now normalizes line endings before hashing. Two artifact tests
  exceeded Windows path length in the managed worktree; fixtures now own a short
  temporary root and explicitly shut down the compatibility runtime before
  cleanup. All 20 affected authority/simulation tests pass after correction.
- Final full Windows coverage suite: **3,373 passed, 19 skipped**, zero test,
  setup, or collection errors. Coverage passes backend **80.45%**,
  backend/security **80.67%**, and core **81.08%**. The suite reported 35 existing
  deprecation warnings. A repeated post-pytest cleanup log was corrected with an
  idempotency guard; the 61-test cleanup group passes without a logging/lock
  exception after that correction.
- [PR #94](https://github.com/kherrera6219/DataLogicEngine/pull/94) has passing
  GitHub Python/NPM security scans, code scans, secret scan, SBOM, governance,
  lint, backend tests, and frontend build at its first repair checkpoint. Packaging and the
  final pushed head must finish before merge. No installed acceptance is claimed.
- The first repair Linux backend job `121691827783` passes **3,366 tests,
  26 skipped**, including all three tests in the previously failing refinement
  workflow module. That historical failure does not reproduce under the
  refreshed source/lock; its original individual cause was not isolated.
- The 4.4.6 bump also required updating the version/upgrade-lineage assertions
  and dependency-count documentation verifier. After those updates and complete
  fixture-owned runtime shutdown, the affected 61-test group passes with zero
  setup errors. The final full run used the same `FLASK_ENV=testing` profile as CI.
- The first 4.4.6 installer attempt failed because `public/icon.png` contains
  JPEG bytes. Packaging now selects the existing valid 512-pixel PNG icon;
  this does not alter the image asset. The second clean-source rebuild passed.
- Full Ruff has the previously recorded **58 errors** in unchanged files;
  full format check reports **862 files** requiring formatting. Changed Python
  code passes scoped Ruff. Repository-wide mypy reports **972 errors** and is
  not treated as a passing gate by this repair.

The former test that patched LlamaIndex availability asserted a removed private
fallback branch. It is replaced with a sentence-boundary behavior assertion;
existing basic-splitter tests remain. Frontend navigation tests now use a valid
browser URL and assert the destination pathname after absolute navigation;
the redirect/error-recovery controls remain exercised.

Production/public release remains **NO-GO** pending the existing release program,
clean-source CI, rebuilt-installed acceptance, signing, and provider/lifecycle
evidence. The dashboard findings and session-scoped Live Trace reset remain
separate open work; this owner-approved chat scope does not claim to fix them.

## Rebuilt engineering artifact

- Clean build source: `0f0d51d1fea7aadfb1f739c98c1b1565063b880c`.
- Installer: `DataLogicEngine Setup 4.4.6.exe`, **350,186,546 bytes**.
- SHA-256: `303148bf4f559937d1a49a8cd98c353e42d36e6c2f7b96bdd13a3a5d4f9b763e`.
- `npm run electron:dist`: pass. Packaged product authority declares 4.4.6.
- Packaging resources and NSIS governance: pass. Payload verification: pass,
  **5,029 backend files**, zero issues. Generated records:
  `reports/packaging_resources_report.json`, `reports/nsis_governance_report.json`,
  and `reports/release-payload-4.4.6.json`.
- Signature: **NotSigned**. Local portable launch, installed acceptance, and live
  provider acceptance: **not run**. Existing installed application/profile was
  not used for a packaging smoke test. CI's isolated Windows runner retains its
  own portable-launch evidence; that does not establish installed acceptance.
- Source checkpoint `0f0d51d1` passes GitHub security scans, backend tests,
  frontend build/browser checks, governance, lint, and Windows packaging/portable
  smoke (CI run `40358828347`, Security run `40358828401`). Docker verification
  also passes at that source checkpoint.
- Documentation checkpoint `f636573e` passes security, frontend, governance,
  lint, and Windows packaging/portable smoke, but its Linux backend suite
  reported one cancellation-test failure (3,365 passed, 26 skipped). The same
  cancellation module passes locally (21 tests), including after full test
  collection; the cause of the intermittent Linux failure remains unproven.
  A GitHub rerun and final-head checks are required; no assertion was weakened.
- Independent cleanup diagnosis found that pytest loaded `tests/conftest.py`
  twice as `conftest` and `tests.conftest`, creating two application runtimes and
  an extra late shutdown handler. The test-only change in `8046c5f9` aliases
  both names to the same module. A full-collection diagnostic confirms one
  object and completed cleanup; 36 focused tests pass. The fresh full Windows
  coverage suite also passes: **3,373 passed, 19 skipped**, zero test/setup/
  collection errors; backend **80.45%**, backend/security **80.67%**, and core
  **81.07%**. Final GitHub checks are pending for that change. The duplicate fixture is
  not claimed as the established cause of the cancellation assertion failure.
- A rerun of the `f636573e` Linux job failed two different tests (3,364 passed,
  26 skipped). In the one-second timeout test, the L5 plan required an estimated
  750 ms with 599 ms remaining, so the plan was rejected before the provider
  began. A privacy-response test independently returned an internal failure;
  the evidence does not establish that it shared the same cause. Both results
  remain negative evidence; an owner decision is pending on correcting timing
  assumptions without removing the security or deadline controls.
