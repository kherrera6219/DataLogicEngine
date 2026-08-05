"""
KA-079: Data Retrieval
Purpose: Optimize data lookup and search operations using indexed queries and vector search fallbacks.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA079RetrievalInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    query: Any = Field(
        default_factory=dict, description="The query parameters for data lookup"
    )
    records: List[Dict[str, Any]] = Field(default_factory=list)
    max_results: Any = None
    filters: Dict[str, Any] = Field(default_factory=dict)


class KA079DataRetrieval(KnowledgeAlgorithm):
    """
    KA-079: Optimized local data retrieval and multi-engine search orchestration.
    """

    input_schema = KA079RetrievalInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-079"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "ka_79_config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA079RetrievalInput) -> Dict[str, Any]:
        query_text, query_filters = self._normalize_query(input_data.query)
        filters = {**query_filters, **input_data.filters}
        records = input_data.records or self._records_from_context(input_data)
        max_results = self._safe_int(
            input_data.max_results, self.config.get("max_results_size", 25)
        )

        self.log_execution_step(
            "Executing Optimized Retrieval",
            {
                "query": query_text[:80],
                "records": len(records),
                "filters": len(filters),
            },
        )

        found_records = self._search_records(records, query_text, filters, max_results)

        return {
            "success": True,
            "status": "supplied_records_ranked",
            "results_count": len(found_records),
            "results": found_records,
            "retrieval_mode": "deterministic_lexical_overlap",
            "external_engine_used": False,
            "filters_applied": filters,
            "local_only": True,
            "store_mutation_applied": False,
            "deterministic": True,
            "limitations": (
                "Ranking covers only supplied records using lexical overlap and "
                "declared filters; it is not vector search or corpus completeness proof."
            ),
        }

    @staticmethod
    def _normalize_query(query: Any) -> tuple[str, Dict[str, Any]]:
        if isinstance(query, dict):
            query_text = str(
                query.get("text") or query.get("q") or query.get("query") or ""
            )
            filters = dict(query.get("filters") or {})
            for key, value in query.items():
                if key not in {
                    "text",
                    "q",
                    "query",
                    "filters",
                    "records",
                    "documents",
                    "max_results",
                }:
                    filters.setdefault(key, value)
            return query_text, filters
        return str(query or ""), {}

    @staticmethod
    def _records_from_context(input_data: KA079RetrievalInput) -> List[Dict[str, Any]]:
        raw = input_data.model_dump()
        query = raw.get("query")
        if isinstance(query, dict):
            nested = query.get("records") or query.get("documents") or query.get("data")
            if isinstance(nested, list):
                return [
                    item if isinstance(item, dict) else {"content": str(item)}
                    for item in nested
                ]

        data = raw.get("data")
        if isinstance(data, list):
            return [
                item if isinstance(item, dict) else {"content": str(item)}
                for item in data
            ]
        if isinstance(data, dict):
            nested = data.get("records") or data.get("documents") or data.get("items")
            if isinstance(nested, list):
                return [
                    item if isinstance(item, dict) else {"content": str(item)}
                    for item in nested
                ]
            return [{"id": key, "content": value} for key, value in data.items()]
        return []

    @classmethod
    def _search_records(
        cls,
        records: List[Dict[str, Any]],
        query_text: str,
        filters: Dict[str, Any],
        max_results: int,
    ) -> List[Dict[str, Any]]:
        query_terms = cls._tokens(query_text)
        results = []
        for index, record in enumerate(records):
            if not cls._matches_filters(record, filters):
                continue
            searchable = cls._record_text(record)
            record_terms = cls._tokens(searchable)
            overlap = query_terms & record_terms
            if query_terms and not overlap:
                continue
            relevance = 1.0 if not query_terms else len(overlap) / len(query_terms)
            if query_text and query_text.lower() in searchable.lower():
                relevance = min(1.0, relevance + 0.25)
            results.append(
                {
                    "id": str(record.get("id", f"record_{index}")),
                    "relevance": round(relevance, 4),
                    "matched_terms": sorted(overlap),
                    "record": record,
                }
            )
        results.sort(key=lambda item: (-item["relevance"], item["id"]))
        return results[: max(1, max_results)]

    @staticmethod
    def _matches_filters(record: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        for key, expected in filters.items():
            if expected in (None, ""):
                continue
            actual = record.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif str(actual).lower() != str(expected).lower():
                return False
        return True

    @staticmethod
    def _record_text(record: Dict[str, Any]) -> str:
        values = []
        for key, value in record.items():
            if isinstance(value, (dict, list)):
                values.append(json.dumps(value, sort_keys=True))
            else:
                values.append(f"{key} {value}")
        return " ".join(values)

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {
            token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 1
        }

    @staticmethod
    def _safe_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(default)


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA079DataRetrieval(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-079 Failed: {e}")
        return {"success": False, "error": str(e)}
