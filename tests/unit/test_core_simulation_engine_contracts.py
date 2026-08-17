"""Contract coverage for the canonical core simulation engine."""

from types import SimpleNamespace

import pytest

from core.simulation.simulation_engine import SimulationEngine


DISABLED_LAYERS = {
    "enable_layer4_reasoning": False,
    "enable_layer5_integration": False,
    "enable_layer6_enhancement": False,
    "enable_layer7_agi": False,
    "enable_layer8_quantum": False,
    "enable_layer9_recursive": False,
    "enable_layer10_synthesis": False,
}


class Execution:
    def __init__(self, output, trace_id="trace-1"):
        self.output = output
        self.trace_id = trace_id

    def require_output(self):
        return self.output


class KAEngine:
    def __init__(self, persona_output=None):
        self.calls = []
        self.persona_output = persona_output or {
            "persona_results": [{"response": {"content": "answer"}, "confidence": 0.8}]
        }

    def list_algorithms(self):
        return [{"ka_id": "KA-001"}, {"ka_id": "KA-019"}, {"ka_id": "KA-014"}]

    def execute_typed(self, ka_id, payload, session_id=None):
        self.calls.append((ka_id, payload, session_id))
        if ka_id == "KA-113":
            return Execution({"complexity_tier": "standard"}, "route")
        if ka_id == "KA-031":
            return Execution(
                {"selected_pipeline": ["KA-001", "KA-019", "KA-014", "KA-999"]},
                "select",
            )
        if ka_id == "KA-012":
            return Execution(self.persona_output, "persona")
        return Execution({"confidence": 0.75, "ka": ka_id}, f"trace-{ka_id}")


class Processor:
    def __init__(self, marker, fail=False):
        self.marker = marker
        self.fail = fail
        self.calls = []

    def process(self, context, extra=None):
        self.calls.append((context.copy(), extra))
        if self.fail:
            raise RuntimeError(f"{self.marker} failed")
        return {**context, self.marker: True, "confidence_score": 0.9, "entropy": 0.2}


class AxisMapper:
    def get_17axis_vector(self, query):
        return {"axis_1": query}


class TruthEngine:
    def calculate_truth_vector(self, records):
        return {"evidence": 0.8} if records else {}

    def get_truth_coordinates(self, vector):
        return {"axis_16": 0.8 if vector else 0.0}

    def get_validation_status(self, vector):
        return bool(vector.get("overall_truth_score")), "measured"


def make_engine(ka_engine=None):
    engine = SimulationEngine(
        config={
            "simulation": {
                "layers": DISABLED_LAYERS,
                "enable_sekre": False,
                "max_simulation_passes": 2,
                "target_confidence_overall": 0.7,
            }
        },
        ka_engine=ka_engine,
    )
    engine.workflow_loader = None
    engine.axis_mapper = None
    engine.truth_engine = None
    return engine


def test_start_get_cancel_and_parameter_overrides():
    engine = make_engine()
    started = engine.start_simulation(
        "query",
        {"scope": "desktop"},
        "session",
        {
            "max_passes": 4,
            "target_confidence": 0.5,
            "personas": {"knowledge": {"enabled": False}, "unknown": {"enabled": True}},
        },
    )
    simulation_id = started["simulation_id"]
    assert engine.get_simulation(simulation_id) is started
    assert started["params"]["max_passes"] == 4
    assert not started["params"]["personas"]["knowledge"]["enabled"]
    assert engine.stats["simulations_started"] == 1
    assert engine.cancel_simulation("missing")["error"]
    cancelled = engine.cancel_simulation(simulation_id)
    assert cancelled["status"] == "cancelled"
    assert cancelled["duration_ms"] >= 0
    assert engine.cancel_simulation(simulation_id) is cancelled
    assert engine.run_simulation_pass("missing")["error"]
    assert engine.run_simulation_pass(simulation_id) is cancelled


def test_component_persona_response_fallback_and_failure_contracts():
    engine = make_engine(KAEngine())
    simulation = engine.start_simulation(
        "query", simulation_params={"personas": {"knowledge": {"components": ["job_role"]}}}
    )
    simulation_id = simulation["simulation_id"]
    component = engine._run_component_simulation(
        "knowledge", "job_role", "query", {}, simulation_id, 1
    )
    assert component["status"] == "completed"
    assert component["confidence"] == 0.8
    assert component["ka_execution_id"] == "persona"

    persona = engine._run_persona_simulation("knowledge", "query", {}, simulation_id, 1)
    assert persona["status"] == "completed"
    assert persona["response"]["content"] == "[Job_role] answer"

    no_engine = make_engine()
    no_engine.active_simulations[simulation_id] = simulation
    assert no_engine._run_component_simulation(
        "knowledge", "job_role", "query", {}, simulation_id, 1
    )["status"] == "failed"

    malformed = make_engine(KAEngine({"persona_results": []}))
    malformed.active_simulations[simulation_id] = simulation
    assert malformed._run_component_simulation(
        "knowledge", "job_role", "query", {}, simulation_id, 1
    )["status"] == "failed"
    assert engine._run_persona_simulation("unknown", "query", {}, simulation_id, 1)["status"] == "failed"

    combined = engine._generate_persona_response(
        "sector",
        {
            "a": {"status": "completed", "response": {"content": "one"}},
            "b": {"status": "failed", "response": {"content": "two"}},
            "c": {"status": "completed", "response": {}},
        },
        "query",
        {},
    )
    assert combined["content"] == "[A] one"
    assert "No Sector Expert" in engine._generate_persona_response("sector", {}, "q", {})["content"]
    for persona_id in ("knowledge", "sector", "regulatory", "compliance"):
        for component_id in ("job_role", "education"):
            fallback = engine._generate_fallback_response(persona_id, component_id, "q")
            assert fallback["is_fallback"]
    assert "Custom Other" in engine._generate_fallback_response("custom", "other", "q")["content"]


def test_confidence_synthesis_and_sekre_gates():
    engine = make_engine()
    assert engine._calculate_overall_confidence({"overall": 1.0}) == 0.0
    assert engine._calculate_overall_confidence({"overall": 0, "a": 0.5, "b": 1.0}) == 0.75
    empty = engine._synthesize_results({}, "q", {}, 1)
    assert empty["confidence"] == 0.0
    synthesis = engine._synthesize_results(
        {
            "knowledge": {
                "status": "completed",
                "response": {"perspective": "Knowledge", "content": "facts"},
                "confidence": 0.9,
            },
            "failed": {"status": "failed"},
        },
        "q",
        {},
        2,
    )
    assert synthesis["confidence"] == 0.9
    assert "Knowledge Perspective" in synthesis["content"]

    sekre = SimpleNamespace(analyze_simulation_results=lambda simulation: {"suggestions": []})
    engine.sekre_engine = sekre
    completed = {"status": "completed", "context": {}, "params": {}}
    engine._run_sekre_analysis(completed)
    assert completed["sekre_analysis"] == {"suggestions": []}
    assert engine.stats["sekre_analyses"] == 1
    engine._run_sekre_analysis({"status": "failed"})
    engine.sekre_engine = None
    engine._run_sekre_analysis(completed)
    assert SimulationEngine._qualifies_for_sekre({"context": {}})
    assert SimulationEngine._qualifies_for_sekre({"context": {"tier": 3}})
    assert not SimulationEngine._qualifies_for_sekre({"context": {"tier": "low"}})

    class FailingSekre:
        def analyze_simulation_results(self, _simulation):
            raise RuntimeError("non-fatal")

    engine.sekre_engine = FailingSekre()
    engine._run_sekre_analysis(completed)


def test_layer5_layer7_activation_skip_success_and_error_paths():
    engine = make_engine()
    simulation = engine.start_simulation("query")
    simulation_id = simulation["simulation_id"]
    context = {"confidence_score": 0.5}

    engine.layer5_engine = Processor("layer5")
    engine.integration_engine_enabled = False
    assert engine._apply_layer5_integration(context, simulation_id) is context
    engine.integration_engine_enabled = True
    assert engine._apply_layer5_integration(context, "missing") is context
    assert engine._apply_layer5_integration(context, simulation_id) is context

    gatekeeper = SimpleNamespace(get_layer5_integration_parameters=lambda _context: {"depth": 2})
    active = {
        **context,
        "gatekeeper": gatekeeper,
        "gatekeeper_decision": {"layer_activations": {"layer_5": {"activate": True}}},
    }
    assert engine._apply_layer5_integration(active, simulation_id)["layer5"]
    engine.layer5_engine = Processor("layer5", fail=True)
    assert engine._apply_layer5_integration(active, simulation_id) is active

    engine.layer7_engine = Processor("layer7")
    engine.agi_simulation_enabled = False
    assert engine._apply_layer7_agi_processing(context, simulation_id) is context
    engine.agi_simulation_enabled = True
    assert engine._apply_layer7_agi_processing(context, "missing") is context
    assert engine._apply_layer7_agi_processing(context, simulation_id) is context
    simulation["passes"] = [{"confidence": {"overall": 0.4}}]
    gatekeeper = SimpleNamespace(get_layer7_agi_parameters=lambda _context: {"mode": "bounded"})
    active7 = {
        **context,
        "pov_engine": object(),
        "gatekeeper": gatekeeper,
        "gatekeeper_decision": {"layer_activations": {"layer_7": {"activate": True}}},
    }
    result = engine._apply_layer7_agi_processing(active7, simulation_id)
    assert result["layer7_applied"]
    assert result["historical_confidence"] == [0.4]
    engine.layer7_engine = Processor("layer7", fail=True)
    assert "layer7_error" in engine._apply_layer7_agi_processing(active7, simulation_id)


def test_layer_pipeline_captures_each_error_and_continues():
    engine = make_engine()
    for layer in range(4, 11):
        setattr(engine, f"layer{layer}_enabled", True)
        setattr(engine, f"layer{layer}_engine", Processor(f"layer{layer}", fail=layer % 2 == 0))
    result = engine._process_simulation_layers({"pov_engine": "pov"}, "sim", 1)
    for layer in (4, 6, 8, 10):
        assert f"layer{layer}_error" in result
    for layer in (5, 7, 9):
        assert result[f"layer{layer}"]


def test_workflow_routing_mapping_persona_pipeline_and_validation_steps():
    ka_engine = KAEngine()
    engine = make_engine(ka_engine)
    engine.axis_mapper = AxisMapper()
    engine.truth_engine = TruthEngine()
    simulation = engine.start_simulation(
        "route me",
        {},
        simulation_params={
            "personas": {
                "knowledge": {"enabled": True, "components": ["job_role"]},
                "sector": {"enabled": False},
                "regulatory": {"enabled": False},
                "compliance": {"enabled": False},
            }
        },
    )
    pass_record = {"persona_results": {}, "confidence": {}}
    engine._run_routing_step(simulation, pass_record)
    assert simulation["context"]["planned_pipeline"][0] == "KA-001"
    engine._run_mapping_step(simulation, pass_record)
    assert simulation["context"]["axis_vector"]["axis_1"] == "route me"
    engine._run_mapping_step(simulation, pass_record)
    engine._run_persona_step(simulation, pass_record, simulation["simulation_id"], 1)
    assert pass_record["confidence"]["knowledge"] == 0.8
    for step in (4, 5, 6, 7, 8, 9, 10):
        engine._run_pipeline_step(simulation, pass_record, step)
    assert {"KA-001", "KA-019", "KA-014"} <= set(pass_record["pipeline_results"])
    engine._run_validation_step(simulation, pass_record)
    assert pass_record["validation"]["is_valid"]
    assert "overall_truth_score" in pass_record["truth_vector"]

    engine.ka_engine = None
    engine._run_routing_step(simulation, pass_record)
    engine._run_pipeline_step(simulation, pass_record, 4)
    engine.truth_engine = None
    engine._run_validation_step(simulation, pass_record)
    engine.axis_mapper = None
    engine._run_mapping_step(simulation, pass_record)


def test_full_pass_completion_max_pass_failure_and_single_persona(monkeypatch):
    engine = make_engine(KAEngine())
    engine.workflow_loader = SimpleNamespace(
        steps=[
            {"step_number": 1, "data": {"name": "route"}},
            {"step_number": 2, "data": {"name": "map"}},
            {"step_number": 3, "data": {"name": "persona"}},
            {"step_number": 4, "data": {"name": "pipeline"}},
            {"step_number": 11, "data": {"name": "validate"}},
        ]
    )
    engine.axis_mapper = AxisMapper()
    engine.truth_engine = TruthEngine()
    result = engine.run_simulation(
        "full",
        simulation_params={"target_confidence": 0.1, "max_passes": 2},
    )
    assert result["status"] == "completed"
    assert result["current_pass"] == 1
    assert result["results"]
    assert engine.stats["simulations_completed"] == 1

    maxed = make_engine(KAEngine())
    result = maxed.run_simulation(
        "max",
        simulation_params={"target_confidence": 1.1, "max_passes": 1},
    )
    assert result["status"] == "completed"
    assert result["current_pass"] == 1

    failed = make_engine()
    simulation = failed.start_simulation("fail")
    monkeypatch.setattr(failed, "_calculate_overall_confidence", lambda _value: 1 / 0)
    assert failed.run_simulation_pass(simulation["simulation_id"])["status"] == "failed"

    single = make_engine(KAEngine())
    assert single.run_single_persona_simulation("invalid", "q")["error"]
    single.workflow_loader = SimpleNamespace(
        steps=[{"step_number": 3, "data": {"name": "persona"}}]
    )
    single_result = single.run_single_persona_simulation("knowledge", "q")
    assert single_result["persona_id"] == "knowledge"
