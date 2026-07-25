"""KA-098: aggregate supplied profiler measurements without fabricating data."""

from __future__ import annotations

from statistics import fmean
from typing import Any

from pydantic import BaseModel, Field

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ProfileSample(BaseModel):
    duration_ms: float = Field(ge=0)
    cpu_percent: float | None = Field(default=None, ge=0, le=100)
    memory_mb: float | None = Field(default=None, ge=0)
    calls: int | None = Field(default=None, ge=0)
    hotspot: str | None = Field(default=None, max_length=500)


class KA098ProfilingInput(BaseModel):
    target: str = Field(default="main_pipeline", min_length=1, max_length=500)
    samples: list[ProfileSample] = Field(
        default_factory=list,
        max_length=100_000,
    )


class KA098Profiling(KnowledgeAlgorithm):
    """Compute measured aggregates; collection remains an owning-service task."""

    input_schema = KA098ProfilingInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-098"

    def _run_logic(self, input_data: KA098ProfilingInput) -> dict[str, Any]:
        if not input_data.samples:
            return {
                "success": False,
                "status": "measurements_required",
                "target": input_data.target,
                "limitations": (
                    "KA-098 analyzes supplied profiler samples; it does not "
                    "attach a hidden profiler or invent measurements."
                ),
            }
        duration_values = [sample.duration_ms for sample in input_data.samples]
        cpu_values = [
            sample.cpu_percent
            for sample in input_data.samples
            if sample.cpu_percent is not None
        ]
        memory_values = [
            sample.memory_mb
            for sample in input_data.samples
            if sample.memory_mb is not None
        ]
        hotspots: dict[str, int] = {}
        for sample in input_data.samples:
            if sample.hotspot:
                hotspots[sample.hotspot] = hotspots.get(sample.hotspot, 0) + 1
        metrics = {
            "sample_count": len(input_data.samples),
            "duration_ms": {
                "mean": round(fmean(duration_values), 6),
                "min": min(duration_values),
                "max": max(duration_values),
            },
            "cpu_percent_mean": (
                round(fmean(cpu_values), 6) if cpu_values else None
            ),
            "memory_mb_peak": max(memory_values) if memory_values else None,
            "calls_total": sum(
                sample.calls or 0 for sample in input_data.samples
            ),
            "hot_spots": [
                {"name": name, "sample_count": count}
                for name, count in sorted(
                    hotspots.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            ],
        }
        return {
            "success": True,
            "profile_id": stable_identifier(
                "profile",
                {"target": input_data.target, "metrics": metrics},
            ),
            "target": input_data.target,
            "metrics": metrics,
            "profile_dump": None,
            "measurement_source": "caller_supplied_profiler_samples",
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA098Profiling(context).run(context)
