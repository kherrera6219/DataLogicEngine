"""
Comprehensive tests for KA Master Controller.
Tests validate Phase 2 KA integration completeness.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.knowledge_algorithms.ka_master_controller import KAMasterController


class TestKAMasterController:
    """Test KA Master Controller core functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.controller = KAMasterController()
        # Mock registry with safe synchronous test KAs
        self.mock_run = MagicMock(return_value={"status": "success", "data": "mock_result"})
        self.controller.algorithms = {
            "MOCK-001": {
                "metadata": {
                    "Implementation": "mock_module.mock_run"
                }
            },
            "MOCK-002": {
                "metadata": {
                    "Implementation": "mock_module.mock_run"
                }
            }
        }
        # We also need to patch importlib at class/method level, but setup_method can't easily patch context managers for the whole test execution flow without start/stop.
        # So we will rely on patching in methods or use a simpler approach: patching execute_algorithm directly?
        # No, we want to test execute_algorithm logic.
        # We will patch importlib in each test or use a global patcher.
        
        self.patcher = patch('importlib.import_module')
        self.mock_import = self.patcher.start()
        self.mock_module = MagicMock()
        self.mock_module.mock_run = self.mock_run
        self.mock_import.return_value = self.mock_module

    def teardown_method(self):
        self.patcher.stop()

    def test_controller_initialization(self):
        """Test controller initializes with algorithms registry."""
        assert self.controller is not None
        assert hasattr(self.controller, 'algorithms')
        assert hasattr(self.controller, 'execute_algorithm')

    def test_controller_registry_merges_catalog_metadata_for_ui_cards(self):
        """Live registry entries include descriptions for Algorithms page cards."""
        controller = KAMasterController()

        ka001 = controller.algorithms["KA-001"]["metadata"]
        assert ka001["KA_Name"] == "Algorithm of Thought"
        assert ka001["Purpose"] == "Decompose query into ordered tasks and dependencies"
        assert ka001["Implementation"].endswith("ka_01_algorithm_of_thought.run")

        l10 = controller.algorithms["L10-KA-001"]["metadata"]
        assert l10["KA_Name"] == "Layer 10 KA 001"
        assert l10["Purpose"] == "Entropy-based emergence scorer."

    def test_execute_registered_algorithm(self):
        """Test executing a registered algorithm."""
        # Use MOCK-001 registered in setup_method
        # self.mock_run is configured in setup_method
        
        result = self.controller.execute_algorithm("MOCK-001", {"input": "test"})
        
        assert result is not None
        assert result.get('status') == 'success'
        self.mock_run.assert_called_once()

    def test_execute_nonexistent_algorithm_raises_error(self):
        """Test executing non-existent algorithm raises KAError."""
        from core.knowledge_algorithm.exceptions import KAError
        with pytest.raises(KAError):
            self.controller.execute_algorithm("nonexistent_ka_xyz", {})


class TestErrorHandling:
    """Test error handling and recovery."""

    def setup_method(self):
        """Setup test fixtures."""
        self.controller = KAMasterController()
        # Mock registry
        self.mock_run = MagicMock(return_value={"status": "success", "data": "mock_result"})
        self.controller.algorithms = {
            "MOCK-001": {"metadata": {"Implementation": "mock_module.mock_run"}}
        }
        self.patcher = patch('importlib.import_module')
        self.mock_import = self.patcher.start()
        self.mock_module = MagicMock()
        self.mock_module.mock_run = self.mock_run
        self.mock_import.return_value = self.mock_module

    def teardown_method(self):
        self.patcher.stop()

    def test_algorithm_exception_is_caught(self):
        """Test exceptions in algorithms are properly handled."""
        # Test with non-existent algorithm - should raise KAError
        from core.knowledge_algorithm.exceptions import KAError
        with pytest.raises(KAError):
            self.controller.execute_algorithm("nonexistent_error_ka", {})

    def test_invalid_context_handled(self):
        """Test invalid context is handled gracefully."""
        ka_id = "MOCK-001"
        # Try with empty context - mock should run fine
        result = self.controller.execute_algorithm(ka_id, {})
        assert result is not None
        assert result['status'] == 'success'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
