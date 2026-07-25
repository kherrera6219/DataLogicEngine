"""
Comprehensive tests for KA Master Controller.
Tests validate Phase 2 KA integration completeness.
"""
from unittest.mock import MagicMock, patch

import pytest

from backend.knowledge_algorithms.contracts import (
    KAExecutionResult,
    KAExecutionState,
    KAOutcomeType,
)
from backend.knowledge_algorithms.ka_master_controller import KAMasterController


def _typed_result(
    ka_id: str = "MOCK-001",
    output: dict | None = None,
) -> KAExecutionResult:
    return KAExecutionResult(
        canonical_id=ka_id,
        ka_version="1.0.0",
        manifest_version="test",
        state=KAExecutionState.SUCCEEDED,
        outcome_type=KAOutcomeType.VALUE,
        success=True,
        output=output or {"status": "success", "data": "mock_result"},
        request_id="request-test",
        run_id="run-test",
        trace_id="trace-test",
    )


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
        self.patcher = patch.object(
            self.controller._canonical_controller,
            "execute",
            return_value=_typed_result(),
        )
        self.mock_execute = self.patcher.start()

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
        assert l10["KA_Name"] == "Entropy Scorer"
        assert l10["Purpose"] == "Layer 10 Entropy Scorer"

    def test_execute_registered_algorithm(self):
        """Test executing a registered algorithm."""
        # Use MOCK-001 registered in setup_method
        # self.mock_run is configured in setup_method
        
        result = self.controller.execute_algorithm("MOCK-001", {"input": "test"})
        
        assert result is not None
        assert result["output"]["status"] == "success"
        self.mock_execute.assert_called_once()

    def test_execute_typed_returns_canonical_result(self):
        result = self.controller.execute_typed("MOCK-001", {"input": "test"})

        assert isinstance(result, KAExecutionResult)
        assert result.require_output()["data"] == "mock_result"

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
        self.patcher = patch.object(
            self.controller._canonical_controller,
            "execute",
            return_value=_typed_result(),
        )
        self.patcher.start()

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
        assert result["output"]["status"] == "success"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
