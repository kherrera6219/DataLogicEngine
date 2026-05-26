"""
KA-012: Persona Simulation
Purpose: Simulates multiple expert personas to provide diverse, multi-perspective analysis.
"""
import logging
import json
import os
import random
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA012Input(BaseModel):
    query: str = Field(..., description="The query to analyze via personas")
    active_personas: List[str] = Field(default=["knowledge", "sector", "regulatory", "compliance"])

class KA012PersonaSimulation(KnowledgeAlgorithm):
    """
    KA-012: Implements the Quad Persona Simulation (Knowledge, Sector, Regulatory, Compliance).
    """
    input_schema = KA012Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-012"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_12_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA012Input) -> Dict[str, Any]:
        query = input_data.query
        active_personas = input_data.active_personas
        
        self.log_execution_step("Persona Simulation", {"personas": active_personas})
        
        persona_configs = self.config.get("personas", {})
        dsqp_profiles = self._construct_dsqp_profiles(query, active_personas)
        results = []
        claims = []
        
        for p_key in active_personas:
            p_info = persona_configs.get(p_key)
            if not p_info:
                # Use default if config missing
                p_info = {"name": p_key.title(), "focus": "general", "base_confidence": 0.8}
                
            persona_res = self._simulate_persona(p_key, p_info, query, dsqp_profiles.get(p_key))
            results.append(persona_res)
            
            # Map response to a structured claim for KA-038
            claims.append({
                "claim_id": f"claim_{query[:10].replace(' ', '_')}", # Simple semantic grouping key
                "content": persona_res["response"],
                "persona_type": p_key,
                "confidence": persona_res["confidence"]
            })
            
        return {
            "success": True,
            "persona_results": results,
            "dsqp_profiles": dsqp_profiles,
            "dsqp_chain": {
                key: value.get("dsqp_chain", [])
                for key, value in dsqp_profiles.items()
            },
            "claims": claims, # Added for KA-038 compatibility
            "summary": f"Simulated {len(results)} expert perspectives."
        }

    def _construct_dsqp_profiles(self, query: str, active_personas: List[str]) -> Dict[str, Any]:
        axis_by_persona = {"knowledge": 8, "sector": 9, "regulatory": 10, "compliance": 11}
        active_axes = [axis_by_persona[p] for p in active_personas if p in axis_by_persona]
        if not active_axes:
            return {}
        try:
            from backend.dsqp import DSQPOrchestrator

            result = DSQPOrchestrator().construct_all_sync(
                query,
                {"active_axes": active_axes},
                active_axes=active_axes,
                context={"query": query, "dsqp_mode": True},
            )
            profiles_by_persona = {}
            for payload in result.get("profiles", {}).values():
                profiles_by_persona[payload["persona_type"]] = payload
            return profiles_by_persona
        except Exception as exc:
            logger.debug("KA-012 DSQP construction skipped: %s", exc)
            return {}

    def _simulate_persona(
        self,
        key: str,
        info: Dict[str, Any],
        query: str,
        dsqp_profile: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        focus = info.get("focus", "general")
        base_confidence = info.get("base_confidence", 0.8)
        name = info.get('name', key.title())
        role_title = name
        if dsqp_profile:
            role_title = dsqp_profile.get("name") or role_title
            focus = dsqp_profile.get("components", {}).get("job_role", {}).get("focus_area", focus)
        
        response = f"[{role_title} Perspective]: Regarding '{query}', my analysis focused on {focus} " \
                   f"indicates that the primary considerations should include the structural integrity " \
                   f"of the proposed solution and adherence to established {key} standards."
        
        return {
            "persona_type": key,
            "name": role_title,
            "response": response,
            "confidence": base_confidence + random.uniform(-0.05, 0.05),
            "dsqp_profile": dsqp_profile,
            "success": True
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA012PersonaSimulation(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-012 Fatal Execution Error: {e}")
        return {"success": False, "error": str(e)}
