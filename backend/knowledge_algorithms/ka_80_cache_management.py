"""
KA-080: Cache Management
Purpose: Manage cache layers, eviction policies, and consistency in transient storage.
"""

import json
import logging
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA080CacheInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    key: str = Field("*", description="The cache key to operate on")
    operation: str = Field("stats", description="The cache operation")
    cache_state: dict[str, Any] = Field(default_factory=dict)
    value: Any = None
    ttl_seconds: Any = None


class KA080CacheManagement(KnowledgeAlgorithm):
    """
    KA-080: Local cache orchestration and consistency management engine.
    """

    input_schema = KA080CacheInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-080"
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "ka_80_config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return {}

    def _run_logic(self, input_data: KA080CacheInput) -> dict[str, Any]:
        cache_key = input_data.key
        operation = input_data.operation.lower()
        state = dict(input_data.cache_state)
        self.log_execution_step(
            "Managing Cache Objects", {"op": operation, "key": cache_key}
        )

        entries = self._entries(state)
        plan = self._operation_plan(
            operation, cache_key, input_data.value, input_data.ttl_seconds, entries
        )
        stats = self._stats(entries)
        return {
            "success": True,
            "operation_result": plan["result"],
            "operation_plan": plan,
            "stats": stats,
            "layer_active": self.config.get("cache_layer", "local"),
            "policy_applied": self.config.get("eviction_policy", "LRU"),
            "consistency_status": self._consistency_status(entries),
            "cache_mutation_applied": False,
            "effect_service_required": operation in {"set", "evict", "delete", "clear"},
            "deterministic": True,
            "limitations": (
                "This evaluates caller-supplied cache metadata and creates an "
                "operation plan. Only KnowledgeStoreService may mutate cache state."
            ),
        }

    @staticmethod
    def _entries(state: dict[str, Any]) -> dict[str, Any]:
        entries = state.get("entries", state)
        return entries if isinstance(entries, dict) else {}

    def _operation_plan(
        self,
        operation: str,
        key: str,
        value: Any,
        ttl_seconds: Any,
        entries: dict[str, Any],
    ) -> dict[str, Any]:
        ttl = self._safe_int(ttl_seconds, self.config.get("default_ttl_seconds", 3600))
        if operation == "get":
            return {
                "operation": operation,
                "key": key,
                "result": "HIT" if key in entries else "MISS",
                "ttl_seconds": ttl,
            }
        if operation == "set":
            return {
                "operation": operation,
                "key": key,
                "result": "WRITE_PLANNED",
                "value_size_bytes": len(str(value).encode()),
                "ttl_seconds": ttl,
            }
        if operation in {"evict", "delete"}:
            return {
                "operation": operation,
                "key": key,
                "result": "EVICT_PLANNED"
                if key in entries or key == "*"
                else "NOOP_MISSING_KEY",
            }
        if operation == "clear":
            return {
                "operation": operation,
                "key": key,
                "result": "CLEAR_PLANNED",
                "affected_entries": len(entries),
            }
        return {
            "operation": operation,
            "key": key,
            "result": "STATS_ONLY",
            "ttl_seconds": ttl,
        }

    def _stats(self, entries: dict[str, Any]) -> dict[str, Any]:
        memory_bytes = sum(
            len(str(key).encode()) + len(str(value).encode())
            for key, value in entries.items()
        )
        max_memory = (
            self._safe_int(self.config.get("max_memory_mb", 2048), 2048) * 1024 * 1024
        )
        stale = sum(
            1
            for value in entries.values()
            if isinstance(value, dict) and value.get("stale")
        )
        hits = sum(
            int(value.get("hits", 0))
            for value in entries.values()
            if isinstance(value, dict)
        )
        misses = sum(
            int(value.get("misses", 0))
            for value in entries.values()
            if isinstance(value, dict)
        )
        total = hits + misses
        return {
            "entry_count": len(entries),
            "hit_ratio": round(hits / total, 4) if total else 0.0,
            "stale_entries": stale,
            "memory_usage_mb": round(memory_bytes / (1024 * 1024), 4),
            "memory_pressure": round(memory_bytes / max_memory, 4)
            if max_memory
            else 0.0,
        }

    @staticmethod
    def _consistency_status(entries: dict[str, Any]) -> str:
        if any(
            isinstance(value, dict) and value.get("stale") for value in entries.values()
        ):
            return "STALE_ENTRIES_PRESENT"
        return "CONSISTENT"

    @staticmethod
    def _safe_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(default)


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA080CacheManagement(context).run(context)
