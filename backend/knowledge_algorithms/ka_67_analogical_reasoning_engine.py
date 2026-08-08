"""
KA-067: Analogical Reasoning Engine
Purpose: Identify patterns and structures in one domain and apply them to solve problems or explain concepts in another (cross-domain transfer).
"""
import logging
import json
import os
from typing import Any, Dict
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA067AnalogicalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_domain: Dict[str, Any] = Field(default_factory=dict, description="Source domain data for analogy mapping")
    target_domain: Dict[str, Any] = Field(default_factory=dict, description="Target domain data for analogy mapping")

class KA067AnalogicalReasoningEngine(KnowledgeAlgorithm):
    """
    KA-067: Structural alignment and cross-domain transfer engine for analogical reasoning.
    """
    input_schema = KA067AnalogicalInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-067"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_67_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA067AnalogicalInput) -> Dict[str, Any]:
        source_domain = input_data.source_domain
        target_domain = input_data.target_domain
        self.log_execution_step("Building Analogical Mappings", {"source": source_domain.get("name")})
        
        analogies = []
        source_relations = sorted(
            source_domain.get("relations", []),
            key=lambda row: (
                str(row.get("entity") or row.get("source") or ""),
                str(row.get("predicate") or ""),
                str(row.get("target") or ""),
            ),
        )
        target_entities = sorted(
            target_domain.get("entities", []),
            key=lambda row: str(row.get("name") or row.get("id") or ""),
        )
        for relation in source_relations:
            source_roles = {
                str(value).strip().lower()
                for value in relation.get("roles", [])
                if str(value).strip()
            }
            ranked = []
            for entity in target_entities:
                target_roles = {
                    str(value).strip().lower()
                    for value in entity.get("roles", entity.get("attributes", []))
                    if str(value).strip()
                }
                union = source_roles | target_roles
                overlap = len(source_roles & target_roles) / len(union) if union else 0.0
                type_match = bool(
                    relation.get("type")
                    and relation.get("type") == entity.get("type")
                )
                score = round((overlap * 0.8) + (0.2 if type_match else 0.0), 6)
                ranked.append((score, str(entity.get("name") or entity.get("id") or ""), entity))
            if not ranked:
                continue
            score, target_name, matched = max(ranked, key=lambda row: (row[0], row[1]))
            if score <= 0 and len(target_entities) > 1:
                continue
            analogies.append(
                {
                    "source_concept": relation.get("entity") or relation.get("source"),
                    "target_concept": target_name,
                    "relation": relation.get("predicate"),
                    "structural_score": score,
                    "matched_roles": sorted(
                        source_roles
                        & {
                            str(value).strip().lower()
                            for value in matched.get("roles", matched.get("attributes", []))
                            if str(value).strip()
                        }
                    ),
                    "validation_status": "candidate_mapping",
                }
            )
        analogies.sort(
            key=lambda row: (
                -row["structural_score"],
                str(row["source_concept"]),
                row["target_concept"],
            )
        )
                  
        return {
            "success": True,
            "analogies": analogies[:self.config.get("max_analogies", 3)],
            "strategy": "deterministic_structural_alignment",
            "transfer_applied": False,
            "deterministic": True,
            "limitations": (
                "Mappings compare explicit roles and types only. They are "
                "candidates and do not establish causal or semantic equivalence."
            ),
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA067AnalogicalReasoningEngine(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-067 Failed: {e}")
        return {"success": False, "error": str(e)}
