"""
Knowledge Algorithm Registry
Handles registration, discovery, and execution of Class-based KAs.
"""
from typing import Dict, Any, Optional, List, Type
import logging
from .base import KnowledgeAlgorithm, KAResult
from .context import EngineContext

logger = logging.getLogger(__name__)

class KARegistry:
    """
    Central registry for all Knowledge Algorithms.
    Stores references to KA Classes.
    """
    _registry: Dict[str, Type[KnowledgeAlgorithm]] = {}

    @classmethod
    def register(cls):
        """
        Class Decorator to register a KnowledgeAlgorithm subclass.
        """
        def decorator(ka_class: Type[KnowledgeAlgorithm]):
            # Instantiate temporarily to get metadata, or assume it's set in init
            # Better pattern: Make metadata class attributes or pass to decorator?
            # For now, we will rely on instantiating it or inspecting it.
            # But wait, base class `__init__` takes args.
            # Let's assume the KA class has ID/Name as class constants or default properties?
            # Or the decorator takes the metadata.
            
            # Architecture Decision: Pass metadata to decorator?
            # No, the previous implementation passed metadata to decorator.
            # Let's keep that pattern but for Classes.
            return ka_class
        return decorator
    
    # Revised Approach:
    # Just a simple register method that takes the class if the class knows its metadata?
    # Or keep the decorator `register(metadata)`?
    
    @classmethod
    def register_class(cls, ka_class: Type[KnowledgeAlgorithm]):
        """
        Register a KA class. The class is expected to have `ka_id` accessible or passed.
        Limitations of ABC: __init__ sets instance attributes.
        We might need to instantiate it to get the ID, or change the ABC to have class-level ID.
        Let's switch design slightly: KA classes define ID as a property or we pass it in register.
        """
        # We will assume the module instantiates it or we just store the class and ID is separate.
        # But for auto-registration, let's stick to the previous pattern:
        # @KARegistry.register_ka(metadata)
        # class MyKA(KnowledgeAlgorithm): ...
        pass

    @classmethod
    def register_ka(cls, ka_class: Type[KnowledgeAlgorithm]):
        """
        Manual registration or decorator.
        We need to get the ID.
        For simplicity in this transition, let's assume we instantiate the KA to register it?
        No, that's wasteful.
        Let's expect the KA to have a `KA_ID` class attribute?
        Or just use the decorator with arguments.
        """
        pass

# Let's rewrite the whole class cleanly based on the plan.
    
    @classmethod
    def register(cls):
        """
        Decorator to register a class.
        Usage: 
        @KARegistry.register
        class KA01(KnowledgeAlgorithm): ...
        
        Using introspection to find KA_ID? 
        Let's enforce `ka_id` as a class attribute for simplicity.
        """
        def decorator(ka_cls: Type[KnowledgeAlgorithm]):
            # We assume the class has a 'ka_id' attribute or we instantiate a dummy to check?
            # Safest is to instantiate it if it has no-arg init? 
            # But the base init has args.
            
            # Let's require the class to define `KA_ID` and `METADATA` as static if possible,
            # OR just trust the module loader to register instance.
            
            # ACTUALLY, the cleanest way:
            # The KA module performs `KARegistry.register_instance(ka_instance)` at the bottom?
            # OR we stick to the decorator taking the ID.
            pass
        return decorator

# DECISION: We will use a decorator that takes no args, but expects the Class to have `ka_id` 
# or we pass the instance.
# Actually, the user requirement said "one module per KA".
# So the module can simply do `KARegistry.register(KAClass)`.
# Let's implementing `register` to take the Class and optionally store it keyed by `ka_id` 
# which we extract from the class (maybe as a class attribute `ka_id`).

    @classmethod
    def register_ka(cls, ka_cls: Type[KnowledgeAlgorithm]):
        """Registers a KA Class."""
        # We need the ID. Let's assume the CLASS has a `ka_id` static field or property.
        # If not, we can't key it easily without instantiation.
        # Let's mandate `ka_id` as a Class Variable in the implementation.
        ka_id = getattr(ka_cls, "ka_id", None)
        if ka_id:
             logger.info(f"Registering KA Class: {ka_id}")
             cls._registry[ka_id] = ka_cls
        else:
            logger.warning(f"Class {ka_cls.__name__} has no 'ka_id', skipping registration.")

    @classmethod
    def get_ka(cls, ka_id: str) -> Optional[Type[KnowledgeAlgorithm]]:
        return cls._registry.get(ka_id)

    @classmethod
    def execute(cls, ka_id: str, state: Dict[str, Any], context: EngineContext, **kwargs) -> Any:
        try:
            ka_cls = cls._registry.get(ka_id)
            if not ka_cls:
                raise ValueError(f"KA '{ka_id}' not found.")
            
            # Instantiate the KA. 
            # We need to know what args __init__ takes.
            # The base class takes (id, name, desc, tier, layer).
            # The subclass should probably supply these via super().__init__ or have them hardcoded.
            # Best pattern: The subclass __init__ takes no args (or just config), and calls super with constants.
            
            ka_instance = ka_cls() 
            logger.debug(f"Executing KA: {ka_instance.name} ({ka_id})")
            
            return ka_instance.execute(state, context)
        except Exception as e:
            logger.error(f"Error executing KA {ka_id}: {e}")
            raise
