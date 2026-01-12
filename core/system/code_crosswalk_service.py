"""
Code Crosswalk Service

This module implements the service for mapping external code systems 
(NAICS, ISO, PSC, FAR/DFARS) to canonical UKG coordinates and entities.
It enables "jurisdictional harmonization" across different data standards.
"""

import logging
from typing import Dict, List, Any, Optional

class CodeCrosswalkService:
    """
    Code Crosswalk Service
    
    Responsibilities:
    1. Map external classification codes to UKG axis coordinates.
    2. Resolve overlapping/conflicting codes between different systems.
    3. Provide "compliance harmonization" lookups.
    """
    
    def __init__(self, uids=None, uns=None):
        self.logger = logging.getLogger(__name__)
        self.uids = uids
        self.uns = uns
        
        # In-memory mapping tables
        # source_system:code -> { coord: str, description: str, related: [] }
        self.crosswalk_table: Dict[str, Dict[str, Any]] = {
            "NAICS": {
                "541512": {"coord": "A02.TECH.541512", "name": "Computer Systems Design Services"},
                "212319": {"coord": "A02.MANU.212319", "name": "Other Crushed and Broken Stone Mining and Quarrying"}
            },
            "ISO": {
                "9001": {"coord": "A07.ISO.9001", "name": "Quality Management Systems"},
                "27001": {"coord": "A07.ISO.27001", "name": "Information Security Management"}
            },
            "FAR": {
                "52.204-21": {"coord": "A06.FAR.52.204.21", "name": "Basic Safeguarding of Covered Contractor Information Systems"}
            },
             "SAM.gov": {
                "ENTITY_DATA": {"coord": "A17.SAM.ENTITY", "name": "SAM Entity Data Object"}
            }
        }

    def register_mapping(self, source_system: str, code: str, ukg_coord: str, name: Optional[str] = None):
        """Register a new crosswalk mapping."""
        if source_system not in self.crosswalk_table:
            self.crosswalk_table[source_system] = {}
            
        self.crosswalk_table[source_system][code] = {
            "coord": ukg_coord,
            "name": name or code
        }
        self.logger.info(f"Registered crosswalk: {source_system}:{code} -> {ukg_coord}")

    def resolve_code(self, source_system: str, code: str) -> Optional[Dict[str, Any]]:
        """Resolve an external code to UKG metadata."""
        system_table = self.crosswalk_table.get(source_system)
        if not system_table:
            return None
        return system_table.get(code)

    def get_related_codes(self, source_system: str, code: str) -> List[Dict[str, str]]:
        """Find related codes in other systems (e.g., NAICS to PSC)."""
        # Placeholder for more complex many-to-many logic
        return []

    def harmonize_compliance(self, codes: List[Dict[str, str]]) -> List[str]:
        """
        Harmonize a list of heterogeneous codes into a set of UKG coordinates.
        Input format: [{'system': 'NAICS', 'code': '541512'}, ...]
        """
        resolved_coords = []
        for item in codes:
            match = self.resolve_code(item['system'], item['code'])
            if match:
                resolved_coords.append(match['coord'])
        return list(set(resolved_coords))

    def check_health(self) -> Dict[str, Any]:
        """System health check."""
        return {
            "healthy": True,
            "systems_covered": list(self.crosswalk_table.keys()),
            "total_mappings": sum(len(v) for v in self.crosswalk_table.values())
        }
