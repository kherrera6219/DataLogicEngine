import logging
import os

try:
    import win32api
    import win32security
except ImportError:
    win32api = None
    win32security = None

logger = logging.getLogger(__name__)


def _fallback_identity():
    return {
        "username": os.environ.get('USERNAME', 'local_user'),
        "sid": "S-1-5-local-fallback",
        "domain": os.environ.get('USERDOMAIN', 'LOCAL'),
        "is_fallback": True
    }


def _allow_fallback_identity() -> bool:
    """
    Fallback identity is intentionally disabled for desktop production mode.
    It is only allowed for explicit dev/testing scenarios.
    """
    explicit = os.environ.get("ALLOW_WINDOWS_IDENTITY_FALLBACK")
    if explicit is not None:
        return explicit.lower() == "true"

    flask_env = os.environ.get("FLASK_ENV", "development").lower()
    is_desktop_mode = os.environ.get("IS_DESKTOP_APP", "false").lower() == "true"
    return flask_env in {"development", "testing"} and not is_desktop_mode


def _fallback_or_raise(reason: str):
    if _allow_fallback_identity():
        return _fallback_identity()
    raise RuntimeError(reason)


def get_windows_user_identity():
    """
    Retrieves the current Windows user's name and SID (Security Identifier).
    Returns a dictionary with 'username', 'sid', 'domain', and 'is_fallback'.
    """
    if win32api is None or win32security is None:
        return _fallback_or_raise("Windows identity APIs unavailable and fallback is disabled")

    try:
        username = win32api.GetUserName()
        # account_type is the SID_NAME_USE enum value; renamed from `type` to avoid
        # shadowing the Python builtin.
        sid, domain, account_type = win32security.LookupAccountName(None, username)
        sid_string = win32security.ConvertSidToStringSid(sid)

        # Validation: Ensure SID is a non-empty string starting with 'S-'
        if not sid_string or not sid_string.startswith("S-") or len(sid_string) < 12:
            raise ValueError(f"Invalid SID format retrieved: {sid_string}")

        return {
            "username": username,
            "sid": sid_string,
            "domain": domain,
            "is_fallback": False
        }
    except Exception as exc:
        logger.error("Windows identity retrieval failed: %s: %s", type(exc).__name__, exc)
        return _fallback_or_raise("Windows identity lookup failed and fallback is disabled")


if __name__ == "__main__":
    identity = get_windows_user_identity()
    print(f"Windows Identity: {identity}")
