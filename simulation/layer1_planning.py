"""
Layer 1: Planning & Intent Engine
Responsible for parsing user queries into structured 17-Axis Intent and Execution Plans.
Replaces the legacy 'Layer 1 Entry' router.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from quad_persona.quad_models import Coord17Intent, ProblemSpec, TierPlan
from simulation.query_analysis_system import QueryAnalysisSystem

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
        self.ka_controller = self.config.get('ka_controller')
        self.parser = Coord17Parser()
        self.qas = QueryAnalysisSystem(self.config.get("qas", {}))
        
    def process_request(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for Layer 1.
        Uses KAs if available, falling back to internal logic.
        """
        logger.info(f"Layer 1 Planning started for: {query[:50]}...")
        
        # KA-004: Input Validation
        normalized_query = query
        if self.ka_controller:
            try:
                # Assuming KA-004 is registered
                val_result = self.ka_controller.execute_algorithm("KA-004", {"query": query})
                if val_result.get("success", False) and val_result.get("output", {}).get("normalized_query"):
                     normalized_query = val_result["output"]["normalized_query"]
                     logger.info("KA-004 Validation Successful")
                elif val_result.get("success") is False:
                     logger.warning(f"KA-004 Validation Failed: {val_result.get('error')}")
            except Exception as e:
                logger.warning(f"KA-004 Execution Failed: {e}")

        # 1. Parse Intent (What do they want?)
        # Use normalized query
        intent = self.parser.parse(normalized_query, context)
        
        # 2. Analyze Complexity (How hard is it?)
        # KA-113: Router / Tier Selection
        # If KA-113 is available, use it to determine Tier.
        
        tier_value = 1
        tier_name = "T1"
        layers_to_run = ["L1", "L9"]
        
        ka_router_used = False
        if self.ka_controller:
            try:
                # Prepare input for KA-113 (needs complexity hint, maybe from KA-005)
                # For now just pass query
                router_result = self.ka_controller.execute_algorithm("KA-113", {
                    "query": normalized_query,
                    "complexity_hint": "hard" if len(normalized_query) > 50 else "easy" 
                })
                
                if router_result.get("success", False):
                    out = router_result.get("output", {})
                    tier_str = out.get("selected_tier", "T1")
                    # Map T1 -> 1
                    try:
                        tier_value = int(tier_str.replace("T", ""))
                    except:
                        tier_value = 1
                    tier_name = tier_str
                    # Update layers if KA-113 provides them, though SDK handler snippet usually just returns tier
                    # But builtins.py version returns layers. Let's check output structure carefully.
                    # The builtins.py version returns "layers". The handlers.py version (stub) does NOT.
                    # We'll use safe defaults or what we get.
                    if "layers" in out:
                         layers_to_run = out["layers"]
                    
                    ka_router_used = True
                    logger.info(f"KA-113 Router selected {tier_name}")
            except Exception as e:
                logger.warning(f"KA-113 Execution Failed: {e}")

        # Fallback to Legacy QAS if KA router failed or not used
        if not ka_router_used:
            # Map our Intent format to the simple dict QAS expects
            axis_vector_proxy = {
                6: bool(intent.axis_6_regulation),
                2: bool(intent.axis_2_sector),
                17: bool(intent.axis_17_security)
            }
            qas_decision = self.qas.analyze(normalized_query, context, axis_vector=axis_vector_proxy)
            tier_value = qas_decision.tier.value
            tier_name = qas_decision.tier.name_short
            layers_to_run = qas_decision.layers_to_run
        
        # 3. Construct Artifacts
        
        # ProblemSpec
        spec = ProblemSpec(
            task_type=self._determine_task_type(normalized_query),
            constraints=self._extract_constraints(normalized_query),
            ambiguities=[f"Axis {a} unclear" for a in intent.ambiguous_axes]
        )
        
        # TierPlan
        plan = TierPlan(
            tier=tier_value,
            tier_name=tier_name,
            allowed_layers=layers_to_run,
            features_enabled=["deep_research"] if tier_value >= 3 else []
        )
        
        logger.info(f"Layer 1 Complete. Tier: {plan.tier_name}. Intent Axes: {len(intent.to_dict())} fields pop.")
        
        return {
            "query_id": context.get("query_id", "gen-" + str(datetime.now().timestamp())),
            "raw_query": normalized_query,
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
