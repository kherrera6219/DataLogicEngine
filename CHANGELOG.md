# Changelog

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ROOT-002 |
| Title | Product change log |
| Document version | v1.9.1 |
| Product version | 4.4.2 |
| Status | active |
| Audience | Users, operators, integrators, maintainers, and release reviewers |
| Owner | Release Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Merged source history, release manifests, and validated phase evidence |
| Confidentiality | Public |
| Last reviewed | 2026-08-21 |
| Next-review trigger | Any user-visible, operational, security, migration, or compatibility change |
| Requirements and evidence | Commit history and `reports/production-readiness/2026/` |

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **TruthGate Layer 8 single-path authority (2026-08-21):** Resolved dual L8 surfaces by selecting the more secure fail-closed path. Absorbed model screening, OPA/Rego policy evaluation, and risk-domain thresholds from the legacy `TrustValidationGateway` into the product L8 authority (`GovernedTenLayerStages.l8` + new `backend/governed_execution/l8_security_controls.py`). Marked `TrustValidationGateway` non-production (`PRODUCTION_ENTRYPOINT=False`, `WORKFLOW_DISPOSITION="legacy_truthcore_compatibility_reference_only"`). Preserves the single KA-owned path (KA-010/024/027/1074 + admitted dependencies), registry authority, and governed-orchestrator integration. Classic TruthGateGateway remains a prefilter shell only.

### Known issue
- **`ten_layers.py` placeholder corruption:** Commit `def93283` ("Promote fail-closed model screening and OPA into product L8") left `backend/governed_execution/ten_layers.py` containing only the string `PLACEHOLDER`. Immediate next engineering action is to restore the prior implementation (e.g. from SHA before the promotion or a local patched copy that already wired screening/OPA) and re-apply the L8 security block. Do not treat the current HEAD as a working L8 implementation until that restore lands.

## [4.4.2] - 2026-08-20

### Fixed
- **Packaged Layer 9/10 dependency injection:** replaced Python source-text
  inspection with deterministic schema and callable-signature checks when the
  manifest injects dependency results. PyInstaller builds no longer omit the
  trust and escalation results required by final containment merely because
  readable `.py` source is absent.
- **Packaged governed-chat regression:** added behavior coverage that disables
  source inspection, executes the real mapping-based Layer 9 dependency chain,
  and proves a no-evidence/not-measured governed chat still reaches the Layer
  10 release decision after one provider response. All five mapping-based
  dependency consumers are covered. The focused runtime/version set passes 49
  tests, and the full Windows source suite passes 3,297 with 18 skipped and zero
  failures or setup errors.
- **Exact-source 4.4.2 engineering rebuild:** source commit
  `103f52e5f9b51f937ac2da8adc17523ec98affdb` produced the unsigned
  358,849,388-byte `DataLogicEngine Setup 4.4.2.exe` with SHA-256
  `ece59ad3e1e36afabd9856b29839254c626638cbcb2d4f00d7efe51c24031f8a`.
  Installer integrity, NSIS governance, the 6,096-file release payload, and
  strict package-owned portable `/ready` pass with zero issues; readiness
  completed in 38,848 ms with verified process ownership and clean shutdown.
  Fresh-installed Google chat, OpenAI quota, signing, and retained CP19-M
  acceptance remain open.

### Changed
- Advanced the substantial runtime-correction batch to product 4.4.2 and
  Windows file version 4.4.2.0. Retained 4.4.1 as an allowed upgrade source;
  public API and governed contract versions are unchanged.

## [4.4.1] - 2026-08-20

### Fixed
- **Layer 4 desktop-chat persistence:** retained concurrent deterministic persona
  construction while serializing required DSQP deliverable saves on the
  originating request thread. This removes the shared Flask-SQLAlchemy session
  race that failed all four persona axes before Google could be called.
- **FROST snapshot delivery:** classified ordinary reasoning checkpoints as
  `frost_snapshot` objects instead of database-authoritative simulation
  artifacts, allowing the durable materialization worker to deliver them
  without a nonexistent simulation row.
- **Exact-source 4.4.1 engineering rebuild:** source commit
  `ab7b1b181d65d0fc10c1a88706258710b2b34807` produced the unsigned
  358,849,159-byte `DataLogicEngine Setup 4.4.1.exe` with SHA-256
  `a92b836145bb23eccc2f89c33a005a6ec66683fae28e13824cd988ec18b05156`.
  Installer integrity, NSIS governance, the 6,096-file release payload, and
  strict package-owned portable `/ready` pass with zero issues; readiness
  completed in 28,447 ms with verified process ownership and clean shutdown.
  The focused runtime set passes 89 tests and the full Windows source suite
  passes 3,295 with 18 skipped and zero failures or setup errors. Fresh
  installed Google chat, OpenAI quota, signing, and retained CP19-M acceptance
  remain open.
- **Desktop chat compatibility aliases:** corrected the gateway virtual-model
  resolver so desktop request modes such as `chat`, `trace`, `explain`, and
  `quad` are normalized through the canonical governed-mode contract before
  policy comparison. The installed field failure had a healthy Google provider
  test but returned HTTP 422 for `/api/v1/gateway/chat` before orchestration,
  session creation, or validation telemetry. Desktop-shaped route and contract
  regressions now pass. Clean source commit
  `e99119e222227eaf98940a9e34f0f587550ce2ca` produced the unsigned
  358,849,321-byte replacement installer with SHA-256
  `78800b84a670f6c5828894a26b6fc76d664fdf3f9e98876cb7d6fa11b15f49e3`.
  Integrity, NSIS governance, the 6,095-file payload, required resources, and
  strict package-owned portable `/ready` pass in 25,138 ms with verified
  process ownership and clean shutdown. Fresh installed Google chat acceptance
  remains required; production/public release stays **NO-GO**.

### Changed
- **Exact-source 4.4.0 engineering rebuild:** source checkpoint
  `c765ba03257e58e69a4cd4b80f92390c71346801` produced the unsigned
  `DataLogicEngine Setup 4.4.0.exe` at 358,848,516 bytes and SHA-256
  `650034eeec76cbfc582ce81551f40d14e527aeea2707682bdf040d808062a591`.
  Installer integrity, NSIS governance, the 6,096-file release payload,
  required packaging resources, and package-owned `/ready` pass; readiness
  completed in 30,701 ms with verified process ownership and clean shutdown.
  OpenAI quota, signing, elevated installed lifecycle, accessibility, provider
  corpus/human review, recovery, independent review, pilot, and soak gates
  remain open, so production/public release stays **NO-GO**.
- **Trace refinement visibility and external spec publication:** the Trace
  Explorer now expands the existing persisted canonical refinement receipt into
  named 12-step governance detail without introducing another trace authority.
  The reviewed 213-row KA registry and axes 14-17 replacement were published to
  connected Google Drive and verified by byte count. Archive/de-rank of three
  stale external Docs remains blocked on file-scoped Google write access.
- **Provider acceptance evidence:** Google `gemini-3.7-flash` passes two bounded
  source-level calls. OpenAI `gpt-5.6-sol` reaches the live API with High
  reasoning but remains blocked by `quota_exhausted`, including a fresh bounded
  retry. No credential or response content is retained in the receipts.
- **Coverage-qualified replacement rebuild:** built the unsigned local 4.4.0
  engineering package at SHA-256
  `1da8b8d6a10b1ce72993448baf0c18d2eb41749f7aa7d76b43d4d085983be521`.
  Static package validation and package-owned portable readiness pass in
  30,790 ms. The
  retained PostgreSQL store advanced to Alembic `b2c3d4e5f6a7`, and the known
  saved Google/OpenAI rows migrated without exposing keys. That artifact is
  superseded by the exact-source engineering rebuild recorded above; signing,
  OpenAI live-provider, and installed acceptance remain open.
  The complete source checkpoint was committed to `main` as `5e8733b3`; the
  installer predates that commit and was not rebuilt from a clean checkout.
- **80% coverage qualification:** raised and independently gated Python
  `backend/` (80.30%), `backend/security/` (80.67%), and `core/` (80.89%), plus
  frontend statements (89.54%), branches (80.69%), functions (86.11%), and
  lines (91.36%). The clean runs pass 3,287 Python and 482 frontend tests, and
  CI now fails when any named scope or metric falls below 80.00%.
- **Clean-runner documentation validation:** replaced four local-only
  historical wildcard references that failed in fresh GitHub checkouts. Commit
  `1a631128` passes active-reference validation with zero errors/warnings and
  the documentation truth gate 10/10. Replacement Deploy run 32099906333 and
  CI/CD Pipeline run 32099906332 pass end to end, including coverage, Windows
  packaging smoke, and Docker image builds.
- **Cloud model defaults:** advanced the single-provider allowlist to OpenAI
  `gpt-5.6-sol` with explicit High reasoning and Google
  `gemini-3.7-flash`. Stored rows using only the two retired defaults migrate
  forward, settings no longer re-offer stale saved model IDs, and the bounded
  live connectivity check now reserves enough output for thinking models.
- **Retained 4.3.0 candidate upgrade:** the 4.4.0 runtime-lock authority now
  admits the prior 4.3.0 engineering identity into the managed migration path
  and advances the retained version only after migrations pass.
- **Portable packaging smoke:** release-review runs can require `/ready`, reject
  a pre-existing listener, and verify that the listener belongs to the exact
  launched package process tree. This prevents an Electron-only process from
  masking a crashed frozen backend.
- **Slow-audit remediation (2026-08-12 through 2026-08-15):** engineering
  hygiene, API surface uniqueness, cloud-BYOK generative locality,
  authority/honesty planes, CI structural guards, and SDK 0.7.0 polish. Phase 5
  decomposition remains partial/deferred; remaining work is carried by
  `docs/audits/DataLogicEngine_Consolidated_Update_Plan_2026-08-18.md`.
  Production release remains **NO-GO** (Phase 8 / signing deferred).
- **Governed layer contract correction:** supplemental L1–L10 metadata now
  derives its names from the live ten-layer authority; provider execution and
  trace persistence are no longer mislabeled as canonical L6/L9.
- **KA client/server manifest parity:** the TypeScript SDK compares the live
  server manifest version, 213-capability count, and generated JSON SHA-256;
  Python and TypeScript catalog generation/parity tests cover drift.
- **G-API hard-off default:** legacy `/api/*` blueprint mirrors are registered
  only when `DLE_LEGACY_API_PREFIXES` is true; product path is `/api/v1/*`.
- **Gateway admin namespace:** client keys/providers live under
  `/api/v1/admin/gateway/*` (ops admin remains `/api/v1/admin/*`).
- **Knowledge pillar levels:** frontend and API use
  `/api/v1/knowledge/pillar-levels` (avoids UKG sector/domain collisions).
- **Regulatory surface:** `/api/v1/regulatory` only; axis-7 compliance standards
  remain on `/api/v1/compliance/*`.
- **Generative locality (G-GEN=B0):** capabilities advertise
  `generative_locality=cloud_byok`; local generative defaults off.
- **DSQP (G-DSQP):** frozen 7-part persona contract (includes Traits and Related
  Roles labels) with dedicated contract module and tests.
- **CI hard guards:** orphan `.pyc` scan and route uniqueness verification run
  as fail-on-error steps; a11y sweep remains soft (`continue-on-error`).
- **Python SDK:** rebuild as `ukg_sdk` 0.7.0 with license notice.

### Added
- Memory authority documentation and `GET` memory-authority surface for the
  operator-visible working-memory system of record.
- Orphan bytecode scanner/purge scripts and unit guard
  (`scripts/scan_orphan_pyc.py`, `tests/unit/test_no_orphan_pyc.py`).
- Packaging resource verification script and Podman first-run recovery messaging.
- Supporting authority docs: `docs/MEMORY_AUTHORITY.md`,
  `docs/AUTH_SURFACE_MATRIX.md`, `docs/DMRF_TRUTH_BOUNDARY.md`,
  `docs/DATASET_EXPORT_HANDOFF.md`, `docs/CI_QUALITY_POLICY.md`,
  `docs/DESKTOP_CSP.md`.

### Removed
- Orphan connector residue for Jira/Salesforce (G-MCP-CONN=delete) and local
  model bytecode clusters under the B0 track.
- Misleading GraphiQL / dead Swagger registration when static assets are absent.

### Historical (still unreleased relative to last published notes)
- See prior CHANGELOG history for Phase 19, Phase 18, and earlier engineering
  checkpoints. Full historical body retained in repository history.

---

## Release Notes

Production/public release remains **NO-GO** until CP19-M and retained installed,
signed, provider, accessibility, recovery, pilot, and soak gates pass.
