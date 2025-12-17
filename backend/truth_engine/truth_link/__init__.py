"""
TruthLink - Inter-Module Communication

Provides:
- Event bus for module messaging
- Priority queues with tier awareness
- SSE transport for real-time streaming
- Integration with Axis 15 (Federated Intelligence)
"""

from backend.truth_engine.truth_link.bus import TruthLinkBus
from backend.truth_engine.truth_link.queues import PriorityQueueManager
from backend.truth_engine.truth_link.transport import SSETransport

__all__ = ["TruthLinkBus", "PriorityQueueManager", "SSETransport"]
