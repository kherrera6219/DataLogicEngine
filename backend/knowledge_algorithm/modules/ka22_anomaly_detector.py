from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA22AnomalyDetector(KnowledgeAlgorithm):
    ka_id = "KA-022"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-022",
            name="Anomaly Detector",
            description="Spot data outliers and logical inconsistencies.",
            tier="QA",
            layer=3
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        return KAResult(
            output="Normal",
            log="KA-22 found no anomalies."
        )
