
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.truth_engine.truth_core.engine import TruthCoreEngine

class TestTruthCoreEngine:
    @pytest.fixture
    def mock_ka_controller(self):
        controller = MagicMock()
        # Setup execute_algorithm to return decent mocks
        async def async_execute(*args, **kwargs):
            return {"output": "mock_result", "confidence": 0.9}
        
        # KA-005 Tiering mock
        def execute_side_effect(ka_id, params):
            if ka_id == "KA-005":
                return {"suggested_tier": "moderate"}
            if ka_id == "KA-113":
                return {"routing_profile": "default"}
            return {"output": {"mock": "data"}, "confidence": 0.9}

        controller.execute_algorithm.side_effect = execute_side_effect
        controller.process_with_persona.return_value = "mock_persona_response"
        return controller

    @pytest.fixture
    def engine(self, mock_ka_controller):
        # Mocking optional service imports if they fail or to control them
        with patch.dict("sys.modules", {
                "backend.truth_engine.truth_gate.quant": MagicMock(),
                "backend.truth_engine.truth_core.agi_planner": MagicMock(),
                "backend.truth_engine.truth_gate.trust_validation_gateway": MagicMock(),
                "backend.truth_engine.truth_core.meta_reasoning_controller": MagicMock(),
                "backend.truth_engine.truth_core.emergence_controller": MagicMock(),
                "models": MagicMock()
            }):
            
            with patch("backend.truth_engine.truth_core.engine.PersonaEnhancer"), \
                 patch("backend.truth_engine.truth_core.engine.RefinementOrchestrator"):
                 
                # Initialize with mocks
                engine = TruthCoreEngine(ka_controller=mock_ka_controller)
                return engine

    @pytest.mark.asyncio
    async def test_determine_tier_heuristic(self, engine):
        # Force KA controller to fail/be None to test heuristic
        engine.ka_controller = None
        
        # Short query -> trivial
        assert await engine.determine_tier("hi") == "trivial"
        
        # Risk keyword -> high_stakes (must be > 5 words to pass trivial check)
        assert await engine.determine_tier("legal assessment regarding the new compliance regulations") == "high_stakes"

    @pytest.mark.asyncio
    async def test_create_session(self, engine):
        session = await engine.create_session("test query", user_id=1, tier="moderate")
        assert session["session_id"] is not None
        assert session["status"] == "created"
        assert session["tier"] == "moderate"
        assert engine.active_sessions[session["session_id"]] == session

    @pytest.mark.asyncio
    async def test_process_workflow_execution(self, engine):
        governed_payload = {
            "ok": True,
            "status": "completed",
            "answer": "governed answer",
            "confidence": None,
            "trace": [
                {"stage_name": "admission", "status": "completed"},
                {"stage_name": "persistence", "status": "completed"},
            ],
            "metadata": {"dsqp": {"profiles": {"8": {}}}},
        }
        governed = MagicMock(
            status="completed",
            answer="governed answer",
            confidence=None,
        )
        governed.to_dict.return_value = governed_payload

        session = await engine.create_session("test", tier="moderate")
        with patch(
            "backend.llm_gateway.gateway.LLMGateway.execute",
            new=AsyncMock(return_value=governed),
        ) as execute:
            result_session = await engine.process(session["session_id"])

        assert result_session["status"] == "completed"
        assert result_session["confidence_score"] is None
        assert len(result_session["workflow_steps"]) == 2
        execute.assert_awaited_once()

    def test_axis_queries_from_coordinate_vector(self):
        vector = {
            "active_axes": [1, "A6", "axis_17"],
            "1": {"uid": "pillar-1", "value": "PL01"},
            "A6": {"value": "octopus-bridge"},
            "axis_17": "public",
        }

        assert TruthCoreEngine._axis_queries_from_coordinate_vector(vector) == [
            (1, "pillar-1"),
            (6, "octopus-bridge"),
            (17, "public"),
        ]

