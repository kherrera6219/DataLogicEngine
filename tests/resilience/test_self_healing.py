import pytest
from backend.knowledge_algorithms.ka_119_predictive_health import KA119PredictiveHealth
from backend.core.resilience_router import ResilienceRouter

class TestResilience:
    
    def test_ka119_prediction(self):
        """Verify KA-119 predicts trend correctly."""
        agent = KA119PredictiveHealth()
        # Rising trend: 100, 110, 120 -> Preidct 130
        history = [100.0, 110.0, 120.0] 
        
        result = agent.run({
            "data": {
                "metric_name": "latency",
                "history": history,
                "threshold": 125.0
            }
        })
        
        print(f"DEBUG KA OUTPUT: {result}")
        assert result["success"] is True
        output = result["output"]
        assert output["predicted_next_value"] == 130.0
        assert output["risk_level"] == "CRITICAL"
        assert output["recommended_action"] == "THROTTLE"

    def test_resilience_router_fallback(self):
        """Verify router falls back to safe function on error."""
        router = ResilienceRouter()
        
        def failing_function(context):
            raise ValueError("Complex Logic Failed")
            
        def fallback_function(context):
            return {"status": "success", "data": "Simple Result"}
            
        result = router.execute_with_fallback(
            failing_function,
            fallback_function,
            {"request_id": "test-1"}
        )
        
        # Should succeed via fallback
        assert result["status"] == "success"
        assert result["data"] == "Simple Result"
        assert result["meta"]["execution_mode"] == "DEGRADED"
        assert result["meta"]["fallback_reason"] == "Complex Logic Failed"

    def test_resilience_router_optimal(self):
        """Verify router uses primary function when healthy."""
        router = ResilienceRouter()
        
        def primary_function(context):
            return {"status": "success", "data": "Complex Result"}
            
        def fallback_function(context):
            return {"status": "success", "data": "Simple Result"}
            
        result = router.execute_with_fallback(
            primary_function,
            fallback_function,
            {"request_id": "test-2"}
        )
        
        assert result["data"] == "Complex Result"
        assert result["meta"]["execution_mode"] == "OPTIMAL"
