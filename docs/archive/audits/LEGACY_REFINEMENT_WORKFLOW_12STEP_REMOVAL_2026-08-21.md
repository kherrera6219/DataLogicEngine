# Legacy RefinementWorkflow12Step Removal — 2026-08-21

## Decision

Remove the **legacy / demonstration** 12-step refinement workflow from the Quad
Persona mathematical framework so the product has **one** 12-step refinement
authority.

## Canonical authority (unchanged)

| Item | Value |
|------|--------|
| Class | `CanonicalRefinementWorkflow` |
| Module | `backend/governed_execution/refinement.py` |
| Registry | KA manifest `authority.refinement_workflow` |
| Owner | governed_execution_orchestrator |
| Entry condition | committed_l9_refine_decision |

This path already executes production-admitted KAs (KA-001, KA-002, KA-003,
KA-011, KA-025, reuse of committed L8/L9 results, etc.).

## What was removed

### Class

`RefinementWorkflow12Step` in
`core/persona/quad/mathematical_framework/refinement.py`

### Former behavior (stub / demo only)

- Sequential steps with fixed confidence returns (0.95–0.995)
- Step names: Tree of Thought, Algorithm of Thought, Gap Analysis, Knowledge
  Verification, NLP Enhancement, Data Consistency, Ethical Analysis, Bias Audit,
  Security Check, Logic Verification, Compliance Check, Final Optimization
- Geometric-mean confidence and 0.95 threshold
- **No** live KA calls; placeholders only
- Module flags: `PRODUCTION_ENTRYPOINT = False`,
  `WORKFLOW_DISPOSITION = "quad_mathematical_demonstration_reference"`

### Why safe to remove

1. Never imported by `backend/governed_execution/orchestrator.py`
2. CP19-G explicitly treated it as a non-product entrypoint
3. Only consumers were:
   - `QuadPersonaMathematicalSystem.process_full` (math demo path)
   - Phase 4b/5 import and correctness tests
4. Real KA implementations (KA-001, KA-002, KA-003, …) remain available via the
   canonical controller for the **governed** workflow

## What was retained

- `DeepRecursiveLearning` in the same module (math helper)
- Module import path `core.persona.quad.mathematical_framework.refinement`
- Flags:
  - `PRODUCTION_ENTRYPOINT = False`
  - `WORKFLOW_DISPOSITION = "removed_legacy_demonstration_reference"`
  (still ends with `reference` for CP19-G proofs)

## Code changes

| Path | Change |
|------|--------|
| `core/persona/quad/mathematical_framework/refinement.py` | Removed `RefinementWorkflow12Step`; kept DRL + flags |
| `core/persona/quad/mathematical_framework/integration.py` | Stopped calling 12-step workflow; points to canonical authority |
| `core/persona/quad/mathematical_framework/__init__.py` | Dropped export of `RefinementWorkflow12Step` |
| `tests/persona/quad/test_phase4b_import_compatibility.py` | Removed export assertions for removed class |
| `tests/persona/quad/test_phase5_correctness.py` | Replaced threshold stub test with non-entrypoint / removal proof |

## How to restore (if ever needed)

1. Recover `RefinementWorkflow12Step` from git history before this removal
   commit (search log for `RefinementWorkflow12Step` or this doc title).
2. Re-export from `mathematical_framework/__init__.py`.
3. Re-wire `QuadPersonaMathematicalSystem.process_full` only if a **demo**
   path is required — do **not** register it as a production entrypoint.
4. Prefer extending `CanonicalRefinementWorkflow` / the KA registry for any
   real product behavior.

## Related systems not touched

Other historical refinement modules may still exist as non-product variants
(e.g. truth_engine / simulation orchestrators). CP19-G continues to assert they
are not product entrypoints and are not wired into the governed orchestrator.
This change only removes the Quad math **12-step demo class**.
