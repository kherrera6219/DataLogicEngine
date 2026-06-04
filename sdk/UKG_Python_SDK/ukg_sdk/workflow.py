from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .exceptions import UKGWorkflowError
from .models import WorkflowResult, EvidencePacket
from ukg_sdk.truth_engine.core import TruthEngine
from .utils import package_data_path, read_json


class ComplexityTier(str, Enum):
    trivial = "TRIVIAL"
    easy = "EASY"
    moderate = "MODERATE"
    hard = "HARD"
    extreme = "EXTREME"


class WorkflowConfig(BaseModel):
    version: str = "2.5"
    truth17_enabled: bool = True
    tiers: Dict[str, Any] = Field(default_factory=dict)
    ka_pipeline_defaults: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class WorkflowRunner:
    workflow: Dict[str, Any]
    truth_engine: Optional[TruthEngine] = None

    @classmethod
    def load_default(cls) -> "WorkflowRunner":
        wf = read_json(package_data_path("workflow.json"))
        te = TruthEngine.load_default()
        return cls(workflow=wf, truth_engine=te)

    def get_tier_policy(self, tier: ComplexityTier) -> Dict[str, Any]:
        tiers = self.workflow.get("tiers") or self.workflow.get("complexity_tiers")
        if isinstance(tiers, dict):
            policy = tiers.get(tier.value) or tiers.get(tier.value.lower())
            if policy:
                return policy

        tier_name = tier.value.lower()
        if isinstance(tiers, list):
            for policy in tiers:
                if not isinstance(policy, dict):
                    continue
                candidate = str(policy.get("tier") or policy.get("name") or "").lower()
                if candidate == tier_name:
                    return policy

        tier_system = self.workflow.get("tier_system") or {}
        if isinstance(tier_system, dict):
            tier_policies = tier_system.get("tiers") or {}
            if isinstance(tier_policies, dict):
                return tier_policies.get(tier.value) or tier_policies.get(tier_name) or {}
            if isinstance(tier_policies, list):
                for policy in tier_policies:
                    if not isinstance(policy, dict):
                        continue
                    candidate = str(policy.get("tier") or policy.get("name") or "").lower()
                    if candidate == tier_name:
                        return policy

        return {}

    def choose_tier(self, *, complexity_score: float, stakes: str = "normal") -> ComplexityTier:
        if stakes in {"high", "critical"}:
            return ComplexityTier.extreme if complexity_score >= 0.65 else ComplexityTier.hard
        if complexity_score < 0.15:
            return ComplexityTier.trivial
        if complexity_score < 0.35:
            return ComplexityTier.easy
        if complexity_score < 0.65:
            return ComplexityTier.moderate
        if complexity_score < 0.85:
            return ComplexityTier.hard
        return ComplexityTier.extreme

    def run_local_stub(
        self,
        *,
        query: str,
        tier: ComplexityTier,
        evidence: Optional[EvidencePacket] = None,
    ) -> WorkflowResult:
        tier_policy = self.get_tier_policy(tier)
        if not tier_policy:
            raise UKGWorkflowError(f"Tier policy not found for {tier}")
        return WorkflowResult(
            tier=tier.value,
            answer={
                "query": query,
                "tier_policy": tier_policy,
                "recommended_pipeline": (
                    tier_policy.get("pipeline")
                    or tier_policy.get("ka_pipeline")
                    or tier_policy.get("ka_pipeline_hint")
                ),
                "notes": [
                    "Local stub only; send this payload to your UKG service (ORCH + KA registry) to execute."
                ],
            },
            confidence=None,
            entropy=None,
            evidence=evidence,
            audit_events=[],
            artifacts={"truth_engine": (self.truth_engine.summarize() if self.truth_engine else None)},
        )
