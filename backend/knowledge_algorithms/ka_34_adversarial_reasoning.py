"""
KA-034: Adversarial Reasoning
Purpose: Stress-test system outputs by applying adversarial constraints and attacks on assumptions.
"""
import json
import logging
import os
import re
from typing import Any, Dict, List

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA034Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    scenario: str = Field("", description="The scenario to test adversarial hits against")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions to stress-test")
    evidence: List[Any] = Field(default_factory=list)


class KA034AdversarialReasoning(KnowledgeAlgorithm):
    """
    KA-034: Deterministic adversarial robustness testing engine for system assumptions.
    """
    input_schema = KA034Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-034"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_34_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA034Input) -> Dict[str, Any]:
        assumptions = input_data.assumptions or self._assumptions_from_scenario(input_data.scenario)
        self.log_execution_step("Running Adversarial Reasoning", {"assumption_count": len(assumptions)})

        threat_models = self.config.get("threat_models", {})
        attacks = [self._attack_assumption(assumption, input_data.scenario, input_data.evidence, threat_models) for assumption in assumptions]
        average_impact = sum(item["impact_score"] for item in attacks) / len(attacks) if attacks else 0.0
        robustness_score = round(max(0.0, 1.0 - average_impact), 4)
        threshold = float(self.config.get("robustness_threshold", 0.6))
        return {
            "success": True,
            "robustness_score": robustness_score,
            "attacks_simulated": attacks,
            "is_robust": robustness_score >= threshold,
            "mitigation_plan": [attack["mitigation"] for attack in attacks if attack["vulnerability_found"]],
            "method": "deterministic_assumption_stress_test",
        }

    @classmethod
    def _attack_assumption(cls, assumption: str, scenario: str, evidence: List[Any], threat_models: Dict[str, Any]) -> Dict[str, Any]:
        text = f"{scenario} {assumption}".lower()
        evidence_text = " ".join(cls._text(item) for item in evidence).lower()
        threat_scores = {
            "misinformation": cls._keyword_score(text, ("claim", "source", "reported", "external")) + (0.2 if assumption.lower() not in evidence_text else 0),
            "logical_injection": cls._keyword_score(text, ("always", "never", "must", "guarantee", "all")),
            "persona_manipulation": cls._keyword_score(text, ("user", "persona", "stakeholder", "tone")),
            "context_poisoning": cls._keyword_score(text, ("context", "memory", "prompt", "retrieval", "input")),
        }
        for threat, configured in threat_models.items():
            threat_scores.setdefault(threat, float(configured) if isinstance(configured, (int, float)) else 0.2)
        threat_type, score = max(threat_scores.items(), key=lambda item: (item[1], item[0]))
        impact = round(min(1.0, max(0.05, score)), 4)
        return {
            "target_assumption": assumption,
            "threat_type": threat_type,
            "impact_score": impact,
            "vulnerability_found": impact >= 0.3,
            "evidence_support": assumption.lower() in evidence_text,
            "mitigation": cls._mitigation(threat_type, assumption),
        }

    @staticmethod
    def _assumptions_from_scenario(scenario: str) -> List[str]:
        clauses = [part.strip() for part in re.split(r"[.;]", scenario) if part.strip()]
        return clauses[:5] or ["scenario is valid"]

    @staticmethod
    def _keyword_score(text: str, keywords: tuple[str, ...]) -> float:
        hits = sum(1 for keyword in keywords if keyword in text)
        return min(0.8, hits * 0.22)

    @staticmethod
    def _mitigation(threat_type: str, assumption: str) -> str:
        actions = {
            "misinformation": "Require corroborating local evidence before trusting the assumption.",
            "logical_injection": "Replace absolute language with bounded preconditions and exception checks.",
            "persona_manipulation": "Separate stakeholder tone adaptation from factual decision logic.",
            "context_poisoning": "Validate retrieved context provenance and isolate untrusted input.",
        }
        return f"{actions.get(threat_type, 'Add explicit validation and monitoring.')} Assumption: {assumption}"

    @staticmethod
    def _text(value: Any) -> str:
        if isinstance(value, dict):
            return " ".join(str(item) for item in value.values())
        return str(value)


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA034AdversarialReasoning(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-034 Failed: {e}")
        return {"success": False, "error": str(e)}
