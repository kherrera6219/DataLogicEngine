"""
TruthMemory Manager - Persistent Memory and Audit

Central manager for caching, audit, and metrics.
"""

import logging
import os
from datetime import datetime, UTC
from typing import Dict, Any, Optional

from backend.truth_engine.truth_memory.audit import TruthAuditRecorder
from backend.truth_engine.truth_memory.cache import TruthCache
from backend.truth_engine.truth_memory.metrics import MetricsTracker
from backend.truth_engine.truth_memory.mlflow_tracker import TruthMemoryMLflowTracker

logger = logging.getLogger(__name__)


class TruthMemoryManager:
    """
    Central manager for TruthMemory subsystem.
    
    Coordinates:
    - Audit logging with hash chains
    - Caching for personas, sessions, citations
    - Metrics tracking
    - Artifact storage
    """

    def __init__(self, db_session=None, cache_backend: str = None):
        """Initialize TruthMemory with components."""
        self.db_session = db_session
        self.audit_logger = TruthAuditRecorder(db_session)
        if cache_backend is None:
            cache_backend = 'redis' if os.environ.get("USE_REDIS", "false").lower() in {"1", "true", "yes", "on"} else 'memory'
        self.cache = TruthCache(backend=cache_backend)
        self.metrics = MetricsTracker(db_session)
        self.mlflow_tracker = TruthMemoryMLflowTracker()
        logger.info("TruthMemoryManager initialized")

    def record_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a complete session with all data."""
        session_id = session_data.get('session_id')
        
        audit_result = self.audit_logger.log_event(
            session_id=session_id,
            event_type='session_complete',
            event_data=session_data
        )
        
        self.cache.set(
            key=f"session:{session_id}",
            value=session_data,
            ttl=3600
        )
        
        if 'confidence_score' in session_data:
            self.metrics.record(
                session_id=session_id,
                metric_name='confidence_score',
                value=session_data['confidence_score'],
                tier=session_data.get('tier')
            )
        
        if 'processing_time_ms' in session_data:
            self.metrics.record(
                session_id=session_id,
                metric_name='latency_ms',
                value=session_data['processing_time_ms'],
                tier=session_data.get('tier')
            )
        tracking_result = self.mlflow_tracker.record_session(session_data)
        
        return {
            'session_id': session_id,
            'audit_event_id': audit_result.get('event_id'),
            'cached': True,
            'metrics_recorded': True,
            'mlflow_tracking': tracking_result,
            'timestamp': datetime.now(UTC).isoformat()
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from cache or database."""
        cached = self.cache.get(f"session:{session_id}")
        if cached:
            return cached
        
        if self.db_session:
            try:
                from models import TruthSession
                session = self.db_session.query(TruthSession).filter_by(
                    session_id=session_id
                ).first()
                if session:
                    return session.to_dict()
            except Exception as e:
                logger.error(f"Failed to get session from DB: {e}")
        
        return None

    def store_artifact(self, session_id: str, artifact_type: str,
                       content: Any, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Store an artifact for a session."""
        import uuid
        import hashlib
        import json
        
        artifact_id = str(uuid.uuid4())
        
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content)
        else:
            content_str = str(content)
        
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()
        
        artifact = {
            'artifact_id': artifact_id,
            'session_id': session_id,
            'artifact_type': artifact_type,
            'content': content,
            'content_hash': content_hash,
            'metadata': metadata or {},
            'created_at': datetime.now(UTC).isoformat()
        }
        
        if self.db_session:
            try:
                from models import TruthArtifact
                from datetime import timedelta
                
                db_artifact = TruthArtifact(
                    artifact_id=artifact_id,
                    session_id=session_id,
                    artifact_type=artifact_type,
                    content=content if isinstance(content, dict) else {'data': content},
                    content_hash=content_hash,
                    artifact_metadata=metadata,
                    retention_until=datetime.now(UTC) + timedelta(days=365 * 7)
                )
                self.db_session.add(db_artifact)
                self.db_session.commit()
            except Exception as e:
                logger.error(f"Failed to store artifact: {e}")
        
        return artifact

    def get_artifacts(self, session_id: str, artifact_type: str = None) -> list:
        """Get artifacts for a session."""
        if not self.db_session:
            return []
        
        try:
            from models import TruthArtifact
            query = self.db_session.query(TruthArtifact).filter_by(session_id=session_id)
            if artifact_type:
                query = query.filter_by(artifact_type=artifact_type)
            return [a.to_dict() for a in query.all()]
        except Exception as e:
            logger.error(f"Failed to get artifacts: {e}")
            return []

    def get_explainability_data(self, session_id: str) -> Dict[str, Any]:
        """Get Article 13 explainability data for session."""
        session = self.get_session(session_id)
        audit_trail = self.audit_logger.get_trail(session_id)
        artifacts = self.get_artifacts(session_id)
        
        return {
            'session_id': session_id,
            'session': session,
            'audit_trail': audit_trail,
            'artifacts': artifacts,
            'reasoning_trace': self._extract_reasoning_trace(session),
            'confidence_breakdown': self._extract_confidence_breakdown(session),
            'personas_used': session.get('personas_used', []) if session else [],
            'axis_context': session.get('axis_context', {}) if session else {},
            'generated_at': datetime.now(UTC).isoformat()
        }

    def _extract_reasoning_trace(self, session: Dict[str, Any]) -> list:
        """Extract reasoning trace from session."""
        if not session:
            return []
        
        workflow_steps = session.get('workflow_steps', [])
        return [
            {
                'step': step.get('step', ''),
                'status': step.get('status', ''),
                'timestamp': step.get('timestamp', '')
            }
            for step in workflow_steps
        ]

    def _extract_confidence_breakdown(self, session: Dict[str, Any]) -> Dict[str, float]:
        """Extract confidence breakdown from session."""
        if not session:
            return {}
        
        return {
            'overall': session.get('confidence_score', 0),
            'safety': session.get('safety_score', 1.0)
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get TruthMemory statistics."""
        return {
            'cache_stats': self.cache.get_stats(),
            'metrics_summary': self.metrics.get_summary(),
            'audit_stats': self.audit_logger.get_stats()
        }
