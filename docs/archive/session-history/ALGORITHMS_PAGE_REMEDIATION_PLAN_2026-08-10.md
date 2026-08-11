# Algorithms Page — Remediation Plan

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
| Document ID | DLE-PLAN-007 |
| Title | Algorithm Registry page remediation and relocation |
| Document version | v1.0.0 |
| Product version | 4.3.0 |
| Status | Complete; AL-1 through AL-10 passed, archived 2026-08-11 |
| Date | 2026-08-10 |
| Baseline commit | `40e2592f` (main) |
| Source review | Conversation review of `frontend/app/algorithms/page.tsx` (622 lines) |
| Owner | Audit session |
| Approver | Kevin Herrera, Product Owner |

## 1. Verdict

**Keep the page. Move it. Fix six code defects. Raise one manifest data gap.**

The page is the visible proof surface for CP19-J/CP19-K — it is how a human
verifies the "one owner, one selector path, receipted effects" claim without
reading the 242 KB qualification evidence set. It is not unneeded complexity.

It is **misplaced** complexity: `AppSidebar.tsx:166` puts it under *Knowledge*,
ungated, next to Knowledge Base and Knowledge Graph. Every other surface that
can cause an effect sits under *System* behind `isAdmin`.

## 2. Measured baseline

Ran `format_algorithm()` over all 213 live manifest entries.

| Card element | Populated | Root cause |
|---|---|---|
| `catalog_version` badge | **0 / 213** | **Code** — key mismatch |
| `notes` description fallback | 0 / 213 | Code — key never emitted |
| Description (`purpose`) | 146 / 213 | **Data** — 67 manifest entries have `purpose = None` |
| Category | 138 / 213 | **Data** — 75 entries have `categories = []` |
| `risk_class` | 114 / 213 | **Data** — 99 entries have `risk_classes = []` |
| `status` | 213 / 213 | Single value `Active` — carries no information |

The three data gaps are nested subsets: every entry missing a purpose is also
missing a category, and every entry missing a category is also missing a risk
class. Example: `KA-036` "Complexity Estimator" —
`purpose=None, categories=[], risk_classes=[]`, yet production-enabled and
`deterministic_heuristic`.

**This is a CP19-K observation worth recording separately.** The checkpoint
reports "213 qualified, zero incomplete," but 99 production-enabled capabilities
carry no declared risk class in their contract.

## 3. Design principle for this work

**Where metadata is absent, the UI must say so — not substitute a value that
looks like an answer.** The current fallback chain (`risk_class || status ||
'Unknown'`) makes 99 cards display `ACTIVE` in the risk slot. That is not a
missing badge; it is a misleading one.

No purpose, category, or risk class will be invented in this work. Backfill is a
separate, owner-approved task against the manifest generator.

## 4. Task table

| ID | Task | Primary file path | Exit gate | Target |
|---|---|---|---|---|
| **AL-1** | Fix `catalog_version` key mismatch: metadata emits `manifest_version`, formatter reads `version` | `backend/routes/ka_routes.py` (`format_algorithm`) | Badge populates for 213/213; backend test asserts non-null | DESKTOP+VM |
| **AL-2** | Split the conflated risk badge. Render risk and status as separate badges; when `risk_class` is absent show an explicit "Risk not declared" marker, not `Active` | `frontend/app/algorithms/page.tsx` | No card shows `Active` in the risk position; 99 show the explicit undeclared marker | DESKTOP |
| **AL-3** | Mark non-executable entries. `KA-033` (Reserved, `placeholder_not_production_enabled`) and `KA-Master` (`experimental_method`, self-selection disabled) currently render an enabled "Plan and run" button that always errors | `frontend/app/algorithms/page.tsx` | Button disabled with a stated reason for exactly those 2; enabled for 211 | DESKTOP |
| **AL-4** | Replace `Uncategorized` with an explicit undeclared marker consistent with AL-2 | `frontend/app/algorithms/page.tsx` | 75 cards state category is undeclared rather than asserting a category | DESKTOP |
| **AL-5** | Surface the silent recent-runs failure. `loadRegistry` swallows a rejected `algorithms.runs(10)` with no message | `frontend/app/algorithms/page.tsx` | A failed run-ledger load renders a visible non-blocking warning | DESKTOP |
| **AL-6** | Bound the poll loop. `useEffect` → `setTimeout(1000)` → `refreshRun` re-fires indefinitely for a stuck `running` run | `frontend/app/algorithms/page.tsx` | Poll count capped with backoff; on cap, state message plus manual Refresh remains available | DESKTOP |
| **AL-7** | Relocate nav entry: *Knowledge* → *System*, `isAdmin`-gated, alongside Diagnostics and Compliance | `frontend/components/layout/AppSidebar.tsx:166` | Entry renders only for `isAdmin`; sidebar test updated | DESKTOP |
| **AL-8** | Remove or repair the inert `?status=` filter — the attribute has one distinct value across all 213 | `backend/routes/ka_routes.py` (`list_algorithms`) | Filter removed, or repointed at `classification` / `production_enabled` | DESKTOP+VM |
| **AL-9** | Strengthen `page.test.tsx`. Current fixtures supply `catalog_version: 'ka-catalog.v1'` — a value production never produces — which is why the AL-1 defect survived | `frontend/app/algorithms/page.test.tsx` | Fixtures mirror real formatter output, including absent purpose/category/risk | DESKTOP |
| **AL-10** | Backfill 67 purposes, 75 categories, 99 risk classes, 99 subsystem bindings, and 85 layer/stage scopes in the generated manifest | `scripts/build_ka_runtime_manifest.py`, `backend/knowledge_algorithms/ka_manifest.v1.generated.json` | **Complete:** all 213 carry purpose, category, risk class, subsystem, and layer/stage scope | DESKTOP+VM |

## 5. Relocation rationale (AL-7)

The dividing line is **effect capability, not sensitivity**.

- *Trace & Review* (Trace Explorer, Truth Engine, Analytics) is read-only.
- *System* (Diagnostics, Compliance) is operator-facing.

The Algorithms page can create a durable plan, confirm it, and execute it —
producing effect proposals bound to authoritative receipts. That is an operator
capability. It belongs in *System*.

Note that in this single-owner desktop product `isAdmin` resolves true for the
owner (`user?.role === 'owner'`), so the gate changes nothing for Kevin in
practice. Its value is semantic: it marks the surface correctly and matches the
precedent already set by Diagnostics and Compliance.

## 6. Sequencing and risk

Execute **AL-9 first** (tests that mirror reality), then AL-1 through AL-8.
At this checkpoint AL-10 was gated on owner approval and was not bundled. The
owner later approved execution; Section 6b records its completion.

**Timing hazard.** At the time of writing, the working tree carries 19 modified
files including CP19-L installed-candidate evidence
(`cp19-l-installer-integrity.json`, `cp19-l-release-payload.json`) and an
in-flight test rename under `tests/knowledge_algorithms/`. Editing
`backend/routes/ka_routes.py` changes backend source after a candidate payload
was hashed.

The target files themselves (`ka_routes.py`, `page.tsx`, `AppSidebar.tsx`,
`page.test.tsx`) are clean, so there is no merge hazard — but the **commit**
should wait until the CP19-L/CP19-M work in the tree is resolved, so the
candidate hash and these UI changes are not entangled in one ambiguous diff.

## 6a. Completion record — 2026-08-10

AL-1 through AL-9 are implemented and validated against baseline `40e2592f`.
Six files changed: `backend/routes/ka_routes.py`,
`frontend/app/algorithms/page.tsx`, `frontend/app/algorithms/page.test.tsx`,
`frontend/components/layout/AppSidebar.tsx`,
`frontend/components/layout/AppSidebar.test.tsx`, and
`tests/integration_routes/test_ka_route_auth_boundaries.py`.

| Gate | Result |
|---|---|
| `page.test.tsx` + `AppSidebar.test.tsx` | 11/11 passed |
| `tests/integration_routes/test_ka_route_auth_boundaries.py` | 24/24 passed |
| Full backend source suite | 3,101 passed, 19 skipped |
| Full frontend suite | 435/435 passed |
| Frontend typecheck / lint | Clean |

**Defect found and fixed during implementation.** The first AL-1b attempt called
`_get_controller().manifest.manifest_version` directly and returned HTTP 500
against a controller test double lacking `manifest`, breaking four route tests.
Replaced with a `_manifest_version()` helper using `getattr` fallbacks: a
display-only catalog version must never fail the list route. The frontend suite
stayed green throughout, so only the backend run exposed it.

The concurrent generated-authority drift was resolved after the source changes
stabilized. The capability inventory was regenerated first, followed by the
runtime manifest and integration authority; both runtime-authority suites now
pass and the complete backend source suite is green.

**At the 2026-08-10 checkpoint, AL-10 was delivered as a proposal, not an
implementation.**
See `reports/production-readiness/2026/phase-19/al10-metadata-backfill-proposal.md`
and its 99-row CSV. Investigation widened the finding: all 99 affected
capabilities also declare **no subsystem**, and 84 declare **no layer**. No
manifest, catalog, or SDK artifact was modified.

## 6b. AL-10 completion record — 2026-08-11

The product owner approved proceeding through the two plans using the strongest
live authorities. Manifest `2026.08.11-al10.1` now derives missing descriptive
contract fields without name-based inference:

- 67 purposes come from parsed implementation module docstrings;
- 75 categories come from the approved CP19-A primary-owner boundary;
- 99 subsystem bindings come from that same one-owner authority;
- 85 missing layer/stage scopes are filled from the owner stage, including the
  reserved `KA-033` row that was outside the original 99-row Algorithms sample;
- 79 pure/advisory capabilities receive `Low`, 19 effect-proposal capabilities
  receive `High`, and the one TruthGate effect-proposal capability receives
  `Critical` risk.

The backend and both generated SDK catalogs, spec-facing 213-row export,
runtime-authority receipt, and CP19-K qualification matrix were regenerated.
The CP19-K evidence source now states that its original zero-incomplete result
covered semantic/execution proof, while AL-10 separately closes descriptive
metadata completeness. Focused manifest, integration-authority, CP19-K, and
spec-export tests pass. AL-10 changes no KA identity, implementation owner,
selector, dependency edge, effect boundary, or release gate.

## 7. Out of scope

- Any change to the governed execution path, selector, or plan/execute contract.
  This work touches presentation and one formatter key only.
- CP19-M installed acceptance rows and every retained release gate.
- Metadata not derivable from the approved implementation, ownership, effect,
  or stage authorities.

---

*End of plan.*
