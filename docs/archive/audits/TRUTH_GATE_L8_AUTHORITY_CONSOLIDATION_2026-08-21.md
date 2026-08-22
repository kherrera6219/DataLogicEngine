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

## Commits (2026-08-21 / 2026-08-22)

| SHA | Summary |
|---|---|
| `d80e59b` | Mark TrustValidationGateway non-production; product L8 is governed ten_layers.l8 |
| `1947ab4` | Add fail-closed L8 model screening and OPA controls for product path |
| `def93283` | Promote fail-closed model screening and OPA into product L8 (ten_layers) — **introduced PLACEHOLDER corruption** |
| `c7a99834` | **Restore** `ten_layers.py` from pre-corruption content and wire screening/OPA into `l8` after the KA plan |

## Defect status — CLOSED

`backend/governed_execution/ten_layers.py` was temporarily reduced to the literal string `PLACEHOLDER` by commit `def93283`.

**Restored in commit `c7a99834` (2026-08-22):**

- Full L1–L10 stage executors restored from the last good pre-corruption content (SHA `1947ab46` / content `2a616536…`).
- Product L8 now imports and runs:
  - `evaluate_model_screening` on the candidate text (fail-closed)
  - `evaluate_opa_policy` with domain threshold from `risk_domain_threshold`
  - Results folded into `ok`, decision flags (`model_screening_block`, `opa_policy_block`), and the decision payload (`model_screening`, `opa_policy`, `risk_domain`, `minimum_confidence`, `measured_confidence`)
- File size restored to a full module (~63 KB); no longer a placeholder.

Do not treat any intermediate HEAD between `def93283` and `c7a99834` as a working L8 implementation. Current main is the restored + secured path.

## Product invariants preserved

- Single product path: gateway → GovernedExecutionOrchestrator → L1–L10 (including L8)
- Fail-closed on screening / OPA / evaluation errors
- Registry authority and KA plan ownership unchanged
- No second production L8 entrypoint

## Related documents

- `HANDOFF.md` — current checkpoint
- `TODO.md` — open production work
- `CHANGELOG.md` → `[Unreleased]`
- `docs/archive/audits/LEGACY_REFINEMENT_WORKFLOW_12STEP_REMOVAL_2026-08-21.md` (related cleanup note)
