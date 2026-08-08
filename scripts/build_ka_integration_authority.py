#!/usr/bin/env python3
"""Generate the Phase 19 Knowledge Algorithm integration authority.

This is not a second runtime registry. It extends the retained Phase 18
identity/source authority with the system owner, consumer, selection, effect,
test, and trace destinations required to integrate every canonical capability
through the one runtime manifest and controller.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CROSSWALK_PATH = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-18"
    / "ka-capability-crosswalk.json"
)
OUTPUT_DIR = ROOT / "reports" / "production-readiness" / "2026" / "phase-19"
DEFAULT_JSON_PATH = OUTPUT_DIR / "ka-integration-authority.json"
DEFAULT_CSV_PATH = OUTPUT_DIR / "ka-integration-authority.csv"
DEFAULT_MARKDOWN_PATH = OUTPUT_DIR / "cp19-a-integration-authority.md"


OWNER_DEFINITIONS: dict[str, dict[str, Any]] = {
    "governed_request_dmrf": {
        "title": "Governed request and DMRF",
        "stage": "admission_and_routing",
        "effect_port": "governed_request_service",
        "consumers": ["truthcore", "simulation", "providers_gateway"],
    },
    "truthcore_l1_l5": {
        "title": "TruthCore Layers 1-5",
        "stage": "candidate_preparation",
        "effect_port": "governed_execution_service",
        "consumers": ["governed_request", "refinement", "simulation"],
    },
    "truthcore_l6_l8": {
        "title": "TruthCore Layers 6-8",
        "stage": "candidate_validation",
        "effect_port": "governed_execution_service",
        "consumers": ["governed_request", "refinement", "truthgate"],
    },
    "truthcore_l9": {
        "title": "TruthCore Layer 9",
        "stage": "meta_evaluation_and_loop_control",
        "effect_port": "governed_execution_service",
        "consumers": ["governed_request", "refinement", "truthcore_l10"],
    },
    "truthcore_l10": {
        "title": "TruthCore Layer 10",
        "stage": "containment_and_release",
        "effect_port": "governed_execution_service",
        "consumers": ["governed_request", "knowledge_lifecycle"],
    },
    "dsqp_quad_persona": {
        "title": "DSQP and Quad Persona",
        "stage": "persona_analysis",
        "effect_port": "persona_context_service",
        "consumers": ["governed_request", "truthcore", "refinement"],
    },
    "truthgate": {
        "title": "TruthGate",
        "stage": "entry_and_l8_policy",
        "effect_port": "policy_decision_service",
        "consumers": [
            "governed_request",
            "ingestion",
            "mcp_connectors",
            "providers_gateway",
        ],
    },
    "truthmemory_truthlink_frost": {
        "title": "TruthMemory, TruthLink, and FROST",
        "stage": "knowledge_lifecycle",
        "effect_port": "knowledge_lifecycle_service",
        "consumers": ["truthcore", "retrieval_graph_memory", "simulation"],
    },
    "ingestion": {
        "title": "Ingestion",
        "stage": "ingestion_pipeline",
        "effect_port": "ingestion_service",
        "consumers": ["retrieval_graph_memory", "truthgate"],
    },
    "retrieval_graph_memory": {
        "title": "Retrieval, graph, and memory",
        "stage": "knowledge_data_plane",
        "effect_port": "knowledge_store_service",
        "consumers": ["governed_request", "ingestion", "truthcore"],
    },
    "simulation": {
        "title": "Simulation",
        "stage": "simulation_job",
        "effect_port": "simulation_job_service",
        "consumers": ["governed_request", "truthcore", "providers_gateway"],
    },
    "mcp_connectors": {
        "title": "MCP and connectors",
        "stage": "governed_tool_execution",
        "effect_port": "mcp_connector_service",
        "consumers": ["governed_request", "truthgate", "providers_gateway"],
    },
    "provider_gateway": {
        "title": "Provider and gateway",
        "stage": "provider_and_external_capability",
        "effect_port": "provider_gateway_service",
        "consumers": ["governed_request", "simulation", "mcp_connectors"],
    },
    "security_operations_lifecycle": {
        "title": "Security, operations, and lifecycle",
        "stage": "security_operations_lifecycle",
        "effect_port": "operations_control_service",
        "consumers": [
            "governed_request",
            "ingestion",
            "mcp_connectors",
            "providers_gateway",
            "simulation",
        ],
    },
    "refinement": {
        "title": "Canonical 12-step refinement",
        "stage": "post_candidate_refinement",
        "effect_port": "governed_execution_service",
        "consumers": ["truthcore_l9", "truthcore_l10"],
    },
    "api_sdk_desktop": {
        "title": "API, SDK, and desktop",
        "stage": "product_interaction",
        "effect_port": "api_command_service",
        "consumers": ["canonical_controller", "trace_evaluation"],
    },
}

# The restored design catalog described KA-1077 as a knowledge-store writer.
# Its reviewed implementation only scores supplied signals and has no effect
# port, so the integration authority must match the runtime contract.
PURE_ADVISORY_OVERRIDES = {
    "KA-006",
    "KA-007",
    "KA-008",
    "KA-019",
    "KA-020",
    "KA-021",
    "KA-056",
    "KA-060",
    "KA-066",
    "KA-067",
    "KA-1036",
    "KA-1038",
    "KA-1044",
    "KA-1047",
    "KA-1045",
    "KA-1077",
    "KA-1086",
    "KA-1085",
    "KA-1087",
    "KA-1089",
    "KA-1095",
    "KA-1099",
    "KA-1104",
    "KA-1106",
    "KA-1108",
    "KA-1110",
    "KA-1112",
    "KA-116",
    *(f"L9-KA-{number:03d}" for number in range(1, 8)),
    *(f"L10-KA-{number:03d}" for number in range(1, 8)),
}


def _ids(start: int, end: int) -> set[str]:
    return {f"KA-{number:03d}" for number in range(start, end + 1)}


GOVERNED_REQUEST_IDS = {
    "KA-004",
    "KA-005",
    "KA-031",
    "KA-033",
    "KA-036",
    "KA-058",
    "KA-059",
    "KA-061",
    "KA-1073",
    "KA-1107",
    "KA-113",
    "KA-Master",
}
PERSONA_IDS = {
    "KA-012",
    "KA-013",
    "KA-028",
    "KA-030",
    "KA-038",
    "KA-057",
    "KA-068",
    "KA-069",
    "KA-1037",
    "KA-1075",
    "KA-1084",
}
SIMULATION_IDS = {
    "KA-032",
    "KA-037",
    "KA-042",
    "KA-070",
    "KA-1080",
    "KA-1081",
    "KA-1091",
    "KA-1101",
    "KA-1103",
}
INGESTION_IDS = _ids(71, 78)
RETRIEVAL_GRAPH_MEMORY_IDS = {
    "KA-018",
    "KA-029",
    "KA-079",
    "KA-080",
    "KA-1039",
    "KA-1040",
    "KA-1043",
    "KA-1046",
    "KA-1048",
    "KA-1049",
    "KA-1076",
    "KA-1077",
    "KA-1078",
    "KA-1079",
    "KA-1092",
}
TRUTHMEMORY_IDS = {
    "KA-023",
    "KA-051",
    "KA-052",
    "KA-053",
    "KA-054",
    "KA-055",
    "KA-062",
    "KA-063",
    "KA-064",
    "KA-065",
    "KA-1071",
    "KA-1082",
    "KA-1083",
    "KA-1086",
    "KA-1088",
    "KA-1089",
    "KA-1093",
    "KA-1094",
    "KA-1095",
    "KA-1096",
    "KA-1105",
    "KA-1109",
    "KA-1111",
    "KA-117",
}
PROVIDER_GATEWAY_IDS = _ids(81, 90) | {
    "KA-1072",
    "KA-111",
    "KA-1114",
}
TRUTHGATE_IDS = {
    "KA-010",
    "KA-016",
    "KA-022",
    "KA-024",
    "KA-027",
    "KA-034",
    "KA-1045",
    "KA-1074",
    "KA-1090",
    "KA-1099",
    "KA-1104",
    "KA-1108",
    "KA-1110",
    "KA-169",
    "KA-172",
    "KA-173",
    "KA-174",
    "KA-176",
    "KA-177",
}
SECURITY_OPERATIONS_IDS = (
    (
        _ids(91, 115)
        | _ids(136, 139)
        | _ids(175, 175)
        | _ids(179, 184)
        | {"KA-1097", "KA-1098", "KA-1100"}
    )
    - GOVERNED_REQUEST_IDS
    - PROVIDER_GATEWAY_IDS
)
L9_OWNER_IDS = {"KA-008", "KA-019", "KA-056", "KA-1087"}
L10_OWNER_IDS = {"KA-020", "KA-021", "KA-116"}
L6_L8_OWNER_IDS = {"KA-014"}

BATCH_30_34_IDS = {
    "KA-006",
    "KA-007",
    "KA-008",
    "KA-019",
    "KA-056",
    "KA-060",
    "KA-066",
    "KA-067",
    "KA-1036",
    "KA-1038",
    "KA-1044",
    "KA-1047",
    "KA-1085",
    "KA-1087",
    *(f"L9-KA-{number:03d}" for number in range(1, 8)),
    *(f"L10-KA-{number:03d}" for number in range(1, 8)),
}

REQUIRED_SAFETY_IDS = (
    TRUTHGATE_IDS
    | {"KA-061", "KA-1107"}
    | {f"L10-KA-{number:03d}" for number in range(1, 8)}
    | {f"L9-KA-{number:03d}" for number in range(1, 8)}
)


WORKFLOW_DISPOSITIONS = [
    {
        "path": "backend/governed_execution/orchestrator.py",
        "system": "governed_lifecycle",
        "disposition": "canonical_product_owner",
        "target_checkpoint": "CP19-D",
        "production_policy": "retain_as_only_answer_and_persistence_owner",
    },
    {
        "path": "backend/dmrf/orchestrator.py",
        "system": "dmrf",
        "disposition": "canonical_routing_library",
        "target_checkpoint": "CP19-D",
        "production_policy": "invoke_only_inside_governed_product_owner",
    },
    {
        "path": "backend/truth_engine/truth_core/engine.py",
        "system": "ten_layer",
        "disposition": "canonical_stage_library",
        "target_checkpoint": "CP19-D",
        "production_policy": "no_independent_provider_answer_or_persistence_path",
    },
    {
        "path": "backend/truth_engine/truth_core/refinement_orchestrator.py",
        "system": "twelve_step_refinement",
        "disposition": "canonical_candidate",
        "target_checkpoint": "CP19-G",
        "production_policy": "migrate_to_one_bounded_post_candidate_subgraph",
    },
    {
        "path": "backend/governed_execution/prompt.py",
        "system": "provider_refinement",
        "disposition": "canonical_message_adapter",
        "target_checkpoint": "CP19-G",
        "production_policy": "one_authorized_rewrite_after_step_findings",
    },
    {
        "path": "core/simulation/refinement_workflow.py",
        "system": "twelve_step_refinement",
        "disposition": "broken_reference_removal_candidate",
        "target_checkpoint": "CP19-G",
        "production_policy": "forbidden_after_cp19_g",
    },
    {
        "path": "core/system/refinement_orchestrator.py",
        "system": "twelve_step_refinement",
        "disposition": "legacy_nonproduction",
        "target_checkpoint": "CP19-G",
        "production_policy": "forbidden_after_cp19_g",
    },
    {
        "path": "core/simulation/refinement_orchestrator.py",
        "system": "twelve_step_refinement",
        "disposition": "legacy_simulation_only",
        "target_checkpoint": "CP19-G",
        "production_policy": "forbidden_from_product_answer_path",
    },
    {
        "path": "core/persona/quad/mathematical_framework/refinement.py",
        "system": "twelve_step_refinement",
        "disposition": "mathematical_reference_fixture",
        "target_checkpoint": "CP19-G",
        "production_policy": "test_and_reference_only",
    },
    {
        "path": "backend/dsqp/dsqp_orchestrator.py",
        "system": "quad_persona_dsqp",
        "disposition": "canonical_profile_construction",
        "target_checkpoint": "CP19-F",
        "production_policy": "retain_inside_governed_product_owner",
    },
    {
        "path": "core/persona/quad/pod_orchestrator/orchestrator.py",
        "system": "quad_persona_dsqp",
        "disposition": "canonical_scaling_library_candidate",
        "target_checkpoint": "CP19-F",
        "production_policy": "use_only_through_dsqp_truthcore_adapter",
    },
    {
        "path": "backend/quad_persona/quad_engine.py",
        "system": "quad_persona_dsqp",
        "disposition": "gateway_compatibility_candidate",
        "target_checkpoint": "CP19-F",
        "production_policy": "retire_product_entry_after_parity",
    },
    {
        "path": "core/persona/quad/quad_engine.py",
        "system": "quad_persona_dsqp",
        "disposition": "legacy_reference_engine",
        "target_checkpoint": "CP19-F",
        "production_policy": "test_and_reference_only_after_cp19_f",
    },
    {
        "path": "core/persona/quad/mathematical_framework/integration.py",
        "system": "quad_persona_dsqp",
        "disposition": "mathematical_reference_fixture",
        "target_checkpoint": "CP19-F",
        "production_policy": "test_and_reference_only",
    },
    {
        "path": "core/orchestration/master_workflow.py",
        "system": "governed_lifecycle",
        "disposition": "legacy_parallel_orchestrator",
        "target_checkpoint": "CP19-D",
        "production_policy": "forbidden_from_product_path_after_cp19_d",
    },
    {
        "path": "core/system/united_system_manager.py",
        "system": "governed_lifecycle",
        "disposition": "legacy_parallel_coordinator",
        "target_checkpoint": "CP19-D",
        "production_policy": "nonproduction_compatibility_only",
    },
]


FINDING_TRANSFERS = {
    "F-01": "CP19-C",
    "F-02": "CP19-D",
    "F-03": "CP19-B",
    "F-04": "CP19-E",
    "F-05": "CP19-I",
    "F-06": "CP19-G",
    "F-07": "CP19-F",
    "F-08": "CP19-B,CP19-E,CP19-K",
    "F-09": "CP19-K",
    "F-10": "CP19-A-M",
    "CP18-E": "CP19-J",
    "CP18-F": "CP19-K",
    "CP18-G": "CP19-L",
    "CP18-H": "CP19-M",
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _primary_owner(row: dict[str, Any]) -> str:
    canonical_id = row["canonical_id"]
    layers = set(row.get("layer_scope", []))
    if canonical_id in GOVERNED_REQUEST_IDS:
        return "governed_request_dmrf"
    if canonical_id in PERSONA_IDS:
        return "dsqp_quad_persona"
    if canonical_id in SIMULATION_IDS:
        return "simulation"
    if canonical_id in INGESTION_IDS:
        return "ingestion"
    if canonical_id in RETRIEVAL_GRAPH_MEMORY_IDS:
        return "retrieval_graph_memory"
    if canonical_id in TRUTHMEMORY_IDS:
        return "truthmemory_truthlink_frost"
    if canonical_id in PROVIDER_GATEWAY_IDS:
        return "provider_gateway"
    if canonical_id in TRUTHGATE_IDS:
        return "truthgate"
    if canonical_id in SECURITY_OPERATIONS_IDS:
        return "security_operations_lifecycle"
    if canonical_id.startswith("L9-KA-") or canonical_id in L9_OWNER_IDS:
        return "truthcore_l9"
    if canonical_id.startswith("L10-KA-") or canonical_id in L10_OWNER_IDS:
        return "truthcore_l10"
    if canonical_id in L6_L8_OWNER_IDS:
        return "truthcore_l6_l8"
    if "L9" in layers:
        return "truthcore_l9"
    if "L10" in layers:
        return "truthcore_l10"
    if layers & {"L6", "L7", "L8"}:
        return "truthcore_l6_l8"
    return "truthcore_l1_l5"


def _consumer_paths(row: dict[str, Any], owner: str, effect_class: str) -> list[str]:
    consumers = {
        "api_sdk_desktop_evaluation",
        "canonical_controller",
        "trace_evaluation",
        *OWNER_DEFINITIONS[owner]["consumers"],
    }
    if effect_class == "effect_oriented_review_required":
        consumers.add("authoritative_effect_service")
    if row.get("contract_status") != "complete":
        consumers.add("contract_parity")
    return sorted(consumers)


def _required_or_optional(canonical_id: str, effect_class: str) -> str:
    if canonical_id == "KA-033":
        return "reserved_disabled"
    if canonical_id in REQUIRED_SAFETY_IDS:
        return "required_when_stage_applicable"
    if effect_class == "effect_oriented_review_required":
        return "conditional_effect_proposal"
    return "conditional"


def _selector_policy(canonical_id: str) -> str:
    if canonical_id == "KA-033":
        return "never_select_until_manifest_revision"
    if canonical_id in REQUIRED_SAFETY_IDS:
        return "required_for_applicable_stage_and_policy_context"
    return "select_only_when_manifest_predicates_and_dependencies_match"


def _entry(row: dict[str, Any]) -> dict[str, Any]:
    canonical_id = row["canonical_id"]
    owner = _primary_owner(row)
    owner_definition = OWNER_DEFINITIONS[owner]
    effect_class = (
        "pure_or_advisory_review_required"
        if canonical_id in PURE_ADVISORY_OVERRIDES
        else row["effect_class"]
    )
    effectful = effect_class == "effect_oriented_review_required"
    test_slug = _slug(canonical_id)
    integration_test = (
        "tests/integration/phase19/test_truthcore_batches_30_34.py"
        f"::test_{test_slug}_owning_path"
        if canonical_id in BATCH_30_34_IDS
        else f"tests/integration/phase19/test_{owner}.py::test_{test_slug}_owning_path"
    )
    return {
        "canonical_id": canonical_id,
        "name": row["name"],
        "implementation_owner": row["implementation"],
        "primary_owner": owner,
        "primary_owner_title": owner_definition["title"],
        "consumer_paths": _consumer_paths(row, owner, effect_class),
        "selector_policy": _selector_policy(canonical_id),
        "required_or_optional": _required_or_optional(canonical_id, effect_class),
        "stage": owner_definition["stage"],
        "declared_layers": row.get("layer_scope", []),
        "effect_class": effect_class,
        "effect_port": owner_definition["effect_port"] if effectful else None,
        "effect_transaction": (
            "proposal_requires_authoritative_policy_idempotency_transaction_receipt"
            if effectful
            else "not_applicable_pure_or_advisory_result"
        ),
        "positive_fixture": (
            f"tests/knowledge_algorithms/phase19/{test_slug}.json#positive_selector"
        ),
        "negative_fixture": (
            f"tests/knowledge_algorithms/phase19/{test_slug}.json#negative_selector"
        ),
        "functional_test": (
            "tests/knowledge_algorithms/test_phase19_per_ka_semantics.py"
            f"::test_{test_slug}_semantic_contract"
        ),
        "integration_test": integration_test,
        "trace_assertion": (
            "planned_selected_admitted_executed_terminal_state"
            + ("_authoritative_effect_receipt" if effectful else "")
        ),
        "current_wiring": {
            "detected_execution_call_sites": row.get("execution_call_sites", []),
            "detected_named_test_functions": row.get("named_test_functions", []),
            "production_enabled": bool(
                (row.get("phase6_production_metadata") or {}).get("production_enabled")
            ),
        },
        "qualification": {
            "contract": "CP19-B",
            "selector": "CP19-C",
            "owning_path": {
                "truthcore_l9": "CP19-E",
                "truthcore_l10": "CP19-E",
                "dsqp_quad_persona": "CP19-F",
                "ingestion": "CP19-H",
                "retrieval_graph_memory": "CP19-H",
                "truthmemory_truthlink_frost": "CP19-H",
                "simulation": "CP19-I",
                "provider_gateway": "CP19-I",
                "security_operations_lifecycle": "CP19-I",
            }.get(owner, "CP19-D"),
            "product_workflow": "CP19-J",
            "per_ka_proof": "CP19-K",
            "source_exit": "CP19-L",
            "installed_exit": "CP19-M",
        },
    }


def build_authority() -> dict[str, Any]:
    crosswalk_bytes = CROSSWALK_PATH.read_bytes()
    crosswalk = json.loads(crosswalk_bytes)
    if crosswalk.get("status") != "approved_cp18_a_authority":
        raise ValueError("retained CP18-A crosswalk is not approved")
    rows = [_entry(row) for row in crosswalk["canonical_capabilities"]]
    rows.sort(key=lambda row: row["canonical_id"])
    owner_counts = Counter({owner: 0 for owner in OWNER_DEFINITIONS})
    owner_counts.update(row["primary_owner"] for row in rows)
    workflow_paths = [row["path"] for row in WORKFLOW_DISPOSITIONS]
    if len(workflow_paths) != len(set(workflow_paths)):
        raise ValueError("workflow disposition paths must be unique")
    missing_workflows = [path for path in workflow_paths if not (ROOT / path).is_file()]
    if missing_workflows:
        raise ValueError(f"workflow disposition paths missing: {missing_workflows}")
    return {
        "schema_version": "dle.ka-integration-authority.v1",
        "authority_version": "2026.07.25-cp19a.1",
        "status": "approved_cp19_a_authority",
        "phase": 19,
        "checkpoint": "CP19-A",
        "runtime_registry": False,
        "runtime_authority": (
            "backend/knowledge_algorithms/ka_manifest.v1.generated.json"
        ),
        "identity_source": CROSSWALK_PATH.relative_to(ROOT).as_posix(),
        "identity_source_sha256": hashlib.sha256(crosswalk_bytes).hexdigest(),
        "invariants": {
            "canonical_capabilities": len(rows),
            "unique_implementation_owners": len(
                {row["implementation_owner"] for row in rows}
            ),
            "unowned_capabilities": sum(not row["primary_owner"] for row in rows),
            "duplicate_primary_owners": 0,
            "runtime_registries_added": 0,
            "findings_waived": False,
            "rebuild_authorized": False,
        },
        "owner_definitions": OWNER_DEFINITIONS,
        "owner_counts": dict(sorted(owner_counts.items())),
        "finding_transfers": FINDING_TRANSFERS,
        "workflow_dispositions": WORKFLOW_DISPOSITIONS,
        "canonical_capabilities": rows,
    }


def json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def csv_text(payload: dict[str, Any]) -> str:
    buffer = io.StringIO(newline="")
    fieldnames = [
        "canonical_id",
        "name",
        "implementation_owner",
        "primary_owner",
        "stage",
        "required_or_optional",
        "selector_policy",
        "effect_class",
        "effect_port",
        "consumer_paths",
        "positive_fixture",
        "negative_fixture",
        "functional_test",
        "integration_test",
        "trace_assertion",
        "detected_call_site_count",
        "detected_named_test_count",
        "production_enabled",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in payload["canonical_capabilities"]:
        writer.writerow(
            {
                "canonical_id": row["canonical_id"],
                "name": row["name"],
                "implementation_owner": row["implementation_owner"],
                "primary_owner": row["primary_owner"],
                "stage": row["stage"],
                "required_or_optional": row["required_or_optional"],
                "selector_policy": row["selector_policy"],
                "effect_class": row["effect_class"],
                "effect_port": row["effect_port"] or "",
                "consumer_paths": ";".join(row["consumer_paths"]),
                "positive_fixture": row["positive_fixture"],
                "negative_fixture": row["negative_fixture"],
                "functional_test": row["functional_test"],
                "integration_test": row["integration_test"],
                "trace_assertion": row["trace_assertion"],
                "detected_call_site_count": len(
                    row["current_wiring"]["detected_execution_call_sites"]
                ),
                "detected_named_test_count": len(
                    row["current_wiring"]["detected_named_test_functions"]
                ),
                "production_enabled": row["current_wiring"]["production_enabled"],
            }
        )
    return buffer.getvalue()


def markdown_text(payload: dict[str, Any]) -> str:
    owner_rows = "\n".join(
        f"| `{owner}` | {OWNER_DEFINITIONS[owner]['title']} | {count} |"
        for owner, count in payload["owner_counts"].items()
    )
    workflow_rows = "\n".join(
        "| `{path}` | {system} | `{disposition}` | {target_checkpoint} | "
        "{production_policy} |".format(**row)
        for row in payload["workflow_dispositions"]
    )
    return f"""# CP19-A Knowledge Algorithm integration authority

**Authority version:** `{payload["authority_version"]}`
**Status:** `{payload["status"]}`
**Release decision:** NO-GO; rebuild not authorized

## Decision

The retained Phase 18 crosswalk remains the only identity/source baseline. This
Phase 19 authority adds integration ownership and evidence destinations; it is
not a second runtime registry. All {payload["invariants"]["canonical_capabilities"]}
canonical capabilities retain exactly one implementation owner and now have
exactly one primary subsystem owner. No CP18-D finding is waived.

The full 213-row matrix is available in `ka-integration-authority.json` and
`ka-integration-authority.csv`.

## Owner allocation

| Owner key | System boundary | KAs |
|---|---|---:|
{owner_rows}

## Workflow dispositions

| Path | System | Disposition | Gate | Production policy |
|---|---|---|---|---|
{workflow_rows}

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
"""


def write_or_check(*, check: bool) -> int:
    payload = build_authority()
    outputs = {
        DEFAULT_JSON_PATH: json_text(payload),
        DEFAULT_CSV_PATH: csv_text(payload),
        DEFAULT_MARKDOWN_PATH: markdown_text(payload),
    }
    stale: list[Path] = []
    for path, content in outputs.items():
        existing = path.read_text(encoding="utf-8") if path.exists() else None
        if existing != content:
            stale.append(path)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
    if check and stale:
        for path in stale:
            print(f"stale: {path.relative_to(ROOT).as_posix()}")
        return 1
    if not check:
        for path in outputs:
            print(f"generated: {path.relative_to(ROOT).as_posix()}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return write_or_check(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
