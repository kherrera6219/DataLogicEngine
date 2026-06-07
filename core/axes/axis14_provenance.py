"""
Universal Knowledge Graph (UKG) System - Axis 14: Source Provenance

This module implements the Source Provenance axis (A14), tracking the origin,
lineage, and chain-of-custody for knowledge elements.
"""

import logging
from typing import Dict, Any
from core.coordinate_system import SourceProvenance

logger = logging.getLogger(__name__)

class SourceProvenanceAxis:
    """Handler for Axis 14: Source Provenance"""
    
    def __init__(self):
        self.axis_number = 14
        self.axis_name = "Source Provenance"
        self.description = "Tracks origin, lineage, and chain-of-custody for knowledge elements"
        self.provenance_types = [p.value for p in SourceProvenance]
        
    def navigate(self, **kwargs) -> Dict[str, Any]:
        """Navigate Axis 14 based on provenance filters."""
        prov_type = kwargs.get('provenance_type')
        source_id = kwargs.get('source_id')
        
        return {
            "axis": self.axis_number,
            "name": self.axis_name,
            "filters": {
                "provenance_type": prov_type,
                "source_id": source_id
            },
            "available_types": self.provenance_types
        }

    def get_provenance_metadata(self, provenance: SourceProvenance, source_id: str) -> Dict[str, Any]:
        """Get standard metadata for a provenance type."""
        return {
            "type": provenance.value,
            "source_id": source_id,
            "requires_verification": provenance in [SourceProvenance.LLM_GENERATED, SourceProvenance.VENDOR_DATA],
            "is_authoritative": provenance in [SourceProvenance.FED_REGISTER, SourceProvenance.US_CODE, SourceProvenance.CFR]
        }
