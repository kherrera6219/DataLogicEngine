# TruthGate L8 Authority Consolidation — 2026-08-21

## Purpose

Document the resolution of dual Layer-8 surfaces in DataLogicEngine so the next session has a clear, authoritative record of what changed and what remains open.

## Decision

Between the two L8 implementations, the **more secure** path was selected and made canonical:

- **Canonical product L8:** `backend.governed_execution.ten_layers.GovernedTenLayerStages.l8`
  - Owned by the governed orchestrator
  - Driven by the truthgate KA plan (KA-010, KA-024, KA-027, KA-1074 + admitted dependencies)
  - Now also executes fail-closed model screening and OPA policy evaluation

- **Legacy / non-production:** `backend.truth_engine.truth_gate.trust_validation_gateway.TrustValidationGateway`
  - Marked `PRODUCTION_ENTRYPOINT = False`
  - `WORKFLOW_DISPOSITION = "legacy_truthcore_compatibility_reference_only"`
  - Retained only for TruthCore private historical workflow compatibility and unit tests
  - Must not be treated as a second product L8 authority on the governed chat path

Classic TruthGateGateway remains a prefilter shell only.

## What was absorbed into product L8

New module: `backend/governed_execution/l8_security_controls.py`

- `evaluate_model_screening(text, metadata=...)` — fail-closed on error
- `evaluate_opa_policy(...)` — fail-closed / deny on error
- `risk_domain_threshold(risk_domain)` — aligned with former TVG RISK_THRESHOLDS (0.95 standard; 0.995 healthcare/finance/legal/safety/high/critical)

These controls preserve the single KA-owned path, registry authority, and governed-orchestrator integration.

## Commits (2026-08-21)

| SHA | Summary |
|---|---|
| `d80e59b` | Mark TrustValidationGateway non-production; product L8 is governed ten_layers.l8 |
| `1947ab4` | Add fail-closed L8 model screening and OPA controls for product path |
| `def93283` | Promote fail-closed model screening and OPA into product L8 (ten_layers) — **introduced PLACEHOLDER corruption** |

## Current defect (must fix next)

`backend/governed_execution/ten_layers.py` currently contains only the literal string:

```
PLACEHOLDER
```

This is a regression introduced in the promotion commit. The intended patch (screening + OPA wiring after `ka_ok` into the L8 decision, recording `model_screening` / `opa_policy` in the decision payload) must be restored before any L8 or CP19-H re-validation is claimed.

**Immediate next action:** restore `ten_layers.py` from a pre-corruption SHA (or a local patched copy that already contains the screening/OPA block) and push the corrected file. Do not proceed with further TruthGate feature work until the restore is complete and focused tests pass.

## Product invariants preserved

- Single product path: gateway → GovernedExecutionOrchestrator → L1–L10 (including L8)
- Fail-closed on screening / OPA / evaluation errors
- Registry authority and KA plan ownership unchanged
- No second production L8 entrypoint

## Related documents

- `HANDOFF.md` — current checkpoint (update after restore)
- `TODO.md` — open restore item
- `CHANGELOG.md` → `[Unreleased]`
- `docs/archive/audits/LEGACY_REFINEMENT_WORKFLOW_12STEP_REMOVAL_2026-08-21.md` (related cleanup note)
