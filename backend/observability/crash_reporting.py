"""
Crash reporting initialization and fallback capture helpers.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_STATE: Dict[str, Any] = {
    "enabled": False,
    "provider": "none",
    "initialized": False,
    "init_error": None,
    "captured_total": 0,
    "fallback_total": 0,
}
_SENTRY_SDK = None


def initialize_crash_reporting(
    *,
    dsn: Optional[str],
    environment: str,
    release: str,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
) -> Dict[str, Any]:
    """
    Initialize crash reporting provider if configured.

    Returns current crash reporting state.
    """
    global _SENTRY_SDK
    _STATE["initialized"] = True

    if not dsn:
        _STATE["enabled"] = False
        _STATE["provider"] = "none"
        _STATE["init_error"] = None
        return crash_reporting_state()

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    except Exception as exc:  # noqa: BLE001
        _STATE["enabled"] = False
        _STATE["provider"] = "none"
        _STATE["init_error"] = f"sentry_import_failed: {exc}"
        logger.warning("Sentry SDK import failed; crash reporting fallback mode only", exc_info=exc)
        return crash_reporting_state()

    try:
        sentry_sdk.init(
            dsn=dsn,
            integrations=[FlaskIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=float(traces_sample_rate),
            profiles_sample_rate=float(profiles_sample_rate),
            environment=environment,
            release=release,
        )
        _SENTRY_SDK = sentry_sdk
        _STATE["enabled"] = True
        _STATE["provider"] = "sentry"
        _STATE["init_error"] = None
    except Exception as exc:  # noqa: BLE001
        _STATE["enabled"] = False
        _STATE["provider"] = "none"
        _STATE["init_error"] = f"sentry_init_failed: {exc}"
        logger.error("Crash reporting provider initialization failed", exc_info=exc)
    return crash_reporting_state()


def capture_exception_with_fallback(
    exc: BaseException,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Capture an exception and always return a stable crash id.

    If provider capture fails or provider is disabled, a deterministic fallback
    UUID is returned and counted.
    """
    _STATE["captured_total"] += 1
    fallback_id = f"crash_{uuid.uuid4().hex}"
    provider_event_id: Optional[str] = None

    if _STATE.get("enabled") and _SENTRY_SDK is not None:
        try:
            with _SENTRY_SDK.push_scope() as scope:
                for key, value in (context or {}).items():
                    try:
                        scope.set_tag(str(key), str(value))
                    except Exception:  # noqa: BLE001
                        continue
                provider_event_id = _SENTRY_SDK.capture_exception(exc)
        except Exception as capture_exc:  # noqa: BLE001
            logger.error("Crash reporting provider capture failed", exc_info=capture_exc)

    if provider_event_id:
        return str(provider_event_id)

    _STATE["fallback_total"] += 1
    return fallback_id


def crash_reporting_state() -> Dict[str, Any]:
    """Return a shallow copy of crash reporting status state."""
    return dict(_STATE)


def crash_reporting_prometheus_lines(prefix: str = "datalogicengine") -> list[str]:
    """Render crash reporting health counters for /metrics."""
    state = crash_reporting_state()
    provider_enabled = 1 if state.get("enabled") else 0
    return [
        f"# HELP {prefix}_crash_reporting_enabled Crash reporting provider enabled flag (1=true, 0=false).",
        f"# TYPE {prefix}_crash_reporting_enabled gauge",
        f"{prefix}_crash_reporting_enabled {provider_enabled}",
        f"# HELP {prefix}_crash_events_captured_total Total captured crash events.",
        f"# TYPE {prefix}_crash_events_captured_total counter",
        f"{prefix}_crash_events_captured_total {int(state.get('captured_total', 0))}",
        f"# HELP {prefix}_crash_events_fallback_total Total crashes handled by fallback IDs.",
        f"# TYPE {prefix}_crash_events_fallback_total counter",
        f"{prefix}_crash_events_fallback_total {int(state.get('fallback_total', 0))}",
    ]

