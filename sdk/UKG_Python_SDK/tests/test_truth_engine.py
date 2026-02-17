
from ukg_sdk.truth_engine.core import TruthEngine

class TestTruthEngine:
    def test_initialization(self):
        import inspect
        print(f"TruthEngine: {TruthEngine}")
        print(f"Sig: {inspect.signature(TruthEngine)}")
        engine = TruthEngine()

    def test_evaluate_basic(self):
        engine = TruthEngine()
        result = engine.evaluate("Is this a test?")
        assert result.ok is True
        assert result.verdict == "pass"
        assert result.confidence >= 0.0 # Default confidence might be 0.0 for stub

    def test_evaluate_veto(self):
        # Mock truthgate to veto
        engine = TruthEngine()
        
        # We can't easily mock inner components without dependency injection or patching
        # But TruthEngine allows injection in init
        
        class VetoGate:
            def create_request(self, query, context=None):
                return {"query": query, "context": context}
            
            def select_tier(self, request):
                return "T0"
                
            def check(self, claim, context):
                return {"veto": True, "confidence": 1.0}

        engine.truthgate = VetoGate()
        result = engine.evaluate("Bad query")
        assert result.ok is False
        assert result.verdict == "veto"
