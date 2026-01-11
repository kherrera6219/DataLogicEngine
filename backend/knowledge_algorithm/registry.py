"""
Knowledge Algorithm Registry
Handles registration, discovery, and execution of Class-based KAs.
"""
from typing import Dict, Any, Optional, List, Type
import logging
from .base import KnowledgeAlgorithm, KAResult, KAMetadata
from .context import EngineContext

logger = logging.getLogger(__name__)

class KARegistry:
    """
    Central registry for all Knowledge Algorithms.
    Stores references to KA Classes and their Metadata.
    """
    _registry: Dict[str, Type[KnowledgeAlgorithm]] = {}
    _metadata: Dict[str, KAMetadata] = {}

    @classmethod
    def register(cls):
        """
        Decorator to register a KA class.
        """
        def decorator(ka_cls: Type[KnowledgeAlgorithm]):
            cls.register_ka(ka_cls)
            return ka_cls
        return decorator

    @classmethod
    def register_ka(cls, ka_cls: Type[KnowledgeAlgorithm]):
        """Registers a KA Class and extracts metadata."""
        # Instantiate a temporary object to get metadata if it's instance-based
        # OR rely on the init arguments being mirrored as class attributes.
        # Given our KA implementation: 
        # super().__init__(ka_id="...", ...)
        # We can't easily get those without instantiation.
        # Safe approach for now: Instantiate once to read metadata.
        
        try:
            temp_instance = ka_cls()
            ka_id = temp_instance.ka_id
            
            meta = KAMetadata(
                id=ka_id,
                name=temp_instance.name,
                description=temp_instance.description,
                tier=temp_instance.tier,
                layer=temp_instance.layer
            )
            
            logger.info(f"Registering KA: {ka_id}")
            cls._registry[ka_id] = ka_cls
            cls._metadata[ka_id] = meta
            
        except Exception as e:
            logger.error(f"Failed to register KA {ka_cls}: {e}")

    @classmethod
    def get_ka(cls, ka_id: str) -> Optional[Type[KnowledgeAlgorithm]]:
        return cls._registry.get(ka_id)
        
    @classmethod
    def get_metadata(cls, ka_id: str) -> Optional[KAMetadata]:
        return cls._metadata.get(ka_id)

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

    @classmethod
    def execute(cls, ka_id: str, state: Dict[str, Any], context: EngineContext, **kwargs) -> Any:
        try:
            ka_cls = cls._registry.get(ka_id)
            if not ka_cls:
                raise ValueError(f"KA '{ka_id}' not found.")
            
            ka_instance = ka_cls() 
            logger.debug(f"Executing KA: {ka_instance.name} ({ka_id})")
            
            return ka_instance.execute(state, context)
        except Exception as e:
            logger.error(f"Error executing KA {ka_id}: {e}")
            raise
