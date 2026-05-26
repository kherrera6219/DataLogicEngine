"""TruthMemory adapter for DMRF telemetry."""

from __future__ import annotations

from backend.truth_engine.truth_memory.audit import AuditLogger
from backend.dmrf.models import DMRFResult


class TruthMemoryDMRFAdapter:
    """Persist DMRF bundles into TruthAuditEvent-compatible audit logs."""

    def __init__(self, db_session=None):
        self.db_session = db_session

    def persist(self, result: DMRFResult, *, session_id: str | None = None) -> dict:
        return AuditLogger(db_session=self.db_session).log_event(
            session_id=session_id,
            event_type="dmrf_result",
            event_data=result.export_bundle(),
            category="dmrf",
        )

