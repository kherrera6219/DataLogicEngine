from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA113ComplexityRouter(KnowledgeAlgorithm):
    ka_id = "KA-113"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-113",
            name="Query Analysis & Complexity Router",
            description="Select how much of the system runs based on difficulty/stakes.",
            tier="Routing",
            layer=1
        )

    def execute(self, params: Dict[str, Any], context: Any = None) -> KAResult:
        query = params.get("query", "")
        
        # Heuristic Complexity Detection
        high_complexity_keywords = {
            'regulatory', 'compliance', 'blockchain', 'quantum', 'ethics', 
            'financial', 'jurisdiction', 'adversarial', 'bayesian'
        }
        
        query_words = set(query.lower().split())
        complexity_hits = len(query_words.intersection(high_complexity_keywords))
        
        # Criteria for high complexity:
        # 1. Length > 100 characters
        # 2. More than 2 high-complexity keywords
        # 3. Contains specific "deep" triggers
        
        complexity = "medium"
        if len(query) > 150 or complexity_hits >= 2:
            complexity = "high"
        elif len(query) < 20 and complexity_hits == 0:
            complexity = "low"
            
        depth = 3
        budget = 1000
        
        if complexity == "high":
            depth = 12 # 12-step sequence
            budget = 5000
        elif complexity == "low":
            depth = 1
            budget = 100
            
        return KAResult(
            output={"tier": complexity, "depth": depth, "budget": budget},
            log=f"KA-113 analyzed query and routed to {complexity} tier (Hits: {complexity_hits})."
        )
