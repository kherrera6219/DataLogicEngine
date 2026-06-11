"""
UKG Axis System

This module provides the central coordination point for the 17-Axis Universal Knowledge Graph (UKG) system.
It handles cross-axis relationships, context resolution, and coordinates between different axes.

The 17-Axis system is structured as follows:
- Axis 1: Pillar Level System (Knowledge Domains)
- Axis 2: Sector of Industry
- Axis 3: Honeycomb System (Cross-domain semantic bridges)
- Axis 4: Branch System (Hierarchical sub-domains)
- Axis 5: Node System (Interdisciplinary convergence)
- Axis 6: Octopus Node (Meta-regulatory aggregation)
- Axis 7: Spiderweb Node (Compliance constraint mesh)
- Axis 8: Knowledge Expert
- Axis 9: Sector Expert
- Axis 10: Regulatory Expert
- Axis 11: Compliance Expert
- Axis 12: Location
- Axis 13: Temporal
- Axis 14: Acquisition Lifecycle
- Axis 15: Risk & Threat Context
- Axis 16: Ethics, Trust & Criticality
- Axis 17: FROST-Mode Selector
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

# Import Axis Managers.
# Module filenames predate the final 17-axis numbering and are kept for import
# stability; the aliases map each module to its canonical axis:
#   axis5_honeycomb.py -> Axis 3 (Honeycomb System)
#   axis3_domain.py    -> Axis 4 (Branch System)
from core.axes.axis1_knowledge import KnowledgeAxis as PillarManager
from core.axes.axis2_sector import SectorManager
from core.axes.axis5_honeycomb import HoneycombSystem  # Axis 3
from core.axes.axis3_domain import DomainManager as BranchManager  # Axis 4
from core.axes.axis6_regulatory import RegulatoryManager as OctopusManager  # Axis 6
from core.axes.axis7_compliance import ComplianceManager as SpiderwebManager  # Axis 7

from core.axes.axis8_knowledge_expert import KnowledgeExpertAxis as KnowledgeExpert
from core.axes.axis9_sector_expert import SectorExpertAxis as SectorExpert
from core.axes.axis10_regulatory_expert import RegulatoryExpertAxis as RegulatoryExpert
from core.axes.axis11_compliance_expert import ComplianceExpertAxis as ComplianceExpert

from core.axes.axis12_location import LocationAxis
from core.axes.axis13_time import TimeAxis

from core.axes.axis14_acquisition_lifecycle import AcquisitionLifecycleAxis
from core.axes.axis15_risk_threat import RiskThreatAxis
from core.axes.axis16_ethics_trust import EthicsTrustAxis
from core.axes.axis17_frost_mode import FrostModeAxis

from core.coordinate_system import (
    UnifiedCoordinateSystem, 
    UnifiedCoordinate, 
    create_coordinate_system
)

class AxisSystem:
    """
    Central coordinator for the 17-Axis Universal Knowledge Graph (UKG) system.
    """

    TOTAL_AXES = 17

    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Axis System.

        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.logging = logging.getLogger(__name__)

        # Track individual axis managers
        self.axis_managers = {}

        # Define the 17 axes
        self.axes = {
            1: {"name": "Pillar Level System", "description": "Top-level knowledge domain selector (PL0001–PL0107)"},
            2: {"name": "Sector of Industry", "description": "Industry context using NAICS / SIC / ISIC / NACE / UNSPSC"},
            3: {"name": "Honeycomb System", "description": "Cross-domain semantic bridges (non-hierarchical)"},
            4: {"name": "Branch System", "description": "Hierarchical sub-domains within pillars/sectors"},
            5: {"name": "Node System", "description": "Interdisciplinary convergence nodes"},
            6: {"name": "Octopus Node", "description": "Meta-regulatory aggregation across jurisdictions"},
            7: {"name": "Spiderweb Node", "description": "Compliance constraint mesh and conflict resolution"},
            8: {"name": "Knowledge Expert", "description": "Scholar / domain expert"},
            9: {"name": "Sector Expert", "description": "Industry practitioner"},
            10: {"name": "Regulatory Expert", "description": "External laws / standards"},
            11: {"name": "Compliance Expert", "description": "Internal policy & controls"},
            12: {"name": "Location", "description": "Jurisdiction, geography, authority"},
            13: {"name": "Temporal", "description": "Time, validity window, regulatory versioning"},
            14: {"name": "Acquisition Lifecycle", "description": "AL1-AL7 acquisition stage routing"},
            15: {"name": "Risk & Threat Context", "description": "Six-dimensional risk decomposition"},
            16: {"name": "Ethics, Trust & Criticality", "description": "Sensitivity and ethics framework routing"},
            17: {"name": "FROST-Mode Selector", "description": "Tier to FROST depth and TruthCore mode bridge"}
        }

        # Initialize axes
        self._init_axes()
        
        # Initialize the Unified Coordinate System
        self.coordinate_system = create_coordinate_system(db_manager, graph_manager)

    def _init_axes(self):
        """Initialize all axis managers."""
        try:
            # Axis 1: Pillar
            self.pillar_manager = PillarManager()
            self.register_axis_manager(1, self.pillar_manager)

            # Axis 2: Sector
            self.sector_manager = SectorManager(self.db_manager, self.graph_manager)
            self.register_axis_manager(2, self.sector_manager)

            # Axis 3: Honeycomb System
            self.honeycomb_system = HoneycombSystem(self.db_manager, self.graph_manager)
            self.register_axis_manager(3, self.honeycomb_system)

            # Axis 4: Branch System. DomainManager implements the hierarchical
            # sub-domain taxonomy (broader/narrower, part_of/has_part) that
            # branch semantics require, so it serves as the Axis 4 manager.
            self.branch_manager = BranchManager(self.db_manager, self.graph_manager)
            self.register_axis_manager(4, self.branch_manager)

            # Axis 5: Node System intentionally has no dedicated manager
            # (audit decision N4, 2026-06-10). Convergence nodes are ordinary
            # knowledge-graph nodes addressed through the coordinate system
            # and graph traversal; resolve_multi_axis_context() returns the
            # documented "unmanaged" resolution for Axis 5 queries.

            # Axis 6: Octopus (Regulatory Frameworks)
            self.octopus_manager = OctopusManager(self.db_manager, self.graph_manager)
            self.register_axis_manager(6, self.octopus_manager)

            # Axis 7: Spiderweb (Compliance Constraints)
            self.spiderweb_manager = SpiderwebManager(self.db_manager, self.graph_manager)
            self.register_axis_manager(7, self.spiderweb_manager)
            
            # Group II: Personas (Axes 8-11)
            # These are typically instantiated per query, but managers might exist
            # Assuming these classes exist and can be instantiated similarly
            # For now, we register them if they are manager-like, or we use POV Engine to manage them.
            # Here we just acknowledge their existence in the system map.
            try:
                self.knowledge_expert = KnowledgeExpert()
                self.register_axis_manager(8, self.knowledge_expert)
            except Exception:
                pass
            
            try:
                self.sector_expert = SectorExpert()
                self.register_axis_manager(9, self.sector_expert)
            except Exception:
                pass

            try:
                self.regulatory_expert = RegulatoryExpert()
                self.register_axis_manager(10, self.regulatory_expert)
            except Exception:
                pass

            try:
                self.compliance_expert = ComplianceExpert()
                self.register_axis_manager(11, self.compliance_expert)
            except Exception:
                pass


            # Axis 12: Location
            self.location_axis = LocationAxis()
            self.register_axis_manager(12, self.location_axis)

            # Axis 13: Temporal
            self.time_axis = TimeAxis()
            self.register_axis_manager(13, self.time_axis)

            # Group IV: Governance (Axes 14-17)
            self.acquisition_lifecycle_axis = AcquisitionLifecycleAxis()
            self.register_axis_manager(14, self.acquisition_lifecycle_axis)
            
            self.risk_threat_axis = RiskThreatAxis()
            self.register_axis_manager(15, self.risk_threat_axis)
            
            self.ethics_trust_axis = EthicsTrustAxis()
            self.register_axis_manager(16, self.ethics_trust_axis)
            
            self.frost_mode_axis = FrostModeAxis()
            self.register_axis_manager(17, self.frost_mode_axis)
            
            self.logging.info(f"[{datetime.now()}] Axis System initialized successfully")

        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error initializing axes: {str(e)}")

    def register_axis_manager(self, axis_number: int, manager: Any) -> None:
        """
        Register an individual axis manager with the system.

        Args:
            axis_number: The axis number (1-17)
            manager: The axis manager instance
        """
        if 1 <= axis_number <= self.TOTAL_AXES:
            self.axis_managers[axis_number] = manager
            axis_name = self.axes.get(axis_number, {}).get('name', f'Axis {axis_number}')
            self.logging.info(f"[{datetime.now()}] Registered axis manager for Axis {axis_number}: {axis_name}")
        else:
            self.logging.error(f"[{datetime.now()}] Invalid axis number: {axis_number}. Must be 1-{self.TOTAL_AXES}")

    def resolve_multi_axis_context(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve a multi-dimensional context across multiple axes.

        Args:
            query_context: Dictionary containing context elements for different axes

        Returns:
            Dict containing the resolved context
        """
        self.logging.info(f"[{datetime.now()}] Resolving multi-axis context")

        resolved_context = {
            'axes': {},
            'confidence': {},
            'cross_axis_relationships': [],
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Process each axis in the query context
            for axis_num, axis_data in query_context.items():
                axis_num = int(axis_num) if isinstance(axis_num, str) and axis_num.isdigit() else axis_num

                if isinstance(axis_num, int) and 1 <= axis_num <= self.TOTAL_AXES:
                    # If we have a manager for this axis, use it to resolve
                    if axis_num in self.axis_managers:
                        axis_manager = self.axis_managers[axis_num]

                        # Call appropriate resolution method based on axis
                        # Note: Different managers might have different signatures
                        if hasattr(axis_manager, 'resolve_context'):
                            axis_result = axis_manager.resolve_context(axis_data)
                            resolved_context['axes'][axis_num] = axis_result

                            # Track confidence of this resolution
                            if isinstance(axis_result, dict) and 'confidence' in axis_result:
                                resolved_context['confidence'][axis_num] = axis_result['confidence']
                        elif hasattr(axis_manager, 'navigate'): # KnowledgeAxis signature
                            axis_result = axis_manager.navigate(**axis_data)
                            resolved_context['axes'][axis_num] = axis_result
                        else:
                            # Basic resolution if no specific method
                            resolved_context['axes'][axis_num] = {
                                'data': axis_data,
                                'status': 'basic_resolution',
                                'confidence': 0.7
                            }
                            resolved_context['confidence'][axis_num] = 0.7
                    else:
                        # No manager, just store the data
                        resolved_context['axes'][axis_num] = {
                            'data': axis_data,
                            'status': 'unmanaged',
                            'confidence': 0.5
                        }
                        resolved_context['confidence'][axis_num] = 0.5

            # Calculate overall context confidence (weighted average)
            if resolved_context['confidence']:
                resolved_context['overall_confidence'] = sum(resolved_context['confidence'].values()) / len(resolved_context['confidence'])
            else:
                resolved_context['overall_confidence'] = 0.0

            resolved_context['status'] = 'success'

        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error resolving multi-axis context: {str(e)}")
            resolved_context['status'] = 'error'
            resolved_context['error'] = str(e)
            resolved_context['overall_confidence'] = 0.0

        return resolved_context

    def create_coordinate(self, **axis_values) -> UnifiedCoordinate:
        """
        Create a unified coordinate with specified axis values.
        
        Args:
            **axis_values: Keyword arguments for axis values
            
        Returns:
            UnifiedCoordinate object
        """
        return self.coordinate_system.create_coordinate(**axis_values)
    
    def parse_coordinate(self, coord_string: str) -> UnifiedCoordinate:
        """
        Parse a coordinate string into a UnifiedCoordinate object.
        
        Args:
            coord_string: The coordinate string to parse
            
        Returns:
            UnifiedCoordinate object
        """
        return self.coordinate_system.parse(coord_string)
    
    def resolve_coordinate(self, coord: UnifiedCoordinate) -> Dict[str, Any]:
        """
        Resolve a coordinate to its full knowledge context.
        
        Args:
            coord: The coordinate to resolve
            
        Returns:
            Dictionary with resolved context for all axes
        """
        return self.coordinate_system.resolve(coord)
    
    def traverse_from_coordinate(self, coord: UnifiedCoordinate, 
                                 query_context: Dict[str, Any] = None) -> List[UnifiedCoordinate]:
        """
        Traverse the knowledge graph from a coordinate using crosswalk systems.
        
        Uses Honeycomb (Axis 3), Octopus (Axis 6), and Spiderweb (Axis 7) 
        traversal patterns.
        
        Args:
            coord: Starting coordinate
            query_context: Optional context to guide traversal
            
        Returns:
            List of discovered coordinates
        """
        return self.coordinate_system.traverse(coord, query_context)
    
    def get_coordinate_system(self) -> UnifiedCoordinateSystem:
        """
        Get the underlying UnifiedCoordinateSystem instance.
        
        Returns:
            The UnifiedCoordinateSystem instance
        """
        return self.coordinate_system
