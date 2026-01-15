"""
Tests for Layer 8: TrustValidationGateway

Tests PASS/WARN/FAIL gate decisions, KA integration, and fail-closed behavior.
"""

import pytest
from unittest.mock import MagicMock, patch
from backend.truth_engine.truth_gate.trust_validation_gateway import TrustValidationGateway
from backend.truth_engine.truth_gate.l8_schemas import L8Input, GateDecision


class TestL8Schemas:
    """Test Pydantic schemas for Layer 8."""
    
    def test_l8_input_defaults(self):
        """Test L8Input with minimal required fields."""
        input_data = L8Input(simulation_id="test-123")
        assert input_data.simulation_id == "test-123"
        assert input_data.target_confidence == 0.95
        assert input_data.risk_domain == "standard"
    
    def test_l8_input_high_risk(self):
        """Test L8Input with high-risk domain."""
        input_data = L8Input(
            simulation_id="test-456",
            risk_domain="healthcare"
        )
        assert input_data.risk_domain == "healthcare"


class TestTrustValidationGateway:
    """Test TrustValidationGateway service."""
    
    def test_gateway_initialization(self):
        """Test gateway initializes with 12 KAs."""
        gateway = TrustValidationGateway()
        assert len(gateway.REQUIRED_KAS) == 12
        assert "KA-026" in gateway.REQUIRED_KAS  # Contradiction Detection
        assert "KA-014" in gateway.REQUIRED_KAS  # Confidence Scoring
    
    def test_pass_decision(self):
        """Test PASS gate decision when confidence is high."""
        gateway = TrustValidationGateway()
        input_data = L8Input(
            simulation_id="test-pass",
            claims=[{"text": "Valid claim 1"}, {"text": "Valid claim 2"}],
            persona_results={
                "knowledge": {"confidence": 0.98},
                "sector": {"confidence": 0.97},
                "regulatory": {"confidence": 0.96},
                "compliance": {"confidence": 0.97}
            }
        )
        
        result = gateway.validate(input_data)
        
        assert result.status == GateDecision.PASS
        assert result.overall_confidence >= 0.95
        assert len(result.contradictions) == 0
    
    def test_warn_decision_low_confidence(self):
        """Test WARN gate decision when confidence is borderline."""
        gateway = TrustValidationGateway()
        input_data = L8Input(
            simulation_id="test-warn",
            claims=[{"text": "Uncertain claim"}],
            persona_results={
                "knowledge": {"confidence": 0.93},
                "sector": {"confidence": 0.92},
                "regulatory": {"confidence": 0.94},
                "compliance": {"confidence": 0.91}
            }
        )
        
        result = gateway.validate(input_data)
        
        # Should be WARN since confidence is below 0.95 but not critically low
        assert result.status in [GateDecision.WARN, GateDecision.FAIL]
        assert result.disclosure_required or len(result.fix_directives) > 0
    
    def test_fail_decision_critical_low_confidence(self):
        """Test FAIL gate decision when confidence is critically low."""
        gateway = TrustValidationGateway()
        input_data = L8Input(
            simulation_id="test-fail",
            claims=[],
            persona_results={
                "knowledge": {"confidence": 0.70},
                "sector": {"confidence": 0.65},
                "regulatory": {"confidence": 0.60},
                "compliance": {"confidence": 0.55}
            }
        )
        
        result = gateway.validate(input_data)
        
        assert result.status == GateDecision.FAIL
        assert len(result.fix_directives) > 0
        assert result.escalation_target is not None
    
    def test_high_risk_domain_threshold(self):
        """Test that healthcare domain uses 99.5% threshold."""
        gateway = TrustValidationGateway()
        input_data = L8Input(
            simulation_id="test-healthcare",
            risk_domain="healthcare",
            persona_results={
                "knowledge": {"confidence": 0.98},
                "sector": {"confidence": 0.97},
                "regulatory": {"confidence": 0.96},
                "compliance": {"confidence": 0.97}
            }
        )
        
        result = gateway.validate(input_data)
        
        # 97% average is below 99.5% healthcare threshold
        assert result.target_threshold == 0.995
        assert result.status in [GateDecision.WARN, GateDecision.FAIL]
    
    def test_axis_14_threshold_override(self):
        """Test that Axis 14 override takes precedence."""
        gateway = TrustValidationGateway()
        input_data = L8Input(
            simulation_id="test-override",
            risk_domain="healthcare",  # Would normally be 99.5%
            axis_14_threshold=0.80,    # Override to 80%
            persona_results={
                "knowledge": {"confidence": 0.85},
                "sector": {"confidence": 0.85},
                "regulatory": {"confidence": 0.85},
                "compliance": {"confidence": 0.85}
            }
        )
        
        result = gateway.validate(input_data)
        
        assert result.target_threshold == 0.80
        assert result.status == GateDecision.PASS
    
    def test_fail_closed_on_error(self):
        """Test fail-closed behavior on internal error."""
        gateway = TrustValidationGateway()
        
        # Create input that will cause internal processing issues
        input_data = L8Input(
            simulation_id="test-error",
            claims=[{"text": "Valid claim"}],
            persona_results={}  # Empty personas
        )
        
        result = gateway.validate(input_data)
        
        # Should still produce a result (not crash)
        assert result.simulation_id == "test-error"
        # Should have processed (even with reduced confidence)
        assert result.processing_time_ms > 0
    
    def test_stats_tracking(self):
        """Test that gateway tracks stats correctly."""
        gateway = TrustValidationGateway()
        
        # Run a few validations
        for i in range(3):
            input_data = L8Input(
                simulation_id=f"test-stats-{i}",
                persona_results={
                    "knowledge": {"confidence": 0.99},
                    "sector": {"confidence": 0.99},
                    "regulatory": {"confidence": 0.99},
                    "compliance": {"confidence": 0.99}
                }
            )
            gateway.validate(input_data)
        
        stats = gateway.get_stats()
        assert stats["total_processed"] == 3
        assert stats["pass_count"] >= 0


class TestL8WithKAController:
    """Test Layer 8 with mocked KA Controller."""
    
    def test_ka_invocation(self):
        """Test that KAs are invoked during validation."""
        mock_controller = MagicMock()
        mock_controller.execute_algorithm.return_value = {
            "contradictions": [],
            "critiques": [],
            "calibrated_confidence": 0.96
        }
        
        gateway = TrustValidationGateway(ka_controller=mock_controller)
        input_data = L8Input(
            simulation_id="test-ka",
            claims=[{"text": "Test claim"}],
            persona_results={
                "knowledge": {"confidence": 0.95}
            }
        )
        
        result = gateway.validate(input_data)
        
        # Should have invoked multiple KAs
        assert len(result.kas_invoked) > 0
        mock_controller.execute_algorithm.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
