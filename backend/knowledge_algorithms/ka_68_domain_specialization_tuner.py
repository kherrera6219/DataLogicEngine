"""KA-068: deterministic domain-specialization planning."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA068TunerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: str = Field(default="general", min_length=1, max_length=100)
    risk_class: Literal["low", "medium", "high", "critical"] = "medium"


class KA068DomainSpecializationTuner(KnowledgeAlgorithm):
    """Propose bounded review settings without changing pipeline weights."""

    input_schema = KA068TunerInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-068"

    def _run_logic(self, input_data: KA068TunerInput) -> dict[str, Any]:
        domain = input_data.domain.strip().casefold()
        policies = {
            "general": ("standard", 0),
            "technical": ("enhanced", 1),
            "medical": ("strict", 1),
            "legal": ("strict", 1),
            "financial": ("strict", 1),
            "creative": ("standard", 0),
        }
        supported = domain in policies
        validation, additional_review_passes = policies.get(domain, policies["general"])
        if input_data.risk_class in {"high", "critical"}:
            validation = "strict"
            additional_review_passes = max(additional_review_passes, 1)
        return {
            "success": True,
            "status": "domain_specialization_proposed",
            "domain_context": domain,
            "supported_domain": supported,
            "tuning_proposal": {
                "validation_strictness": validation,
                "additional_review_passes": additional_review_passes,
                "risk_class": input_data.risk_class,
            },
            "pipeline_weights_changed": False,
            "search_started": False,
            "context_applied": False,
            "deterministic": True,
            "limitations": (
                "The domain is caller-declared. The KA proposes review settings only "
                "and does not change routing, validation, search, or model weights."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA068DomainSpecializationTuner(context).run(context)
