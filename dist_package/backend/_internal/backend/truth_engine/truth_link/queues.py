"""
TruthLink Priority Queue Manager

Tier-aware priority queues for request processing.
"""

import logging
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from collections import defaultdict
import heapq

logger = logging.getLogger(__name__)


class PriorityQueueManager:
    """
    Manages priority queues for tier-based processing.
    
    Priority levels (P0-P5):
    - P0: Trivial (SLA 1s)
    - P1: Moderate (SLA 3s)
    - P2: High-Stakes (SLA 10s)
    - P3: Extreme (SLA 60s)
    - P4: Autonomous (SLA 300s)
    - P5: HITL (SLA 30s)
    """
    
    PRIORITY_CONFIG = {
        'p0': {'name': 'Trivial', 'sla_ms': 1000, 'max_queue': 1000},
        'p1': {'name': 'Moderate', 'sla_ms': 3000, 'max_queue': 500},
        'p2': {'name': 'High-Stakes', 'sla_ms': 10000, 'max_queue': 200},
        'p3': {'name': 'Extreme', 'sla_ms': 60000, 'max_queue': 100},
        'p4': {'name': 'Autonomous', 'sla_ms': 300000, 'max_queue': 50},
        'p5': {'name': 'HITL', 'sla_ms': 30000, 'max_queue': 20}
    }

    def __init__(self):
        """Initialize priority queue manager."""
        self.queues = {p: [] for p in self.PRIORITY_CONFIG}
        self.processed = defaultdict(int)
        self.sla_violations = defaultdict(int)
        logger.info("PriorityQueueManager initialized")

    def enqueue(self, priority: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Add item to priority queue."""
        if priority not in self.PRIORITY_CONFIG:
            priority = 'p1'
        
        config = self.PRIORITY_CONFIG[priority]
        
        if len(self.queues[priority]) >= config['max_queue']:
            return {
                'success': False,
                'error': 'Queue full',
                'queue': priority,
                'queue_size': len(self.queues[priority])
            }
        
        item['_queued_at'] = datetime.now(UTC).isoformat()
        item['_priority'] = priority
        item['_sla_deadline'] = config['sla_ms']
        
        heapq.heappush(self.queues[priority], 
                       (datetime.now(UTC).timestamp(), item))
        
        return {
            'success': True,
            'queue': priority,
            'queue_size': len(self.queues[priority]),
            'sla_ms': config['sla_ms']
        }

    def dequeue(self, priority: str = None) -> Optional[Dict[str, Any]]:
        """Get next item from queue (highest priority first)."""
        if priority:
            if self.queues[priority]:
                _, item = heapq.heappop(self.queues[priority])
                self._check_sla(priority, item)
                self.processed[priority] += 1
                return item
            return None
        
        for p in ['p0', 'p1', 'p2', 'p3', 'p4', 'p5']:
            if self.queues[p]:
                _, item = heapq.heappop(self.queues[p])
                self._check_sla(p, item)
                self.processed[p] += 1
                return item
        
        return None

    def _check_sla(self, priority: str, item: Dict[str, Any]) -> None:
        """Check if SLA was violated."""
        queued_at = datetime.fromisoformat(item.get('_queued_at', datetime.now(UTC).isoformat()))
        wait_time_ms = (datetime.now(UTC) - queued_at).total_seconds() * 1000
        
        sla_ms = self.PRIORITY_CONFIG[priority]['sla_ms']
        if wait_time_ms > sla_ms:
            self.sla_violations[priority] += 1
            logger.warning(f"SLA violation for {priority}: {wait_time_ms:.0f}ms > {sla_ms}ms")

    def peek(self, priority: str) -> Optional[Dict[str, Any]]:
        """Peek at next item without removing."""
        if self.queues[priority]:
            return self.queues[priority][0][1]
        return None

    def get_queue_status(self, priority: str = None) -> Dict[str, Any]:
        """Get status of queue(s)."""
        if priority:
            config = self.PRIORITY_CONFIG.get(priority, {})
            return {
                'priority': priority,
                'name': config.get('name', 'Unknown'),
                'size': len(self.queues.get(priority, [])),
                'max_size': config.get('max_queue', 0),
                'sla_ms': config.get('sla_ms', 0),
                'processed': self.processed[priority],
                'sla_violations': self.sla_violations[priority]
            }
        
        return {
            p: {
                'name': config['name'],
                'size': len(self.queues[p]),
                'max_size': config['max_queue'],
                'sla_ms': config['sla_ms'],
                'processed': self.processed[p],
                'sla_violations': self.sla_violations[p]
            }
            for p, config in self.PRIORITY_CONFIG.items()
        }

    def get_total_pending(self) -> int:
        """Get total pending items across all queues."""
        return sum(len(q) for q in self.queues.values())

    def clear_queue(self, priority: str) -> int:
        """Clear a specific queue."""
        if priority in self.queues:
            count = len(self.queues[priority])
            self.queues[priority] = []
            return count
        return 0

    def tier_to_priority(self, tier: str) -> str:
        """Convert tier name to priority level."""
        mapping = {
            'trivial': 'p0',
            'moderate': 'p1',
            'high_stakes': 'p2',
            'extreme': 'p3',
            'autonomous': 'p4',
            'hitl': 'p5'
        }
        return mapping.get(tier, 'p1')
