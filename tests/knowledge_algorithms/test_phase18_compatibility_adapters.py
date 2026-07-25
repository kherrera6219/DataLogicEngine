from __future__ import annotations

from unittest.mock import MagicMock

from core.engine.ka_engine import KAEngine
from core.knowledge_algorithm.ka_loader import KALoader


def test_phase18_core_engine_reads_only_the_canonical_manifest():
    engine = KAEngine()

    assert len(engine.ka_registry) == 213
    assert len(engine.list_algorithms()) == 213
    assert engine.get_algorithm_info("1")["ka_id"] == "KA-001"
    assert engine.get_algorithm_info("generated-v1:KA-133") is None
    assert (
        engine.register_algorithm(
            "KA-9999",
            "Private",
            "Must be rejected",
            "private.module",
            "PrivateKA",
        )
        is False
    )
    assert "KA-9999" not in engine.ka_registry


def test_phase18_core_engine_executes_through_canonical_controller():
    engine = KAEngine()

    completed = engine.execute_algorithm("KA-004", {"query": "validate"})
    unavailable = engine.execute_algorithm("KA-1036", {})

    assert completed["status"] == "completed"
    assert completed["results"]["is_valid"] is True
    assert completed["trace_id"]
    assert unavailable["status"] == "failed"
    assert unavailable["error_code"] == "KA_IMPLEMENTATION_UNAVAILABLE"
    assert engine.stats == {
        "total_executions": 2,
        "successful_executions": 1,
        "failed_executions": 1,
    }


def test_phase18_core_engine_pipeline_stops_on_canonical_failure():
    engine = KAEngine()

    result = engine.execute_pipeline(
        [
            {"ka_id": "KA-004", "params": {"query": "ok"}},
            {"ka_id": "KA-1036", "params": {}},
            {"ka_id": "KA-005", "params": {"query": "not reached"}},
        ],
        session_id="session-1",
    )

    assert result["overall_status"] == "failed"
    assert len(result["steps"]) == 2
    assert result["steps"][1]["error_code"] == "KA_IMPLEMENTATION_UNAVAILABLE"


def test_phase18_legacy_loader_accepts_numeric_ids_without_private_scanning():
    memory = MagicMock()
    loader = KALoader(memory_manager=memory)

    result = loader.execute_ka(
        4,
        {"query": "validate"},
        session_id="session-1",
        pass_num=2,
        layer_num=3,
    )

    assert len(loader.get_available_kas()) == 132
    assert result["status"] == "success"
    assert result["ka_id"] == "KA-004"
    assert result["findings"]["is_valid"] is True
    memory.add_memory_entry.assert_called_once()
