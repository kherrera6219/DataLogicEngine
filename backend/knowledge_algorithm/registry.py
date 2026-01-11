"""
Knowledge Algorithm Registry
Handles registration, discovery, and execution of KAs.
"""
from typing import Callable, Dict, Any, Optional, List
import logging
from dataclasses import dataclass, field
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class KAMetadata:
    """Metadata for a Knowledge Algorithm."""
    id: str
    name: str
    description: str
    tier: str
    layer: int
    inputs: List[str]
    outputs: List[str]
    risk_level: str = "Low"

class KARegistry:
    """
    Central registry for all Knowledge Algorithms.
    """
    _registry: Dict[str, Callable] = {}
    _metadata: Dict[str, KAMetadata] = {}

    @classmethod
    def register(cls, meta: KAMetadata):
        """Decorator to register a function as a Knowledge Algorithm."""
        def decorator(func: Callable):
            logger.info(f"Registering KA: {meta.id} - {meta.name}")
            cls._registry[meta.id] = func
            cls._metadata[meta.id] = meta
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    @classmethod
    def get_ka(cls, ka_id: str) -> Optional[Callable]:
        """Retrieve a specific KA function by ID."""
        return cls._registry.get(ka_id)

    @classmethod
    def get_metadata(cls, ka_id: str) -> Optional[KAMetadata]:
        """Retrieve metadata for a KA."""
        return cls._metadata.get(ka_id)

    @classmethod
    def execute(cls, ka_id: str, *args, **kwargs) -> Any:
        """Execute a KA by ID safely."""
        func = cls.get_ka(ka_id)
        if not func:
            raise ValueError(f"KA '{ka_id}' not found in registry.")
        
        try:
            logger.debug(f"Executing KA: {ka_id}")
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing KA {ka_id}: {str(e)}")
            raise

    @classmethod
    def list_algorithms(cls) -> List[Dict[str, Any]]:
        """List all registered algorithms."""
        return [
            {
                "id": m.id,
                "name": m.name,
                "tier": m.tier,
                "description": m.description
            }
            for m in cls._metadata.values()
        ]
