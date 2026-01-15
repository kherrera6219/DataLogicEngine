import pytest
from backend.truth_engine.truth_gate.quant import QuantValidationService
from backend.truth_engine.truth_gate.schemas import QuantBundle
from backend.truth_engine.truth_core.engine import TruthCoreEngine

class TestLayer6QuantValidation:
    
    def test_logical_backend_entropy(self):
        """Verify text-based entropy scoring (vague words reduce confidence)."""
        service = QuantValidationService()
        
        strong_claim = "The projected revenue is 5 million dollars."
        weak_claim = "Maybe the revenue could possibly be around 5 million."
        
        # Test Strong
        res_strong = service.validate("draft", [strong_claim])
        conf_strong = res_strong.confidence_map["claim_0"]
        assert conf_strong > 0.9, "Strong claim should have high confidence"
        
        # Test Weak
        res_weak = service.validate("draft", [weak_claim])
        conf_weak = res_weak.confidence_map["claim_0"]
        assert conf_weak < 0.8, "Weak claim should have low confidence (penalty applied)"
        
    def test_statistical_backend_anomaly(self):
        """
        Verify robust Median-Absolute-Deviation (MAD) anomaly detection.
        MAD is better than 3-sigma for outliers.
        """
        service = QuantValidationService()
        
        # Data with some variance (Median=10)
        # 10, 11, 9, 10, 10, 12 => Median 10. MAD approx 1.
        # Outlier 1000 => |1000-10| / 1 = 990 >> 3.5 threshold
        data = {
            "tables": {
                "financials": [
                    {"val": 10}, {"val": 12}, {"val": 11}, {"val": 9}, {"val": 10},
                    {"val": 1000} # MASSIVE OUTLIER
                ]
            }
        }
        
        res = service.validate("draft", [], data_context=data)
        
        assert len(res.anomalies) > 0, "Should detect outlier using MAD"
        assert "Statistical Anomaly" in res.anomalies[0]
        assert "1000" in res.anomalies[0]
        
    def test_schema_validation(self):
        """Verify Pydantic schema enforcement."""
        service = QuantValidationService()
        
        # Empty draft should trigger schema error/flag
        res = service.validate(" ", ["claim"])
        
        assert res.is_valid is False
        assert any("Input Schema Error" in flag for flag in res.validation_flags)
        
    def test_engine_integration(self):
        """Verify TruthCore initializes Layer 6."""
        engine = TruthCoreEngine()
        assert engine.quant_service is not None
        assert "quant_validation" in engine.REFINEMENT_STEPS
