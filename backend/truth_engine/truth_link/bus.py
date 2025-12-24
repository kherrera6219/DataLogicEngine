"""
TruthLink Event Bus

Inter-module messaging system.
"""

import logging
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List, Callable, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class TruthLinkBus:
    """
    Event bus for inter-module communication.
    
    Supports:
    - Publish/subscribe pattern
    - Priority-based message routing
    - Message persistence
    - Dead letter queue
    """
    
    MODULES = ['truth_core', 'truth_gate', 'truth_memory', 'truth_link']
    
    MESSAGE_TYPES = [
        'session_created',
        'session_completed',
        'tier_selected',
        'policy_evaluated',
        'budget_updated',
        'audit_logged',
        'artifact_stored',
        'metric_recorded'
    ]

    def __init__(self, db_session=None):
        """Initialize event bus."""
        self.db_session = db_session
        self.subscribers = defaultdict(list)
        self.message_queue = []
        self.dead_letter_queue = []
        self.processed_count = 0
        self.failed_count = 0
        
        from backend.truth_engine.truth_link.transport import SSETransport
        self.sse_transport = SSETransport()
        
        logger.info("TruthLinkBus initialized")

    def publish(self, source_module: str, message_type: str, 
                payload: Dict[str, Any], target_module: str = None,
                priority: int = 1, session_id: str = None) -> Dict[str, Any]:
        """Publish a message to the bus."""
        message_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)
        
        message = {
            'message_id': message_id,
            'source_module': source_module,
            'target_module': target_module,
            'message_type': message_type,
            'priority': priority,
            'payload': payload,
            'session_id': session_id,
            'status': 'pending',
            'created_at': timestamp.isoformat()
        }
        
        self.message_queue.append(message)
        self.message_queue.sort(key=lambda m: m['priority'], reverse=True)
        
        if self.db_session:
            try:
                from models import TruthLinkMessage
                
                db_message = TruthLinkMessage(
                    message_id=message_id,
                    source_module=source_module,
                    target_module=target_module,
                    message_type=message_type,
                    priority=priority,
                    payload=payload,
                    link_session_id=session_id,
                    status='pending',
                    created_at=timestamp
                )
                self.db_session.add(db_message)
                self.db_session.commit()
            except Exception as e:
                logger.error(f"Failed to persist message: {e}")
        
        self._dispatch(message)
        
        return message

    def subscribe(self, message_type: str, handler: Callable[[Dict[str, Any]], None],
                  target_module: str = None) -> str:
        """Subscribe to a message type."""
        subscription_id = str(uuid.uuid4())
        
        self.subscribers[message_type].append({
            'subscription_id': subscription_id,
            'handler': handler,
            'target_module': target_module
        })
        
        logger.info(f"Subscribed to {message_type} with ID {subscription_id}")
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from messages."""
        for message_type, subs in self.subscribers.items():
            for i, sub in enumerate(subs):
                if sub['subscription_id'] == subscription_id:
                    del subs[i]
                    return True
        return False

    def _dispatch(self, message: Dict[str, Any]) -> None:
        """Dispatch message to subscribers and SSE clients."""
        message_type = message['message_type']
        target_module = message.get('target_module')
        
        subscribers = self.subscribers.get(message_type, [])
        
        for sub in subscribers:
            if target_module and sub['target_module'] and sub['target_module'] != target_module:
                continue
            
            try:
                sub['handler'](message)
                self.processed_count += 1
                message['status'] = 'delivered'
            except Exception as e:
                logger.error(f"Handler failed for message {message['message_id']}: {e}")
                self.failed_count += 1
                message['retry_count'] = message.get('retry_count', 0) + 1
                
                if message['retry_count'] >= 3:
                    message['status'] = 'dead_letter'
                    self.dead_letter_queue.append(message)
        
        try:
            sse_payload = {
                'message_id': message['message_id'],
                'message_type': message_type,
                'source_module': message['source_module'],
                'session_id': message.get('session_id'),
                'timestamp': message.get('created_at')
            }
            self.sse_transport.broadcast(message_type, sse_payload)
        except Exception as e:
            logger.warning(f"SSE broadcast failed: {e}")

    def get_pending_messages(self, target_module: str = None) -> List[Dict[str, Any]]:
        """Get pending messages for a module."""
        messages = [m for m in self.message_queue if m['status'] == 'pending']
        
        if target_module:
            messages = [m for m in messages 
                       if m.get('target_module') is None or m['target_module'] == target_module]
        
        return messages

    def get_dead_letter_queue(self) -> List[Dict[str, Any]]:
        """Get messages in dead letter queue."""
        return self.dead_letter_queue

    def retry_dead_letter(self, message_id: str) -> bool:
        """Retry a message from dead letter queue."""
        for i, message in enumerate(self.dead_letter_queue):
            if message['message_id'] == message_id:
                message['status'] = 'pending'
                message['retry_count'] = 0
                self.message_queue.append(message)
                del self.dead_letter_queue[i]
                self._dispatch(message)
                return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get bus statistics."""
        return {
            'queue_size': len(self.message_queue),
            'dead_letter_size': len(self.dead_letter_queue),
            'processed_count': self.processed_count,
            'failed_count': self.failed_count,
            'subscriber_count': sum(len(subs) for subs in self.subscribers.values()),
            'sse_clients': len(self.sse_transport.clients),
            'modules': self.MODULES,
            'message_types': self.MESSAGE_TYPES
        }


def create_default_bus(db_session=None) -> TruthLinkBus:
    """Create bus with default handlers."""
    bus = TruthLinkBus(db_session)
    
    def log_handler(message: Dict[str, Any]) -> None:
        logger.debug(f"Message received: {message['message_type']} from {message['source_module']}")
    
    for msg_type in TruthLinkBus.MESSAGE_TYPES:
        bus.subscribe(msg_type, log_handler)
    
    return bus
