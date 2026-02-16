"""
Trace & Provenance Service

This module provides audit-grade traceability for the UKG system.
It records every operation, artifact creation, and state mutation, 
linking them through the Unified Artifact Envelope (UAE) and FROST snapshots.
"""

import logging
import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from core.system.uae_models import UnifiedArtifactEnvelope

class TraceProvenanceService:
    """
    Trace & Provenance Service
    
    Responsibilities:
    1. Maintain a high-fidelity audit log of all system events.
    2. Link artifacts via parent-child provenance chains.
    3. Integration with the 17-axis coordinate system for spatial auditing.
    4. Provide causal trace graphs for simulation runs.
    """
    
    def __init__(self, uae_store=None):
        self.logger = logging.getLogger(__name__)
        
        # In-memory log (should be backed by durable storage/Elasticsearch in production)
        self.trace_log: List[Dict[str, Any]] = []
        
        # Artifact lookup for provenance traversal
        self.artifacts: Dict[str, UnifiedArtifactEnvelope] = {}

    def log_event(self, 
                  event_type: str, 
                  source_id: str, 
                  payload: Dict[str, Any], 
                  coord: Optional[str] = None,
                  run_id: Optional[str] = None) -> str:
        """Log a generic system event."""
        event_id = f"trace_{uuid.uuid4().hex[:12]}"
        
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "source_id": source_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "coord": coord,
            "run_id": run_id,
            "payload": payload
        }
        
        self.trace_log.append(event)
        self.logger.debug(f"Logged trace event: {event_id} ({event_type})")
        return event_id

    def register_artifact(self, envelope: UnifiedArtifactEnvelope):
        """Register an artifact in the trace service and log its creation."""
        self.artifacts[envelope.artifact_id] = envelope
        
        self.log_event(
            event_type="artifact_creation",
            source_id=envelope.provenance[-1].source_id if envelope.provenance else "unknown",
            payload={
                "artifact_id": envelope.artifact_id,
                "payload_type": envelope.payload_type,
                "confidence": envelope.confidence_vector.overall
            },
            coord=str(envelope.coord17),
            run_id=envelope.run_id
        )

    def get_provenance_chain(self, artifact_id: str) -> List[UnifiedArtifactEnvelope]:
        """Traverse backwards in the provenance chain for an artifact."""
        chain = []
        current_id = artifact_id
        
        visited = set()
        while current_id in self.artifacts and current_id not in visited:
            visited.add(current_id)
            envelope = self.artifacts[current_id]
            chain.append(envelope)
            
            # For simplicity, follow the first input_id of the last provenance entry
            if envelope.provenance and envelope.provenance[-1].input_ids:
                current_id = envelope.provenance[-1].input_ids[0]
            else:
                break
                
        return chain

    def build_causal_graph(self, run_id: str) -> Dict[str, Any]:
        """Build a graph of all artifacts and events for a specific run."""
        run_artifacts = [a for a in self.artifacts.values() if a.run_id == run_id]
        
        nodes = []
        edges = []
        
        for art in run_artifacts:
            nodes.append({
                "id": art.artifact_id,
                "label": art.payload_type,
                "type": "artifact"
            })
            
            for prov in art.provenance:
                for input_id in prov.input_ids:
                    edges.append({
                        "from": input_id,
                        "to": art.artifact_id,
                        "label": prov.operation
                    })
                    
        return {"nodes": nodes, "edges": edges}

    def check_health(self) -> Dict[str, Any]:
        """System health check."""
        return {
            "healthy": True,
            "event_count": len(self.trace_log),
            "artifact_count": len(self.artifacts)
        }
