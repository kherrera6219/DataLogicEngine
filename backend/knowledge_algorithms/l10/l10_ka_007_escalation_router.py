"""L10-KA-007: human escalation routing."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import uuid

HIGH_TOUCH_DOMAINS = {"healthcare", "finance", "legal", "high_risk", "regulated"}


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    domain = str(inputs.get("risk_domain") or inputs.get("domain") or "standard").lower()
    confidence = float(inputs.get("confidence", inputs.get("decayed_confidence", 1.0)) or 0.0)
    violations = inputs.get("violations") or []
    should_escalate = domain in HIGH_TOUCH_DOMAINS or confidence < 0.90 or bool(violations)
    ticket = None
    if should_escalate:
        ticket = {
            "ticket_id": f"hitl_{uuid.uuid4().hex[:12]}",
            "queue": "human_review",
            "risk_domain": domain,
            "created_at": datetime.now(UTC).isoformat(),
            "reason": inputs.get("reason") or "Layer 10 escalation policy",
        }
        _write_optional_audit(ticket, inputs)
    return {
        "success": True,
        "escalated": should_escalate,
        "hitl_ticket": ticket,
    }


def _write_optional_audit(ticket: dict[str, Any], inputs: dict[str, Any]) -> None:
    try:
        from backend.truth_engine.truth_memory.audit import AuditLogger
        from extensions import db

        AuditLogger(db_session=db.session).log_event(
            session_id=inputs.get("session_id"),
            event_type="l10_human_escalation",
            event_data=ticket,
            category="safety",
        )
    except Exception:
        return
