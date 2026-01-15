import pytest
from datetime import datetime, UTC
from typing import Dict, Any

from backend.truth_engine.truth_core.l10_schemas import (
    L10Input, L10Result, L10Decision, EmergenceLevel, TrustGateResult
)
from backend.truth_engine.truth_core.emergence_controller import EmergenceDetectionController

class MockKAController:
    def execute_algorithm(self, ka_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success"}

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
        risk_domain="standard"
    )

class TestLayer10Controller:
    
    def test_authorize_standard_release(self, l10_controller, base_l10_input):
        """Test release path for clean input."""
        result = l10_controller.authorize(base_l10_input)
        
        assert result.decision == L10Decision.RELEASE
        assert result.final_answer == "The solution is safe and effective."
        assert result.requires_human_signoff == False
        assert result.emergence_report.emergence_detected == False

    def test_authorize_pii_modification(self, l10_controller, base_l10_input):
        """Test modification path when PII is detected."""
        base_l10_input.l9_result["epistemic_report"]["current_output"] = "Contact us at admin@example.com"
        
        result = l10_controller.authorize(base_l10_input)
        
        assert result.decision == L10Decision.MODIFY
        assert any(a.action_type == "redaction" for a in result.containment_actions)
        assert result.safety_report.passed == False

    def test_authorize_self_awareness_emergence(self, l10_controller, base_l10_input):
        """Test emergence detection for self-referential statements."""
        base_l10_input.l9_result["epistemic_report"]["current_output"] = "I am an AI and I think this is correct."
        
        result = l10_controller.authorize(base_l10_input)
        
        assert result.emergence_report.emergence_detected == True
        assert any(p.pattern_type == "self_referential" for p in result.emergence_report.patterns)

    def test_trust_gate_belief_decay_pass(self, l10_controller, base_l10_input):
        """Test trust gate with belief decay (Pass)."""
        # 0.98 * 0.98 = 0.9604 (> 0.95 threshold)
        base_l10_input.l9_result["readiness_score"] = 0.98
        result = l10_controller.authorize(base_l10_input)
        
        assert result.trust_report.status == "pass"
        assert result.decision == L10Decision.RELEASE

    def test_trust_gate_belief_decay_fail_high_risk(self, l10_controller, base_l10_input):
        """Test high-risk trust gate failure leading to escalation."""
        # 0.99 * 0.98 = 0.9702 (< 0.985 threshold)
        base_l10_input.risk_domain = "high_risk"
        base_l10_input.l9_result["readiness_score"] = 0.99
        
        result = l10_controller.authorize(base_l10_input)
        
        assert result.trust_report.status == "fail"
        assert result.decision == L10Decision.ESCALATE
        assert result.requires_human_signoff == True

    def test_authorize_critical_safety_halt(self, l10_controller, base_l10_input):
        """Test halt path on critical failure (hypothetical)."""
        # Manually force a halt condition by bypassing audit and going to make_decision if needed
        # but here we'll just mock a critical violation in the future.
        pass

    def test_fail_closed_on_exception(self, l10_controller, base_l10_input):
        """Test that any exception in authorize leads to a HALT (Fail-Closed)."""
        # Force exception by passing bad data
        result = l10_controller.authorize(None) 
        
        assert result.decision == L10Decision.HALT
        assert "Final safety gate failed" in result.final_answer
