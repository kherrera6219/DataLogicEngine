import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock core dependency BEFORE importing KA
mock_core = MagicMock()
sys.modules["core"] = mock_core
sys.modules["core.knowledge_algorithm"] = mock_core.knowledge_algorithm
sys.modules["core.knowledge_algorithm.ka_base"] = mock_core.knowledge_algorithm.ka_base
# Fake Base Class to avoid MagicMock inheritance issues
class FakeKnowledgeAlgorithm:
    def __init__(self, context, *args):
        self.context = context
        self.config = {}
    def log_execution_step(self, *args, **kwargs):
        pass

# Ensure KnowledgeAlgorithm base class exists and accepts init args
mock_core.knowledge_algorithm.ka_base.KnowledgeAlgorithm = FakeKnowledgeAlgorithm 

# Mock other common dependencies that might trigger import errors
sys.modules["extensions"] = MagicMock()
sys.modules["models"] = MagicMock()
sys.modules["flask_jwt_extended"] = MagicMock()
sys.modules["backend.auth"] = MagicMock() 

# Now import the KA under test
# We might need to handle if it was already imported badly
if 'backend.knowledge_algorithms.ka_50_knowledge_integrity_validator' in sys.modules:
    del sys.modules['backend.knowledge_algorithms.ka_50_knowledge_integrity_validator']

from backend.knowledge_algorithms.ka_50_knowledge_integrity_validator import KA050KnowledgeIntegrityValidator, KA050Input, run

class TestKA050EdgeCases:
    @pytest.fixture
    def empty_context(self):
        return {}

    def test_load_config_failure(self, empty_context):
        """Test graceful failure when config cannot be loaded."""
        with patch('backend.knowledge_algorithms.ka_50_knowledge_integrity_validator.os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=OSError("Read error")):
            
            algo = KA050KnowledgeIntegrityValidator(empty_context)
            assert algo.config == {}

    def test_dangling_edge_detection(self, empty_context):
        """Test detection of edges pointing to missing nodes."""
        algo = KA050KnowledgeIntegrityValidator(empty_context)
        input_data = KA050Input(snapshot={
            "nodes": [{"id": "n1", "confidence": 1.0}],
            "edges": [{"source": "n1", "target": "missing_node"}]
        })
        
        result = algo._run_logic(input_data)
        assert result["success"]
        assert result["status"] in ["FAILED", "QUARANTINED"]
        assert any(i["type"] == "DANGLING_EDGE" for i in result["integrity_report"])

    def test_low_confidence_detection(self, empty_context):
        """Test detection of low confidence nodes."""
        algo = KA050KnowledgeIntegrityValidator(empty_context)
        # Assuming default min_conf is 0.3
        input_data = KA050Input(snapshot={
            "nodes": [{"id": "weak_node", "confidence": 0.1}],
            "edges": []
        })
        
        result = algo._run_logic(input_data)
        assert any(i["type"] == "LOW_CONFIDENCE_NODE" for i in result["integrity_report"])

    def test_quarantine_logic(self, empty_context):
        """Test quarantine status based on config."""
        algo = KA050KnowledgeIntegrityValidator(empty_context)
        algo.config["quarantine_on_failure"] = True
        
        input_data = KA050Input(snapshot={
             "nodes": [{"id": "n1", "confidence": 0.1}], # Force failure
             "edges": []
        })
        
        result = algo._run_logic(input_data)
        assert result["status"] == "QUARANTINED"

        # Test valid case
        input_data_valid = KA050Input(snapshot={
             "nodes": [{"id": "n1", "confidence": 0.9}], 
             "edges": []
        })
        result_valid = algo._run_logic(input_data_valid)
        assert result_valid["status"] == "PASSED"

    def test_run_wrapper_exception(self, empty_context):
        """Test top-level run function captures exceptions."""
        with patch('backend.knowledge_algorithms.ka_50_knowledge_integrity_validator.KA050KnowledgeIntegrityValidator') as MockClass:
            MockClass.side_effect = Exception("Critical Init Failure")
            
            result = run(context=empty_context)
            assert result["success"] is False
            assert "Critical Init Failure" in result["error"]

    def test_load_config_missing(self, empty_context):
        """Test config loading when file does not exist."""
        with patch('backend.knowledge_algorithms.ka_50_knowledge_integrity_validator.os.path.exists', return_value=False):
            algo = KA050KnowledgeIntegrityValidator(empty_context)
            assert algo.config == {}

    def test_run_wrapper_success(self, empty_context):
        """Test top-level run function success path."""
        # We need to mock the instance method run, NOT the module-level run
        with patch('backend.knowledge_algorithms.ka_50_knowledge_integrity_validator.KA050KnowledgeIntegrityValidator') as MockClass:
            mock_instance = MockClass.return_value
            mock_instance.run.return_value = {"success": True}
            
            result = run(context=empty_context)
            assert result["success"] is True
            mock_instance.run.assert_called_once()
