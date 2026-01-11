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

@dataclass
class EngineContext:
    """
    Shared context object for Dependency Injection into KAs.
    Holds references to global services (LLM, Knowledge Graph, Logging, Config).
    """
    llm: Any = field(default_factory=LLMInterface)
    knowledge_graph: Any = field(default_factory=KnowledgeGraphInterface)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("KA_Engine"))
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Optional tools or services
    tools: Dict[str, Any] = field(default_factory=dict)

def create_default_context() -> EngineContext:
    """Factory to create a standard context with default (mock/real) services."""
    return EngineContext()
