import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from backend.simulation.multi_agent_engine import MultiAgentSimulationEngine as SimulationEngine, create_multi_agent_simulation_engine as create_simulation_engine


def test_create_simulation_engine_factory():
    engine = create_simulation_engine()
    assert isinstance(engine, SimulationEngine)


def test_create_simulation_happy_path_strips_query():
    engine = SimulationEngine(max_concurrent_simulations=2)
    sim_id = engine.create_simulation("  summarize this  ", {"source": "test"})

    assert sim_id in engine.active_simulations
    assert engine.active_simulations[sim_id]["query"] == "summarize this"
    assert engine.simulation_count == 1


@pytest.mark.parametrize(
    "query,context,expected_error",
    [
        ("", {}, "non-empty string"),
        (None, {}, "non-empty string"),
        ("x" * 10001, {}, "maximum length"),
        ("valid", "not-a-dict", "dictionary"),
    ],
)
def test_create_simulation_validation(query, context, expected_error):
    engine = SimulationEngine()

    with pytest.raises(ValueError, match=expected_error):
        engine.create_simulation(query, context)


def test_create_simulation_rate_limit():
    engine = SimulationEngine(max_concurrent_simulations=1)
    engine.active_simulations["existing"] = {"status": "running"}

    with pytest.raises(RuntimeError, match="Maximum concurrent simulations"):
        engine.create_simulation("q", {})


@pytest.mark.asyncio
async def test_run_simulation_success_quick_depth():
    engine = SimulationEngine()
    sim_id = engine.create_simulation("How should we store records?", {"tenant": "acme"})

    responses = [
        "context analysis",
        "argument one",
        "argument two",
        "synthesized conclusion",
    ]
    with patch.object(engine, "_call_llm", new=AsyncMock(side_effect=responses)):
        result = await engine.run_simulation(sim_id, depth="quick")

    assert result["status"] == "completed"
    assert result["consensus_reached"] is True
    assert result["event_count"] == 4
    assert result["final_conclusion"] == "synthesized conclusion"
    assert sim_id not in engine.active_simulations


@pytest.mark.asyncio
async def test_run_simulation_invalid_inputs():
    engine = SimulationEngine()
    sim_id = engine.create_simulation("q", {})

    with pytest.raises(ValueError, match="Invalid depth"):
        await engine.run_simulation(sim_id, depth="invalid")

    with pytest.raises(ValueError, match="not found"):
        await engine.run_simulation("missing-id")


@pytest.mark.asyncio
async def test_run_simulation_timeout_returns_timeout_status():
    engine = SimulationEngine()
    sim_id = engine.create_simulation("q", {})

    async def slow_call(*_args, **_kwargs):
        await asyncio.sleep(0.05)
        return "slow response"

    with patch.object(engine, "_call_llm", new=slow_call):
        result = await engine.run_simulation(sim_id, depth="quick", timeout=0.01)

    assert result["status"] == "timeout"
    assert "timeout" in result["metadata"]["error"].lower()
    assert sim_id not in engine.active_simulations


@pytest.mark.asyncio
async def test_run_simulation_failure_returns_failed_status():
    engine = SimulationEngine()
    sim_id = engine.create_simulation("q", {})

    async def failing_call(*_args, **_kwargs):
        raise RuntimeError("llm unavailable")

    with patch.object(engine, "_call_llm", new=failing_call):
        result = await engine.run_simulation(sim_id, depth="quick")

    assert result["status"] == "failed"
    assert result["metadata"]["error_type"] == "RuntimeError"
    assert "llm unavailable" in result["metadata"]["error"]
    assert sim_id not in engine.active_simulations


@pytest.mark.asyncio
async def test_call_llm_uses_phase10_turn_adapter():
    gateway = SimpleNamespace(
        generate_simulation_turn=AsyncMock(return_value="gateway-output")
    )
    engine = SimulationEngine(llm_gateway=gateway)

    result = await engine._call_llm("Prompt body", "Analyst")

    assert result == "gateway-output"
    gateway.generate_simulation_turn.assert_awaited_once_with(
        prompt="Prompt body", persona="Analyst", max_tokens=500
    )


@pytest.mark.asyncio
async def test_call_llm_raises_when_phase10_adapter_returns_empty():
    gateway = SimpleNamespace(generate_simulation_turn=AsyncMock(return_value=""))
    engine = SimulationEngine(llm_gateway=gateway)

    with pytest.raises(RuntimeError, match="empty response"):
        await engine._call_llm("Prompt body", "Analyst")


def test_process_query_without_running_loop():
    engine = SimulationEngine()
    expected = {"status": "completed", "final_conclusion": "ok"}

    with patch.object(engine, "create_simulation", return_value="sim-1"):
        with patch.object(engine, "run_simulation", new=AsyncMock(return_value=expected)):
            result = engine.process_query("q", {})

    assert result == expected


@pytest.mark.asyncio
async def test_process_query_with_running_loop():
    engine = SimulationEngine()
    expected = {"status": "completed", "final_conclusion": "async-ok"}

    with patch.object(engine, "create_simulation", return_value="sim-2"):
        with patch.object(engine, "run_simulation", new=AsyncMock(return_value=expected)):
            result = engine.process_query("q", {})

    assert result == expected
