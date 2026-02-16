import pytest
from unittest.mock import patch
from backend.knowledge_algorithms.ka_master_controller import KAMasterController
from backend.truth_engine.truth_core.engine import TruthCoreEngine

@pytest.fixture
def mock_ka_master():
    with patch('backend.knowledge_algorithms.ka_master_controller.KAMasterController') as mock:
        yield mock

@pytest.fixture
def truth_engine():
    return TruthCoreEngine()

class TestCoreIntegration:
    async def test_ka_master_routing(self):
        controller = KAMasterController()
        # Mock the registry to include a test KA
        controller.algorithms = {
            "KA-001": {"id": "KA-001", "metadata": {"Implementation": "backend.knowledge_algorithms.ka_01_algorithm_of_thought.run"}}
        }
        
        with patch('backend.knowledge_algorithms.ka_01_algorithm_of_thought.run', return_value={"output": "success"}):
            result = controller.execute_algorithm("KA-001", {"query": "test"})
            assert result["output"] == "success"

    @pytest.mark.asyncio
    async def test_truth_engine_coordination(self, truth_engine):
        # Create a session first
        session = await truth_engine.create_session("test query")
        session_id = session['session_id']
        
        # Mock the workflow execution
        with patch.object(truth_engine, '_execute_workflow', return_value={"response": "Final Consensus", "confidence": 0.99}):
            final_result = await truth_engine.process(session_id)
            assert final_result['status'] == 'completed'
            assert final_result['result']['response'] == "Final Consensus"

    def test_end_to_end_logic_flow(self):
        # Test how KA results feed into the Truth Engine
        # This is a high-level integration test
        pass
