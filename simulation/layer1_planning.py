"""
Layer 1: Planning & Intent Engine
Responsible for parsing user queries into structured 17-Axis Intent and Execution Plans.
Replaces the legacy 'Layer 1 Entry' router.
"""

import logging
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

from quad_persona.quad_models import Coord17Intent, ProblemSpec, TierPlan
from simulation.query_analysis_system import QueryAnalysisSystem, ExecutionTier

logger = logging.getLogger(__name__)

class Coord17Parser:
    """
    Parses raw text into a 17-Axis Intent structure using heuristics/keywords.
    In a full system, this would use an NLP model.
    """
    
    # Simple Keyword Maps for Demonstration
    AXIS_KEYWORDS = {
        # Axis 6: Regulatory
        "regulatory": ["hipaa", "gdpr", "far", "dfars", "itar", "regulation", "law", "compliance"],
        # Axis 2: Sector
        "sector": ["healthcare", "finance", "defense", "military", "aerospace", "banking"],
        # Axis 5: Tools
        "tool": ["python", "java", "aws", "azure", "docker", "kubernetes", "radar", "f-22"],
        # Axis 17: Security
        "security": ["secret", "top secret", "classified", "confidential", "internal"],
        # Axis 4: Methods
        "method": ["agile", "waterfall", "scrum", "devops", "design", "analysis"]
    }

    def parse(self, query: str, context: Dict[str, Any]) -> Coord17Intent:
        """Parse query text into Coord17Intent."""
        query_lower = query.lower()
        intent = Coord17Intent()
        
        # --- Axis Parsing Logic ---
        
        # Axis 6: Regulatory
        for kw in self.AXIS_KEYWORDS["regulatory"]:
            if kw in query_lower:
                intent.axis_6_regulation.append(kw.upper())
        
        # Axis 2: Sector
        for kw in self.AXIS_KEYWORDS["sector"]:
            if kw in query_lower:
                intent.axis_2_sector.append(kw.title())
                
        # Axis 5: Tools
        for kw in self.AXIS_KEYWORDS["tool"]:
            if kw in query_lower:
                intent.axis_5_tool.append(kw.upper())
                
        # Axis 17: Security
        for kw in self.AXIS_KEYWORDS["security"]:
            if kw in query_lower:
                intent.axis_17_security.append(kw.upper())
        
        # Axis 4: Methods
        for kw in self.AXIS_KEYWORDS["method"]:
            if kw in query_lower:
                intent.axis_4_method.append(kw.title())
                
        # Default Security if context implies it
        if context.get("user_role") == "admin" and not intent.axis_17_security:
             intent.axis_17_security.append("INTERNAL_ONLY")
             
        # Identify Ambiguities (Simple logic: if no sector, mark generic)
        if not intent.axis_2_sector:
            intent.ambiguous_axes.append(2)
            
        return intent

class Layer1PlanningEngine:
    """
    Refactored Layer 1 Engine.
    Orchestrates Intent Parsing, Analysis (QAS), and Plan Generation.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.parser = Coord17Parser()
        self.qas = QueryAnalysisSystem(self.config.get("qas", {}))
        
    def process_request(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for Layer 1.
        
        Returns:
            {
                "problem_spec": dict,
                "intent": dict,
                "tier_plan": dict,
                "raw_query": str
            }
        """
        logger.info(f"Layer 1 Planning started for: {query[:50]}...")
        
        # 1. Parse Intent (What do they want?)
        intent = self.parser.parse(query, context)
        
        # 2. Analyze Complexity (How hard is it?)
        # Map our Intent format to the simple dict QAS expects
        axis_vector_proxy = {
            6: bool(intent.axis_6_regulation),
            2: bool(intent.axis_2_sector),
            17: bool(intent.axis_17_security)
        }
        
        qas_decision = self.qas.analyze(query, context, axis_vector=axis_vector_proxy)
        
        # 3. Construct Artifacts
        
        # ProblemSpec
        spec = ProblemSpec(
            task_type=self._determine_task_type(query),
            constraints=self._extract_constraints(query),
            ambiguities=[f"Axis {a} unclear" for a in intent.ambiguous_axes]
        )
        
        # TierPlan
        plan = TierPlan(
            tier=qas_decision.tier.value,
            tier_name=qas_decision.tier.name_short,
            allowed_layers=qas_decision.layers_to_run,
            features_enabled=["deep_research"] if qas_decision.tier.value >= 3 else []
        )
        
        logger.info(f"Layer 1 Complete. Tier: {plan.tier_name}. Intent Axes: {len(intent.to_dict())} fields pop.")
        
        return {
            "query_id": qas_decision.query_id,
            "raw_query": query,
            "problem_spec": spec.to_dict(),
            "intent": intent.to_dict(),
            "tier_plan": plan.to_dict()
        }

    def _determine_task_type(self, query: str) -> str:
        q = query.lower()
        if "compare" in q or "vs" in q: return "compare"
        if "how to" in q or "design" in q: return "design"
        if "explain" in q or "what is" in q: return "explain"
        if "verify" in q or "check" in q: return "verification"
        return "general_inquiry"

    def _extract_constraints(self, query: str) -> List[str]:
        constraints = []
        q = query.lower()
        if "only" in q: constraints.append("scope_limited")
        if "cite" in q or "source" in q: constraints.append("must_cite_sources")
        return constraints
