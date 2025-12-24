"""
Universal Knowledge Graph (UKG) System - Axis 14: Risk & Confidence

This module implements the Risk & Confidence axis for the 17-Axis UKG system,
providing risk classification, confidence scoring, and validation metrics.
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RiskClass(Enum):
    """Risk classification levels"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ConfidenceImpact(Enum):
    """Confidence impact types"""
    DIRECT_UP = "Direct ↑"
    INDIRECT_UP = "Indirect ↑"
    DIRECT_DOWN = "Direct ↓"
    INDIRECT_DOWN = "Indirect ↓"
    NEUTRAL = "Neutral"


class RiskAxis:
    """Handler for Axis 14: Risk & Confidence - Risk Classification and Confidence Scoring"""
    
    def __init__(self):
        """Initialize the Risk & Confidence axis handler."""
        self.axis_number = 14
        self.axis_name = "Risk & Confidence"
        self.description = "Risk classification, confidence scoring, and validation metrics for knowledge elements"
        
        self.risk_classes = [rc.value for rc in RiskClass]
        self.confidence_impacts = [ci.value for ci in ConfidenceImpact]
        
        self.risk_thresholds = {
            "low": {"min_confidence": 0.85, "max_entropy": 0.15},
            "medium": {"min_confidence": 0.70, "max_entropy": 0.30},
            "high": {"min_confidence": 0.50, "max_entropy": 0.50},
            "critical": {"min_confidence": 0.0, "max_entropy": 1.0}
        }
    
    def navigate(self, **kwargs) -> Dict[str, Any]:
        """
        Navigate the Risk & Confidence axis based on provided parameters.
        
        Parameters:
        - risk_class (str): Filter by risk class (Low, Medium, High, Critical)
        - min_confidence (float): Minimum confidence score (0.0-1.0)
        - max_confidence (float): Maximum confidence score (0.0-1.0)
        - confidence_impact (str): Filter by confidence impact type
        - include_validation_metrics (bool): Include detailed validation metrics
        
        Returns:
        - Dict containing the navigation results
        """
        risk_class = kwargs.get('risk_class')
        min_confidence = kwargs.get('min_confidence', 0.0)
        max_confidence = kwargs.get('max_confidence', 1.0)
        confidence_impact = kwargs.get('confidence_impact')
        include_validation_metrics = kwargs.get('include_validation_metrics', False)
        
        try:
            result_data = {
                "axis": self.axis_number,
                "name": self.axis_name,
                "filters_applied": {
                    "risk_class": risk_class,
                    "confidence_range": [min_confidence, max_confidence],
                    "confidence_impact": confidence_impact
                },
                "risk_classes_available": self.risk_classes,
                "confidence_impacts_available": self.confidence_impacts
            }
            
            if include_validation_metrics:
                result_data["validation_metrics"] = self._get_validation_metrics()
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error navigating Risk & Confidence axis: {str(e)}")
            return {
                "axis": self.axis_number,
                "name": self.axis_name,
                "error": str(e)
            }
    
    def assess_risk(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk for a knowledge entity.
        
        Args:
            entity_data: Dictionary containing entity information
            
        Returns:
            Risk assessment results
        """
        confidence = entity_data.get('confidence', 0.5)
        entropy = entity_data.get('entropy', 0.5)
        sources_count = entity_data.get('sources_count', 1)
        validation_status = entity_data.get('validation_status', 'pending')
        
        risk_class = self._calculate_risk_class(confidence, entropy, sources_count)
        confidence_impact = self._calculate_confidence_impact(entity_data)
        
        return {
            "entity_id": entity_data.get('id'),
            "risk_class": risk_class.value,
            "confidence_score": confidence,
            "entropy_score": entropy,
            "confidence_impact": confidence_impact.value,
            "validation_status": validation_status,
            "risk_factors": self._identify_risk_factors(entity_data),
            "mitigation_suggestions": self._get_mitigation_suggestions(risk_class),
            "assessed_at": datetime.now(UTC).isoformat()
        }
    
    def _calculate_risk_class(self, confidence: float, entropy: float, sources_count: int) -> RiskClass:
        """Calculate risk class based on confidence, entropy, and source count."""
        if confidence >= 0.85 and entropy <= 0.15 and sources_count >= 3:
            return RiskClass.LOW
        elif confidence >= 0.70 and entropy <= 0.30:
            return RiskClass.MEDIUM
        elif confidence >= 0.50 or sources_count >= 2:
            return RiskClass.HIGH
        else:
            return RiskClass.CRITICAL
    
    def _calculate_confidence_impact(self, entity_data: Dict[str, Any]) -> ConfidenceImpact:
        """Calculate the confidence impact type."""
        has_direct_sources = entity_data.get('has_direct_sources', False)
        is_validated = entity_data.get('is_validated', False)
        
        if is_validated and has_direct_sources:
            return ConfidenceImpact.DIRECT_UP
        elif is_validated:
            return ConfidenceImpact.INDIRECT_UP
        elif has_direct_sources:
            return ConfidenceImpact.NEUTRAL
        else:
            return ConfidenceImpact.INDIRECT_DOWN
    
    def _identify_risk_factors(self, entity_data: Dict[str, Any]) -> List[str]:
        """Identify risk factors for an entity."""
        factors = []
        
        if entity_data.get('confidence', 1.0) < 0.5:
            factors.append("Low confidence score")
        if entity_data.get('entropy', 0.0) > 0.5:
            factors.append("High entropy signal")
        if entity_data.get('sources_count', 0) < 2:
            factors.append("Insufficient source validation")
        if not entity_data.get('is_validated', False):
            factors.append("Pending validation")
        if entity_data.get('age_days', 0) > 365:
            factors.append("Stale knowledge (>1 year old)")
        if entity_data.get('contradiction_count', 0) > 0:
            factors.append("Has contradicting information")
            
        return factors
    
    def _get_mitigation_suggestions(self, risk_class: RiskClass) -> List[str]:
        """Get mitigation suggestions based on risk class."""
        suggestions = {
            RiskClass.LOW: [
                "Continue standard monitoring",
                "Schedule periodic validation"
            ],
            RiskClass.MEDIUM: [
                "Increase source validation",
                "Cross-reference with additional axes",
                "Schedule expert review"
            ],
            RiskClass.HIGH: [
                "Immediate source verification required",
                "Engage domain expert for validation",
                "Consider confidence recalibration",
                "Review dependent knowledge elements"
            ],
            RiskClass.CRITICAL: [
                "URGENT: Halt propagation to dependent systems",
                "Immediate expert intervention required",
                "Quarantine affected knowledge chains",
                "Initiate containment protocol",
                "Full audit trail review"
            ]
        }
        return suggestions.get(risk_class, [])
    
    def _get_validation_metrics(self) -> Dict[str, Any]:
        """Get system-wide validation metrics."""
        return {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "pending_validations": 0,
            "average_confidence": 0.0,
            "risk_distribution": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            },
            "last_updated": datetime.now(UTC).isoformat()
        }
    
    def calculate_aggregate_confidence(self, entities: List[Dict[str, Any]]) -> float:
        """Calculate aggregate confidence score for multiple entities."""
        if not entities:
            return 0.0
        
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for entity in entities:
            confidence = entity.get('confidence', 0.5)
            weight = 1.0 - entity.get('entropy', 0.5)
            weighted_confidence += confidence * weight
            total_weight += weight
        
        if total_weight > 0:
            return weighted_confidence / total_weight
        return 0.0
    
    def get_axis_metadata(self) -> Dict[str, Any]:
        """Get metadata about this axis."""
        return {
            "axis_number": self.axis_number,
            "axis_name": self.axis_name,
            "description": self.description,
            "risk_classes": self.risk_classes,
            "confidence_impacts": self.confidence_impacts,
            "risk_thresholds": self.risk_thresholds
        }
