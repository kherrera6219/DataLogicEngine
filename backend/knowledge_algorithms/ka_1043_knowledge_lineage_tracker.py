"""KA-1043: deterministic validation and ordering of knowledge lineage."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class LineageEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=200)
    version_id: str = Field(min_length=1, max_length=200)
    parent_version_ids: list[str] = Field(default_factory=list, max_length=100)
    event_type: Literal[
        "created",
        "derived",
        "validated",
        "corrected",
        "simulated",
        "promoted",
        "archived",
    ]
    source_ref: str = Field(min_length=1, max_length=2_000)

    @model_validator(mode="after")
    def validate_parents(self) -> LineageEvent:
        if self.version_id in self.parent_version_ids:
            raise ValueError("a version cannot be its own parent")
        if len(self.parent_version_ids) != len(set(self.parent_version_ids)):
            raise ValueError("parent version IDs must be unique")
        return self


class KA1043Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "knowledge_id": "knowledge-1",
                    "events": [
                        {
                            "event_id": "event-1",
                            "version_id": "v1",
                            "event_type": "created",
                            "source_ref": "commit:1",
                        },
                        {
                            "event_id": "event-2",
                            "version_id": "v2",
                            "parent_version_ids": ["v1"],
                            "event_type": "validated",
                            "source_ref": "simulation:2",
                        },
                    ],
                }
            ]
        },
    )

    knowledge_id: str = Field(min_length=1, max_length=200)
    events: list[LineageEvent] = Field(min_length=1, max_length=10_000)

    @model_validator(mode="after")
    def validate_identity(self) -> KA1043Input:
        event_ids = [item.event_id for item in self.events]
        version_ids = [item.version_id for item in self.events]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("event IDs must be unique")
        if len(version_ids) != len(set(version_ids)):
            raise ValueError("version IDs must be unique")
        return self


class KA1043KnowledgeLineageTracker(KnowledgeAlgorithm):
    """Build a lineage graph from supplied immutable version events."""

    input_schema = KA1043Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1043"

    def _run_logic(self, input_data: KA1043Input) -> dict[str, Any]:
        events = {item.version_id: item for item in input_data.events}
        known = set(events)
        missing = sorted(
            {
                parent_id
                for item in input_data.events
                for parent_id in item.parent_version_ids
                if parent_id not in known
            }
        )
        children: dict[str, list[str]] = defaultdict(list)
        indegree = {version_id: 0 for version_id in known}
        for item in input_data.events:
            for parent_id in item.parent_version_ids:
                if parent_id in known:
                    children[parent_id].append(item.version_id)
                    indegree[item.version_id] += 1
        for child_ids in children.values():
            child_ids.sort()

        ready = sorted(
            version_id for version_id, degree in indegree.items() if degree == 0
        )
        ordered: list[str] = []
        while ready:
            version_id = ready.pop(0)
            ordered.append(version_id)
            for child_id in children.get(version_id, []):
                indegree[child_id] -= 1
                if indegree[child_id] == 0:
                    ready.append(child_id)
                    ready.sort()
        cycle_nodes = sorted(set(known) - set(ordered))
        roots = sorted(
            item.version_id
            for item in input_data.events
            if not [parent for parent in item.parent_version_ids if parent in known]
        )
        leaves = sorted(version_id for version_id in known if not children[version_id])
        ordered_events = [
            {
                "event_id": events[version_id].event_id,
                "version_id": version_id,
                "parent_version_ids": sorted(events[version_id].parent_version_ids),
                "event_type": events[version_id].event_type,
                "source_ref": events[version_id].source_ref,
            }
            for version_id in ordered
        ]
        complete = not missing and not cycle_nodes
        return {
            "success": True,
            "status": "lineage_valid" if complete else "lineage_incomplete",
            "knowledge_id": input_data.knowledge_id,
            "lineage_complete": complete,
            "root_version_ids": roots,
            "leaf_version_ids": leaves,
            "topological_version_order": ordered,
            "ordered_events": ordered_events,
            "missing_parent_version_ids": missing,
            "cycle_version_ids": cycle_nodes,
            "event_count": len(input_data.events),
            "lineage_persisted": False,
            "deterministic": True,
            "limitations": (
                "The result validates and orders caller-supplied lineage only. "
                "It does not prove source authenticity or persist lineage events."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1043KnowledgeLineageTracker(context).run(context)
