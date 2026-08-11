# Phase 18 KA capability inventory summary

## Identity

| Field | Value |
|---|---|
| Schema | `dle.ka-capability-inventory.v1` |
| Source-input SHA-256 | `04a8646079f42e824306d7081f7bfe4cf31f141e0548b6953fc7449062c87b33` |
| Status | `cp18_a_inventory_verified` |

## Counts

| Measure | Count |
|---|---:|
| Live executable registry entries | 132 |
| Unregistered Layer-9 implementations | 0 |
| Original design rows | 114 |
| Expanded historical metadata rows | 277 |
| SDK registry rows | 114 |
| Proposed canonical distinct capabilities | 213 |
| Existing implementations requiring Phase 18 qualification | 213 |
| Missing implementations to build | 0 |
| Generated generic scaffolds retained as history, not capabilities | 64 |
| Classified identity conflicts | 62 |
| Unclassified source definitions | 0 |
| Semantic duplicate definitions collapsed to aliases | 1 |
| Similar-name candidate pairs reviewed as materially distinct | 11 |
| Unresolved semantic duplicate candidates | 0 |
| Exact canonical name collisions | 0 |
| Exact canonical purpose collisions | 0 |
| Exact canonical purpose/input/output contract collisions | 0 |
| Classified implementation surfaces | 213 |
| Unclassified implementation surfaces | 0 |
| Classified integration/API/SDK/UI surfaces | 142 |
| Unclassified integration/API/SDK/UI surfaces | 0 |
| Canonical capabilities with literal runtime execution call sites | 11 |
| Canonical capabilities with any test reference | 213 |
| Canonical capabilities with an individually named test function | 213 |

## Proposed identity policy

- Keep current executable IDs stable so existing runtime semantics are not
  silently changed.
- Restore original design capabilities displaced by current numeric semantics
  into `KA-1xxx` IDs that retain the historical final three digits.
- Preserve conflicting historical IDs only as generation-scoped aliases.
- Preserve every distinct named design/executable capability.
- Collapse a true semantic duplicate to one canonical KA plus a scoped
  compatibility alias; retain similar names separately only when their inputs,
  outputs, layer, effect, or decision semantics materially differ.
- Retain numbered generic scaffold rows as historical evidence; do not claim
  them as distinct production algorithms without a semantic contract.

## CP18-A disposition

The no-loss and identity decisions are `approved_cp18_a_authority` and enforced by
`scripts/verify_ka_capability_inventory.py`. Approval covers the capability
authority only. Implementation, wiring, individual-test, and installed
acceptance counts remain the work queue for CP18-B through CP18-H.
