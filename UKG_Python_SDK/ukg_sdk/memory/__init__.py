from .base import MemoryAdapter, MemoryRecord
from .in_memory import InMemoryMemoryAdapter

__all__ = [
    "MemoryAdapter",
    "MemoryRecord",
    "InMemoryMemoryAdapter",
]

# Optional adapters (may require extras)
try:  # pragma: no cover
    from .postgres import PostgresMemoryAdapter  # type: ignore
    __all__.append("PostgresMemoryAdapter")
except Exception:
    PostgresMemoryAdapter = None  # type: ignore

try:  # pragma: no cover
    from .redis import RedisMemoryAdapter  # type: ignore
    __all__.append("RedisMemoryAdapter")
except Exception:
    RedisMemoryAdapter = None  # type: ignore
