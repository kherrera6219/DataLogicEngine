"""
Universal Knowledge Graph (UKG) System - Axis 16: Arrows of Time

This module implements the Arrows of Time axis for the 17-Axis UKG system,
providing advanced temporal reasoning with causality chains, chronological 
consistency, and predictive modeling capabilities.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class TimeDirection(Enum):
    """Time direction types"""
    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"
    BIDIRECTIONAL = "bidirectional"


class CausalityType(Enum):
    """Causality relationship types"""
    CAUSES = "causes"
    CAUSED_BY = "caused_by"
    ENABLES = "enables"
    PREVENTS = "prevents"
    CORRELATES = "correlates"
    FOLLOWS = "follows"
    PRECEDES = "precedes"


class TemporalConsistency(Enum):
    """Temporal consistency states"""
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    PARADOX = "paradox"
    UNCERTAIN = "uncertain"


class ArrowsOfTimeAxis:
    """Handler for Axis 16: Arrows of Time - Advanced Temporal Reasoning and Causality"""
    
    def __init__(self):
        """Initialize the Arrows of Time axis handler."""
        self.axis_number = 16
        self.axis_name = "Arrows of Time"
        self.description = "Advanced temporal reasoning with causality chains, chronological consistency, and predictive modeling"
        
        self.time_directions = [d.value for d in TimeDirection]
        self.causality_types = [c.value for c in CausalityType]
        self.consistency_states = [c.value for c in TemporalConsistency]
        
        self.causality_chains = {}
        self.temporal_anchors = {}
        self.predictions = []
    
    def navigate(self, **kwargs) -> Dict[str, Any]:
        """
        Navigate the Arrows of Time axis based on provided parameters.
        
        Parameters:
        - time_direction (str): Direction of temporal analysis (past, present, future)
        - causality_type (str): Type of causality relationship
        - anchor_event (str): Reference event for temporal navigation
        - horizon (int): Number of time steps to project (positive=future, negative=past)
        - include_predictions (bool): Include predictive modeling results
        
        Returns:
        - Dict containing the navigation results
        """
        time_direction = kwargs.get('time_direction')
        causality_type = kwargs.get('causality_type')
        anchor_event = kwargs.get('anchor_event')
        horizon = kwargs.get('horizon', 0)
        include_predictions = kwargs.get('include_predictions', False)
        
        try:
            result_data = {
                "axis": self.axis_number,
                "name": self.axis_name,
                "filters_applied": {
                    "time_direction": time_direction,
                    "causality_type": causality_type,
                    "anchor_event": anchor_event,
                    "horizon": horizon
                },
                "time_directions_available": self.time_directions,
                "causality_types_available": self.causality_types,
                "consistency_states": self.consistency_states
            }
            
            if anchor_event:
                result_data["causality_chain"] = self._get_causality_chain(anchor_event, time_direction)
            
            if include_predictions and horizon > 0:
                result_data["predictions"] = self._get_predictions(anchor_event, horizon)
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error navigating Arrows of Time axis: {str(e)}")
            return {
                "axis": self.axis_number,
                "name": self.axis_name,
                "error": str(e)
            }
    
    def create_causality_link(self, source_event: str, target_event: str,
                               causality_type: str, strength: float = 0.5,
                               metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a causality link between events.
        
        Args:
            source_event: The source event identifier
            target_event: The target event identifier
            causality_type: Type of causal relationship
            strength: Strength of the causal relationship (0.0-1.0)
            metadata: Additional metadata for the link
            
        Returns:
            Created causality link
        """
        link_id = str(uuid.uuid4())
        
        link = {
            "link_id": link_id,
            "source_event": source_event,
            "target_event": target_event,
            "causality_type": causality_type,
            "strength": max(0.0, min(1.0, strength)),
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        if source_event not in self.causality_chains:
            self.causality_chains[source_event] = []
        self.causality_chains[source_event].append(link)
        
        logger.info(f"Created causality link: {source_event} -> {target_event} ({causality_type})")
        
        return link
    
    def analyze_causality_chain(self, start_event: str, max_depth: int = 5) -> Dict[str, Any]:
        """
        Analyze the causality chain from a starting event.
        
        Args:
            start_event: Starting event identifier
            max_depth: Maximum depth to traverse
            
        Returns:
            Causality chain analysis
        """
        visited = set()
        chain = []
        
        def traverse(event: str, depth: int, direction: str):
            if depth > max_depth or event in visited:
                return
            visited.add(event)
            
            links = self.causality_chains.get(event, [])
            for link in links:
                chain.append({
                    "depth": depth,
                    "link": link,
                    "direction": direction
                })
                traverse(link["target_event"], depth + 1, direction)
        
        traverse(start_event, 0, "forward")
        
        for event, links in self.causality_chains.items():
            for link in links:
                if link["target_event"] == start_event and event not in visited:
                    chain.append({
                        "depth": -1,
                        "link": link,
                        "direction": "backward"
                    })
        
        return {
            "start_event": start_event,
            "chain_length": len(chain),
            "max_depth_reached": max(c["depth"] for c in chain) if chain else 0,
            "chain": chain,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def check_temporal_consistency(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check temporal consistency of a set of events.
        
        Args:
            events: List of events with timestamps
            
        Returns:
            Consistency analysis results
        """
        inconsistencies = []
        paradoxes = []
        
        sorted_events = sorted(events, key=lambda e: e.get('timestamp', ''))
        
        for i, event in enumerate(sorted_events):
            causes = [c for c in self.causality_chains.get(event.get('id', ''), [])
                      if c["causality_type"] in ["causes", "enables"]]
            
            for cause in causes:
                target_idx = next((j for j, e in enumerate(sorted_events) 
                                   if e.get('id') == cause["target_event"]), None)
                if target_idx is not None and target_idx < i:
                    paradoxes.append({
                        "type": "reverse_causality",
                        "source_event": event.get('id'),
                        "target_event": cause["target_event"],
                        "message": "Effect appears before cause"
                    })
        
        consistency_state = TemporalConsistency.CONSISTENT.value
        if paradoxes:
            consistency_state = TemporalConsistency.PARADOX.value
        elif inconsistencies:
            consistency_state = TemporalConsistency.INCONSISTENT.value
        
        return {
            "events_analyzed": len(events),
            "consistency_state": consistency_state,
            "inconsistencies": inconsistencies,
            "paradoxes": paradoxes,
            "is_consistent": len(inconsistencies) == 0 and len(paradoxes) == 0,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def create_temporal_anchor(self, anchor_id: str, anchor_time: datetime,
                                significance: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a temporal anchor point for reference.
        
        Args:
            anchor_id: Unique identifier for the anchor
            anchor_time: The datetime of the anchor
            significance: Description of the anchor's significance
            metadata: Additional metadata
            
        Returns:
            Created temporal anchor
        """
        anchor = {
            "anchor_id": anchor_id,
            "anchor_time": anchor_time.isoformat(),
            "significance": significance,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "linked_events": []
        }
        
        self.temporal_anchors[anchor_id] = anchor
        
        return anchor
    
    def generate_prediction(self, base_event: str, horizon_days: int,
                            confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Generate a prediction based on causality chains.
        
        Args:
            base_event: The event to base predictions on
            horizon_days: Number of days into the future to predict
            confidence_threshold: Minimum confidence for predictions
            
        Returns:
            Prediction results
        """
        prediction_id = str(uuid.uuid4())
        
        causality_data = self.causality_chains.get(base_event, [])
        
        predicted_events = []
        for link in causality_data:
            if link["causality_type"] in ["causes", "enables", "follows"]:
                confidence = link["strength"] * 0.8
                if confidence >= confidence_threshold:
                    predicted_events.append({
                        "event": link["target_event"],
                        "probability": confidence,
                        "basis": f"Causal link from {base_event}",
                        "horizon_applicable": horizon_days
                    })
        
        prediction = {
            "prediction_id": prediction_id,
            "base_event": base_event,
            "horizon_days": horizon_days,
            "generated_at": datetime.utcnow().isoformat(),
            "predicted_events": predicted_events,
            "confidence_threshold": confidence_threshold,
            "model_version": "1.0.0"
        }
        
        self.predictions.append(prediction)
        
        return prediction
    
    def _get_causality_chain(self, anchor_event: str, direction: Optional[str]) -> List[Dict]:
        """Get causality chain for an event."""
        if direction == TimeDirection.PAST.value:
            return [link for event, links in self.causality_chains.items()
                    for link in links if link["target_event"] == anchor_event]
        elif direction == TimeDirection.FUTURE.value:
            return self.causality_chains.get(anchor_event, [])
        else:
            forward = self.causality_chains.get(anchor_event, [])
            backward = [link for event, links in self.causality_chains.items()
                        for link in links if link["target_event"] == anchor_event]
            return forward + backward
    
    def _get_predictions(self, anchor_event: Optional[str], horizon: int) -> List[Dict]:
        """Get predictions for an event."""
        if anchor_event:
            return [p for p in self.predictions 
                    if p["base_event"] == anchor_event and p["horizon_days"] <= horizon]
        return self.predictions[-10:]
    
    def get_axis_metadata(self) -> Dict[str, Any]:
        """Get metadata about this axis."""
        return {
            "axis_number": self.axis_number,
            "axis_name": self.axis_name,
            "description": self.description,
            "time_directions": self.time_directions,
            "causality_types": self.causality_types,
            "consistency_states": self.consistency_states,
            "total_causality_links": sum(len(links) for links in self.causality_chains.values()),
            "total_anchors": len(self.temporal_anchors),
            "total_predictions": len(self.predictions)
        }
