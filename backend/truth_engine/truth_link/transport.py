"""
TruthLink SSE Transport

Server-Sent Events transport for real-time streaming.
"""

import logging
import json
import queue
import threading
from datetime import datetime, UTC
from typing import Dict, Any, Generator

logger = logging.getLogger(__name__)


class SSETransport:
    """
    Server-Sent Events transport for real-time communication.
    
    Provides:
    - Real-time event streaming
    - Client connection management
    - Event broadcasting
    """

    def __init__(self):
        """Initialize SSE transport."""
        self.clients = {}
        self.message_queues = {}
        self.lock = threading.Lock()
        logger.info("SSETransport initialized")

    def register_client(self, client_id: str) -> str:
        """Register a new SSE client."""
        with self.lock:
            self.clients[client_id] = {
                'connected_at': datetime.now(UTC).isoformat(),
                'last_event': None,
                'event_count': 0
            }
            self.message_queues[client_id] = queue.Queue(maxsize=100)
        
        logger.info(f"SSE client registered: {client_id}")
        return client_id

    def unregister_client(self, client_id: str) -> bool:
        """Unregister an SSE client."""
        with self.lock:
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.message_queues:
                del self.message_queues[client_id]
        
        logger.info(f"SSE client unregistered: {client_id}")
        return True

    def send_event(self, client_id: str, event_type: str, 
                   data: Dict[str, Any], event_id: str = None) -> bool:
        """Send event to specific client."""
        if client_id not in self.message_queues:
            return False
        
        event = {
            'id': event_id or datetime.now(UTC).isoformat(),
            'event': event_type,
            'data': data,
            'timestamp': datetime.now(UTC).isoformat()
        }
        
        try:
            self.message_queues[client_id].put_nowait(event)
            
            with self.lock:
                if client_id in self.clients:
                    self.clients[client_id]['last_event'] = event_type
                    self.clients[client_id]['event_count'] += 1
            
            return True
        except queue.Full:
            logger.warning(f"Message queue full for client {client_id}")
            return False

    def broadcast(self, event_type: str, data: Dict[str, Any]) -> int:
        """Broadcast event to all connected clients."""
        sent_count = 0
        
        for client_id in list(self.clients.keys()):
            if self.send_event(client_id, event_type, data):
                sent_count += 1
        
        return sent_count

    def stream_events(self, client_id: str) -> Generator[str, None, None]:
        """Generator for streaming SSE events to client."""
        if client_id not in self.message_queues:
            self.register_client(client_id)
        
        yield self._format_sse_event('connected', {'client_id': client_id})
        
        while client_id in self.clients:
            try:
                event = self.message_queues[client_id].get(timeout=30)
                yield self._format_sse_event(
                    event['event'],
                    event['data'],
                    event['id']
                )
            except queue.Empty:
                yield self._format_sse_event('heartbeat', {'timestamp': datetime.now(UTC).isoformat()})
            except Exception as e:
                logger.error(f"Error streaming to client {client_id}: {e}")
                break

    def _format_sse_event(self, event_type: str, data: Dict[str, Any], 
                          event_id: str = None) -> str:
        """Format event as SSE message."""
        lines = []
        
        if event_id:
            lines.append(f"id: {event_id}")
        
        lines.append(f"event: {event_type}")
        lines.append(f"data: {json.dumps(data)}")
        lines.append("")
        
        return "\n".join(lines) + "\n"

    def get_client_count(self) -> int:
        """Get number of connected clients."""
        return len(self.clients)

    def get_client_info(self, client_id: str = None) -> Dict[str, Any]:
        """Get client connection info."""
        if client_id:
            return self.clients.get(client_id, {})
        return self.clients

    def get_stats(self) -> Dict[str, Any]:
        """Get transport statistics."""
        total_events = sum(
            client.get('event_count', 0) 
            for client in self.clients.values()
        )
        
        return {
            'connected_clients': len(self.clients),
            'total_events_sent': total_events,
            'queue_sizes': {
                client_id: q.qsize() 
                for client_id, q in self.message_queues.items()
            }
        }
