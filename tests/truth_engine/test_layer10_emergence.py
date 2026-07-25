from typing import Any

import pytest

from backend.knowledge_algorithms.contracts import (
    KAExecutionResult,
    KAExecutionState,
    KAOutcomeType,
)
from backend.truth_engine.truth_core.emergence_controller import (
    EmergenceDetectionController,
)
from backend.truth_engine.truth_core.l10_schemas import (
    EmergenceLevel,
    L10Decision,
    L10Input,
)


def _typed_result(ka_id: str, output: dict[str, Any]) -> KAExecutionResult:
    return KAExecutionResult(
        canonical_id=ka_id,
        ka_version="1.0.0",
        manifest_version="test",
        state=KAExecutionState.SUCCEEDED,
        outcome_type=KAOutcomeType.VALUE,
        success=True,
        output=output,
        request_id="request-test",
        run_id="run-test",
        trace_id=f"trace-{ka_id}",
    )


class MockKAController:
    def execute_typed(
        self,
        ka_id: str,
        inputs: dict[str, Any],
    ) -> KAExecutionResult:
        content = str(inputs.get("content", ""))

        # Lane A: Emergence
        if ka_id == "KA-021":
            return _typed_result(
                ka_id,
                {"is_emergent": "emergent" in content},
            )
        if ka_id == "KA-108":
            return _typed_result(
                ka_id,
                {"escalation_detected": "bypass" in content},
            )

        # Lane A: Safety
        if ka_id in {"KA-058", "KA-059"}:
            pii_found = ka_id == "KA-059" and "@" in content
            return _typed_result(
                ka_id,
                {
                    "passed": not pii_found,
                    "flag": "PII_found" if pii_found else None,
                },
            )
        if ka_id == "L10-KA-001":
            return _typed_result(ka_id, {"entropy_score": 0.2})
        if ka_id == "L10-KA-002":
            return _typed_result(ka_id, {"awareness_detected": False})
        if ka_id == "L10-KA-004":
            violations = (
                [
                    {
                        "type": "ethical_breach",
                        "severity": "major",
                        "message": "Unethical content detected",
                    }
                ]
                if "unethical" in content
                else []
            )
            return _typed_result(ka_id, {"violations": violations})

        # Lane B: Commit
        if ka_id == "KA-109":
            return _typed_result(ka_id, {"class": "PUBLIC"})
        if ka_id == "KA-079":
            return _typed_result(ka_id, {"authorized": True})

        return _typed_result(ka_id, {"status": "success", "passed": True})

@pytest.fixture
def l10_controller():
    return EmergenceDetectionController(ka_controller=MockKAController())

@pytest.fixture
def base_l10_input():
    return L10Input(
        simulation_id="test-sim-123",
        l9_result={
            "readiness_score": 0.98,
            "epistemic_report": {
                "current_output": "The solution is safe and effective.",
                "review_conducted": "full_meta_analysis"
            }
        },
        risk_domain="standard",
        reasoning_trace={"steps": ["L1", "L2", "L3"]}
    )

class TestLayer10Controller:
    
    def test_authorize_standard_release(self, l10_controller, base_l10_input):
        """Test release path for clean input."""
        result = l10_controller.authorize(base_l10_input)
        
        assert result.decision == L10Decision.RELEASE
        assert result.final_answer == "The solution is safe and effective."
        assert not result.requires_human_signoff
        assert not result.emergence_report.emergence_detected
        assert "KA-109" in result.kas_invoked  # Lane B triggered

    def test_authorize_pii_modification(self, l10_controller, base_l10_input):
        """Test modification path when PII is detected (KA-059)."""
        base_l10_input.l9_result["epistemic_report"]["current_output"] = "Contact us at admin@example.com"
        
        result = l10_controller.authorize(base_l10_input)
        
        assert result.decision == L10Decision.MODIFY
        assert "[REDACTED EMAIL]" in result.final_answer
        assert any(a.action_type == "redact" for a in result.containment_actions)

    def test_authorize_emergence_flagged(self, l10_controller, base_l10_input):
        """Test emergence detection via KA-021."""
        base_l10_input.l9_result["epistemic_report"]["current_output"] = "This is an emergent pattern."
        
        result = l10_controller.authorize(base_l10_input)
        
        assert result.emergence_report.emergence_detected
        assert result.emergence_report.overall_level == EmergenceLevel.MODERATE

    def test_trust_gate_belief_decay_pass(self, l10_controller, base_l10_input):
        """Test trust gate with 98% belief decay (Pass)."""
        # 0.98 * 0.98 = 0.9604 (> 0.95 threshold)
        base_l10_input.l9_result["readiness_score"] = 0.98
        result = l10_controller.authorize(base_l10_input)
        
        assert result.trust_report.status == "pass"
        assert result.decision == L10Decision.RELEASE

    def test_trust_gate_belief_decay_fail_high_risk(self, l10_controller, base_l10_input):
        """Test high-risk trust gate failure leading to escalation (KA-095)."""
        # 0.99 * 0.98 = 0.9702 (< 0.985 threshold)
        base_l10_input.risk_domain = "high_risk"
        base_l10_input.l9_result["readiness_score"] = 0.99
        
        result = l10_controller.authorize(base_l10_input)
        
        assert result.trust_report.status == "fail"
        assert result.decision == L10Decision.ESCALATE
        assert result.requires_human_signoff
        assert "KA-095" in result.kas_invoked

    def test_fail_closed_on_exception(self, l10_controller, base_l10_input):
        """Test that any exception in authorize leads to a HALT (Fail-Closed)."""
        result = l10_controller.authorize(None) 
        
        assert result.decision == L10Decision.HALT
        assert "Final safety gate failed" in result.final_answer

    def test_lane_b_knowledge_commit_authorization(self, l10_controller, base_l10_input):
        """Verify Lane B KAs are invoked during successful release."""
        result = l10_controller.authorize(base_l10_input)
        
        assert "KA-109" in result.kas_invoked
        assert "KA-079" in result.kas_invoked
        # Decision was RELEASE, so Lane B logic executed

    def test_lane_b_persists_authorized_knowledge_to_graphs(self, monkeypatch, base_l10_input):
        """Verify Lane B writes authorized knowledge into NetworkX and Neo4j helpers."""
        from backend.storage.uskd_memory_graph import UskdMemoryGraph

        memory_graph = UskdMemoryGraph()
        merged_nodes = []
        merged_relationships = []

        class FakeGraphStore:
            @staticmethod
            def merge_knowledge_node(properties):
                merged_nodes.append(properties)
                return True

            @staticmethod
            def merge_relationship_by_uid(source_uid, target_uid, rel_type, props=None):
                merged_relationships.append((source_uid, target_uid, rel_type, props))
                return True

        monkeypatch.setattr("backend.storage.get_uskd_memory_graph", lambda: memory_graph)
        monkeypatch.setattr("backend.storage.get_graph_store", lambda: FakeGraphStore())

        base_l10_input.coordinate_vector = {"active_axes": [1], "1": {"uid": "pillar-1", "value": "PL01"}}
        memory_graph.add_pillar("pillar-1", code="PL01", name="Healthcare")
        controller = EmergenceDetectionController(ka_controller=MockKAController())

        result = controller.authorize(base_l10_input)

        assert result.decision == L10Decision.RELEASE
        assert merged_nodes[0]["node_type"] == "authorized_knowledge"
        assert merged_relationships[0][2] == "AUTHORIZED_KNOWLEDGE"
        matches = memory_graph.coordinate_nodes(axis_number=1, text="safe and effective")
        assert matches[0]["data"]["promotion_authorized"] is True
