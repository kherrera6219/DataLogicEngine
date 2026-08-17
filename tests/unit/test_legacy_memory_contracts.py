"""Behavioral coverage for the in-process memory and graph simulation contracts."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from core.simulation.memory_manager import (
    MemoryEntry,
    MemoryManager,
    MemoryStream,
    WorkingMemory,
)
from core.simulation.memory_simulation import MemorySimulationEngine, create_sample_simulation


def test_memory_entry_stream_and_working_memory_round_trip():
    timestamp = datetime.now(UTC) - timedelta(minutes=5)
    entry = MemoryEntry(
        "entry-1",
        "Architecture policy evidence",
        "insight",
        "auditor",
        {"scope": "release"},
        timestamp,
    )
    entry.access()
    entry.update_salience(2.0)
    assert entry.salience == 1.0
    entry.update_salience(-1.0)
    assert entry.salience == 0.0
    entry.update_salience(0.75)

    restored_entry = MemoryEntry.from_dict(entry.to_dict())
    assert restored_entry.entry_id == "entry-1"
    assert restored_entry.access_count == 1
    assert restored_entry.salience == 0.75

    stream = MemoryStream("stream-1", "Release", "topic", {"owner": "qa"})
    assert stream.get_entry("missing") is None
    assert stream.add_entry(restored_entry) is True
    assert stream.get_entry("entry-1") is restored_entry
    assert stream.find_entries("architecture evidence") == [restored_entry]
    assert stream.find_entries("unmatched") == []
    assert stream.get_recent_entries(1) == [restored_entry]

    restored_stream = MemoryStream.from_dict(stream.to_dict())
    assert restored_stream.stream_id == "stream-1"
    assert restored_stream.entries["entry-1"].content == "Architecture policy evidence"

    working = WorkingMemory(capacity=2)
    assert working.add("one") is True
    working.add("two")
    working.add("three")
    assert [item["content"] for item in working.get_recent()] == ["two", "three"]
    assert [item["content"] for item in working.get_recent(1)] == ["three"]
    assert working.clear() is True
    assert working.get_recent() == []


def test_memory_manager_persistence_search_conversation_and_context(tmp_path):
    storage_path = tmp_path / "memory" / "memory.json"
    manager = MemoryManager(str(storage_path))

    assert set(manager.streams) >= {
        "general",
        "knowledge_expert",
        "sector_expert",
        "regulatory_expert",
        "compliance_expert",
    }
    assert manager.add_memory("missing", "fact", "test", "missing") is None

    custom_id = manager.create_memory_stream("Custom", "topic", "custom", {"a": 1})
    assert custom_id == "custom"
    assert manager.create_memory_stream("Duplicate", "topic", "custom") == "custom"
    assert manager.get_memory_stream("custom").metadata == {"a": 1}

    memory_id = manager.add_memory(
        "Release architecture evidence is complete",
        "fact",
        "auditor",
        "custom",
        {"qualified": True},
    )
    assert memory_id
    assert manager.find_memories("architecture evidence", ["missing", "custom"])["custom"][0].entry_id == memory_id
    assert manager.find_memories("not-present", ["custom"]) == {}

    insight_ids = manager.extract_insights(
        "Release policy question",
        "unused response",
        {
            "knowledge": "Architecture evidence response",
            "sector": "Operational sector response",
            "unknown": "This stream is intentionally absent",
        },
    )
    assert len(insight_ids) == 3

    assert manager.get_conversation_memories("new") == []
    assert manager.create_conversation_memory("conv-1", {"title": "Coverage"}) is True
    assert manager.create_conversation_memory("conv-1") is True
    conversation_entry = manager.add_conversation_memory(
        "conv-1", "user", "Architecture coverage question", {"turn": 1}
    )
    assert conversation_entry
    assert manager.add_conversation_memory("conv-2", "assistant", "Created automatically")
    assert manager.get_conversation_memories("conv-1", 1)[0]["source"] == "user"

    context = manager.generate_memory_context("architecture evidence", "conv-1")
    assert "custom" not in context["memories"]
    assert "knowledge_expert" in context["memories"]
    assert context["working_memory"]
    assert manager.get_working_memory(1)
    assert manager.clear_working_memory() is True

    assert manager.save_memories() is True
    saved = json.loads(storage_path.read_text(encoding="utf-8"))
    assert "custom" in saved["streams"]
    reloaded = MemoryManager(str(storage_path))
    assert reloaded.get_memory_stream("custom").entries[memory_id].content.startswith("Release")


def test_memory_manager_load_and_save_fail_closed(tmp_path):
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("not json", encoding="utf-8")
    manager = MemoryManager(str(invalid_path))
    assert "general" in manager.streams

    with patch("builtins.open", side_effect=OSError("blocked")):
        assert manager.save_memories() is False


def test_memory_simulation_complete_lifecycle_and_graph_queries():
    engine = create_sample_simulation()

    assert engine.stop_simulation()["status"] == "error"
    assert engine.run_simulation_step()["status"] == "error"
    assert engine.get_simulation_results()["status"] == "error"

    started = engine.start_simulation({"seed_activations": {"PL01": 0.8}})
    assert started["graph_stats"]["pillar_count"] == 3
    step = engine.run_simulation_step()
    assert step["status"] == "success"
    assert step["results"]["pillar_activations"]["PL01"] > 0.8
    assert step["results"]["sector_activities"]["GOV"]["influence"] > 0
    assert step["results"]["domain_activities"]["FEDGOV"]["specialization"] > 0

    results = engine.get_simulation_results()
    assert results["steps_completed"] == 1
    stopped = engine.stop_simulation()
    assert stopped["status"] == "success"
    assert stopped["simulation_id"] == started["simulation_id"]

    exported = engine.export_graph("json")
    assert exported["status"] == "success"
    assert exported["graph"]["metadata"]["node_count"] == engine.graph.number_of_nodes()
    assert engine.export_graph("yaml")["status"] == "error"
    assert engine.export_graph("gexf")["status"] in {"success", "error"}

    path = engine.get_path_between("FEDGOV", "GOV")
    assert path["status"] == "success"
    assert path["path_length"] >= 2
    assert engine.get_path_between("missing", "GOV")["status"] == "error"

    engine.graph.add_node("isolated-a", type="test", name="A")
    engine.graph.add_node("isolated-b", type="test", name="B")
    assert engine.get_path_between("isolated-a", "isolated-b")["status"] == "no_path"

    search = engine.search_graph({"node_type": "sector", "axis": 2, "name_contains": "tech"})
    assert search["count"] == 1
    assert search["nodes"][0]["id"] == "TECH"
    assert engine.search_graph({"node_type": "unknown"})["count"] == 0


def test_memory_simulation_validation_and_empty_branches():
    engine = MemorySimulationEngine()
    assert engine.load_pillar_levels([{}, {"pillar_id": "P", "name": "P"}])["pillar_count"] == 1
    assert engine.load_sectors(
        [
            {},
            {"sector_code": "S", "name": "Parent"},
            {"sector_code": "C", "name": "Child", "parent_sector_code": "S"},
        ]
    )["sector_count"] == 2
    assert engine.load_domains(
        [
            {},
            {"domain_code": "D", "name": "Parent", "sector_code": "S"},
            {"domain_code": "DC", "name": "Child", "parent_domain_code": "D"},
        ]
    )["domain_count"] == 2

    pillar_connections = [
        {},
        {"pillar_id": "missing", "sector_id": "S"},
        {"pillar_id": "P", "sector_id": "S", "weight": 0.5},
    ]
    domain_connections = [
        {},
        {"domain_id": "missing", "pillar_id": "P"},
        {"domain_id": "D", "pillar_id": "P", "weight": 0.5},
    ]
    assert engine.connect_pillars_to_sectors(pillar_connections)["connection_count"] == 1
    assert engine.connect_domains_to_pillars(domain_connections)["connection_count"] == 1

    engine.start_simulation({"seed_activations": {"P": -1}})
    assert engine.run_simulation_step()["results"]["pillar_activations"]["P"] >= 0
