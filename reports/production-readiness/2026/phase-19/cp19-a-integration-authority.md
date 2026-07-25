# CP19-A Knowledge Algorithm integration authority

**Authority version:** `2026.07.25-cp19a.1`
**Status:** `approved_cp19_a_authority`
**Release decision:** NO-GO; rebuild not authorized

## Decision

The retained Phase 18 crosswalk remains the only identity/source baseline. This
Phase 19 authority adds integration ownership and evidence destinations; it is
not a second runtime registry. All 213
canonical capabilities retain exactly one implementation owner and now have
exactly one primary subsystem owner. No CP18-D finding is waived.

The full 213-row matrix is available in `ka-integration-authority.json` and
`ka-integration-authority.csv`.

## Owner allocation

| Owner key | System boundary | KAs |
|---|---|---:|
| `api_sdk_desktop` | API, SDK, and desktop | 0 |
| `dsqp_quad_persona` | DSQP and Quad Persona | 11 |
| `governed_request_dmrf` | Governed request and DMRF | 12 |
| `ingestion` | Ingestion | 8 |
| `mcp_connectors` | MCP and connectors | 0 |
| `provider_gateway` | Provider and gateway | 13 |
| `refinement` | Canonical 12-step refinement | 0 |
| `retrieval_graph_memory` | Retrieval, graph, and memory | 15 |
| `security_operations_lifecycle` | Security, operations, and lifecycle | 37 |
| `simulation` | Simulation | 9 |
| `truthcore_l10` | TruthCore Layer 10 | 12 |
| `truthcore_l1_l5` | TruthCore Layers 1-5 | 24 |
| `truthcore_l6_l8` | TruthCore Layers 6-8 | 17 |
| `truthcore_l9` | TruthCore Layer 9 | 12 |
| `truthgate` | TruthGate | 19 |
| `truthmemory_truthlink_frost` | TruthMemory, TruthLink, and FROST | 24 |

## Workflow dispositions

| Path | System | Disposition | Gate | Production policy |
|---|---|---|---|---|
| `backend/governed_execution/orchestrator.py` | governed_lifecycle | `canonical_product_owner` | CP19-D | retain_as_only_answer_and_persistence_owner |
| `backend/dmrf/orchestrator.py` | dmrf | `canonical_routing_library` | CP19-D | invoke_only_inside_governed_product_owner |
| `backend/truth_engine/truth_core/engine.py` | ten_layer | `canonical_stage_library` | CP19-D | no_independent_provider_answer_or_persistence_path |
| `backend/truth_engine/truth_core/refinement_orchestrator.py` | twelve_step_refinement | `canonical_candidate` | CP19-G | migrate_to_one_bounded_post_candidate_subgraph |
| `backend/governed_execution/prompt.py` | provider_refinement | `canonical_message_adapter` | CP19-G | one_authorized_rewrite_after_step_findings |
| `core/simulation/refinement_workflow.py` | twelve_step_refinement | `broken_reference_removal_candidate` | CP19-G | forbidden_after_cp19_g |
| `core/system/refinement_orchestrator.py` | twelve_step_refinement | `legacy_nonproduction` | CP19-G | forbidden_after_cp19_g |
| `core/simulation/refinement_orchestrator.py` | twelve_step_refinement | `legacy_simulation_only` | CP19-G | forbidden_from_product_answer_path |
| `core/persona/quad/mathematical_framework/refinement.py` | twelve_step_refinement | `mathematical_reference_fixture` | CP19-G | test_and_reference_only |
| `backend/dsqp/dsqp_orchestrator.py` | quad_persona_dsqp | `canonical_profile_construction` | CP19-F | retain_inside_governed_product_owner |
| `core/persona/quad/pod_orchestrator/orchestrator.py` | quad_persona_dsqp | `canonical_scaling_library_candidate` | CP19-F | use_only_through_dsqp_truthcore_adapter |
| `backend/quad_persona/quad_engine.py` | quad_persona_dsqp | `gateway_compatibility_candidate` | CP19-F | retire_product_entry_after_parity |
| `core/persona/quad/quad_engine.py` | quad_persona_dsqp | `legacy_reference_engine` | CP19-F | test_and_reference_only_after_cp19_f |
| `core/persona/quad/mathematical_framework/integration.py` | quad_persona_dsqp | `mathematical_reference_fixture` | CP19-F | test_and_reference_only |
| `core/orchestration/master_workflow.py` | governed_lifecycle | `legacy_parallel_orchestrator` | CP19-D | forbidden_from_product_path_after_cp19_d |
| `core/system/united_system_manager.py` | governed_lifecycle | `legacy_parallel_coordinator` | CP19-D | nonproduction_compatibility_only |

## Authority fields

Every row records canonical identity, implementation owner, primary subsystem
owner, governed consumers, selection policy, required/optional classification,
stage, effect port/transaction boundary, positive and negative selector fixture
destinations, named semantic and owning-path test destinations, trace assertion,
current detected wiring/tests, and CP19-B through CP19-M qualification owners.

## Exit

CP19-A authorizes CP19-B contract-parity work only. It does not authorize
selector activation, subsystem effects, a rebuilt artifact, installed
acceptance, or production launch.
