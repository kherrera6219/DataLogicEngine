from pathlib import Path

from backend.llm_gateway.gateway import LLMGateway


ROOT = Path(__file__).resolve().parents[2]


def test_gateway_duplicate_orchestration_helpers_are_absent():
    assert not hasattr(LLMGateway, "_legacy_process")
    assert not hasattr(LLMGateway, "_run_ukg_overlay")
    assert not hasattr(LLMGateway, "_run_quad_analysis")


def test_sdk_overlay_contains_transport_only():
    source = (ROOT / "sdk/UKG_Python_SDK/ukg_sdk/overlay.py").read_text(encoding="utf-8")

    assert 'client.post("/gateway/chat"' in source
    assert "DMRFOrchestrator" not in source
    assert "DSQPOrchestrator" not in source
    assert "TruthCore" not in source
    assert "provider.complete" not in source


def test_legacy_sdk_truth_engine_names_are_transport_only():
    sources = [
        (ROOT / "sdk/UKG_Python_SDK/ukg_sdk/api.py").read_text(encoding="utf-8"),
        (ROOT / "sdk/UKG_Python_SDK/ukg_sdk/truth_engine/core.py").read_text(
            encoding="utf-8"
        ),
    ]

    combined = "\n".join(sources)
    assert '"/gateway/chat"' in combined
    assert "KAExecutor" not in combined
    assert "TruthGate(" not in combined
    assert "TruthCore(" not in combined
    assert "provider.complete" not in combined


def test_public_truthcore_process_uses_canonical_gateway_not_private_workflow():
    source = (
        ROOT / "backend/truth_engine/truth_core/engine.py"
    ).read_text(encoding="utf-8")
    process_body = source.split("    async def process(", 1)[1].split(
        "    def _refresh_graph_context", 1
    )[0]

    assert "LLMGateway" in process_body
    assert "GovernedRequest" in process_body
    assert "self._execute_workflow(" not in process_body


def test_simulation_turns_cannot_recursively_call_gateway():
    source = (ROOT / "backend/simulation/multi_agent_engine.py").read_text(encoding="utf-8")

    assert "gateway.process(" not in source
    assert "generate_simulation_turn" in source
    assert "SIMULATION_PHASE10_BOUNDARY" in source
