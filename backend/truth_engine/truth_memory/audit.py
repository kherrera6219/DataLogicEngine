"""
TruthMemory Audit Logger

SHA-256 hash chain-based immutable audit logging.
"""

import logging
import hashlib
import uuid
import json
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Immutable audit logger with hash chains.
    
    Each event is linked to the previous via SHA-256 hash,
    creating a blockchain-like immutable audit trail.
    """

    def __init__(self, db_session=None, retention_years: int = 7):
        """Initialize audit logger."""
        self.db_session = db_session
        self.retention_years = retention_years
        self.in_memory_chain = {}
        self.event_count = 0
        logger.info("AuditLogger initialized")

    def log_event(self, session_id: str, event_type: str, 
                  event_data: Dict[str, Any], 
                  category: str = 'general') -> Dict[str, Any]:
        """
        Log an audit event with hash chain linking.
        
        Returns event record with hash.
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)
        
        previous_hash = self._get_previous_hash(session_id)
        
        event_payload = {
            'event_id': event_id,
            'session_id': session_id,
            'event_type': event_type,
            'category': category,
            'data': event_data,
            'timestamp': timestamp.isoformat()
        }
        
        current_hash = self._compute_hash(previous_hash, event_payload)
        
        retention_until = timestamp + timedelta(days=365 * self.retention_years)
        
        event_record = {
            'event_id': event_id,
            'session_id': session_id,
            'event_type': event_type,
            'event_category': category,
            'event_data': event_data,
            'hash_chain': current_hash,
            'previous_hash': previous_hash,
            'timestamp': timestamp.isoformat(),
            'retention_until': retention_until.isoformat()
        }
        
        if self.db_session:
            try:
                from models import TruthAuditEvent
                
                db_event = TruthAuditEvent(
                    event_id=event_id,
                    session_id=session_id,
                    event_type=event_type,
                    event_category=category,
                    event_data=event_data,
                    hash_chain=current_hash,
                    previous_hash=previous_hash,
                    timestamp=timestamp,
                    retention_until=retention_until,
                    compliance_flags={'eu_ai_act_article_53': True}
                )
                self.db_session.add(db_event)
                self.db_session.commit()
                logger.info(f"Persisted audit event {event_id} with hash {current_hash[:16]}...")
            except Exception as e:
                logger.error(f"Failed to persist audit event: {e}")
                self.db_session.rollback()
        
        if session_id not in self.in_memory_chain:
            self.in_memory_chain[session_id] = []
        self.in_memory_chain[session_id].append(event_record)
        
        self.event_count += 1
        
        return event_record

    def _get_previous_hash(self, session_id: str) -> str:
        """Get the hash of the previous event in the chain."""
        if self.db_session:
            try:
                from models import TruthAuditEvent
                previous = self.db_session.query(TruthAuditEvent).filter_by(
                    session_id=session_id
                ).order_by(TruthAuditEvent.id.desc()).first()
                
                if previous:
                    return previous.hash_chain
            except Exception as e:
                logger.warning(f"Failed to get previous hash from DB: {e}")
        
        if session_id in self.in_memory_chain and self.in_memory_chain[session_id]:
            return self.in_memory_chain[session_id][-1]['hash_chain']
        
        return '0' * 64

    def _compute_hash(self, previous_hash: str, payload: Dict[str, Any]) -> str:
        """Compute SHA-256 hash linking to previous event."""
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        combined = f"{previous_hash}{payload_str}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def verify_chain(self, session_id: str) -> Dict[str, Any]:
        """Verify integrity of audit chain for session."""
        events = self.get_trail(session_id)
        
        if not events:
            return {'valid': True, 'events_checked': 0, 'message': 'No events to verify'}
        
        is_valid = True
        broken_at = None
        
        for i, event in enumerate(events):
            if i == 0:
                expected_previous = '0' * 64
            else:
                expected_previous = events[i - 1]['hash_chain']
            
            if event['previous_hash'] != expected_previous:
                is_valid = False
                broken_at = i
                break
            
            payload = {
                'event_id': event['event_id'],
                'session_id': event['session_id'],
                'event_type': event['event_type'],
                'category': event.get('event_category', 'general'),
                'data': event.get('event_data', {}),
                'timestamp': event['timestamp']
            }
            
            expected_hash = self._compute_hash(event['previous_hash'], payload)
            if event['hash_chain'] != expected_hash:
                is_valid = False
                broken_at = i
                break
        
        return {
            'valid': is_valid,
            'events_checked': len(events),
            'broken_at': broken_at,
            'message': 'Chain verified successfully' if is_valid else f'Chain broken at event {broken_at}'
        }

    def get_trail(self, session_id: str) -> List[Dict[str, Any]]:
        """Get complete audit trail for session."""
        if self.db_session:
            try:
                from models import TruthAuditEvent
                events = self.db_session.query(TruthAuditEvent).filter_by(
                    session_id=session_id
                ).order_by(TruthAuditEvent.timestamp).all()
                
                return [e.to_dict() for e in events]
            except Exception as e:
                logger.error(f"Failed to get audit trail from DB: {e}")
        
        return self.in_memory_chain.get(session_id, [])

    def get_stats(self) -> Dict[str, Any]:
        """Get audit logger statistics."""
        return {
            'total_events': self.event_count,
            'sessions_tracked': len(self.in_memory_chain),
            'retention_years': self.retention_years
        }
