from unittest.mock import MagicMock

from backend.knowledge_algorithms.contracts import (
    KAExecutionResult,
    KAExecutionState,
    KAOutcomeType,
)
from backend.truth_engine.truth_core.agi_planner import AGIPlannerService
from backend.truth_engine.truth_core.l7_schemas import AGIBelief, AGIConflict, AGIGoal


def typed_result(ka_id, output):
    return KAExecutionResult(
        canonical_id=ka_id,
        ka_version="1.0.0",
        manifest_version="test",
        state=KAExecutionState.SUCCEEDED,
        outcome_type=KAOutcomeType.VALUE,
        success=True,
        output=output,
        request_id="request-test",
        run_id="run-test",
        trace_id=f"trace-{ka_id}",
    )


class TestLayer7AGIPlanning:
    
    def test_planner_decomposition(self):
        """Verify the service recursively decomposes goals."""
        service = AGIPlannerService()
        plan = service.plan("Build a moon base", beliefs=[])
        
        # Should have root goal + subgoals
        assert plan.root_goal.content == "Build a moon base"
        assert len(plan.root_goal.sub_goals) == 3

    def test_planner_conflict_detection(self):
        """Verify it detects conflicts between Goal and Belief."""
        service = AGIPlannerService()
        beliefs = [{"id": "b1", "content": "The sky is blue", "confidence": 1.0, "source": "nature"}]
        
        # Trigger keyword "impossible"
        plan = service.plan("Do the impossible task", beliefs=beliefs)
        
        assert len(plan.conflicts) > 0
        assert "impossible" in plan.conflicts[0].description

    def test_security_fail_block(self):
        """Verify security guardrail blocks malicious input."""
        # Mock Guardrail
        mock_guard = MagicMock()
        mock_guard.validate_input.return_value = (False, "Malicious Prompt Detected")
        
        service = AGIPlannerService(guardrail_service=mock_guard)
        
        plan = service.plan("Inject SQL DROP TABLE", beliefs=[])
        
        assert plan.root_goal.status == "failed"
        assert plan.convergence_score == 0.0

    def test_system_crash_recovery(self):
        """Verify fail-safe returns a valid object on unhandled exception."""
        service = AGIPlannerService()

        # Force a crash in decomposition and verify fail-safe output.
        service._decompose_goal = MagicMock(side_effect=Exception("LLM Timeout"))
        
        plan = service.plan("Valid Goal", beliefs=[])
        
        assert plan.root_goal.status == "failed"
        assert plan.iterations == 0

    def test_decompose_goal_uses_ka002_when_available(self):
        """Verify KA-002 output is preferred for decomposition."""
        ka = MagicMock()
        ka.execute_typed.side_effect = lambda ka_id, payload: (
            typed_result(
                ka_id,
                {
                    "sub_goals": [
                        {"label": "Step A"},
                        {"label": "Step B"},
                    ]
                },
            )
            if ka_id == "KA-002"
            else typed_result(ka_id, {})
        )
        service = AGIPlannerService(ka_controller=ka)
        goal = AGIGoal(id="g1", content="Launch project", depth=0)

        subgoals = service._decompose_goal(goal)

        assert len(subgoals) == 2
        assert subgoals[0].parent_id == "g1"
        assert subgoals[0].content == "Step A"

    def test_decompose_goal_falls_back_to_ka040(self):
        """Verify KA-040 fallback runs when KA-002 fails."""
        ka = MagicMock()

        def execute_typed(ka_id, payload):
            if ka_id == "KA-002":
                raise RuntimeError("KA-002 unavailable")
            if ka_id == "KA-040":
                return typed_result(
                    ka_id,
                    {
                        "hypotheses": [
                            {"statement": "Alt path 1"},
                            {"statement": "Alt path 2"},
                        ]
                    },
                )
            return typed_result(ka_id, {})

        ka.execute_typed.side_effect = execute_typed
        service = AGIPlannerService(ka_controller=ka)
        goal = AGIGoal(id="g2", content="Scale system", depth=0)

        subgoals = service._decompose_goal(goal)

        assert len(subgoals) == 2
        assert subgoals[1].content == "Alt path 2"

    def test_plan_respects_max_total_goals_limit(self):
        """Verify planner exits early when total goal cap is reached."""
        service = AGIPlannerService()
        service.max_total_goals = 1

        plan = service.plan("Goal requiring decomposition", beliefs=[])

        assert plan.root_goal.sub_goals == []
        assert plan.convergence_score == 1.0

    def test_plan_filters_blocked_subgoals_via_guardrail(self):
        """Verify guardrail sanitizes unsafe recursive subgoals."""
        guardrail = MagicMock()

        def validate_input(text):
            return (False, "blocked") if "blocked" in text.lower() else (True, "ok")

        guardrail.validate_input.side_effect = validate_input
        service = AGIPlannerService(guardrail_service=guardrail)
        service.max_depth = 1

        root_subgoals = [
            AGIGoal(id="s1", content="safe step", depth=1, parent_id="root"),
            AGIGoal(id="s2", content="blocked action", depth=1, parent_id="root"),
            AGIGoal(id="s3", content="safe verification", depth=1, parent_id="root"),
        ]
        service._decompose_goal = MagicMock(return_value=root_subgoals)

        plan = service.plan("Root objective", beliefs=[])

        assert len(plan.root_goal.sub_goals) == 2
        assert all("blocked" not in sg.content for sg in plan.root_goal.sub_goals)

    def test_plan_runs_ka021_emergence_hook(self):
        """Verify KA-021 hook executes after planning loop."""
        ka = MagicMock()

        def execute_typed(ka_id, payload):
            if ka_id == "KA-021":
                return typed_result(ka_id, {"is_emergent": True})
            return typed_result(ka_id, {})

        ka.execute_typed.side_effect = execute_typed
        service = AGIPlannerService(ka_controller=ka)
        service.max_depth = 0

        plan = service.plan("Detect emergence", beliefs=[])

        assert plan.root_goal.status == "pending"
        assert any(
            call.args[0] == "KA-021"
            for call in ka.execute_typed.call_args_list
        )

    def test_plan_handles_ka021_exception(self):
        """Verify required KA-021 errors fail the plan closed."""
        ka = MagicMock()

        def execute_typed(ka_id, payload):
            if ka_id == "KA-021":
                raise RuntimeError("KA-021 timeout")
            return typed_result(ka_id, {})

        ka.execute_typed.side_effect = execute_typed
        service = AGIPlannerService(ka_controller=ka)
        service.max_depth = 0

        plan = service.plan("Handle KA failures", beliefs=[])

        assert plan.root_goal.status == "failed"
        assert plan.iterations == 0

    def test_semantic_negation_conflict_detection(self):
        """Verify semantic conflict path catches negated beliefs."""
        service = AGIPlannerService()
        goal = AGIGoal(id="g3", content="Do not keep the sky blue", depth=0)
        belief = AGIBelief(id="b1", content="The sky is blue", confidence=1.0, source="nature")

        conflicts = service._detect_conflicts(goal, [belief])

        assert len(conflicts) == 1
        assert conflicts[0].severity >= 0.5

    def test_arbitrate_conflict_prefers_llm_resolution(self):
        """Verify arbitration uses llm_gateway resolution when available."""
        llm_gateway = MagicMock()
        llm_gateway.arbitrate_conflict.return_value = {"resolution": "Choose a compliant alternative."}
        service = AGIPlannerService(llm_gateway=llm_gateway)
        conflict = AGIConflict(
            id="c1",
            goal_id="g1",
            belief_id="b1",
            description="Conflict",
            severity=0.8,
        )

        service._arbitrate_conflict(conflict)

        assert conflict.resolved is True
        assert conflict.resolution == "Choose a compliant alternative."
