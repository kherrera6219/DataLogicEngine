# AL-10 — KA Metadata Backfill Proposal

| Field | Value |
|---|---|
| Document ID | DLE-PROP-001 |
| Title | Contract metadata backfill proposal for 99 KA capabilities |
| Document version | v1.0.0 |
| Product version | 4.3.0 |
| Status | **approved and implemented 2026-08-11** |
| Date | 2026-08-10 |
| Manifest reviewed | `2026.08.08-cp19k.24` (213 capabilities) |
| Data artifact | `al10-metadata-backfill-proposal.csv` (99 rows) |
| Source plan | `docs/archive/session-history/ALGORITHMS_PAGE_REMEDIATION_PLAN_2026-08-10.md` (AL-10) |
| Owner | Audit session |
| Approver | Kevin Herrera, Product Owner |

## 1. What this was, and how it closed

This proposal assembled **evidence already present in the repository** for the
99 capabilities with incomplete contract metadata. It proposes derivation
**rules**, not 99 individual invented values, so that approval is a small number
of policy decisions rather than a line-by-line guessing exercise.

The product owner subsequently authorized proceeding through the plan. The
implementation uses these evidence sources directly and records the derivation
policy in manifest authority; the original CSV remains the pre-approval review
artifact and still carries `status = PROPOSED_REQUIRES_OWNER_APPROVAL`.

## 2. The gap, measured

| Missing fields | Capabilities |
|---|---|
| purpose + category + risk_class | 67 |
| category + risk_class | 8 |
| risk_class only | 24 |
| **Total affected** | **99** |

**98 of the 99 are production-enabled.**

The gap is wider than the three fields the Algorithms page exposed:

| Additional contract field | Missing across the 99 |
|---|---|
| `subsystems` | **99 / 99** |
| `layers` | 84 / 99 |

Every one of these capabilities declares no owning subsystem in its contract,
and 84 declare no layer binding.

## 3. Bearing on CP19-K

CP19-K reports **213 qualified, zero incomplete**. That statement is defensible
under whatever criteria the qualification matrix applied, and this proposal does
not dispute the checkpoint.

It does record a tension worth an explicit disposition: **98 production-enabled
capabilities carry no declared risk class, no declared subsystem, and in 84
cases no declared layer.** If the qualification criteria intentionally excluded
contract descriptive completeness, that exclusion should be stated in the
checkpoint record so the "zero incomplete" claim is not read more broadly than
intended.

This is a documentation-of-scope question, not an allegation that the
integration work is wrong.

## 4. Proposed rules

### R1 — Risk class from declared effect class *(mechanical, 79 of 99)*

`effect_class` is already declared for all 99 and is objective.

| `effect_class` | Count | Proposed risk class | Confidence |
|---|---|---|---|
| `pure_or_advisory_review_required` | 79 | `Low` | Mechanical — the capability applies no effect |
| `effect_oriented_review_required` | 20 | **OWNER_DECISION** | Effect-capable; risk is a governance judgment |

The 20 effect-oriented rows are left blank deliberately. Assigning a risk band
to a capability that can propose an effect is a governance claim, and I will not
make it on your behalf.

### R2 — Purpose from the implementation module docstring *(79 of 99)*

The authoritative description of what a KA does is the live code. Each row's
`candidate_purpose` is the first line of the docstring of its declared
`implementation_source`, extracted by AST parse — not paraphrased.

| Evidence quality | Count | Disposition |
|---|---|---|
| Substantive module docstring | 79 | Reviewable candidate |
| Docstring only restates ID and name | 20 | **Unusable** — flagged `name_echo_unusable` |

Example of a usable candidate — `KA-036` *Complexity Estimator*:
"bounded complexity estimation from supplied request signals."

Example of an unusable one — `KA-037` *Resource Allocator*: the docstring reads
`KA-037: Resource Allocator`, which adds nothing. Those 20 need a human to write
a real purpose, or need the docstring fixed first at source.

### R3 — Category: no mechanical rule offered

A controlled vocabulary of 24 values is already in use across the 138 complete
entries: Analysis, Capability, Compliance, Context, Control, Coordination,
Creativity, Ethics, General, Governance, Learning, Lifecycle, Memory, Meta,
Optimization, Persona, QA, Reasoning, Reserved, Routing, Safety, Synthesis,
Truth, UX.

Category could not be derived from declared data, because the fields that would
normally imply it — `subsystems` and `layers` — are themselves absent for these
rows (Section 2). Deriving a category from the capability *name* would be
inference dressed as evidence, so all 75 are marked `OWNER_DECISION`.

**Recommendation:** backfill `subsystems` first. Once each capability declares
an owning subsystem, category follows from it consistently rather than being
assigned 75 separate times.

## 5. Recommended sequence

1. **Decide the CP19-K scope statement** (Section 3). This is a records
   question and blocks nothing else.
2. **Approve or reject R1.** If approved, 79 risk classes land mechanically and
   the remaining 20 become a bounded review list.
3. **Approve R2 for the 79 usable docstrings.** Reject the 20 echoes; fix those
   docstrings at source, then re-run the extractor rather than hand-writing
   manifest prose that will drift from the code.
4. **Backfill `subsystems` for all 99** — the highest-leverage field, since it
   unblocks category and restores the ownership claim CP19-A depends on.
5. **Only then assign categories**, derived from the subsystem.
6. Regenerate via `scripts/build_ka_runtime_manifest.py`; confirm
   `test_phase18_runtime_manifest` and `test_phase18_runtime_authority` pass.

## 6. Completion record

- Manifest `2026.08.11-al10.2` fills 67 purposes, 75 categories, 99 risk
  classes, 99 subsystem bindings, and 85 layer/stage scopes. The extra layer row
  is reserved `KA-033`, which was not one of the original 99 risk-gap rows.
- Risk derivation assigns `Low` to 79 pure/advisory rows, `High` to 19
  effect-proposal rows, and `Critical` to the one TruthGate effect-proposal row.
- The backend, Python SDK, TypeScript SDK, spec export, runtime-authority receipt,
  and CP19-K qualification matrix were regenerated in lockstep.
- Focused runtime-manifest, integration-authority, CP19-K matrix, and spec-export
  tests pass. All 213 entries now carry purpose, category, risk, subsystem, and
  layer/stage metadata.
- This is a data-quality and governance-completeness change. It does not change
  identity, execution behavior, selector admission, effect application, or the
  standing production/public release **NO-GO**.

---

*End of proposal and completion record.*
