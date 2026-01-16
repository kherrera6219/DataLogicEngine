from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import logging

# Placeholder interfaces for dependencies to avoid circular imports or heavy setup
# In a real app, these might be abstract base classes or actual client types.
class LLMInterface:
    def prompt(self, prompt_text: str, **kwargs) -> str:
        # Mock implementation for now
        return f"[LLM Response to: {prompt_text[:20]}...]"

class KnowledgeGraphInterface:
    def query(self, query: str, filters: Dict) -> Any:
        # Mock implementation
        return []

from core.axes.axis_system import AxisSystem

@dataclass
class EngineContext:
    """
    Shared context object for Dependency Injection into KAs.
    Holds references to global services (LLM, Knowledge Graph, Logging, Config).
    """
    llm: Any = field(default_factory=LLMInterface)
    knowledge_graph: Any = field(default_factory=KnowledgeGraphInterface)
    axis_system: Any = field(default=None)  # Type: Optional[AxisSystem]
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("KA_Engine"))
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Optional tools or services
    tools: Dict[str, Any] = field(default_factory=dict)

def create_default_context() -> EngineContext:
    """Factory to create a standard context."""
    # Initialize real AxisSystem
    try:
        axis_sys = AxisSystem()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to init AxisSystem for context: {e}")
        axis_sys = None
        
    return EngineContext(axis_system=axis_sys)
