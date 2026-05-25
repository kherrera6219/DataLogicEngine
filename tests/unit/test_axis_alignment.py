import uuid
import sys
from pathlib import Path

from backend.truth_engine.truth_core.engine import TruthCoreEngine
from core.axes.axis_system import AxisSystem
from core.coordinate_system import AxisCoordinate, CoordinateResolver, UnifiedCoordinate
from models import KnowledgeGraphNode, TraceRun

SDK_PATH = Path(__file__).resolve().parents[2] / "sdk" / "UKG_Python_SDK"
if str(SDK_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PATH))

from ukg_sdk.coordinates17 import CoordinateResolver17  # noqa: E402


def test_axis_14_to_17_names_are_canonical():
    assert UnifiedCoordinate.AXIS_NAMES[14] == "Acquisition Lifecycle"
    assert UnifiedCoordinate.AXIS_NAMES[15] == "Risk & Threat Context"
    assert UnifiedCoordinate.AXIS_NAMES[16] == "Ethics, Trust & Criticality"
    assert UnifiedCoordinate.AXIS_NAMES[17] == "FROST-Mode Selector"

    axis_system = AxisSystem()
    assert axis_system.axes[14]["name"] == "Acquisition Lifecycle"
    assert axis_system.axes[15]["name"] == "Risk & Threat Context"
    assert axis_system.axes[16]["name"] == "Ethics, Trust & Criticality"
    assert axis_system.axes[17]["name"] == "FROST-Mode Selector"


def test_axis_managers_resolve_canonical_phase_b_contexts():
    axis_system = AxisSystem()

    axis14 = axis_system.axis_managers[14].resolve_context("FAR RFP CLIN solicitation")
    assert axis14["stage_code"] == "AL2"
    assert "KA-024" in axis14["ka_hooks"]
    assert "KA-029" in axis14["ka_hooks"]

    axis15 = axis_system.axis_managers[15].resolve_context("security compliance audit risk")
    assert set(axis15["dimensions"]) == {
        "technical",
        "security",
        "compliance",
        "financial",
        "schedule",
        "reputational",
    }
    assert axis15["composite_score"] > 0

    axis16 = axis_system.axis_managers[16].resolve_context("critical regulated patient workflow")
    assert axis16["criticality"] == "CRITICAL"
    assert axis16["requires_human_review"] is True

    axis17 = axis_system.axis_managers[17].resolve_context({"tier": "high_stakes"})
    assert axis17["frost_layer_depth"] == 7
    assert axis17["truth_engine_mode"] == "regulatory_strict"


def test_coordinate_resolver_uses_canonical_axis_contexts():
    resolver = CoordinateResolver()

    axis14 = resolver.resolve_axis(AxisCoordinate(14, "2.1"))
    assert axis14["acquisition_lifecycle_context"]["lifecycle_stage"] == "solicitation"

    axis15 = resolver.resolve_axis(AxisCoordinate(15, "70.2"))
    assert axis15["risk_threat_context"]["dominant_dimension"] == "security"

    axis16 = resolver.resolve_axis(AxisCoordinate(16, "4.2"))
    assert axis16["ethics_trust_context"]["criticality"] == "CRITICAL"

    axis17 = resolver.resolve_axis(AxisCoordinate(17, "3"))
    assert axis17["frost_mode_context"]["frost_layer_depth"] == 7
    assert axis17["frost_mode_context"]["truth_engine_mode"] == "regulatory_strict"


def test_truthcore_accepts_axis17_frost_mode_bridge():
    engine = TruthCoreEngine()
    steps = engine.get_workflow_steps(
        "moderate",
        axis17_context={"truth_engine_mode": "regulatory_strict", "frost_layer_depth": 7},
    )

    assert "trust_validation" in steps
    assert "meta_reasoning" in steps


def test_sdk_coordinate_resolver_uses_bundled_offline_taxonomy():
    coord = CoordinateResolver17().resolve(
        "Review FAR solicitation compliance audit risk for healthcare patient data"
    )
    data = coord.to_dict()

    assert data["axis_1"] == "compliance"
    assert data["axis_2"] in {"government_acquisition", "healthcare"}
    assert data["axis_14"] == "AL2"
    assert data["axis_15"] == "risk_0.70"
    assert data["axis_16"] == "CRITICAL"
    assert data["axis_17"] == "high_stakes"
    assert {14, 15, 16, 17}.issubset(set(data["active_axes"]))


def test_legacy_axis_concepts_are_node_metadata_and_trace_has_frost_fields():
    node = KnowledgeGraphNode(node_id="node-test")
    node.set_axis_legacy_metadata(
        provenance="fed_register",
        object_type="regulation",
        validation_state="certified",
        security_classification="public",
    )

    assert node.node_metadata["legacy_axis_metadata"] == {
        "provenance": "fed_register",
        "object_type": "regulation",
        "validation_state": "certified",
        "security_classification": "public",
    }

    run = TraceRun(
        run_id=uuid.uuid4(),
        frost_depth=7,
        truth_engine_mode="regulatory_strict",
    )
    audit_bundle = run.to_dict()["audit_bundle"]
    assert audit_bundle["frost_depth"] == 7
    assert audit_bundle["truth_engine_mode"] == "regulatory_strict"
