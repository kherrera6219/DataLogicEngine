"""KA-085: deterministic, in-memory tabular feature construction."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import statistics
from typing import Any

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


class KA085FeatureInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_data: list[dict[str, Any]] = Field(min_length=1, max_length=10_000)
    max_categories: int = Field(default=32, ge=1, le=256)

    @field_validator("raw_data")
    @classmethod
    def _validate_records(
        cls,
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        for record in records:
            if len(record) > 500:
                raise ValueError("feature records exceed the 500-column limit")
            for key, value in record.items():
                if not str(key).strip() or len(str(key)) > 200:
                    raise ValueError("feature names must contain 1 through 200 characters")
                if isinstance(value, (dict, list, set, tuple)):
                    raise ValueError("feature values must be scalar")
                if isinstance(value, float) and not math.isfinite(value):
                    raise ValueError("numeric feature values must be finite")
        return records


class KA085FeatureEngineering(KnowledgeAlgorithm):
    """Apply measured median imputation, scaling, and bounded one-hot encoding."""

    input_schema = KA085FeatureInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-085"

    def _run_logic(self, input_data: KA085FeatureInput) -> dict[str, Any]:
        columns = sorted(
            {str(key) for record in input_data.raw_data for key in record}
        )
        numeric_columns: list[str] = []
        categorical_columns: list[str] = []
        dropped_columns: list[dict[str, str]] = []
        for column in columns:
            present = [
                record.get(column)
                for record in input_data.raw_data
                if record.get(column) is not None
            ]
            if present and all(self._is_number(value) for value in present):
                numeric_columns.append(column)
            elif present and all(isinstance(value, (str, bool)) for value in present):
                categories = {self._category_key(value) for value in present}
                if len(categories) <= input_data.max_categories:
                    categorical_columns.append(column)
                else:
                    dropped_columns.append(
                        {"column": column, "reason": "category_limit_exceeded"}
                    )
            else:
                dropped_columns.append(
                    {"column": column, "reason": "unsupported_or_empty_values"}
                )

        numeric_stats = self._numeric_stats(
            input_data.raw_data,
            numeric_columns,
        )
        category_features = self._category_features(
            input_data.raw_data,
            categorical_columns,
        )
        engineered_records = [
            self._engineer_record(
                record,
                numeric_stats=numeric_stats,
                category_features=category_features,
            )
            for record in input_data.raw_data
        ]
        feature_names = sorted(
            {name for record in engineered_records for name in record}
        )
        plan_payload = {
            "numeric_stats": numeric_stats,
            "category_feature_names": {
                column: sorted(mapping.values())
                for column, mapping in category_features.items()
            },
            "dropped_columns": dropped_columns,
            "feature_names": feature_names,
        }
        plan_sha256 = hashlib.sha256(
            json.dumps(
                plan_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.log_execution_step(
            "Engineering Measured Features",
            {
                "record_count": len(input_data.raw_data),
                "feature_count": len(feature_names),
            },
        )
        return {
            "success": True,
            "schema_version": "dle.feature-engineering-result.v1",
            "plan_sha256": plan_sha256,
            "records_processed": len(input_data.raw_data),
            "feature_count": len(feature_names),
            "feature_names": feature_names,
            "engineered_records": engineered_records,
            "numeric_feature_stats": numeric_stats,
            "categorical_feature_counts": {
                column: len(mapping)
                for column, mapping in category_features.items()
            },
            "dropped_columns": dropped_columns,
            "operations_applied": [
                "median_imputation",
                "standard_scaling",
                "bounded_one_hot_encoding",
            ],
            "artifact_created": False,
            "persistence_applied": False,
        }

    @staticmethod
    def _is_number(value: Any) -> bool:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )

    @classmethod
    def _numeric_stats(
        cls,
        records: list[dict[str, Any]],
        columns: list[str],
    ) -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        for column in columns:
            values = [
                float(record[column])
                for record in records
                if cls._is_number(record.get(column))
            ]
            median = statistics.median(values)
            imputed = [
                float(record[column])
                if cls._is_number(record.get(column))
                else median
                for record in records
            ]
            mean = statistics.fmean(imputed)
            standard_deviation = math.sqrt(
                statistics.fmean([(value - mean) ** 2 for value in imputed])
            )
            result[column] = {
                "median": round(median, 12),
                "mean": round(mean, 12),
                "standard_deviation": round(standard_deviation, 12),
            }
        return result

    @classmethod
    def _category_features(
        cls,
        records: list[dict[str, Any]],
        columns: list[str],
    ) -> dict[str, dict[str, str]]:
        output: dict[str, dict[str, str]] = {}
        for column in columns:
            categories = sorted(
                {
                    cls._category_key(record.get(column))
                    for record in records
                }
            )
            output[column] = {
                category: (
                    f"one_hot:{column}:"
                    f"{hashlib.sha256(category.encode('utf-8')).hexdigest()[:12]}"
                )
                for category in categories
            }
        return output

    @classmethod
    def _engineer_record(
        cls,
        record: dict[str, Any],
        *,
        numeric_stats: dict[str, dict[str, float]],
        category_features: dict[str, dict[str, str]],
    ) -> dict[str, float]:
        output: dict[str, float] = {}
        for column, stats in numeric_stats.items():
            value = (
                float(record[column])
                if cls._is_number(record.get(column))
                else stats["median"]
            )
            deviation = stats["standard_deviation"]
            output[f"scaled:{column}"] = round(
                0.0 if deviation == 0.0 else (value - stats["mean"]) / deviation,
                12,
            )
        for column, mapping in category_features.items():
            selected = mapping[cls._category_key(record.get(column))]
            for feature_name in mapping.values():
                output[feature_name] = 1.0 if feature_name == selected else 0.0
        return dict(sorted(output.items()))

    @staticmethod
    def _category_key(value: Any) -> str:
        return "__missing__" if value is None else json.dumps(value, sort_keys=True)


def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        return KA085FeatureEngineering(context).run(context)
    except Exception as exc:  # pragma: no cover - legacy adapter boundary
        logger.error("KA-085 failed: %s", exc)
        return {"success": False, "error": str(exc)}
