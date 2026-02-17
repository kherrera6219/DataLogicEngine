import pytest
from typing import Dict, Any

from backend.truth_engine.truth_core.l10_schemas import (
    L10Input, L10Decision, EmergenceLevel
)
from backend.truth_engine.truth_core.emergence_controller import EmergenceDetectionController

class MockKAController:
    def execute_algorithm(self, ka_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        content = str(inputs.get("content", ""))
        
        # Lane A: Emergence
        if ka_id == "KA-021" and "emergent" in content:
            return {"emergence_detected": True}
        if ka_id == "KA-108" and "bypass" in content:
            return {"escalation_detected": True}
        
        # Lane A: Safety
        if ka_id == "KA-059" and "@" in content:
            return {"passed": False, "flag": "PII_found"}
        if ka_id == "L10-KA-004" and "unethical" in content:
            return {"violations": [{"type": "ethical_breach", "severity": "major", "message": "Unethical content detected"}]}
            
        # Lane B: Commit
        if ka_id == "KA-109":
            return {"class": "PUBLIC"}
        if ka_id == "KA-079":
            return {"authorized": True}
            
        return {"status": "success", "passed": True}

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
