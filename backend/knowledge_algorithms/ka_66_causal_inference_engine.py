"""
KA-066: Causal Inference Engine
Purpose: Infer cause-effect relationships from events and dependencies, and represent them in a causal graph.
"""
import json
import logging
import os
from typing import Any, Dict, List

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA066CausalInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Events to analyze for causal links")
    dependencies: List[Dict[str, Any]] = Field(default_factory=list, description="Known dependencies between events or nodes")
    confounders: List[str] = Field(default_factory=list)


class KA066CausalInferenceEngine(KnowledgeAlgorithm):
    """
    KA-066: Causal relationship mapping and inference engine for structured knowledge graphs.
    """
    input_schema = KA066CausalInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-066"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_66_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA066CausalInput) -> Dict[str, Any]:
        events = input_data.events
        dependencies = input_data.dependencies
        self.log_execution_step("Inferring Causal Relationships", {"event_count": len(events), "dependency_count": len(dependencies)})

        event_index = {str(event.get("id", index)): event for index, event in enumerate(events)}
        causal_claims = [
            self._claim_from_dependency(dep, event_index, input_data.confounders)
            for dep in dependencies
        ]
        causal_claims.extend(self._claims_from_temporal_order(events, input_data.confounders))
        causal_claims = self._dedupe_claims(causal_claims)
        threshold = float(self.config.get("min_correlation_threshold", 0.7))
        accepted = [claim for claim in causal_claims if claim["confidence"] >= threshold]
        return {
            "success": True,
            "causal_graph_fragment": accepted,
            "candidate_claims": causal_claims,
            "inference_method": "deterministic_temporal_dependency_scoring",
            "threshold": threshold,
        }

    @classmethod
    def _claim_from_dependency(cls, dep: Dict[str, Any], event_index: Dict[str, Dict[str, Any]], confounders: List[str]) -> Dict[str, Any]:
        source = str(dep.get("source") or dep.get("cause") or "")
        target = str(dep.get("target") or dep.get("effect") or "")
        support = float(dep.get("weight", dep.get("confidence", 0.65)) or 0.65)
        temporal = cls._temporal_support(event_index.get(source), event_index.get(target))
        confounder_penalty = cls._confounder_penalty(source, target, confounders)
        confidence = round(max(0.0, min(0.98, support * 0.55 + temporal * 0.35 - confounder_penalty)), 4)
        return {
            "cause": source,
            "effect": target,
            "relationship_type": "PROBABLE_CAUSE" if confidence >= 0.7 else "POSSIBLE_CAUSE",
            "confidence": confidence,
            "signals": {"dependency_support": support, "temporal_support": temporal, "confounder_penalty": confounder_penalty},
        }

    @classmethod
    def _claims_from_temporal_order(cls, events: List[Dict[str, Any]], confounders: List[str]) -> List[Dict[str, Any]]:
        ordered = sorted(events, key=lambda item: item.get("timestamp", item.get("time", 0)))
        claims = []
        for left, right in zip(ordered, ordered[1:]):
            source = str(left.get("id", left.get("name", "")))
            target = str(right.get("id", right.get("name", "")))
            if not source or not target:
                continue
            penalty = cls._confounder_penalty(source, target, confounders)
            confidence = round(max(0.0, 0.62 - penalty), 4)
            claims.append({
                "cause": source,
                "effect": target,
                "relationship_type": "TEMPORAL_PRECEDENCE",
                "confidence": confidence,
                "signals": {"dependency_support": 0.0, "temporal_support": 1.0, "confounder_penalty": penalty},
            })
        return claims

    @staticmethod
    def _temporal_support(source: Dict[str, Any] | None, target: Dict[str, Any] | None) -> float:
        if not source or not target:
            return 0.4
        source_time = source.get("timestamp", source.get("time"))
        target_time = target.get("timestamp", target.get("time"))
        if source_time is None or target_time is None:
            return 0.5
        return 1.0 if source_time <= target_time else 0.1

    @staticmethod
    def _confounder_penalty(source: str, target: str, confounders: List[str]) -> float:
        pair = f"{source} {target}".lower()
        return 0.15 if any(confounder.lower() in pair for confounder in confounders) else 0.0

    @staticmethod
    def _dedupe_claims(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        best: Dict[tuple[str, str], Dict[str, Any]] = {}
        for claim in claims:
            key = (claim["cause"], claim["effect"])
            if key not in best or claim["confidence"] > best[key]["confidence"]:
                best[key] = claim
        return sorted(best.values(), key=lambda item: (-item["confidence"], item["cause"], item["effect"]))


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA066CausalInferenceEngine(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-066 Failed: {e}")
        return {"success": False, "error": str(e)}
