"""Generate the canonical Knowledge Algorithm runtime manifest."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_ka_integration_authority import (
    DEFAULT_JSON_PATH as INTEGRATION_AUTHORITY_PATH,
)  # noqa: E402
from scripts.build_ka_integration_authority import (
    build_authority as build_integration_authority,
)  # noqa: E402

CROSSWALK_PATH = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-18"
    / "ka-capability-crosswalk.json"
)
DEFAULT_OUTPUT_PATH = (
    ROOT / "backend" / "knowledge_algorithms" / "ka_manifest.v1.generated.json"
)
SDK_OUTPUT_PATH = (
    ROOT
    / "sdk"
    / "UKG_Python_SDK"
    / "ukg_sdk"
    / "data"
    / "ka_manifest.v1.generated.json"
)
TYPESCRIPT_OUTPUT_PATH = (
    ROOT / "sdk" / "DataLogicEngine_TypeScript_SDK" / "src" / "ka-manifest.generated.ts"
)

OWNER_CATEGORY: dict[str, str] = {
    "governed_request_dmrf": "Routing",
    "truthcore_l1_l5": "Reasoning",
    "truthcore_l6_l8": "Analysis",
    "truthcore_l9": "Meta",
    "truthcore_l10": "Safety",
    "dsqp_quad_persona": "Persona",
    "truthgate": "Safety",
    "truthmemory_truthlink_frost": "Memory",
    "ingestion": "Lifecycle",
    "retrieval_graph_memory": "Memory",
    "simulation": "Analysis",
    "mcp_connectors": "Control",
    "provider_gateway": "Capability",
    "security_operations_lifecycle": "Governance",
    "refinement": "QA",
    "api_sdk_desktop": "UX",
}

OWNER_LAYER_SCOPE: dict[str, list[str]] = {
    "governed_request_dmrf": ["L1"],
    "truthcore_l1_l5": ["L1-L5"],
    "truthcore_l6_l8": ["L6-L8"],
    "truthcore_l9": ["L9"],
    "truthcore_l10": ["L10"],
    "dsqp_quad_persona": ["L4", "L5"],
    "truthgate": ["L8"],
    "truthmemory_truthlink_frost": ["knowledge_lifecycle"],
    "ingestion": ["ingestion"],
    "retrieval_graph_memory": ["L2"],
    "simulation": ["simulation"],
    "mcp_connectors": ["mcp"],
    "provider_gateway": ["provider_gateway"],
    "security_operations_lifecycle": ["operations"],
    "refinement": ["refinement"],
    "api_sdk_desktop": ["product_interaction"],
}

CONTRACT_METADATA_POLICY = {
    "checkpoint": "AL-10",
    "purpose_source": "implementation_module_docstring",
    "category_source": "cp19_a_primary_owner",
    "risk_source": "declared_effect_class_and_cp19_a_primary_owner",
    "subsystem_source": "cp19_a_primary_owner",
    "layer_source": "cp19_a_primary_owner_stage_scope",
}

# CP19-C corrects three reciprocal design-reference relationships into
# prerequisite order. The retained CP18 crosswalk remains the identity/source
# baseline; these integration-only corrections do not rename or remove a KA.
CP19_C_DEPENDENCY_OVERRIDES: dict[str, dict[str, Any]] = {
    "KA-065": {
        "dependencies": [],
        "rationale": (
            "Regression testing is an input to integrity validation and must "
            "not depend on the validators that consume its result."
        ),
    },
    "KA-117": {
        "dependencies": ["KA-065", "KA-1094"],
        "rationale": (
            "Knowledge integrity consumes regression and contradiction "
            "evidence before persistence; the system-wide auditor is downstream."
        ),
    },
    "KA-1099": {
        "dependencies": ["KA-065", "KA-117"],
        "rationale": (
            "The system integrity audit aggregates completed regression and "
            "knowledge-integrity results."
        ),
    },
    "KA-1111": {
        "dependencies": ["KA-1112"],
        "rationale": (
            "Goal-drift monitoring evaluates history and long-horizon plans "
            "before the evolution controller admits an action."
        ),
    },
    "KA-1100": {
        "dependencies": ["KA-1107", "KA-1108", "KA-1111"],
        "rationale": (
            "Evolution admission consumes escalation, capability, and prior "
            "goal-drift constraints; it is not a prerequisite of the monitor."
        ),
    },
}

CP19_E_LAYER_IDS = {
    *(f"L9-KA-{number:03d}" for number in range(1, 8)),
    *(f"L10-KA-{number:03d}" for number in range(1, 8)),
}

# Layer 9's readiness and loop decisions consume the earlier meta-evaluation
# outputs. Layer 10's terminal decision consumes every preceding safety result.
# These are executable prerequisite edges, not duplicated implementation
# authority.
CP19_E_DEPENDENCY_OVERRIDES: dict[str, dict[str, Any]] = {
    "L9-KA-006": {
        "dependencies": [
            "L9-KA-001",
            "L9-KA-002",
            "L9-KA-003",
            "L9-KA-004",
        ],
        "rationale": "Readiness is calculated only from committed L9 measurements.",
    },
    "L9-KA-005": {
        "dependencies": ["L9-KA-006"],
        "rationale": "The refinement trigger consumes measured readiness.",
    },
    "L9-KA-007": {
        "dependencies": ["L9-KA-005", "L9-KA-006"],
        "rationale": "Loop admission consumes the refinement and readiness decisions.",
    },
    "L10-KA-007": {
        "dependencies": ["L10-KA-004", "L10-KA-006"],
        "rationale": "Human review routing consumes ethics and terminal trust results.",
    },
    "L10-KA-005": {
        "dependencies": [
            "L10-KA-001",
            "L10-KA-002",
            "L10-KA-003",
            "L10-KA-004",
            "L10-KA-006",
            "L10-KA-007",
        ],
        "rationale": "The containment decision consumes every preceding L10 safety result.",
    },
}

CP19_E_ADMISSION_OVERRIDES: dict[str, dict[str, Any]] = {
    canonical_id: {
        "production_enabled": True,
        "classification": (
            "deterministic_heuristic"
            if canonical_id
            in {
                "L9-KA-002",
                "L9-KA-004",
                "L9-KA-006",
                "L10-KA-001",
                "L10-KA-002",
                "L10-KA-004",
            }
            else "production_validator"
        ),
        "deterministic": True,
        "performance_budget_ms": 5_000,
        "contract_status": "cp19_e_production_qualified",
        "guarantee": (
            "Produces deterministic bounded L9/L10 control evidence from "
            "supplied committed state and never establishes external truth."
        ),
        "limitations": (
            "Scores are control measurements or heuristics, not calibrated "
            "probabilities; missing required input fails closed or remains "
            "explicitly not measured."
        ),
    }
    for canonical_id in CP19_E_LAYER_IDS
}

CP19_E_IO_OVERRIDES: dict[str, dict[str, list[str]]] = {
    "L9-KA-001": {
        "inputs": ["Committed L1-L8 trace", "executed layer IDs"],
        "outputs": ["Trace integrity findings", "trace completeness"],
    },
    "L9-KA-002": {
        "inputs": ["Original query", "candidate answer"],
        "outputs": ["Measured lexical/numeric drift", "limitations"],
    },
    "L9-KA-003": {
        "inputs": ["Measured persona results", "agreement threshold"],
        "outputs": ["Agreement findings", "measurement status"],
    },
    "L9-KA-004": {
        "inputs": ["Candidate measurements", "committed trace"],
        "outputs": ["Weaknesses", "observed failure modes"],
    },
    "L9-KA-005": {
        "inputs": ["Convergence decision", "measured readiness", "issues"],
        "outputs": ["Refinement decision", "target layer"],
    },
    "L9-KA-006": {
        "inputs": ["Committed L9 measurement outputs"],
        "outputs": ["Readiness measurement", "measurement coverage"],
    },
    "L9-KA-007": {
        "inputs": ["Iteration budget", "refinement decision", "prior attempts"],
        "outputs": ["Loop admission", "exhaustion decision"],
    },
    "L10-KA-001": {
        "inputs": ["Candidate content"],
        "outputs": ["Token entropy heuristic", "divergence flag"],
    },
    "L10-KA-002": {
        "inputs": ["Candidate content"],
        "outputs": ["Self-reference indicators", "capability indicators"],
    },
    "L10-KA-003": {
        "inputs": ["Candidate content"],
        "outputs": ["Redacted content", "PII type counts"],
    },
    "L10-KA-004": {
        "inputs": ["Candidate content"],
        "outputs": ["Ethics rule findings", "policy tier"],
    },
    "L10-KA-005": {
        "inputs": ["Committed L10 results", "final action"],
        "outputs": ["Containment/release decision", "signoff requirement"],
    },
    "L10-KA-006": {
        "inputs": ["Measured confidence", "risk threshold"],
        "outputs": ["Belief-decay trust result", "measurement status"],
    },
    "L10-KA-007": {
        "inputs": ["Trust/ethics results", "risk context"],
        "outputs": ["Deterministic review proposal", "dispatch count"],
    },
}

CP19_F_PERSONA_IDS = {"KA-012", "KA-013", "KA-028", "KA-030", "KA-038"}

# CP19-F makes the causal dataflow executable: profile-backed perspective
# analysis precedes weighting, and weighting precedes conflict disposition.
# The retained Phase 18 edges were design references in the opposite direction.
CP19_F_DEPENDENCY_OVERRIDES: dict[str, dict[str, Any]] = {
    "KA-012": {
        "dependencies": [],
        "rationale": (
            "Persona analysis consumes validated DSQP profiles and produces "
            "the findings that downstream weighting requires."
        ),
    },
    "KA-013": {
        "dependencies": ["KA-012"],
        "rationale": (
            "Persona weighting consumes committed KA-012 findings and measured "
            "DSQP profile coverage."
        ),
    },
    "KA-030": {
        "dependencies": ["KA-013"],
        "rationale": (
            "Conflict disposition consumes weighted, retained dissent and "
            "turns it into mandatory prompt constraints."
        ),
    },
    "KA-038": {
        "dependencies": ["KA-013", "KA-030"],
        "rationale": (
            "Consensus readiness consumes committed persona sufficiency and "
            "the exact retained-dissent disposition."
        ),
    },
}

CP19_F_ADMISSION_OVERRIDES: dict[str, dict[str, Any]] = {
    canonical_id: {
        "production_enabled": True,
        "classification": "deterministic_heuristic",
        "deterministic": True,
        "performance_budget_ms": 250,
        "contract_status": "cp19_f_production_qualified",
        "guarantee": (
            "Produces deterministic bounded persona findings, authority "
            "weights, sufficiency measurements, and dissent dispositions from "
            "validated DSQP profiles without making provider calls."
        ),
        "limitations": (
            "Profile coverage and authority weighting are orchestration "
            "measurements, not factual correctness, calibrated confidence, or "
            "substantive consensus."
        ),
    }
    for canonical_id in CP19_F_PERSONA_IDS
}

CP19_F_IO_OVERRIDES: dict[str, dict[str, list[str]]] = {
    "KA-012": {
        "inputs": [
            "Validated axes 8-11 DSQP profiles",
            "normalized query",
            "bounded governed context",
        ],
        "outputs": [
            "Persona findings",
            "constraints",
            "objections",
            "zero provider subcalls",
        ],
    },
    "KA-013": {
        "inputs": [
            "Committed KA-012 persona findings",
            "domain authority policy",
            "profile coverage threshold",
        ],
        "outputs": [
            "Normalized authority weights",
            "retained dissent",
            "persona sufficiency measurement",
        ],
    },
    "KA-030": {
        "inputs": [
            "Committed KA-013 dissent",
            "normalized query",
        ],
        "outputs": [
            "Conflict dispositions",
            "mandatory prompt constraints",
            "silent-dissent count",
        ],
    },
    "KA-028": {
        "inputs": ["Normalized query", "existing persona identifiers"],
        "outputs": [
            "Bounded additional perspective prompts",
            "selection order",
            "no context effect",
        ],
    },
    "KA-038": {
        "inputs": [
            "Committed KA-013 sufficiency",
            "committed KA-030 dissent disposition",
            "optional declared claim support scores",
        ],
        "outputs": [
            "Consensus-readiness decision",
            "retained-dissent count",
            "no fabricated confidence",
        ],
    },
}

CP19_G_REFINEMENT_IDS = {"KA-003", "KA-005", "KA-011", "KA-025"}

# The live implementations of these refinement observations are self-contained.
# KA-003's design dependency on ensemble synthesis would make a pre-synthesis
# gap observation impossible and is therefore corrected at the runtime
# prerequisite boundary.
CP19_G_DEPENDENCY_OVERRIDES: dict[str, dict[str, Any]] = {
    "KA-003": {
        "dependencies": [],
        "rationale": (
            "Gap analysis compares committed current and desired state before "
            "synthesis and does not consume an ensemble result."
        ),
    },
}

CP19_G_ADMISSION_OVERRIDES: dict[str, dict[str, Any]] = {
    canonical_id: {
        "production_enabled": True,
        "classification": "deterministic_heuristic",
        "deterministic": True,
        "performance_budget_ms": 300,
        "contract_status": "cp19_g_production_qualified",
        "guarantee": (
            "Produces a bounded deterministic refinement observation from "
            "committed request, claim, validator, and trace state without "
            "provider calls or direct effects."
        ),
        "limitations": (
            "Outputs are refinement structure and heuristic observations, not "
            "external evidence, calibrated confidence, or release authority."
        ),
    }
    for canonical_id in CP19_G_REFINEMENT_IDS
}

# KA-025 is also a required cold-path dependency of retrieval lifecycle
# execution. Its controller/module import can exceed the refinement-only
# 300 ms allowance on a clean shared runner, so keep the execution bounded but
# allow one second for first dispatch.
CP19_G_ADMISSION_OVERRIDES["KA-025"]["performance_budget_ms"] = 1_000

CP19_G_IO_OVERRIDES: dict[str, dict[str, list[str]]] = {
    "KA-003": {
        "inputs": [
            "Committed claim/validator state",
            "desired supported-claim state",
        ],
        "outputs": [
            "Explicit missing or mismatched state",
            "bounded heuristic impact",
        ],
    },
    "KA-005": {
        "inputs": [
            "Normalized query",
        ],
        "outputs": [
            "Deterministic intent/domain classification",
            "workflow tier hint",
            "non-calibrated classification score",
        ],
    },
    "KA-011": {
        "inputs": [
            "Committed claim and validator records",
            "bounded structural model type",
        ],
        "outputs": [
            "Structural summary",
            "explicit non-calibrated measurement status",
        ],
    },
    "KA-025": {
        "inputs": [
            "Committed claim/evidence dependency nodes",
        ],
        "outputs": [
            "Dependency graph",
            "measured DAG status and depth",
        ],
    },
}

CP19_G_REFINEMENT_STEPS: list[dict[str, Any]] = [
    {
        "step": 1,
        "step_id": "structured_decomposition",
        "name": "Structured decomposition",
        "purpose": "Decompose the refinement obligation into bounded tasks.",
        "candidate_ka_ids": ["KA-001"],
        "execution_policy": "reuse_committed_or_execute",
    },
    {
        "step": 2,
        "step_id": "alternative_branches",
        "name": "Alternative branches",
        "purpose": "Consider alternative reasoning branches without provider fan-out.",
        "candidate_ka_ids": ["KA-002"],
        "execution_policy": "execute_only_when_production_admitted",
    },
    {
        "step": 3,
        "step_id": "missing_information",
        "name": "Missing information and unresolved claims",
        "purpose": "Identify unsupported, contradicted, or unresolved claims.",
        "candidate_ka_ids": ["KA-003"],
        "execution_policy": "execute_required",
    },
    {
        "step": 4,
        "step_id": "input_source_evidence_validation",
        "name": "Input, source, and evidence validation",
        "purpose": "Consume committed normalization, provenance, and validation results.",
        "candidate_ka_ids": ["KA-004", "KA-009", "KA-018"],
        "execution_policy": "reuse_committed_validation",
    },
    {
        "step": 5,
        "step_id": "deep_causal_analytical_review",
        "name": "Deep causal and analytical review",
        "purpose": "Map claim dependencies and structural analytical constraints.",
        "candidate_ka_ids": ["KA-011", "KA-025"],
        "execution_policy": "execute_required",
    },
    {
        "step": 6,
        "step_id": "self_critique_contradiction_review",
        "name": "Self-critique and contradiction review",
        "purpose": "Consume committed contradiction and meta-evaluation findings.",
        "candidate_ka_ids": ["KA-026", "L9-KA-004"],
        "execution_policy": "reuse_committed_validation",
    },
    {
        "step": 7,
        "step_id": "policy_safety_review",
        "name": "Ethics, security, privacy, risk, and compliance",
        "purpose": "Carry forward L8 policy constraints before rewrite.",
        "candidate_ka_ids": ["KA-024", "L10-KA-003", "L10-KA-004"],
        "execution_policy": "reuse_l8_and_defer_release_checks",
    },
    {
        "step": 8,
        "step_id": "recursive_learning_decision",
        "name": "Recursive-learning decision",
        "purpose": "Consume the bounded L9 recursion and loop decision.",
        "candidate_ka_ids": ["L9-KA-005", "L9-KA-006", "L9-KA-007"],
        "execution_policy": "reuse_committed_validation",
    },
    {
        "step": 9,
        "step_id": "semantic_intent_alignment",
        "name": "Semantic and intent alignment",
        "purpose": "Recheck normalized intent and persona constraints.",
        "candidate_ka_ids": ["KA-005", "KA-012", "KA-013", "KA-030"],
        "execution_policy": "execute_and_reuse_committed",
    },
    {
        "step": 10,
        "step_id": "authorized_external_validation",
        "name": "External validation when authorized",
        "purpose": "Use external research only through a separately authorized service.",
        "candidate_ka_ids": ["KA-1114"],
        "execution_policy": "typed_skip_until_authorized_and_qualified",
    },
    {
        "step": 11,
        "step_id": "synthesis_measured_scoring",
        "name": "Synthesis and measured scoring",
        "purpose": "Collect all findings and measured readiness into rewrite constraints.",
        "candidate_ka_ids": ["KA-030", "L9-KA-006"],
        "execution_policy": "reuse_committed_validation",
    },
    {
        "step": 12,
        "step_id": "memory_lifecycle_proposal",
        "name": "Memory and lifecycle proposal",
        "purpose": "Create an unapplied lifecycle proposal pending L10 release.",
        "candidate_ka_ids": ["KA-051", "KA-1079", "KA-1109"],
        "execution_policy": "proposal_only",
    },
]

CP19_H_OWNER_IDS = {
    # TruthGate entry and Layer-8 policy/trust owners. KA-034 remains an
    # evaluation-only adversarial research method.
    "KA-010",
    "KA-016",
    "KA-022",
    "KA-024",
    "KA-027",
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
    # TruthMemory, TruthLink, and FROST owners. Experimental distillation,
    # fusion, multimodal, and continuous-learning methods remain explicitly
    # evaluation-only.
    "KA-023",
    "KA-052",
    "KA-053",
    "KA-062",
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
    # Secure ingestion pipeline.
    *(f"KA-{number:03d}" for number in range(71, 79)),
    # Retrieval, graph, memory, provenance, lineage, pruning, tiering, and
    # promotion owners. KA-029 remains an evaluation-only expansion method.
    "KA-018",
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
    # Deterministic prerequisites owned by already-integrated TruthCore/DMRF
    # lifecycle positions.
    "KA-017",
    "KA-1107",
    "KA-1112",
}

CP19_H_VALIDATOR_IDS = {
    "KA-024",
    "KA-065",
    "KA-074",
    "KA-1079",
    "KA-1090",
    "KA-1094",
    "KA-1099",
    "KA-117",
    "KA-172",
    "KA-174",
    "KA-176",
    "KA-177",
}

# CP19-H converts design relationships into executable lifecycle order. The
# ingestion chain is serial because each decision consumes the preceding
# acquisition state. Knowledge validation precedes quarantine, promotion, and
# release; those proposals never apply their own effects.
CP19_H_DEPENDENCY_OVERRIDES: dict[str, dict[str, Any]] = {
    **{
        f"KA-{number:03d}": {
            "dependencies": [f"KA-{number - 1:03d}"],
            "rationale": (
                "Secure ingestion executes acquisition, cleaning, transformation, "
                "validation, mapping, resolution, enrichment, and archival "
                "proposal decisions in committed order."
            ),
        }
        for number in range(72, 79)
    },
    "KA-010": {
        "dependencies": [],
        "rationale": (
            "Content bias scanning is self-contained; population disparity "
            "analysis remains a separate conditional cohort decision."
        ),
    },
    "KA-1071": {
        "dependencies": ["KA-018"],
        "rationale": (
            "Knowledge provenance tracking consumes the source provenance "
            "observation before lifecycle publication."
        ),
    },
    "KA-117": {
        "dependencies": ["KA-065"],
        "rationale": (
            "Knowledge integrity consumes regression results before any "
            "quarantine or promotion decision."
        ),
    },
    "KA-1094": {
        "dependencies": ["KA-117", "KA-1071"],
        "rationale": (
            "Quarantine admission consumes committed integrity and provenance "
            "results and remains a proposal to the knowledge lifecycle service."
        ),
    },
    "KA-1109": {
        "dependencies": ["KA-024", "KA-1074"],
        "rationale": (
            "Containment classification consumes the shared trust and privacy "
            "policy decisions before proposing an effect."
        ),
    },
    "KA-1079": {
        "dependencies": ["KA-117", "KA-1094", "KA-1109"],
        "rationale": (
            "Promotion is evaluated only after integrity, quarantine, and "
            "containment decisions have committed."
        ),
    },
    "KA-1096": {
        "dependencies": ["KA-1079"],
        "rationale": (
            "Knowledge release staging consumes the promotion decision and "
            "cannot release independently."
        ),
    },
    "KA-1107": {
        "dependencies": ["KA-004", "KA-005"],
        "rationale": (
            "Reasoning-boundary enforcement consumes normalized input and "
            "classification; simulation cost is not an entry-policy prerequisite."
        ),
    },
    "KA-1108": {
        "dependencies": ["KA-1112"],
        "rationale": (
            "Capability escalation consumes the system-introspection record; "
            "experimental emergence research is not a production prerequisite."
        ),
    },
}

# CP19-K batch-specific admission is limited to deterministic KAs whose named
# owner paths are qualified here. KA-Master remains non-selectable: the
# CanonicalKAController is the authority and must never recursively select its
# compatibility wrapper as a production algorithm.
CP19_K_ADMISSION_IDS = {
    "KA-006",
    "KA-007",
    "KA-008",
    "KA-019",
    "KA-020",
    "KA-021",
    "KA-002",
    "KA-014",
    "KA-015",
    "KA-026",
    "KA-029",
    "KA-034",
    "KA-035",
    "KA-036",
    "KA-040",
    "KA-051",
    "KA-054",
    "KA-055",
    "KA-056",
    "KA-057",
    "KA-058",
    "KA-059",
    "KA-063",
    "KA-060",
    "KA-066",
    "KA-067",
    "KA-068",
    "KA-069",
    "KA-1037",
    "KA-1036",
    "KA-1038",
    "KA-1044",
    "KA-1047",
    "KA-1041",
    "KA-1042",
    "KA-1075",
    "KA-1073",
    "KA-1084",
    "KA-1085",
    "KA-1087",
    "KA-1102",
    "KA-1106",
    "KA-116",
    "KA-039",
    "KA-041",
    "KA-043",
    "KA-044",
    "KA-045",
    "KA-046",
    "KA-047",
    "KA-048",
    "KA-049",
    "KA-050",
    "KA-161",
    "KA-162",
    "KA-163",
    "KA-165",
    "KA-167",
    "KA-168",
    "KA-178",
    "KA-104",
    "KA-105",
    "KA-109",
    "KA-1098",
    "KA-138",
    "KA-139",
    "KA-183",
}

CP19_K_ADMISSION_OVERRIDES: dict[str, dict[str, Any]] = {
    canonical_id: {
        "production_enabled": True,
        "classification": "deterministic_heuristic",
        "deterministic": True,
        "performance_budget_ms": 750,
        "contract_status": "cp19_k_production_qualified",
        "guarantee": (
            "Produces a bounded deterministic owner-consumed decision from "
            "explicit inputs without provider calls or direct effects."
        ),
        "limitations": (
            "The result is a supplied-evidence measurement or routing proposal; "
            "it does not establish external truth, execute a selected plan, or "
            "apply persistence or provider effects."
        ),
    }
    for canonical_id in CP19_K_ADMISSION_IDS
}

# The restored design catalog marked KA-1077 as a memory writer. The reviewed
# implementation only ranks supplied signals and explicitly applies no write.
CP19_K_PURE_ADVISORY_OVERRIDES = {
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
    "KA-039",
    "KA-041",
    "KA-043",
    "KA-044",
    "KA-045",
    "KA-046",
    "KA-047",
    "KA-048",
    "KA-049",
    "KA-050",
    "KA-161",
    "KA-162",
    "KA-163",
    "KA-165",
    "KA-167",
    "KA-168",
    "KA-178",
    *(f"L9-KA-{number:03d}" for number in range(1, 8)),
    *(f"L10-KA-{number:03d}" for number in range(1, 8)),
}

# CP19-K batches 12-18 make owner-consumed dependencies explicit and remove
# stale design edges that would otherwise trigger unrelated maintenance or
# simulation work inside pure context/routing decisions.
CP19_K_DEPENDENCY_OVERRIDES: dict[str, dict[str, Any]] = {
    "KA-1100": {
        "dependencies": [],
        "rationale": (
            "System-evolution admission consumes explicit validation, rollback, "
            "scope, risk, and human-approval evidence and must not silently run "
            "reasoning, introspection, or release KAs."
        ),
    },
    "KA-1101": {
        "dependencies": [],
        "rationale": (
            "Chaos admission consumes explicit environment, magnitude, duration, "
            "rollback, monitoring, service-allowlist, and human-approval evidence."
        ),
    },
    "KA-1103": {
        "dependencies": [],
        "rationale": (
            "Rollback planning validates the explicit checkpoint chain and target "
            "hash without silently starting simulation planning or admission."
        ),
    },
    "KA-1114": {
        "dependencies": [],
        "rationale": (
            "External research consumes explicit gateway-authenticated approval, "
            "connector, domain, source, and time budgets in one owner transaction; "
            "it must not silently trigger unrelated routing and policy KAs."
        ),
    },
    "KA-019": {
        "dependencies": [],
        "rationale": (
            "Knowledge synthesis organizes explicit findings and must not "
            "silently initiate evidence or persona-consensus workflows."
        ),
    },
    "KA-1047": {
        "dependencies": [],
        "rationale": (
            "Meta-selection consumes explicit approved performance history and "
            "must not trigger learning, temporal maintenance, or routing effects."
        ),
    },
    "KA-002": {
        "dependencies": [],
        "rationale": (
            "Candidate-tree planning decomposes an explicit goal and does not "
            "silently trigger normalization or graph expansion."
        ),
    },
    "KA-009": {
        "dependencies": [],
        "rationale": (
            "Evidence scoring consumes bounded supplied evidence; provenance "
            "and source-trust decisions remain separate owner gates."
        ),
    },
    "KA-026": {
        "dependencies": ["KA-009"],
        "rationale": (
            "Contradiction review follows the exact evidence-validation result "
            "and never starts a persona or provider path implicitly."
        ),
    },
    "KA-1042": {
        "dependencies": ["KA-026"],
        "rationale": (
            "Impact propagation consumes committed contradiction findings over "
            "the caller-supplied dependency graph."
        ),
    },
    "KA-1102": {
        "dependencies": [],
        "rationale": (
            "Entropy quantification is a pure calculation over one explicit "
            "distribution and must not trigger reasoning or persona execution."
        ),
    },
    "KA-014": {
        "dependencies": ["KA-009", "KA-026", "KA-1041", "KA-1102"],
        "rationale": (
            "The confidence decision consumes committed evidence, contradiction, "
            "normalization, and entropy measurements without duplicated claims."
        ),
    },
    "KA-015": {
        "dependencies": [],
        "rationale": (
            "Temporal validity is measured from explicit fact windows and an "
            "explicit reference time; it must not trigger temporal-maintenance "
            "proposals as a hidden prerequisite."
        ),
    },
    "KA-1083": {
        "dependencies": ["KA-1082"],
        "rationale": (
            "Revalidation scheduling consumes committed confidence-drift "
            "measurements instead of trusting a duplicated caller claim."
        ),
    },
    "KA-052": {
        "dependencies": ["KA-1083"],
        "rationale": (
            "Temporal maintenance proposals consume the committed revalidation "
            "schedule and never infer or apply retirement independently."
        ),
    },
    "KA-1105": {
        "dependencies": ["KA-1082", "KA-1083"],
        "rationale": (
            "Obsolescence review consumes both committed drift measurements and "
            "the derived revalidation schedule before proposing review."
        ),
    },
    "KA-031": {
        "dependencies": ["KA-005", "KA-036", "KA-1073", "KA-113"],
        "rationale": (
            "Core algorithm selection consumes committed query classification, "
            "bounded complexity, intent clarification, and tier routing results; "
            "simulation validation is not a routing prerequisite."
        ),
    },
    "KA-1074": {
        "dependencies": [],
        "rationale": (
            "Field-level privacy transformation consumes explicit field labels "
            "and must not trigger DMRF plan-boundary enforcement as a hidden "
            "prerequisite."
        ),
    },
    "KA-1088": {
        "dependencies": [],
        "rationale": (
            "Lifecycle planning consumes explicit record state, validation, "
            "confidence, drift, and retirement fields; analytics, compression, "
            "pruning, and scheduling remain separate owner evidence."
        ),
    },
    "KA-1099": {
        "dependencies": [],
        "rationale": (
            "System-component integrity audits explicit component state and "
            "hash evidence; knowledge-record regression gates remain separate."
        ),
    },
    "KA-1106": {
        "dependencies": [],
        "rationale": (
            "Human-override normalization consumes an explicit completed "
            "override record and does not silently initiate escalation."
        ),
    },
}

CP19_H_ADMISSION_OVERRIDES: dict[str, dict[str, Any]] = {
    canonical_id: {
        "production_enabled": True,
        "classification": (
            "production_validator"
            if canonical_id in CP19_H_VALIDATOR_IDS
            else "deterministic_heuristic"
        ),
        "deterministic": True,
        "performance_budget_ms": 750,
        "contract_status": "cp19_h_production_qualified",
        "guarantee": (
            "Produces one bounded deterministic owning-subsystem decision from "
            "supplied service state through the canonical selector and controller."
        ),
        "limitations": (
            "The result is a measured validation, heuristic, or effect proposal; "
            "it does not independently establish external truth or apply a "
            "data, memory, graph, policy, quarantine, promotion, or release effect."
        ),
    }
    for canonical_id in CP19_H_OWNER_IDS
}

CP19_H_IO_OVERRIDES: dict[str, dict[str, list[str]]] = {
    "KA-071": {
        "inputs": ["Securely acquired bounded source records"],
        "outputs": [
            "Ingestion admission proposal",
            "record count",
            "no direct materialization",
        ],
    },
    "KA-078": {
        "inputs": ["Retention-eligible record identifiers"],
        "outputs": [
            "Archival proposal",
            "retention destination and policy",
            "no direct archive effect",
        ],
    },
}

CP19_H_SUBSYSTEM_REGISTRY: dict[str, Any] = {
    "schema_version": "dle.ka-subsystem-registry.v1",
    "registry_version": "2026.08.08-cp19k.6",
    "owners": {
        "dsqp_quad_persona": {
            "adaptation": [
                "KA-057",
                "KA-068",
                "KA-069",
                "KA-1037",
                "KA-1075",
                "KA-1084",
            ],
        },
        "truthcore_l1_l5": {
            "context_dependencies": [
                "KA-003",
                "KA-011",
                "KA-015",
                "KA-017",
                "KA-025",
                "KA-040",
            ],
            "inference_mapping": ["KA-041", "KA-043", "KA-044", "KA-049"],
            "signal_analysis": [
                "KA-039",
                "KA-045",
                "KA-046",
                "KA-047",
                "KA-165",
                "KA-167",
            ],
            "language_identity_explanation": [
                "KA-048",
                "KA-050",
                "KA-161",
                "KA-162",
                "KA-163",
                "KA-168",
                "KA-178",
            ],
        },
        "truthcore_l6_l8": {
            "evidence_confidence_entropy": [
                "KA-002",
                "KA-009",
                "KA-014",
                "KA-026",
                "KA-035",
                "KA-1041",
                "KA-1042",
                "KA-1102",
            ],
            "planning_control": ["KA-006", "KA-007", "KA-060"],
            "advanced_reasoning": [
                "KA-066",
                "KA-067",
                "KA-1036",
                "KA-1044",
                "KA-1047",
                "KA-1085",
            ],
        },
        "truthcore_l9": {
            "synthesis_explainability": [
                "KA-008",
                "KA-019",
                "KA-056",
                "KA-1038",
                "KA-1087",
            ],
            "exact_loop_suite": [
                *(f"L9-KA-{number:03d}" for number in range(1, 8)),
            ],
        },
        "truthcore_l10": {
            "oversight_release": [
                "KA-020",
                "KA-021",
                "KA-1106",
                "KA-1112",
                "KA-116",
            ],
            "exact_release_suite": [
                *(f"L10-KA-{number:03d}" for number in range(1, 8)),
            ],
        },
        "truthgate": {
            "entry": [
                "KA-034",
                "KA-022",
                "KA-172",
                "KA-173",
                "KA-174",
                "KA-176",
                "KA-177",
            ],
            "layer_8": [
                "KA-010",
                "KA-016",
                "KA-024",
                "KA-027",
                "KA-1045",
                "KA-1074",
                "KA-1090",
                "KA-1099",
                "KA-1104",
                "KA-1108",
                "KA-1110",
                "KA-169",
            ],
        },
        "ingestion": {
            "secure_pipeline": [f"KA-{number:03d}" for number in range(71, 79)],
        },
        "retrieval_graph_memory": {
            "retrieval": ["KA-018", "KA-079", "KA-1049", "KA-1077", "KA-1092"],
            "maintenance": [
                "KA-080",
                "KA-1039",
                "KA-1040",
                "KA-1043",
                "KA-1046",
                "KA-1048",
                "KA-1076",
                "KA-1078",
            ],
            "promotion": ["KA-029", "KA-1079"],
        },
        "truthmemory_truthlink_frost": {
            "release": [
                "KA-065",
                "KA-1071",
                "KA-1094",
                "KA-1109",
                "KA-1079",
                "KA-1096",
                "KA-117",
            ],
            "maintenance": [
                "KA-023",
                "KA-052",
                "KA-053",
                "KA-062",
                "KA-064",
                "KA-1082",
                "KA-1083",
                "KA-1086",
                "KA-1088",
                "KA-1089",
                "KA-1093",
                "KA-1095",
                "KA-1105",
                "KA-1111",
            ],
            "content_evolution": [
                "KA-051",
                "KA-053",
                "KA-054",
                "KA-055",
                "KA-063",
            ],
        },
    },
}

CP19_I_OWNER_IDS = {
    # Simulation owner.
    "KA-032",
    "KA-037",
    "KA-042",
    "KA-070",
    "KA-1080",
    "KA-1081",
    "KA-1091",
    "KA-1101",
    "KA-1103",
    # Provider and gateway owner.
    *(f"KA-{number:03d}" for number in range(81, 91)),
    "KA-1072",
    "KA-111",
    "KA-1114",
    # Security, operations, and lifecycle owner.
    *(f"KA-{number:03d}" for number in range(91, 116)),
    *(f"KA-{number:03d}" for number in range(136, 140)),
    "KA-175",
    *(f"KA-{number:03d}" for number in range(179, 185)),
    "KA-1097",
    "KA-1098",
    "KA-1100",
}

# KA-031 remains owned by governed-request/DMRF selection, but CP19-I admits it
# as the canonical compatibility router required to close transferred finding
# F-05. It is not duplicated under the simulation owner.
CP19_I_ADDITIONAL_ADMISSION_IDS = {"KA-031"}

CP19_I_VALIDATOR_IDS = {
    "KA-082",
    "KA-084",
    "KA-095",
    "KA-097",
    "KA-106",
    "KA-109",
    "KA-1081",
    "KA-1098",
    "KA-136",
    "KA-137",
    "KA-138",
    "KA-139",
    "KA-175",
    "KA-182",
    "KA-183",
}

CP19_I_DEPENDENCY_OVERRIDES: dict[str, dict[str, Any]] = {
    "KA-083": {
        "dependencies": ["KA-087", "KA-088", "KA-089", "KA-090"],
        "rationale": (
            "Deployment admission consumes version, experiment, pruning, and "
            "quantization proposals before the provider owner may record a "
            "release-preparation receipt."
        ),
    },
    "KA-081": {
        "dependencies": ["KA-085", "KA-086"],
        "rationale": (
            "Model-training admission consumes the committed feature plan and "
            "measured tuning proposal before an authoritative provider service "
            "may persist a queued-job receipt."
        ),
    },
    "KA-113": {
        "dependencies": ["KA-004", "KA-005"],
        "rationale": (
            "Complexity routing consumes the normalized query and committed "
            "query classification. Simulation cost estimation is downstream "
            "of routing and is not an admission prerequisite."
        ),
    },
    "KA-070": {
        "dependencies": ["KA-042"],
        "rationale": (
            "Graph ripple simulation consumes the bounded local "
            "counterfactual projection; unrelated data-quality scoring is not "
            "a simulation prerequisite."
        ),
    },
    "KA-1081": {
        "dependencies": ["KA-1080"],
        "rationale": (
            "Simulation budget admission consumes the canonical bounded cost "
            "estimate rather than independently trusting a duplicate estimate."
        ),
    },
    "KA-1101": {
        "dependencies": ["KA-1081", "KA-1099"],
        "rationale": (
            "Chaos admission consumes the simulation budget decision and "
            "system-integrity state before an authoritative fault service may "
            "consider the proposal."
        ),
    },
}

CP19_I_ADMISSION_OVERRIDES: dict[str, dict[str, Any]] = {
    canonical_id: {
        "production_enabled": True,
        "classification": (
            "production_validator"
            if canonical_id in CP19_I_VALIDATOR_IDS
            else "deterministic_heuristic"
        ),
        "deterministic": True,
        "performance_budget_ms": 1_000,
        "contract_status": "cp19_i_production_qualified",
        "guarantee": (
            "Produces one bounded deterministic subsystem decision or effect "
            "proposal from declared service state through the canonical "
            "selector and controller."
        ),
        "limitations": (
            "The result does not call a provider or connector, start a job, "
            "change configuration, emit a notification, mutate infrastructure, "
            "or apply another effect. Only the owning authoritative service may "
            "act and issue an idempotent verified receipt."
        ),
    }
    for canonical_id in CP19_I_OWNER_IDS | CP19_I_ADDITIONAL_ADMISSION_IDS
}

CP19_I_SUBSYSTEM_REGISTRY: dict[str, Any] = {
    "schema_version": "dle.ka-extended-subsystem-registry.v1",
    "registry_version": "2026.08.08-cp19k.3",
    "owners": {
        "simulation": {
            "planning": ["KA-1080", "KA-1081", "KA-037", "KA-032"],
            "counterfactual": ["KA-042", "KA-070"],
            "outcome_archive": ["KA-1091"],
            "rollback": ["KA-1103"],
            "chaos_admission": ["KA-1101"],
            "compatibility_routing": ["KA-113", "KA-031"],
        },
        "mcp_connectors": {
            "admission": [
                "KA-022",
                "KA-024",
                "KA-136",
                "KA-137",
                "KA-177",
                "KA-179",
            ],
            "result_validation": [
                "KA-010",
                "KA-096",
                "KA-097",
                "KA-175",
                "KA-182",
            ],
            "recovery": ["KA-106", "KA-184"],
        },
        "provider_gateway": {
            "request": ["KA-082", "KA-084", "KA-1072", "KA-111"],
            "request_governance": ["KA-022", "KA-1072"],
            "response_monitoring": ["KA-084", "KA-137", "KA-182"],
            "model_lifecycle": [
                *(f"KA-{number:03d}" for number in range(81, 91)),
            ],
            "external_research": ["KA-111", "KA-1114"],
        },
        "security_operations_lifecycle": {
            "observability": [
                *(f"KA-{number:03d}" for number in range(91, 101)),
            ],
            "service_control": [
                *(f"KA-{number:03d}" for number in range(101, 110)),
                "KA-1097",
                "KA-1098",
            ],
            "messaging": ["KA-093", "KA-110", "KA-112", "KA-114", "KA-115"],
            "security": [
                *(f"KA-{number:03d}" for number in range(136, 140)),
                "KA-175",
                *(f"KA-{number:03d}" for number in range(179, 185)),
            ],
            "evolution": ["KA-1100"],
        },
    },
}


def normalize_ka_id(value: str) -> str:
    clean = str(value).strip().upper()
    if clean == "KA-MASTER":
        return "KA-Master"
    layer_match = re.fullmatch(r"(L(?:9|10)-KA-)(\d+)", clean)
    if layer_match:
        return f"{layer_match.group(1)}{int(layer_match.group(2)):03d}"
    numeric_match = re.fullmatch(r"KA-(\d+)", clean)
    if numeric_match:
        number = int(numeric_match.group(1))
        width = 3 if number < 1000 else 4
        return f"KA-{number:0{width}d}"
    return clean


def module_from_path(path: str) -> str:
    return path.removesuffix(".py").replace("/", ".").replace("\\", ".")


def choose_entrypoint(row: dict[str, Any]) -> dict[str, Any] | None:
    implementation = row.get("implementation")
    if not implementation:
        return None
    module = module_from_path(implementation)
    if row["canonical_id"].startswith("L9-KA-"):
        classes = [
            name
            for name in row["implementation_analysis"].get("classes", [])
            if not name.endswith("Input")
        ]
        if len(classes) != 1:
            raise ValueError(
                f"{row['canonical_id']}: expected one Layer-9 execution class, "
                f"got {classes}"
            )
        return {
            "adapter": "class_execute",
            "module": module,
            "class_name": classes[0],
            "callable": "execute",
        }
    return {
        "adapter": "module_run",
        "module": module,
        "callable": "run",
    }


def _implementation_purpose(row: dict[str, Any]) -> str | None:
    implementation = row.get("implementation")
    if not implementation:
        return None
    source_path = ROOT / implementation
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    docstring = ast.get_docstring(module, clean=True) or ""
    canonical_id = str(row["canonical_id"])
    name_key = re.sub(r"[^a-z0-9]+", " ", str(row["name"]).lower()).strip()

    for raw_line in docstring.splitlines():
        line = raw_line.strip().lstrip("-* ").strip()
        if not line:
            continue
        if line.lower().startswith("purpose:"):
            purpose = line.split(":", 1)[1].strip()
            if purpose:
                return purpose
            continue
        id_prefix = re.match(
            rf"^{re.escape(canonical_id)}\s*:\s*(.+)$", line, re.IGNORECASE
        )
        if id_prefix:
            candidate = id_prefix.group(1).strip()
            candidate_key = re.sub(
                r"[^a-z0-9]+", " ", candidate.lower()
            ).strip()
            if candidate_key != name_key:
                return candidate
            continue
        if line.lower().startswith(("ka for ", "args:", "returns:")):
            continue
        return line
    return None


def _contract_metadata(
    row: dict[str, Any], integration: dict[str, Any], effect_class: str
) -> dict[str, Any]:
    owner = integration["primary_owner"]
    purpose = row.get("purpose") or _implementation_purpose(row)
    if not purpose:
        raise ValueError(
            f"{row['canonical_id']}: production contract purpose is not declared"
        )

    categories = list(row.get("categories") or [OWNER_CATEGORY[owner]])
    subsystems = list(row.get("subsystems") or [owner])
    layers = list(row.get("layer_scope") or OWNER_LAYER_SCOPE[owner])
    risk_classes = list(row.get("risk_classes") or [])
    if not risk_classes:
        risk_classes = (
            ["Low"]
            if effect_class == "pure_or_advisory_review_required"
            else ["Critical"]
            if owner == "truthgate"
            else ["High"]
        )
    return {
        "purpose": purpose,
        "categories": categories,
        "subsystems": subsystems,
        "layers": layers,
        "risk_classes": risk_classes,
    }


def build_manifest() -> dict[str, Any]:
    crosswalk = json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))
    if crosswalk.get("status") != "approved_cp18_a_authority":
        raise ValueError("CP18-A crosswalk is not approved")
    integration_authority = build_integration_authority()
    if integration_authority.get("status") != "approved_cp19_a_authority":
        raise ValueError("CP19-A integration authority is not approved")
    integration_by_id = {
        row["canonical_id"]: row
        for row in integration_authority["canonical_capabilities"]
    }

    rows = crosswalk["canonical_capabilities"]
    scoped_alias_index = {
        alias: row["canonical_id"]
        for row in rows
        for alias in row.get("scoped_aliases", [])
    }

    def resolve_design_dependency(value: str) -> str:
        normalized = normalize_ka_id(value)
        return scoped_alias_index.get(
            f"design-v1:{normalized}",
            normalized,
        )

    entries: dict[str, dict[str, Any]] = {}
    purpose_owners: dict[str, str] = {}
    for row in rows:
        integration = integration_by_id[row["canonical_id"]]
        pure_advisory_override = row["canonical_id"] in CP19_K_PURE_ADVISORY_OVERRIDES
        effect_class = (
            "pure_or_advisory_review_required"
            if pure_advisory_override
            else row["effect_class"]
        )
        metadata = _contract_metadata(row, integration, effect_class)
        purpose_key = re.sub(
            r"[^a-z0-9]+", " ", metadata["purpose"].lower()
        ).strip()
        prior_purpose_owner = purpose_owners.get(purpose_key)
        if prior_purpose_owner and prior_purpose_owner != row["canonical_id"]:
            metadata["purpose"] = (
                f"{metadata['purpose'].rstrip('.')} for {row['name']}."
            )
            purpose_key = re.sub(
                r"[^a-z0-9]+", " ", metadata["purpose"].lower()
            ).strip()
        purpose_owners[purpose_key] = row["canonical_id"]
        design_contracts = row.get("design_contracts", [])
        versions = [
            str(contract["version"])
            for contract in design_contracts
            if contract.get("version")
        ]
        production = row.get("phase6_production_metadata") or {}
        dependencies = sorted(
            {
                resolve_design_dependency(dependency)
                for dependency in row.get("dependency_source_ids", [])
            }
        )
        override = (
            CP19_K_DEPENDENCY_OVERRIDES.get(row["canonical_id"])
            or CP19_I_DEPENDENCY_OVERRIDES.get(row["canonical_id"])
            or CP19_H_DEPENDENCY_OVERRIDES.get(row["canonical_id"])
            or CP19_G_DEPENDENCY_OVERRIDES.get(row["canonical_id"])
            or CP19_F_DEPENDENCY_OVERRIDES.get(row["canonical_id"])
            or CP19_E_DEPENDENCY_OVERRIDES.get(row["canonical_id"])
            or CP19_C_DEPENDENCY_OVERRIDES.get(row["canonical_id"])
        )
        if override is not None:
            dependencies = list(override["dependencies"])
        existing = bool(row.get("implementation"))
        admission_override = (
            CP19_K_ADMISSION_OVERRIDES.get(row["canonical_id"])
            or CP19_I_ADMISSION_OVERRIDES.get(row["canonical_id"])
            or CP19_H_ADMISSION_OVERRIDES.get(row["canonical_id"])
            or CP19_G_ADMISSION_OVERRIDES.get(row["canonical_id"])
            or CP19_F_ADMISSION_OVERRIDES.get(row["canonical_id"])
            or CP19_E_ADMISSION_OVERRIDES.get(row["canonical_id"])
        )
        io_override = (
            CP19_H_IO_OVERRIDES.get(row["canonical_id"])
            or CP19_G_IO_OVERRIDES.get(row["canonical_id"])
            or CP19_F_IO_OVERRIDES.get(row["canonical_id"])
            or CP19_E_IO_OVERRIDES.get(row["canonical_id"], {})
        )
        entries[row["canonical_id"]] = {
            "canonical_id": row["canonical_id"],
            "name": row["name"],
            "purpose": metadata["purpose"],
            "version": versions[0] if versions else "1.0.0",
            "identity_class": row["identity_class"],
            "aliases": {
                "scoped": row.get("scoped_aliases", []),
                "unscoped": [],
            },
            "implementation": {
                "status": (
                    "implemented_cp19_b_contract_parity"
                    if existing
                    else "implementation_required"
                ),
                "source": row.get("implementation"),
                "entrypoint": choose_entrypoint(row),
            },
            "contract": {
                "version": "dle.ka-execution.v1",
                "status": (
                    admission_override["contract_status"]
                    if admission_override
                    else "cp19_b_contract_parity"
                ),
                "inputs": io_override.get("inputs", row.get("input_descriptions", [])),
                "outputs": io_override.get(
                    "outputs", row.get("output_descriptions", [])
                ),
                "categories": metadata["categories"],
                "layers": metadata["layers"],
                "personas": row.get("persona_scope", []),
                "subsystems": metadata["subsystems"],
                "dependencies": dependencies,
                "dependency_result_contract": ("dle.ka-execution-result.v1#output"),
                "dependency_input_field": "dependency_results",
                "triggers": row.get("triggers", []),
                "risk_classes": metadata["risk_classes"],
                "effect_class": effect_class,
                "reads_memory": any(
                    contract.get("reads_memory") for contract in design_contracts
                ),
                "writes_memory": False
                if pure_advisory_override
                else any(
                    contract.get("writes_memory") for contract in design_contracts
                ),
                "produces_artifacts": any(
                    contract.get("produces_artifacts") for contract in design_contracts
                ),
                "audit_events": any(
                    contract.get("audit_events") for contract in design_contracts
                ),
                "limitations": (
                    admission_override["limitations"]
                    if admission_override
                    else production.get("limitations")
                )
                or "Phase 19 capability limitation review required.",
                "guarantee": (
                    admission_override["guarantee"]
                    if admission_override
                    else production.get("guarantee")
                )
                or (
                    "No production guarantee until CP19-K per-KA proof and "
                    "CP19-M rebuilt-installed acceptance pass."
                ),
                "performance_budget_ms": (
                    admission_override["performance_budget_ms"]
                    if admission_override
                    else production.get("performance_budget_ms", 1000)
                ),
            },
            "admission": {
                "production_enabled": (
                    admission_override["production_enabled"]
                    if admission_override
                    else bool(production.get("production_enabled"))
                ),
                "classification": (
                    admission_override["classification"]
                    if admission_override
                    else production.get("classification")
                )
                or "implementation_required",
                "deterministic": (
                    admission_override["deterministic"]
                    if admission_override
                    else production.get("deterministic")
                ),
                "direct_execution": (
                    "canonical_selector_required"
                    if row["canonical_id"] != "KA-033"
                    else "reserved_disabled"
                ),
            },
            "integration": {
                "authority_version": integration_authority["authority_version"],
                "primary_owner": integration["primary_owner"],
                "consumer_paths": integration["consumer_paths"],
                "selector_policy": integration["selector_policy"],
                "required_or_optional": (
                    "conditional"
                    if pure_advisory_override
                    else integration["required_or_optional"]
                ),
                "stage": integration["stage"],
                "effect_port": (
                    None if pure_advisory_override else integration["effect_port"]
                ),
                "effect_transaction": (
                    "not_applicable_pure_or_advisory_result"
                    if pure_advisory_override
                    else integration["effect_transaction"]
                ),
                "qualification": integration["qualification"],
            },
            "migration_notes": row["migration_notes"],
        }

    return {
        "schema_version": "dle.ka-runtime-manifest.v1",
        "manifest_version": "2026.08.11-al10.2",
        "status": "cp19_j_product_workflow_authority",
        "authority": {
            "crosswalk": CROSSWALK_PATH.relative_to(ROOT).as_posix(),
            "crosswalk_schema_version": crosswalk["schema_version"],
            "crosswalk_source_input_sha256": crosswalk["source_input_sha256"],
            "integration_authority": INTEGRATION_AUTHORITY_PATH.relative_to(
                ROOT
            ).as_posix(),
            "integration_authority_version": integration_authority["authority_version"],
            "contract_metadata_policy": CONTRACT_METADATA_POLICY,
            "duplicate_policy": "one_semantic_capability_one_canonical_id",
            "dependency_result_contract": ("dle.ka-execution-result.v1#output"),
            "dependency_input_field": "dependency_results",
            "dependency_overrides": {
                **CP19_C_DEPENDENCY_OVERRIDES,
                **CP19_E_DEPENDENCY_OVERRIDES,
                **CP19_F_DEPENDENCY_OVERRIDES,
                **CP19_G_DEPENDENCY_OVERRIDES,
                **CP19_H_DEPENDENCY_OVERRIDES,
                **CP19_I_DEPENDENCY_OVERRIDES,
                **CP19_K_DEPENDENCY_OVERRIDES,
            },
            "production_admission_checkpoint": "CP19-I",
            "production_admission_ids": sorted(
                CP19_E_LAYER_IDS
                | CP19_F_PERSONA_IDS
                | CP19_G_REFINEMENT_IDS
                | CP19_H_OWNER_IDS
                | CP19_I_OWNER_IDS
                | CP19_I_ADDITIONAL_ADMISSION_IDS
                | CP19_K_ADMISSION_IDS
            ),
            "refinement_workflow": {
                "schema_version": "dle.refinement-workflow-registry.v1",
                "registry_version": "2026.07.25-cp19g.1",
                "owner": "governed_execution_orchestrator",
                "entry_condition": "committed_l9_refine_decision",
                "max_provider_rewrites": 1,
                "provider_subcalls_from_steps": 0,
                "effect_application_authorized": False,
                "steps": CP19_G_REFINEMENT_STEPS,
            },
            "subsystem_execution_registry": CP19_H_SUBSYSTEM_REGISTRY,
            "extended_subsystem_execution_registry": CP19_I_SUBSYSTEM_REGISTRY,
            "product_workflow": {
                "schema_version": "dle.ka-product-workflow.v1",
                "checkpoint": "CP19-J",
                "owner": "canonical_ka_product_service",
                "selector": "ManifestKASelector",
                "executor": "KAPlanExecutor",
                "controller": "CanonicalKAController",
                "durable_record": "ka_product_runs",
                "principal_owned": True,
                "encrypted_request_and_result": True,
                "idempotent_plan": True,
                "exact_plan_confirmation": True,
                "cooperative_cancellation": True,
                "cross_process_redis_lease": True,
                "stale_run_reconciliation": True,
                "effect_application_authorized": False,
                "scopes": [
                    "ka:read",
                    "ka:plan",
                    "ka:execute",
                    "ka:cancel",
                ],
                "evidence_surfaces": [
                    "history",
                    "result",
                    "trace",
                    "artifacts",
                    "effects",
                ],
            },
        },
        "capability_count": len(entries),
        "alias_index": {
            alias: canonical_id
            for alias, canonical_id in sorted(scoped_alias_index.items())
        },
        "entries": {key: entries[key] for key in sorted(entries)},
    }


def json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def typescript_text(payload: dict[str, Any]) -> str:
    return (
        "/* Generated by scripts/build_ka_runtime_manifest.py. Do not edit. */\n"
        'import type { KARuntimeManifestCatalog } from "./ka-types.js";\n\n'
        "export const KA_RUNTIME_MANIFEST: KARuntimeManifestCatalog = "
        f"{json.dumps(payload, indent=2, ensure_ascii=False)};\n"
    )


def write_or_check(path: Path, *, check: bool) -> int:
    payload = build_manifest()
    outputs = [(path, json_text(payload))]
    if path == DEFAULT_OUTPUT_PATH:
        outputs.extend(
            [
                (SDK_OUTPUT_PATH, json_text(payload)),
                (TYPESCRIPT_OUTPUT_PATH, typescript_text(payload)),
            ]
        )
    stale = []
    for output, content in outputs:
        existing = output.read_text(encoding="utf-8") if output.exists() else None
        if existing != content:
            stale.append(output)
            if not check:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(content, encoding="utf-8", newline="\n")
    if check and stale:
        for output in stale:
            print(f"STALE {output.relative_to(ROOT)}")
        return 1
    action = "verified" if check else "generated"
    print(
        f"KA runtime manifests {action}: "
        + ", ".join(output.relative_to(ROOT).as_posix() for output, _ in outputs)
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output
    if not output.is_absolute():
        output = ROOT / output
    return write_or_check(output.resolve(), check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
