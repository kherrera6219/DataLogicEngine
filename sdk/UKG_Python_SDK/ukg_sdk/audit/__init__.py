from .base import AuditEvent, AuditStore
from .file_store import FileAuditStore

__all__ = [
    "AuditEvent",
    "AuditStore",
    "FileAuditStore",
]

# Optional store
try:  # pragma: no cover
    from .postgres import PostgresAuditStore  # type: ignore
    __all__.append("PostgresAuditStore")
except Exception:
    PostgresAuditStore = None  # type: ignore
