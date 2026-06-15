from .base import AuditEvent, AuditStore, InMemoryAuditStore
from .file_store import FileAuditStore

__all__ = [
    "AuditEvent",
    "AuditStore",
    "FileAuditStore",
    "InMemoryAuditStore",
]

# Optional store
try:  # pragma: no cover
    from .postgres import PostgresAuditStore  # type: ignore
    __all__.append("PostgresAuditStore")
except Exception:
    PostgresAuditStore = None  # type: ignore
