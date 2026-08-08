"""
KA-019: Knowledge Synthesis
Purpose: Merge and unify multiple knowledge fragments and findings into a consistent state.
"""
import logging
import json
import os
from typing import Any, Dict, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA019Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: List[Dict[str, Any]] = Field(default_factory=list, description="A list of knowledge fragments to synthesize")
    dependency_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

class KA019KnowledgeSynthesis(KnowledgeAlgorithm):
    """
    KA-019: Synthesis engine for diverse findings onto a unified state.
    """
    input_schema = KA019Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-019"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_19_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA019Input) -> Dict[str, Any]:
        findings = input_data.findings
        dependencies = input_data.dependency_results
        self.log_execution_step("Synthesizing Results", {"findingsCount": len(findings)})
        
        unified_state = {cat: [] for cat in self.config.get("categories", ["FACT", "ASSUMPTION"])}
        for index, f in enumerate(findings):
            cat = f.get("category", "FACT").upper()
            if cat in unified_state:
                confidence = max(0.0, min(1.0, float(f.get("confidence", 0.5))))
                unified_state[cat].append({
                    "finding_id": str(f.get("id") or f"finding-{index + 1}"),
                    "content": f.get("content", ""),
                    "confidence": confidence,
                    "source_ka": f.get("source_ka", "unknown"),
                    "evidence_refs": sorted(set(f.get("evidence_refs") or [])),
                })
                
        for cat in unified_state:
            unified_state[cat] = self._resolve_conflicts(unified_state[cat])
            
        return {
            "success": True,
            "unified_knowledge": unified_state,
            "summary_points": self._generate_summary(unified_state),
            "dependencies_consumed": sorted(dependencies),
            "knowledge_persisted": False,
            "deterministic": True,
            "limitations": (
                "Synthesis organizes caller-supplied findings and does not "
                "resolve factual contradictions or establish truth."
            ),
        }

    def _resolve_conflicts(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        best: Dict[str, Dict[str, Any]] = {}
        for item in items:
            signature = " ".join(str(item["content"]).lower().split())
            current = best.get(signature)
            if current is None or (item["confidence"], item["finding_id"]) > (
                current["confidence"],
                current["finding_id"],
            ):
                best[signature] = item
        return sorted(
            best.values(),
            key=lambda item: (-item["confidence"], item["finding_id"]),
        )

    def _generate_summary(self, state: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        summary = []
        for cat, items in state.items():
            if items:
                summary.append(f"{cat}: {len(items)} items synthesized.")
        return summary

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA019KnowledgeSynthesis(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-019 Failed: {e}")
        return {"success": False, "error": str(e)}
