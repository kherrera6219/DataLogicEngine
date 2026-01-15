"""
Unit tests for Layer 9 MetaReasoningController.

Tests cover:
- L9 schemas (L9Input, L9Result)
- Gate decisions (FINALIZE, REFINE)
- KA invocation
- Iteration limits
- Belief drift detection
- Persona agreement auditing
"""

import pytest
from unittest.mock import Mock, patch


class TestL9Schemas:
    """Test Layer 9 Pydantic schemas."""
    
    def test_l9_input_defaults(self):
        """Test L9Input with default values."""
        from backend.truth_engine.truth_core.l9_schemas import L9Input
        
        input_data = L9Input(
            simulation_id="test-123",
            l8_gate_result={"status": "PASS", "overall_confidence": 0.95}
        )
        
        assert input_data.simulation_id == "test-123"
        assert input_data.risk_domain == "standard"
        assert input_data.iteration_state["current_iteration"] == 1
        assert input_data.iteration_state["max_iterations"] == 5
    
    def test_l9_input_high_risk(self):
        """Test L9Input with high-risk domain."""
        from backend.truth_engine.truth_core.l9_schemas import L9Input
        
        input_data = L9Input(
            simulation_id="test-456",
            l8_gate_result={"status": "WARN"},
            risk_domain="healthcare"
        )
        
        assert input_data.risk_domain == "healthcare"
    
    def test_l9_decision_enum(self):
        """Test L9Decision enum."""
        from backend.truth_engine.truth_core.l9_schemas import L9Decision
        
        assert L9Decision.FINALIZE.value == "FINALIZE"
        assert L9Decision.REFINE.value == "REFINE"
    
    def test_refinement_plan(self):
        """Test RefinementPlan schema."""
        from backend.truth_engine.truth_core.l9_schemas import (
            RefinementPlan, RefinementDirective
        )
        
        plan = RefinementPlan(
            target_layer=5,
            preserve_layers=[1, 2, 3, 4],
            rerun_layers=[5, 6, 7, 8],
            directives=RefinementDirective(
                focus="compliance_detail",
                required_changes=["Add HIPAA mapping"]
            ),
            iteration_count=2
        )
        
        assert plan.target_layer == 5
        assert plan.iteration_count == 2
        assert len(plan.preserve_layers) == 4


class TestMetaReasoningController:
    """Test MetaReasoningController service."""
    
    def test_controller_initialization(self):
        """Test controller initializes correctly."""
        from backend.truth_engine.truth_core.meta_reasoning_controller import (
            MetaReasoningController
        )
        
        controller = MetaReasoningController()
        
        assert controller.max_iterations == 5
        assert controller.total_processed == 0
        assert controller.ka_controller is None
    
    def test_finalize_decision_high_confidence(self):
        """Test FINALIZE decision on high confidence input."""
        from backend.truth_engine.truth_core.meta_reasoning_controller import (
            MetaReasoningController
        )
        from backend.truth_engine.truth_core.l9_schemas import L9Input, L9Decision
        
        controller = MetaReasoningController()
        
        input_data = L9Input(
            simulation_id="test-finalize",
            l8_gate_result={
                "status": "PASS",
                "overall_confidence": 0.99,
                "domain_confidences": [
                    {"domain": "knowledge", "confidence": 0.99},
                    {"domain": "compliance", "confidence": 0.98}
                ]
            }
        )
        
        result = controller.evaluate(input_data)
        
        assert result.decision == L9Decision.FINALIZE
        assert result.readiness_score >= 0.95
        assert result.epistemic_report is not None
    
    def test_refine_decision_low_confidence(self):
        """Test REFINE decision on low confidence input."""
        from backend.truth_engine.truth_core.meta_reasoning_controller import (
            MetaReasoningController
        )
        from backend.truth_engine.truth_core.l9_schemas import L9Input, L9Decision
        
        controller = MetaReasoningController()
        
        input_data = L9Input(
            simulation_id="test-refine",
            l8_gate_result={
                "status": "WARN",
                "overall_confidence": 0.7,
                "domain_confidences": [
                    {"domain": "knowledge", "confidence": 0.7},
                    {"domain": "compliance", "confidence": 0.6}
                ]
            }
        )
        
        result = controller.evaluate(input_data)
        
        assert result.decision == L9Decision.REFINE
        assert result.readiness_score < 0.95
        assert result.refinement_plan is not None
    
    def test_max_iterations_force_finalize(self):
        """Test max iterations forces FINALIZE."""
        from backend.truth_engine.truth_core.meta_reasoning_controller import (
            MetaReasoningController
        )
        from backend.truth_engine.truth_core.l9_schemas import L9Input, L9Decision
        
        controller = MetaReasoningController()
        
        input_data = L9Input(
            simulation_id="test-max-iter",
            l8_gate_result={"overall_confidence": 0.8},
            iteration_state={
                "current_iteration": 5,
                "max_iterations": 5
            }
        )
        
        result = controller.evaluate(input_data)
        
        assert result.decision == L9Decision.FINALIZE
        assert any("Max iterations" in flag for flag in result.disclosure_flags)
    
    def test_high_risk_domain_threshold(self):
        """Test high-risk domain uses stricter threshold."""
        from backend.truth_engine.truth_core.meta_reasoning_controller import (
            MetaReasoningController
        )
        from backend.truth_engine.truth_core.l9_schemas import L9Input, L9Decision
        
        controller = MetaReasoningController()
        
        # 0.96 confidence - passes standard but fails high-risk
        input_data = L9Input(
            simulation_id="test-high-risk",
            l8_gate_result={
                "overall_confidence": 0.96,
                "domain_confidences": [
                    {"domain": "knowledge", "confidence": 0.96}
                ]
            },
            risk_domain="healthcare"
        )
        
        result = controller.evaluate(input_data)
        
        # Should REFINE because 0.96 < 0.99 threshold for high-risk
        assert result.decision == L9Decision.REFINE
    
    def test_stats_tracking(self):
        """Test controller tracks statistics."""
        from backend.truth_engine.truth_core.meta_reasoning_controller import (
            MetaReasoningController
        )
        from backend.truth_engine.truth_core.l9_schemas import L9Input
        
        controller = MetaReasoningController()
        
        input_data = L9Input(
            simulation_id="test-stats",
            l8_gate_result={"overall_confidence": 0.99}
        )
        
        controller.evaluate(input_data)
        
        stats = controller.get_stats()
        assert stats["total_processed"] == 1


class TestL9KAs:
    """Test Layer 9 KAs."""
    
    def test_trace_analyzer_ka(self):
        """Test L9-KA-001 Trace Analyzer."""
        from knowledge_algorithms.l9.l9_ka_001_trace_analyzer import TraceAnalyzerKA
        
        ka = TraceAnalyzerKA()
        
        result = ka.execute({
            "trace": {
                "layer1": {"output": "parsed"},
                "layer2": {"output": "retrieved"},
                "layer3": {"output": "agents"}
            },
            "layers": [1, 2, 3]
        })
        
        assert "integrity_score" in result
        assert "issues" in result
        assert result["layers_analyzed"] == 3
    
    def test_belief_drift_ka(self):
        """Test L9-KA-002 Belief Drift Detector."""
        from knowledge_algorithms.l9.l9_ka_002_belief_drift import BeliefDriftDetectorKA
        
        ka = BeliefDriftDetectorKA()
        
        # Test numerical drift
        result = ka.execute({
            "original_query": "Reduce antibiotics by 20%",
            "final_solution": "Implement 40% reduction plan"
        })
        
        assert "drift_detected" in result
        assert "drift_score" in result
    
    def test_recursion_trigger_ka(self):
        """Test L9-KA-005 Recursion Trigger."""
        from knowledge_algorithms.l9.l9_ka_005_recursion_trigger import RecursionTriggerKA
        
        ka = RecursionTriggerKA()
        
        result = ka.execute({
            "readiness": 0.8,
            "issues": []
        })
        
        assert result["trigger_refinement"] == True
        assert "target_layer" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
