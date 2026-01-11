from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class KAMetadata:
    """Metadata for a Knowledge Algorithm."""
    id: str
    name: str
    description: str
    tier: str
    layer: int
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    risk_level: str = "Low"

@dataclass
class KAResult:
    """
    Standardized output format for all Knowledge Algorithms.
    """
    output: Any  # The primary result (text, score, boolean, etc.)
    artifacts: Dict[str, Any] = field(default_factory=dict)  # Auxiliary data, evidence, graphs
    scores: Dict[str, float] = field(default_factory=dict)  # Confidence, compliance scores, etc.
    confidence_delta: float = 0.0  # Proposed adjustment to system confidence
    flags: Dict[str, bool] = field(default_factory=dict)  # Status flags (e.g., violations found)
    log: str = ""  # Human-readable reasoning trace
    success: bool = True  # High-level success/failure indicator
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class KnowledgeAlgorithm(ABC):
    """
    Abstract Base Class for all Knowledge Algorithms.
    Enforces modularity, standardized execution, and metadata.
    """
    def __init__(self, ka_id: str, name: str, description: str, tier: str, layer: int):
        self.ka_id = ka_id
        self.name = name
        self.description = description
        self.tier = tier
        self.layer = layer

    @abstractmethod
    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        """
        Execute the algorithm's logic.
        
        Args:
            state: The current state of the query/reasoning (read-only or atomic updates via return).
            context: Shared EngineContext containing dependencies (LLM, Logger, KG).
            
        Returns:
            KAResult object containing the outcome.
        """
        pass
