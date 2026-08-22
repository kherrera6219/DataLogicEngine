"""Owner-only, fail-closed policy for optional runtime usage-data capture."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

CAPTURE_FLAG_KEY = "training_data_capture_enabled"
CAPTURE_SUBDIR = "capture"
CAPTURE_SCHEMA_VERSION = "dle.training-capture.v1"
CAPTURE_POLICY = "export-only"
ALLOWED_CAPTURE_FIELDS = (
    "schema_version",
    "run_id",
    "query",
    "released_answer",
    "confidence",
    "tier",
    "status",
    "truthgate_decision",
    "stages",
    "release_authorized",
    "quarantine",
    "containment_class",
    "captured_at",
    "source",
)


def is_training_data_capture_enabled() -> bool:
    """Return True only when the owner flag exists and is explicitly True.

    Missing rows, locked-off values, and any lookup failure stay OFF.
    """

    try:
        from models import FeatureFlag

        flag = FeatureFlag.query.filter_by(flag_key=CAPTURE_FLAG_KEY).first()
        if flag is None:
            return False
        return flag.value is True
    except Exception:
        logger.debug("Capture flag lookup failed closed", exc_info=True)
        return False


def get_capture_settings_payload() -> dict[str, Any]:
    """Owner-visible capture policy. Missing flag stays default OFF."""

    return {
        "enabled": is_training_data_capture_enabled(),
        "default": False,
        "flag_key": CAPTURE_FLAG_KEY,
        "policy": CAPTURE_POLICY,
        "redaction_enforced": True,
        "schema_version": CAPTURE_SCHEMA_VERSION,
    }


def get_or_create_capture_flag(*, description: str | None = None) -> Any:
    """Return the capture flag row, creating it as OFF when absent."""

    from extensions import db
    from models import FeatureFlag

    flag = FeatureFlag.query.filter_by(flag_key=CAPTURE_FLAG_KEY).first()
    if flag is None:
        flag = FeatureFlag(
            flag_key=CAPTURE_FLAG_KEY,
            value=False,
            description=description
            or "Owner-only runtime capture of released traces for later dataset export.",
            is_locked=False,
        )
        db.session.add(flag)
        db.session.flush()
    return flag


def set_training_data_capture_enabled(
    enabled: bool,
    *,
    actor_id: int | None,
    actor_username: str | None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Persist the capture flag and write an immutable audit event."""

    from extensions import db
    from models import AuditLog, FeatureFlagAuditEvent

    flag = get_or_create_capture_flag()
    old_value = bool(flag.value)
    new_value = bool(enabled)
    flag.value = new_value
    if actor_id is not None:
        flag.updated_by = actor_id

    db.session.add(
        FeatureFlagAuditEvent(
            flag_key=CAPTURE_FLAG_KEY,
            old_value=old_value,
            new_value=new_value,
            actor_id=actor_id,
            actor_username=actor_username,
            change_reason=reason or "owner_toggle",
            source="api",
        )
    )
    db.session.add(
        AuditLog(
            user_id=actor_id,
            action="training_data_capture_toggled",
            details=(
                f"flag={CAPTURE_FLAG_KEY} old={old_value} new={new_value}"
                + (f" reason={reason}" if reason else "")
            ),
        )
    )
    db.session.commit()
    return flag.to_dict()
