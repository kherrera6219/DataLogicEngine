"""
United System Manager

This module provides the central coordination mechanism for all UKG system components.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable

from core.system.unified_identity_service import UnifiedIdentityService
from core.system.unified_numbering_service import UnifiedNumberingService
from core.system.code_crosswalk_service import CodeCrosswalkService
from core.system.trace_service import TraceProvenanceService
from core.system.refinement_orchestrator import RefinementOrchestrator
from core.system.unified_mapping_system import UnifiedMappingSystem
from core.system.persona_construction_service import PersonaConstructionService

class UnitedSystemManager:
    """
    United System Manager
    
    The central coordinator for all UKG system components. This class manages
    component registration, inter-component communication, and provides a
    unified interface for accessing system components.
    """
    
    def __init__(self, config=None):
        """
        Initialize the United System Manager.
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        logging.info(f"[{datetime.now()}] Initializing UnitedSystemManager...")
        self.config = config or {}
        
        # Components registry
        self.components = {}
        
        # Event handlers
        self.event_handlers = {}
        
        # System status
        self.status = {
            'initialized': True,
            'start_time': datetime.now().isoformat(),
            'component_count': 0,
            'healthy': True
        }
        
        # Core Unified System Services
        self.uids = None
        self.uns = None
        self.crosswalk = None
        self.trace = None
        self.refinement = None
        self.mapping = None
        self.persona_construction = None
        
        logging.info(f"[{datetime.now()}] UnitedSystemManager initialized")
    
    def register_component(self, name: str, component: Any) -> bool:
        """
        Register a component with the system.
        
        Args:
            name: Component name
            component: Component instance
            
        Returns:
            bool: True if registration was successful
        """
        if name in self.components:
            logging.warning(f"[{datetime.now()}] USM: Component '{name}' already registered")
            return False
        
        self.components[name] = component
        self.status['component_count'] += 1
        logging.info(f"[{datetime.now()}] USM: Component '{name}' registered")
        return True
    
    def get_component(self, name: str) -> Optional[Any]:
        """
        Get a component by name.
        
        Args:
            name: Component name
            
        Returns:
            Component instance or None if not found
        """
        return self.components.get(name)
    
    def register_event_handler(self, event_name: str, handler: Callable) -> bool:
        """
        Register an event handler.
        
        Args:
            event_name: Event name
            handler: Handler function
            
        Returns:
            bool: True if registration was successful
        """
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        
        self.event_handlers[event_name].append(handler)
        logging.info(f"[{datetime.now()}] USM: Event handler registered for '{event_name}'")
        return True
    
    def trigger_event(self, event_name: str, event_data: Dict) -> List[Any]:
        """
        Trigger an event and call all registered handlers.
        
        Args:
            event_name: Event name
            event_data: Event data
            
        Returns:
            list: List of handler return values
        """
        if event_name not in self.event_handlers:
            logging.warning(f"[{datetime.now()}] USM: No handlers for event '{event_name}'")
            return []
        
        results = []
        handlers = self.event_handlers[event_name]
        for handler in handlers:
            try:
                result = handler(event_data)
                results.append(result)
            except Exception as e:
                logging.error(f"[{datetime.now()}] USM: Error in event handler: {str(e)}")
        
        return results
    
    def initialize_unified_system(self, axis_registry_path: str):
        """Initialize the core Unified System services."""
        logging.info("Initializing UKG Unified System...")
        
        # 0. FROST Service
        from core.system.frost_service import FROSTService
        self.frost = FROSTService()
        self.register_component("frost", self.frost)
        
        # 1. Identity Service
        self.uids = UnifiedIdentityService()
        self.register_component("uids", self.uids)
        
        # 2. Numbering Service
        self.uns = UnifiedNumberingService(registry_path=axis_registry_path)
        self.register_component("uns", self.uns)
        
        # 3. Crosswalk Service
        self.crosswalk = CodeCrosswalkService(uids=self.uids, uns=self.uns)
        self.register_component("crosswalk", self.crosswalk)
        
        # 4. Trace Service
        self.trace = TraceProvenanceService()
        self.register_component("trace", self.trace)
        
        # 5. Mapping System (17-Axis)
        self.mapping = UnifiedMappingSystem(
            uids=self.uids, 
            uns=self.uns, 
            crosswalk=self.crosswalk,
            graph_manager=self.get_component("graph_manager"),
            memory_manager=self.get_component("memory_manager"),
            united_system_manager=self
        )
        self.register_component("mapping", self.mapping)
        
        # 6. Refinement Orchestrator
        self.refinement = RefinementOrchestrator(
            ka_controller=self.get_component("ka_controller"),
            frost=self.frost,
            trace=self.trace
        )
        self.register_component("refinement", self.refinement)
        
        # 7. Persona Construction Service
        self.persona_construction = PersonaConstructionService(
            uids=self.uids,
            uns=self.uns,
            mapping=self.mapping
        )
        self.register_component("persona_construction", self.persona_construction)
        
        logging.info("UKG Unified System initialized successfully.")

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the current system status.
        
        Returns:
            dict: System status information
        """
        # Update component health
        component_health = {}
        all_healthy = True
        
        for name, component in self.components.items():
            component_health[name] = True
            
            # Check for health check method
            if hasattr(component, 'check_health') and callable(component.check_health):
                try:
                    health_status = component.check_health()
                    component_health[name] = health_status.get('healthy', True)
                    if not health_status.get('healthy', True):
                        all_healthy = False
                except Exception as e:
                    logging.error(f"[{datetime.now()}] USM: Error checking component health: {str(e)}")
                    component_health[name] = False
                    all_healthy = False
        
        # Update status
        self.status['healthy'] = all_healthy
        self.status['component_health'] = component_health
        self.status['last_updated'] = datetime.now().isoformat()
        
        return self.status
    
    def initialize_connections(self) -> bool:
        """
        Initialize connections between components.
        
        Returns:
            bool: True if initialization was successful
        """
        try:
            # Database manager connection
            db_manager = self.get_component('db_manager')
            if db_manager:
                # Connect graph manager to database
                graph_manager = self.get_component('graph_manager')
                if graph_manager:
                    graph_manager.set_db_manager(db_manager)
                
                # Connect memory manager to database
                memory_manager = self.get_component('memory_manager')
                if memory_manager:
                    memory_manager.set_db_manager(db_manager)
            
            # Other connections as needed
            
            logging.info(f"[{datetime.now()}] USM: Component connections initialized")
            return True
        except Exception as e:
            logging.error(f"[{datetime.now()}] USM: Error initializing connections: {str(e)}")
            return False
    
    def shutdown(self) -> bool:
        """
        Shutdown the system.
        
        Returns:
            bool: True if shutdown was successful
        """
        try:
            # Trigger shutdown event
            self.trigger_event('system_shutdown', {
                'time': datetime.now().isoformat()
            })
            
            # Shutdown components
            for name, component in self.components.items():
                if hasattr(component, 'shutdown') and callable(component.shutdown):
                    try:
                        component.shutdown()
                        logging.info(f"[{datetime.now()}] USM: Component '{name}' shutdown")
                    except Exception as e:
                        logging.error(f"[{datetime.now()}] USM: Error shutting down component '{name}': {str(e)}")
            
            # Update status
            self.status['initialized'] = False
            self.status['shutdown_time'] = datetime.now().isoformat()
            
            logging.info(f"[{datetime.now()}] USM: System shutdown complete")
            return True
        except Exception as e:
            logging.error(f"[{datetime.now()}] USM: Error during shutdown: {str(e)}")
            return False