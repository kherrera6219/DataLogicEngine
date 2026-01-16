from typing import Dict, Any, List
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA31AlgorithmSelectionEngine(KnowledgeAlgorithm):
    ka_id = "KA-031"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-031",
            name="Algorithm Selection Engine",
            description="Select KA pipeline given query, policies, and budget.",
            tier="Routing",
            layer=1
        )

    def execute(self, params: Dict[str, Any], context: Any = None) -> KAResult:
        complexity_tier = params.get("tier", "medium")
        
        # Define base pipeline components
        pipeline = ["KA-001", "KA-002", "KA-007", "KA-012"] # AoT, ToT, Recursive Control, Persona
        
        if complexity_tier == "high":
            # Inject deep planning and synthesis
            pipeline.insert(2, "KA-006") # Deep Planning
            pipeline.extend(["KA-019", "KA-030", "KA-014"]) # Synthesis, Conflict Res, Confidence
        elif complexity_tier == "medium":
            pipeline.extend(["KA-019", "KA-014"])
        else: # low
            pipeline = ["KA-012", "KA-014"] # Fast path
            
        return KAResult(
            output=pipeline,
            artifacts={"planned_pipeline": pipeline, "complexity_tier": complexity_tier},
            log=f"KA-031 selected '{complexity_tier}' pipeline: {', '.join(pipeline)}"
        )
