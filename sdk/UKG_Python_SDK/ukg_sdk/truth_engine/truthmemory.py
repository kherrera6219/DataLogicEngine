"""
Simplified implementation of the TruthMemory component.

This module provides a minimal in‑memory logging facility and stubs for
persistent storage adapters.  The real system would need to enforce immutability,
retention policies and support compliance queries.
"""
from __future__ import annotations

from typing import Any, Dict, List


class InMemoryMemoryAdapter:
    """Default in‑memory storage backend."""

    def __init__(self) -> None:
        # Each request/response pair is appended to this list
        self._history: List[Dict[str, Any]] = []

    def log(self, entry: Dict[str, Any]) -> None:
        self._history.append(entry)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)


class PostgresMemoryAdapter(InMemoryMemoryAdapter):
    """
    Stub for a Postgres memory adapter.

    In a full implementation, this would connect to a Postgres instance and
    persist entries using SQLAlchemy or psycopg2.  It inherits from
    InMemoryMemoryAdapter to reuse the in‑memory log in this stub.
    """

    def __init__(self, dsn: str = "") -> None:
        super().__init__()
        self.dsn = dsn

    # Additional database logic would go here.


class RedisMemoryAdapter(InMemoryMemoryAdapter):
    """
    Stub for a Redis memory adapter.

    In a full implementation, this would persist history to a Redis database
    using a sorted set or list structure.  Here we simply fall back to the
    in‑memory list.
    """

    def __init__(self, url: str = "") -> None:
        super().__init__()
        self.url = url

    # Additional Redis logic would go here.


class TruthMemory:
    """High‑level memory manager that delegates to a backend adapter."""

    def __init__(self, adapter: str = "inmemory") -> None:
        if adapter.lower() == "postgres":
            self._adapter = PostgresMemoryAdapter()
        elif adapter.lower() == "redis":
            self._adapter = RedisMemoryAdapter()
        else:
            self._adapter = InMemoryMemoryAdapter()

    def log_request(self, request: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Log a request/response pair."""
        entry = {
            "request": request,
            "result": result,
        }
        self._adapter.log(entry)

    def get_history(self) -> List[Dict[str, Any]]:
        return self._adapter.get_history()