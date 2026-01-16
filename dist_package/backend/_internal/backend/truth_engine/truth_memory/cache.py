"""
TruthMemory Cache

High-performance caching for personas, sessions, and citations.
"""

import logging
import time
from typing import Dict, Any, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)


class TruthCache:
    """
    LRU cache with TTL support.
    
    Caches:
    - Personas: persona:{role_key}
    - Sessions: session:{request_id}
    - Citations: citation:{claim_id}
    """
    
    DEFAULT_TTL = {
        'persona': 86400,
        'session': 3600,
        'citation': 604800
    }
    
    MAX_SIZE = 10000

    def __init__(self, backend: str = 'memory', max_size: int = None):
        """Initialize cache with backend."""
        self.backend = backend
        self.max_size = max_size or self.MAX_SIZE
        self.cache = OrderedDict()
        self.ttls = {}
        self.hits = 0
        self.misses = 0
        logger.info(f"TruthCache initialized with {backend} backend")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            if self._is_expired(key):
                self._evict(key)
                self.misses += 1
                return None
            
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        
        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL."""
        if ttl is None:
            key_type = key.split(':')[0] if ':' in key else 'session'
            ttl = self.DEFAULT_TTL.get(key_type, 3600)
        
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[key] = value
        self.cache.move_to_end(key)
        self.ttls[key] = time.time() + ttl
        
        return True

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self.cache:
            self._evict(key)
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.ttls.clear()
        self.hits = 0
        self.misses = 0

    def _is_expired(self, key: str) -> bool:
        """Check if key is expired."""
        if key not in self.ttls:
            return False
        return time.time() > self.ttls[key]

    def _evict(self, key: str) -> None:
        """Evict a specific key."""
        if key in self.cache:
            del self.cache[key]
        if key in self.ttls:
            del self.ttls[key]

    def _evict_oldest(self) -> None:
        """Evict oldest entry (LRU)."""
        if self.cache:
            oldest_key = next(iter(self.cache))
            self._evict(oldest_key)

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_delete:
            self._evict(key)
        return len(keys_to_delete)

    def get_or_set(self, key: str, factory: callable, ttl: int = None) -> Any:
        """Get value or compute and cache it."""
        value = self.get(key)
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value, ttl)
        return value

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'backend': self.backend,
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'utilization': len(self.cache) / self.max_size
        }

    def cache_persona(self, role_key: str, persona_data: Dict[str, Any]) -> bool:
        """Cache persona with default persona TTL."""
        return self.set(f"persona:{role_key}", persona_data, self.DEFAULT_TTL['persona'])

    def get_persona(self, role_key: str) -> Optional[Dict[str, Any]]:
        """Get cached persona."""
        return self.get(f"persona:{role_key}")

    def cache_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Cache session with default session TTL."""
        return self.set(f"session:{session_id}", session_data, self.DEFAULT_TTL['session'])

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session."""
        return self.get(f"session:{session_id}")

    def cache_citation(self, claim_id: str, citation_data: Dict[str, Any]) -> bool:
        """Cache citation with default citation TTL."""
        return self.set(f"citation:{claim_id}", citation_data, self.DEFAULT_TTL['citation'])

    def get_citation(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get cached citation."""
        return self.get(f"citation:{claim_id}")
