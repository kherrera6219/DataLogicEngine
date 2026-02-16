"""
Shared OAuth token lifecycle helpers for MCP connectors.

Tokens are stored in the `oauth_accounts` table keyed by connector provider
namespace (`connector:<name>`) and user id.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, Mapping, Optional

from extensions import db
from models import OAuthAccount

logger = logging.getLogger(__name__)

CONNECTOR_PROVIDER_PREFIX = "connector:"
DEFAULT_REFRESH_SKEW_SECONDS = 60


class OAuthTokenError(RuntimeError):
    """Raised when connector OAuth token acquisition/refresh fails."""


def connector_provider_key(connector: str) -> str:
    normalized = _normalize_connector(connector)
    return f"{CONNECTOR_PROVIDER_PREFIX}{normalized}"


def get_connector_oauth_token(
    connector: str,
    *,
    execution_context: Optional[Mapping[str, Any]] = None,
    refresh_callback: Optional[Callable[[str, OAuthAccount], Mapping[str, Any]]] = None,
    min_ttl_seconds: int = DEFAULT_REFRESH_SKEW_SECONDS,
) -> Optional[dict[str, Any]]:
    """
    Resolve a usable OAuth token payload for a connector.

    Returns `None` when no connector OAuth account exists for the execution user.
    Raises `OAuthTokenError` when a token exists but is expired/invalid and cannot
    be refreshed.
    """
    user_id = _extract_user_id(execution_context)
    if user_id is None:
        return None

    account = _load_account_for_user(connector, user_id)
    if not account:
        return None

    token_payload = _normalize_token_payload(account.token)
    access_token = _extract_access_token(token_payload)
    refresh_token = _extract_refresh_token(account, token_payload)
    expires_at = _extract_expires_at(token_payload, fallback=account.token_expires_at)

    if access_token and not _is_expired(expires_at, min_ttl_seconds=min_ttl_seconds):
        token_payload["access_token"] = access_token
        if refresh_token and "refresh_token" not in token_payload:
            token_payload["refresh_token"] = refresh_token
        if expires_at:
            token_payload["expires_at"] = expires_at.isoformat()
        return token_payload

    if not refresh_callback:
        raise OAuthTokenError(
            f"Connector OAuth token for '{connector}' is missing/expired and no refresh callback is configured."
        )
    if not refresh_token:
        raise OAuthTokenError(
            f"Connector OAuth token for '{connector}' is missing/expired and no refresh token is available."
        )

    refreshed_payload = dict(refresh_callback(refresh_token, account) or {})
    new_access_token = _extract_access_token(refreshed_payload)
    if not new_access_token:
        raise OAuthTokenError(f"OAuth refresh for connector '{connector}' did not return access_token.")

    merged_payload = {**token_payload, **refreshed_payload}
    merged_payload["access_token"] = new_access_token
    new_refresh_token = str(refreshed_payload.get("refresh_token") or refresh_token).strip() or None
    new_expires_at = _extract_expires_at(merged_payload, fallback=expires_at)

    _persist_account_token(
        account=account,
        token_payload=merged_payload,
        refresh_token=new_refresh_token,
        expires_at=new_expires_at,
    )

    if new_expires_at:
        merged_payload["expires_at"] = new_expires_at.isoformat()
    if new_refresh_token:
        merged_payload["refresh_token"] = new_refresh_token
    return merged_payload


def upsert_connector_oauth_token(
    connector: str,
    *,
    user_id: int,
    access_token: str,
    refresh_token: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    token_payload: Optional[Mapping[str, Any]] = None,
    provider_user_id: Optional[str] = None,
) -> OAuthAccount:
    """Create or update a stored connector OAuth token for a specific user."""
    normalized_connector = _normalize_connector(connector)
    provider_key = connector_provider_key(normalized_connector)
    safe_access_token = str(access_token or "").strip()
    if not safe_access_token:
        raise ValueError("access_token is required")

    account = OAuthAccount.query.filter_by(provider=provider_key, user_id=int(user_id)).first()
    if not account:
        account = OAuthAccount(
            user_id=int(user_id),
            provider=provider_key,
            provider_user_id=provider_user_id or f"{provider_key}:{int(user_id)}",
        )
        db.session.add(account)

    payload = _normalize_token_payload(token_payload)
    payload["access_token"] = safe_access_token
    if refresh_token:
        payload["refresh_token"] = str(refresh_token)

    parsed_expires_at = _coerce_datetime(expires_at) or _extract_expires_at(payload)
    account.token = payload
    account.refresh_token = str(refresh_token).strip() if refresh_token else payload.get("refresh_token")
    account.token_expires_at = parsed_expires_at
    db.session.commit()
    return account


def _load_account_for_user(connector: str, user_id: int) -> Optional[OAuthAccount]:
    provider_key = connector_provider_key(connector)
    try:
        return (
            OAuthAccount.query.filter_by(provider=provider_key, user_id=int(user_id))
            .order_by(OAuthAccount.updated_at.desc())
            .first()
        )
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        logger.warning("Failed loading connector OAuth account for %s user_id=%s: %s", connector, user_id, exc)
        return None


def _persist_account_token(
    *,
    account: OAuthAccount,
    token_payload: Mapping[str, Any],
    refresh_token: Optional[str],
    expires_at: Optional[datetime],
) -> None:
    account.token = dict(token_payload or {})
    account.refresh_token = str(refresh_token).strip() if refresh_token else None
    account.token_expires_at = _coerce_datetime(expires_at)
    account.updated_at = datetime.now(UTC)
    try:
        db.session.commit()
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        raise OAuthTokenError(f"Failed to persist refreshed connector OAuth token: {exc}") from exc


def _extract_user_id(execution_context: Optional[Mapping[str, Any]]) -> Optional[int]:
    if not isinstance(execution_context, Mapping):
        return None
    raw_user_id = execution_context.get("user_id")
    if raw_user_id in (None, ""):
        return None
    try:
        return int(str(raw_user_id).strip())
    except (TypeError, ValueError):
        logger.debug("Connector OAuth context contains non-integer user_id=%r", raw_user_id)
        return None


def _normalize_connector(connector: str) -> str:
    text = str(connector or "").strip().lower()
    if not text:
        raise ValueError("connector is required")
    return text


def _normalize_token_payload(payload: Any) -> dict[str, Any]:
    return dict(payload) if isinstance(payload, Mapping) else {}


def _extract_access_token(payload: Mapping[str, Any]) -> Optional[str]:
    for key in ("access_token", "token"):
        candidate = payload.get(key)
        if candidate:
            value = str(candidate).strip()
            if value:
                return value
    return None


def _extract_refresh_token(account: OAuthAccount, payload: Mapping[str, Any]) -> Optional[str]:
    candidate = account.refresh_token or payload.get("refresh_token")
    if not candidate:
        return None
    value = str(candidate).strip()
    return value or None


def _extract_expires_at(payload: Mapping[str, Any], fallback: Optional[datetime] = None) -> Optional[datetime]:
    expires_at = _coerce_datetime(payload.get("expires_at"))
    if expires_at:
        return expires_at

    expires_at_unix = payload.get("expires_at_unix")
    parsed_unix = _coerce_datetime(expires_at_unix)
    if parsed_unix:
        return parsed_unix

    expires_in = payload.get("expires_in")
    try:
        if expires_in is not None:
            seconds = int(float(expires_in))
            if seconds > 0:
                return datetime.now(UTC) + timedelta(seconds=seconds)
    except (TypeError, ValueError):
        pass

    return _coerce_datetime(fallback)


def _coerce_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    return None


def _is_expired(expires_at: Optional[datetime], *, min_ttl_seconds: int) -> bool:
    if expires_at is None:
        return False
    skew = timedelta(seconds=max(0, int(min_ttl_seconds)))
    return expires_at <= (datetime.now(UTC) + skew)

