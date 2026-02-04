import pytest
from unittest.mock import MagicMock, patch
import sys
import importlib

# Fake Base Class to avoid MagicMock inheritance issues
class FakeKnowledgeAlgorithm:
    def __init__(self, context, *args):
        self.context = context
        self.config = {}
    def log_execution_step(self, *args, **kwargs):
        pass

class TestKA050EdgeCases:
    @pytest.fixture
    def mock_dependencies(self):
        """
        Setup mocks for all dependencies including core, extensions, auth.
        Returns the mock_core object which has the Fake base class injected.
        """
        mock_core = MagicMock()
        mock_core.knowledge_algorithm.ka_base.KnowledgeAlgorithm = FakeKnowledgeAlgorithm
        
        mock_modules = {
            "extensions": MagicMock(),
            "models": MagicMock(),
            "flask_jwt_extended": MagicMock(),
            "backend.auth": MagicMock(),
            "core": mock_core,
            "core.knowledge_algorithm": mock_core.knowledge_algorithm,
            "core.knowledge_algorithm.ka_base": mock_core.knowledge_algorithm.ka_base,
        }
        return mock_modules

    @pytest.fixture
    def ka_module(self, mock_dependencies):
        """
        Import the KA module within a patched sys.modules environment.
        This ensures imports inside the module (like form core) use our mocks.
        """
        with patch.dict(sys.modules, mock_dependencies):
            # If it was already imported by another test (unlikely given the unique name, but possible), reload it
            module_name = 'backend.knowledge_algorithms.ka_50_knowledge_integrity_validator'
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            module = importlib.import_module(module_name)
            yield module
            # Cleanup is handled by patch.dict context variable restoration, 
            # but we might want to unimport the module to be safe? 
            # patch.dict handles sys.modules restoration, so the *module object* will remain in memory 
            # but sys.modules entry will be reverted. Ideally we want to remove our poisoned module.
            if module_name in sys.modules:
                del sys.modules[module_name]

    @pytest.fixture
    def empty_context(self):
        return {}

    def test_load_config_failure(self, ka_module, empty_context):
        """Test graceful failure when config cannot be loaded."""
        KA050Validator = ka_module.KA050KnowledgeIntegrityValidator
        
        with patch('backend.knowledge_algorithms.ka_50_knowledge_integrity_validator.os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=OSError("Read error")):
            
            algo = KA050Validator(empty_context)
            assert algo.config == {}

    def test_dangling_edge_detection(self, ka_module, empty_context):
        """Test detection of edges pointing to missing nodes."""
        KA050Validator = ka_module.KA050KnowledgeIntegrityValidator
        KA050Input = ka_module.KA050Input
        
        algo = KA050Validator(empty_context)
        input_data = KA050Input(snapshot={
            "nodes": [{"id": "n1", "confidence": 1.0}],
            "edges": [{"source": "n1", "target": "missing_node"}]
        })
        
        result = algo._run_logic(input_data)
        assert result["success"]
        assert result["status"] in ["FAILED", "QUARANTINED"]
        assert any(i["type"] == "DANGLING_EDGE" for i in result["integrity_report"])

    def test_low_confidence_detection(self, ka_module, empty_context):
        """Test detection of low confidence nodes."""
        KA050Validator = ka_module.KA050KnowledgeIntegrityValidator
        KA050Input = ka_module.KA050Input
        
        algo = KA050Validator(empty_context)
        # Assuming default min_conf is 0.3
        input_data = KA050Input(snapshot={
            "nodes": [{"id": "weak_node", "confidence": 0.1}],
            "edges": []
        })
        
        result = algo._run_logic(input_data)
        assert any(i["type"] == "LOW_CONFIDENCE_NODE" for i in result["integrity_report"])

    def test_quarantine_logic(self, ka_module, empty_context):
        """Test quarantine status based on config."""
        KA050Validator = ka_module.KA050KnowledgeIntegrityValidator
        KA050Input = ka_module.KA050Input
        
        algo = KA050Validator(empty_context)
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

    def test_run_wrapper_exception(self, ka_module, empty_context):
        """Test top-level run function captures exceptions."""
        run_func = ka_module.run
        
        with patch('backend.knowledge_algorithms.ka_50_knowledge_integrity_validator.KA050KnowledgeIntegrityValidator') as MockClass:
            MockClass.side_effect = Exception("Critical Init Failure")
            
            result = run_func(context=empty_context)
            assert result["success"] is False
            assert "Critical Init Failure" in result["error"]

    def test_load_config_missing(self, ka_module, empty_context):
        """Test config loading when file does not exist."""
        KA050Validator = ka_module.KA050KnowledgeIntegrityValidator
        
        with patch('backend.knowledge_algorithms.ka_50_knowledge_integrity_validator.os.path.exists', return_value=False):
            algo = KA050Validator(empty_context)
            assert algo.config == {}

    def test_run_wrapper_success(self, ka_module, empty_context):
        """Test top-level run function success path."""
        run_func = ka_module.run
        
        # We need to mock the instance method run, NOT the module-level run
        with patch('backend.knowledge_algorithms.ka_50_knowledge_integrity_validator.KA050KnowledgeIntegrityValidator') as MockClass:
            mock_instance = MockClass.return_value
            mock_instance.run.return_value = {"success": True}
            
            result = run_func(context=empty_context)
            assert result["success"] is True
            mock_instance.run.assert_called_once()
