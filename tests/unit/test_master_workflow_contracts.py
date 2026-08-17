"""Contracts for shared workflow state, triggers, and legacy orchestration."""

from core.orchestration.master_workflow import (
    MasterWorkflowOrchestrator,
    SharedStateManager,
    TriggerAction,
    TriggerCondition,
    TriggerSystem,
    create_master_orchestrator,
)


def test_shared_state_metrics_personas_rollbacks_and_trigger_log():
    state = SharedStateManager()
    assert state.get_layer_metric(5, "missing") is None
    state.update_consensus_strength(0.8)
    state.update_cross_verification_score(0.9)
    state.update_preliminary_confidence(0.85)
    assert state.get_layer_metric(5, "consensus_strength") == 0.8
    assert state.get_layer_metric(8, "cross_verification_score") == 0.9
    assert state.get_layer_metric(10, "preliminary_confidence") == 0.85
    assert state.state["confidence_history"][0]["confidence"] == 0.85

    rollback_id = state.save_rollback_point({"safe": True})
    assert state.get_rollback_point(rollback_id) == {"safe": True}
    assert state.get_rollback_point("missing") is None
    state.log_trigger(TriggerCondition.ALL_CLEAR, TriggerAction.FINALIZE_OUTPUT, "done")
    state.update_persona_state("knowledge", {"confidence": 0.9})
    snapshot = state.get_state()
    assert snapshot["trigger_log"][0]["condition"] == "all_clear"
    assert snapshot["persona_states"]["knowledge"]["confidence"] == 0.9


def test_trigger_system_all_conditions_actions_and_iterations():
    state = SharedStateManager()
    triggers = TriggerSystem(
        state,
        {"confidence_threshold": 0.9, "max_refinement_iterations": 1, "conflict_variance_threshold": 0.3},
    )
    assert triggers.evaluate_conditions({"confidence": 0.95}) == [TriggerCondition.ALL_CLEAR]
    assert triggers._check_persona_conflict({"personas_output": {"one": {}}}) is False
    assert triggers._check_persona_conflict(
        {"personas_output": {"one": {"status": "error"}, "two": {"status": "success"}}}
    ) is False

    context = {
        "confidence": 0.5,
        "personas_output": {
            "one": {"status": "success", "confidence": 0.9},
            "two": {"status": "success", "confidence": 0.4},
        },
        "conflicts": ["conflict"],
        "compliance_check": {"status": "violation"},
    }
    conditions = triggers.evaluate_conditions(context)
    assert TriggerCondition.PERSONA_CONFLICT_DETECTED in conditions
    assert TriggerCondition.COMPLIANCE_VIOLATION_DETECTED in conditions
    assert TriggerCondition.REFINEMENT_LOOP_INCOMPLETE in conditions
    assert triggers.get_action(TriggerCondition.PERSONA_CONFLICT_DETECTED) is TriggerAction.PERSONA_ARBITRATION

    triggers.increment_iteration()
    context["compliance_check"] = {}
    context["regulatory_check"] = {"status": "violation"}
    conditions = triggers.evaluate_conditions(context)
    assert TriggerCondition.THRESHOLD_NOT_MET_AFTER_MAX in conditions
    assert TriggerCondition.REFINEMENT_LOOP_INCOMPLETE not in conditions
    assert triggers.get_action(TriggerCondition.THRESHOLD_NOT_MET_AFTER_MAX) is TriggerAction.MANUAL_REVIEW_ALERT
    assert triggers.get_action(None) is TriggerAction.MANUAL_REVIEW_ALERT
    triggers.reset_iteration()
    assert triggers.current_iteration == 0


def test_master_workflow_real_fallback_execution_completes():
    orchestrator = create_master_orchestrator(
        {"triggers": {"confidence_threshold": 0.9, "max_refinement_iterations": 1}}
    )
    result = orchestrator.execute(
        "How should a legal compliance policy address technology risk?",
        {"coordinates": {"a11": "legal"}},
    )

    assert result["status"] == "completed"
    assert result["confidence"] >= 0.9
    assert result["final_answer"]
    assert result["triggers_fired"][-1]["action"] == "finalize_output"
    assert set(result["steps"]) == {
        "step_1_parse_coordinate",
        "step_2_activate_personas",
        "step_3_simulation_stack",
        "step_4_refinement_engine",
        "step_5_output_finalization",
    }
    assert orchestrator.get_execution_log()


class PersonaEngine:
    def process_query(self, query):
        return {
            "persona_responses": {"knowledge": {"status": "success", "confidence": 0.8}},
            "response": {"text": query},
        }


class SimulationEngine:
    def start_simulation(self, **kwargs):
        return {
            "simulation_id": "sim",
            "status": "completed",
            "confidence": {"knowledge": 0.9, "sector": 0.8, "regulatory": 0.7, "compliance": 0.6, "overall": 0.85},
        }


class RefinementEngine:
    def __init__(self, result=None, fail=False):
        self.smm = object()
        self.result = result or {
            "status": "success",
            "final_confidence": 0.92,
            "refined_answer_text": "refined",
            "refinement_steps_log": {"one": {}},
            "research_needs": ["source"],
        }
        self.fail = fail

    def run(self, **kwargs):
        if self.fail:
            raise RuntimeError("refinement failed")
        return self.result


def test_master_workflow_optional_subsystem_branches():
    orchestrator = MasterWorkflowOrchestrator()
    orchestrator.quad_persona_engine = PersonaEngine()
    personas = orchestrator._step2_activate_personas("query", {"axis_scores": {}})
    assert list(personas["personas_output"]) == ["knowledge"]
    assert personas["synthesis"] == {"text": "query"}

    orchestrator.layer1_engine = None
    orchestrator.layer2_engine = None
    orchestrator.layer3_engine = None
    orchestrator.simulation_engine = SimulationEngine()
    simulation = orchestrator._step3_run_simulation_stack("query", {"axis_scores": {}}, personas)
    assert simulation["simulation_id"] == "sim"
    assert len(simulation["layers_executed"]) == 7
    assert simulation["simulation_confidence"]["overall"] == 0.85

    orchestrator.refinement_orchestrator = RefinementEngine()
    refined = orchestrator._step4_run_refinement_engine("query", simulation)
    assert refined["refined_answer"] == "refined"
    assert refined["research_needs"] == ["source"]
    finalized = orchestrator._step5_output_finalization("query", refined)
    assert finalized["final_answer"] == "refined"
    assert finalized["governance_check"]["status"] == "passed"

    orchestrator.refinement_orchestrator = RefinementEngine({"status": "error"})
    assert len(orchestrator._step4_run_refinement_engine("query", simulation)["refinement_steps"]) == 12
    orchestrator.refinement_orchestrator = RefinementEngine(fail=True)
    assert len(orchestrator._step4_run_refinement_engine("query", simulation)["refinement_steps"]) == 12


def test_master_workflow_arbitration_rollback_and_manual_finalize_edges():
    orchestrator = MasterWorkflowOrchestrator()
    arbitration = orchestrator._handle_persona_arbitration(
        {
            "personas_output": {
                "knowledge": {"confidence": 0.9},
                "regulatory": {"confidence": 0.4},
            },
            "conflicts": ["one"],
        }
    )
    assert arbitration["arbitration_applied"] is True
    assert arbitration["conflicts_resolved"] == 1
    assert all(item["arbitrated"] for item in arbitration["personas_output"].values())
    assert orchestrator._handle_persona_arbitration({})["weighted_average"] == 0.5

    assert orchestrator._handle_containment_rollback({})["rollback_applied"] is False
    orchestrator.shared_state.save_rollback_point({"layer_context": {"safe": True}})
    rollback = orchestrator._handle_containment_rollback(
        {
            "compliance_check": {"status": "failed"},
            "regulatory_check": {"status": "failed"},
        }
    )
    assert rollback["rollback_applied"] is True
    assert rollback["restored_context"] == {"safe": True}
    assert len(rollback["adjustments_made"]) == 2

    fallback = orchestrator._step5_output_finalization("query", {"final_confidence": 0.75})
    assert "75.0% confidence" in fallback["final_answer"]
