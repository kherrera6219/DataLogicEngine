import logging
from core.simulation.location_context_engine import LocationContextEngine as CoreLocationContextEngine

class LocationContextEngine(CoreLocationContextEngine):
    """
    Wrapper for LocationContextEngine that maintains compatibility with the legacy backend interface
    while using the consolidated core implementation.
    """
    
    def __init__(self, config: dict, ukg_db_manager=None):
        """
        Initialize the LocationContextEngine.
        """
        # Pass ukg_db_manager to core init
        super().__init__(config=config, ukg_db_manager=ukg_db_manager)
        logging.info("LocationContextEngine (Consolidated) initialized as backend wrapper")
    
    # All methods are now inherited from CoreLocationContextEngine