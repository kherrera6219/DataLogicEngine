# Codex Work Queue — Spec vs. App Findings Remediation

> **Codex handoff document.** This is a *supporting review input*, not a phase
> authority. `PRODUCTION_COMPLETION_PLAN_2026.md` remains the sole active
> execution plan, and nothing here changes any release gate or the standing
> production/public release **NO-GO**. Work items below are remediation of
> documentation and presentation drift found outside the CP19-M path.
>
> Companion documents:
> `docs/archive/session-history/ALGORITHMS_PAGE_REMEDIATION_PLAN_2026-08-10.md` (completed Algorithms page plan),
> `CODEX_WORK_QUEUE_2026-08-10.md` (full remediation queue),
> `docs/audits/UKG_Spec_vs_App_Findings_2026-08-10.md` (evidence),
> `reports/production-readiness/2026/phase-19/al10-metadata-backfill-proposal.md`
> (AL-10 proposal and completion record).

| Field | Value |
|---|---|
| Document ID | DLE-QUEUE-004 |
| Title | Codex verification and remediation queue |
| Document version | v1.0.0 |
| Product version | 4.4.0 |
| Status | validated — confirmed source/spec/hygiene batch implemented; owner decisions retained |
| Source finding report | `docs/audits/UKG_Spec_vs_App_Findings_2026-08-10.md` |
| Baseline commit | `40e2592f` |
| Date | 2026-08-10 |
| Owner | Audit session |
| Approver | Kevin Herrera, Product Owner |

## Rules for this queue

1. **Verify before you change.** Every item in Group V is verification-only.
   Run those first and record the result. If a V item contradicts the finding
   report, stop and report — do not proceed to the matching C item.
2. **Do not touch Group D.** Those require a product-owner decision. Codex may
   gather evidence for them but must not implement either branch.
3. This queue does **not** supersede `PRODUCTION_COMPLETION_PLAN_2026.md`. It is
   remediation of documentation/wiring drift found outside the CP19-M path.
   Release-gate status stays **NO-GO**; nothing here changes that.
4. Add the failing test before the fix, per standing phase rules.
5. Pre-commit runs ruff + frontend lint + frontend typecheck. Unused imports in
   utility scripts will fail the commit.
6. Use `.venv311` for all script execution. `.venv` (3.13, Windows Store)
   silently no-ops in subprocess contexts.

## Current validation and disposition

Validated against the current tree after the `d5ee1252` checkpoint. The source
report's `40e2592f` snapshot is useful evidence, but several conclusions were
already stale. Detailed evidence is in
`reports/production-readiness/2026/phase-19/supporting-plan-validation-2026-08-10.md`.

| Group | Current disposition |
|---|---|
| V | Complete. Manifest 213/211; defense supervisor has zero production importers; DSQP is seven-part, not five-part; 16 axis managers with Axis 5 explicitly unmanaged; 507 resolved Flask rules; trace UI is partial for named refinement/debate detail; three merged worktrees contain uncommitted files and were preserved. |
| D | Complete. D-1 needed no change because DSQP is seven-part. D-2 retired the disconnected fail-open supervisor. D-3 selects `docs/openapi.yaml` and live `/api/v1` routes; the old `/ukg/*` contract is archived roadmap history. |
| C | Complete or dispositioned. C-1, C-2, C-5, C-6, and C-8 are implemented. C-3/C-4 close through an explicit live crosswalk: the coordinate encodes `Qualifications & Skills`, while AxisSystem/manager display `Sector Expert` / `Sector Expert Persona`; the unverified external `Sector Expert Mapping` label was not adopted. C-7 is obsolete. |
| S | S-1, S-2, and S-3 generated under `docs/spec-exports/`, with a deterministic generator and freshness tests. S-3 uses the repository's canonical v3.2 copy and labels semantic matches as review candidates, not compatibility claims. |
| H | H-2 complete. H-1 is blocked because all three merged worktrees contain uncommitted files. H-3 remains an external project-knowledge action. H-4 passes for attributable repository work; the separately owned untracked whitepaper remains intentionally excluded. |

---

## Group V — Verification only (no code change)

Run all of these before any remediation. Record pass/fail per row.

| ID | Check | Command / file | Expected result | Target |
|---|---|---|---|---|
| V-1 | Full source suite still green | `.venv311\Scripts\python.exe -m pytest -q` | 3,070 passed / 18 skipped per `HANDOFF.md`; report actual | DESKTOP+VM |
| V-2 | KA manifest capability count | `backend/knowledge_algorithms/manifest.py` → `load_manifest()` | `capability_count == 213`, `manifest_version == 2026.08.08-cp19k.24`, 211 production-enabled | DESKTOP+VM |
| V-3 | `defense_supervisor` importers | grep production tree excluding `.claude/worktrees`, `frontend/dist*`, `dist/` | Zero non-test importers; confirm `prompt_injection_shield.py`, `ai_guardrail.py`, `llm_gateway/gateway.py` all return 0 | DESKTOP+VM |
| V-4 | DSQP profile component count | `backend/dsqp/dsqp_chain.py` lines 24–28 | Exactly 5 components; `trait`/`related_role`/`job_training` absent repo-wide | DESKTOP+VM |
| V-5 | Which control screens injection in the live path | `backend/llm_gateway/gateway.py`, TruthGate KA admission (KA-061 and CP19-K Batch 05 KAs) | Name the authoritative screen; state whether `defense_supervisor` is redundant or missing | DESKTOP+VM |
| V-6 | Axis manager registration | `core/axes/axis_system.py` | 16 registered managers; Axis 5 documented unmanaged at lines 132–136 | DESKTOP+VM |
| V-7 | Resolved Flask URL rules (not decorators) | `scripts/verify_route_manifest.py` | Report actual resolved rule count vs the 484 self-declared in `HANDOFF.md` | DESKTOP+VM |
| V-8 | Frontend trace component coverage | `frontend/**/*.tsx,ts` | Confirm whether Quad Persona debate and 12-step workflow render under alternative component names; `QuadPersona`/`12-Step`/`TenLayer` return zero | DESKTOP |
| V-9 | Stale git worktrees are abandoned | `.claude/worktrees/` | Three worktrees present; confirm none is an active branch before any cleanup | DESKTOP+VM |

---

## Group D — Product-owner decision required (Codex: gather evidence, do not implement)

| ID | Decision | Evidence to assemble | Why Codex must not decide |
|---|---|---|---|
| D-1 | **DSQP profile contract: 5-part or 7-part?** Either implement Traits + Related Roles, or amend the patent technical disclosure and `UKG_Canonical_Architecture_v1_0.docx` to the 5-part contract. | Current 5 components; the `overlapping_roles` key at `dsqp_chain.py:336` and whether it satisfies "Related Roles"; blast radius of adding two components across `core/system/persona_construction_service.py`, `ten_layers.py` L4/L5, `KA-012`/`KA-013`/`KA-030` | DSQP is the primary patent claim. Changing either the code or the disclosure has IP consequences. |
| D-2 | **`defense_supervisor`: wire or deprecate?** **DECIDED: deprecate/remove.** | V-3/V-5 proved zero production importers and complete live gateway/TruthGate screening | Wiring it would create a duplicate pre-provider disclosure and fail-open control surface. |
| D-3 | **Canonical API contract: converge or diverge formally?** **DECIDED:** current `/api/v1` contract is authoritative; `/ukg/*` is archived roadmap history. | Path-by-path mapping plus live route/contract tests | Prevents a non-callable roadmap contract from shipping or being represented as compatibility. |

---

## Group C — Code changes (proceed after matching V item passes)

| ID | Task | Primary file path | Exit gate | Target |
|---|---|---|---|---|
| C-1 | Rename `axis5_honeycomb.py` → `axis3_honeycomb.py`; update the alias comment block and all importers | `core/axes/axis5_honeycomb.py`, `core/axes/axis_system.py:34-38` | Module filename matches its canonical axis number; `axis_system.py` alias comment removed as no longer needed; full suite green | DESKTOP+VM |
| C-2 | Rename `axis3_domain.py` → `axis4_branch.py`; rename `DomainManager` → `BranchManager` at source rather than by import alias | `core/axes/axis3_domain.py`, `core/axes/axis_system.py:35,39` | No `as BranchManager` aliasing remains; full suite green | DESKTOP+VM |
| C-3 | **DISPOSITIONED.** Do not adopt unverified `Sector Expert Mapping`; document the live coordinate/persona label roles | `core/coordinate_system.py` (AXIS_NAMES entry 9) | Coordinate payload and persona display labels have an explicit, non-conflicting crosswalk | DESKTOP+VM |
| C-4 | **DONE.** Add a regression for the Axis 9 live crosswalk | `tests/unit/test_axis_alignment.py` | Coordinate `Qualifications & Skills`, AxisSystem `Sector Expert`, and manager `Sector Expert Persona` stay bound to Axis 9 | DESKTOP+VM |
| C-5 | Decide Axis 5: either build a dedicated Node System manager or add an explicit test asserting the documented "unmanaged" contract | `core/axes/axis_system.py:132-136` | If unmanaged is retained, a test asserts `resolve_multi_axis_context()` returns the documented unmanaged shape for Axis 5 — so it is a contract, not an omission | DESKTOP+VM |
| C-6 | **DONE.** Remove `defense_supervisor` | retired module/prompt/test; `backend/llm_gateway/gateway.py` | Module, prompt, dedicated test, stale gateway wording, and release-payload requirement removed; live controls remain | DESKTOP+VM |
| C-7 | **After D-1 only.** Implement Traits + Related Roles, or remove the 7-part claim | `backend/dsqp/dsqp_chain.py`, `core/system/persona_construction_service.py` | Component count in code matches the contract stated in the patent disclosure; test asserts the count | DESKTOP+VM |
| C-8 | **DONE.** Add a guard test for live security ownership and explicit retirement | `tests/security/test_security_module_wiring.py` | Retired supervisor/prompt cannot re-enter the payload; gateway governance must import both live input controls | DESKTOP+VM |

**Note on C-8.** This is the highest-value item in Group C. The
`defense_supervisor` gap survived multiple audit cycles specifically because a
passing unit test made it look live. A wiring assertion prevents that class of
defect from recurring across the whole security surface.

---

## Group S — Specification corrections (project knowledge, outside the repo)

These are not Codex-executable — the files live in the Claude project knowledge
base, not the repository. Codex should **generate the corrected artifacts** into
the repo so they can be uploaded.

| ID | Task | Primary file path | Exit gate | Target |
|---|---|---|---|---|
| S-1 | Regenerate a spec-facing KA registry from the live manifest, covering all 213 IDs with contract fields | source: `backend/knowledge_algorithms/ka_manifest.v1.generated.json`; generator: `scripts/build_ka_runtime_manifest.py`; planned output: docs/spec-exports/ka_registry_213.yaml | Output contains all 213 canonical IDs including `KA-Master`, `L9-KA-001..007`, `L10-KA-001..007`, the `KA-10xx/11xx` series, and the `KA-136..139` / `KA-161..184` bands | DESKTOP+VM |
| S-2 | Emit a corrected axes 14–17 block for `17_axis_coordinate_schema.yaml` | planned output: docs/spec-exports/17_axis_coordinate_schema_axes14-17.yaml | Axis 14 = Acquisition Lifecycle, 15 = Risk & Threat Context, 16 = Ethics/Trust/Criticality, 17 = FROST-Mode Selector, with encodings matching `core/coordinate_system.py` | DESKTOP+VM |
| S-3 | Emit a spec-vs-live API delta table | inputs: `docs/openapi.yaml`, canonical `ukg_canonical_api_v3_2_enhanced.yaml`; planned output: docs/spec-exports/api_delta.md | Every canonical `/ukg/*` path marked present / absent / renamed against the 67 live paths | DESKTOP+VM |

**S-1 is the highest-leverage item in the entire queue.** The project-knowledge
registry understates the app by 99 capabilities. Until it is regenerated, every
document, onboarding read, and licensing conversation sourced from it is wrong.

---

## Group H — Hygiene

| ID | Task | Primary file path | Exit gate | Target |
|---|---|---|---|---|
| H-1 | Confirm then remove the three stale git worktrees | `.claude/worktrees/{dazzling-antonelli, strange-margulis-cc69c5, stupefied-ramanujan-516b57}` | After V-9 confirms none is active: worktrees pruned. They currently triple every repo-wide grep result and have caused false audit readings | DESKTOP+VM |
| H-2 | Add worktree and build-output exclusions to the standard audit scan pattern | `scripts/` audit helpers | A repo-wide grep helper excludes `.claude/worktrees`, `frontend/dist*`, `dist/`, `build/`, `htmlcov*` by default | DESKTOP+VM |
| H-3 | Move the two superseded gap analyses out of retrievable project knowledge | `UKG_DataLogicEngine_Gap_Analysis_2026_05_23.docx`, `UKG_DataLogicEngine_Validated_Gap_Analysis_v2.docx` | Kevin removes/renames in project knowledge. Their headline claims (no DSQP, axes 14–17 not built, L10 empty, ~94 stub KAs) are now false and are being surfaced by semantic search as current | DESKTOP |
| H-4 | Clear the 5 uncommitted working-tree entries before starting | repo root | `git status --short` clean, so remediation diffs are attributable | DESKTOP+VM |

---

## Group AL — Algorithms page (COMPLETE)

Source plan: `docs/archive/session-history/ALGORITHMS_PAGE_REMEDIATION_PLAN_2026-08-10.md`.
Implemented and validated in session 2026-08-10 against baseline `40e2592f`.
Codex should **verify, not redo**, AL-1 through AL-9.

Files changed (5): `backend/routes/ka_routes.py`,
`frontend/app/algorithms/page.tsx`, `frontend/app/algorithms/page.test.tsx`,
`frontend/components/layout/AppSidebar.tsx`,
`frontend/components/layout/AppSidebar.test.tsx`.

| ID | Task | Status | Evidence |
|---|---|---|---|
| AL-1 | `catalog_version` key mismatch (`version` vs `manifest_version`) | **DONE** | 0/213 → 213/213 populated |
| AL-1b | Catalog version identical on all 213; moved to one header indicator, added `manifest_version` to list response behind a `getattr` helper | **DONE** | `_manifest_version()` cannot 500 the route |
| AL-2 | Split conflated risk badge (`risk_class \|\| status \|\| 'Unknown'`) | **DONE** | 99 cards no longer show `ACTIVE` as a risk tier |
| AL-3 | Disable planning for `KA-033` and `KA-Master` | **DONE** | 2 disabled, 211 enabled |
| AL-4 | `Uncategorized` → explicit undeclared marker | **DONE** | 75 cards |
| AL-5 | Surface silent run-ledger load failure | **DONE** | Warning card, `role="status"` |
| AL-6 | Bound the poll loop (60 attempts, linear backoff, operator notice) | **DONE** | — |
| AL-7 | Relocate nav: Knowledge (ungated) → System (`isAdmin`) | **DONE** | Both directions tested |
| AL-8 | Inert `?status=` filter repointed at `classification` | **DONE** | 1 value → 4 values |
| AL-9 | Test fixtures mirror real formatter output | **DONE** | 11/11 pass |
| **AL-10** | **Manifest metadata backfill (99 capabilities)** | **DONE** | Manifest `2026.08.11-al10.2`; all 213 descriptive contracts complete; KA-025 cold-start budget corrected |

Validation at completion: 11/11 frontend tests; 23/23
`tests/integration_routes/test_ka_route_auth_boundaries.py`; 1,122 passed
across `tests/knowledge_algorithms` + `tests/integration_routes`; frontend
typecheck and lint clean.

**Two pre-existing failures are not from this work.** `test_phase18_runtime_authority`
and `test_phase18_runtime_manifest` fail on "generated catalog stale". Verified
by stashing all five changed files and re-running: identical failures. Root
cause is a one-line `crosswalk_source_input_sha256` drift from an
already-modified `ka-capability-crosswalk.json`.

### AL-10 completion

Proposal: `reports/production-readiness/2026/phase-19/al10-metadata-backfill-proposal.md`
Data: `al10-metadata-backfill-proposal.csv` (99 rows).

| ID | Task | Exit gate | Target |
|---|---|---|---|
| AL-10a | Record a CP19-K scope statement covering contract descriptive completeness | **DONE** — source evidence distinguishes CP19-K semantic/execution scope from AL-10 descriptive completeness | DESKTOP+VM |
| AL-10b | Derive risk class from declared `effect_class` and primary owner | **DONE** — 79 `Low`, 19 `High`, one TruthGate `Critical` | DESKTOP+VM |
| AL-10c | Derive missing purposes from implementation module docstrings | **DONE** — parser consumes `Purpose:` and substantive module descriptions | DESKTOP+VM |
| AL-10d | Backfill `subsystems` from CP19-A primary owner | **DONE** — all 213 rows populated | DESKTOP+VM |
| AL-10e | Assign categories from primary-owner policy | **DONE** — all 213 rows populated without name inference | DESKTOP+VM |
| AL-10f | Regenerate catalogs, runtime authority, spec export, and qualification matrix | **DONE** — focused authority and staleness tests pass | DESKTOP+VM |

AL-10 preserved the sequencing rule: subsystem ownership was established before
category derivation, and capability names were not used as governance evidence.

### Prior environment and concurrent-activity notes — resolved

The normal frontend test command now explicitly supplies the supported test
environment and passes. The earlier generated-catalog drift was also repaired
before this validation batch. The main worktree is attributable except for the
separately owned untracked archive whitepaper, which this batch does not stage.

## Suggested execution order

1. Review/upload the three generated files under `docs/spec-exports/`.
2. Treat D-2/D-3 as complete; use only the live gateway/TruthGate controls and
   `docs/openapi.yaml` integration authority.
3. Preserve the tested Axis 9 coordinate/persona crosswalk unless a later ADR
   deliberately changes both schema roles.
4. Recover or deliberately discard the uncommitted worktree contents before
   H-1 cleanup; do not force-remove them.
5. Continue CP19-M under the root production plan.

## Out of scope for this queue

- CP19-M installed acceptance rows and every retained release gate.
- Installed/packaged artifact behavior — all findings here are source-level.
- Per-KA semantic depth. This review checked registration, ownership, and
  wiring, not reasoning quality.
- The 242 KB CP19-K qualification evidence set was not audited row-by-row.

---

*End of work queue.*
