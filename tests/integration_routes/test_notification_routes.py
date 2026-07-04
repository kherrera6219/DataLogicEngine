"""
Integration tests for notification preference routes.

Covers:
- Unauthenticated requests are rejected as JSON 401s.
- GET creates a default row on first access and returns all expected keys.
- POST persists boolean and digest_frequency changes; re-GET reflects them.
- POST rejects invalid digest_frequency values (400).
- POST rejects non-boolean values for boolean fields (400).
- Only known keys are accepted; unknown keys are silently ignored.
"""

import os

os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SESSION_SECRET", "test-secret")
os.environ.setdefault("SECRET_KEY", "test-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt")
os.environ.setdefault("OPENAI_API_KEY", "mock-key")
os.environ.setdefault("USE_REDIS", "False")
os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")

from tests.conftest import seed_login_session

_ENDPOINT = "/api/v1/user/notifications"

_EXPECTED_KEYS = {
    "email_on_run_complete",
    "email_on_run_failed",
    "email_on_simulation_complete",
    "inapp_run_complete",
    "inapp_run_failed",
    "inapp_simulation_complete",
    "inapp_system_alerts",
    "digest_frequency",
}


def _assert_json_unauthorized(resp):
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["success"] is False
    assert body["code"] == "UNAUTHORIZED"


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

class TestNotificationAuthGuard:
    def test_get_requires_auth(self, client):
        resp = client.get(_ENDPOINT)
        _assert_json_unauthorized(resp)

    def test_post_requires_auth(self, client):
        resp = client.post(_ENDPOINT, json={})
        _assert_json_unauthorized(resp)


# ---------------------------------------------------------------------------
# Default row creation
# ---------------------------------------------------------------------------

class TestNotificationDefaults:
    def test_get_returns_all_keys_with_defaults(self, app, client):
        seed_login_session(client, app, username="notif_default", email="notif_default@test.com")
        resp = client.get(_ENDPOINT)

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        prefs = body["preferences"]
        assert _EXPECTED_KEYS == set(prefs.keys()), f"Unexpected keys: {set(prefs.keys()) ^ _EXPECTED_KEYS}"

        # Validate default values match the model defaults.
        assert prefs["email_on_run_complete"] is True
        assert prefs["email_on_run_failed"] is True
        assert prefs["email_on_simulation_complete"] is False
        assert prefs["inapp_run_complete"] is True
        assert prefs["inapp_run_failed"] is True
        assert prefs["inapp_simulation_complete"] is True
        assert prefs["inapp_system_alerts"] is True
        assert prefs["digest_frequency"] == "none"

    def test_get_twice_does_not_duplicate_row(self, app, client):
        """Calling GET twice must not raise a uniqueness error."""
        seed_login_session(client, app, username="notif_dedup", email="notif_dedup@test.com")
        r1 = client.get(_ENDPOINT)
        r2 = client.get(_ENDPOINT)
        assert r1.status_code == 200
        assert r2.status_code == 200


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

class TestNotificationPersistence:
    def test_post_persists_boolean_changes(self, app, client):
        seed_login_session(client, app, username="notif_bool", email="notif_bool@test.com")

        # Flip two defaults.
        resp = client.post(_ENDPOINT, json={
            "email_on_run_complete": False,
            "inapp_system_alerts": False,
        })
        assert resp.status_code == 200
        saved = resp.get_json()["preferences"]
        assert saved["email_on_run_complete"] is False
        assert saved["inapp_system_alerts"] is False
        # Untouched key keeps its default.
        assert saved["email_on_run_failed"] is True

        # Re-GET confirms the change is durable.
        resp2 = client.get(_ENDPOINT)
        assert resp2.status_code == 200
        loaded = resp2.get_json()["preferences"]
        assert loaded["email_on_run_complete"] is False
        assert loaded["inapp_system_alerts"] is False

    def test_post_persists_digest_frequency(self, app, client):
        seed_login_session(client, app, username="notif_digest", email="notif_digest@test.com")

        resp = client.post(_ENDPOINT, json={"digest_frequency": "weekly"})
        assert resp.status_code == 200
        assert resp.get_json()["preferences"]["digest_frequency"] == "weekly"

        resp2 = client.get(_ENDPOINT)
        assert resp2.get_json()["preferences"]["digest_frequency"] == "weekly"

    def test_post_partial_update_does_not_reset_other_fields(self, app, client):
        seed_login_session(client, app, username="notif_partial", email="notif_partial@test.com")

        # First call: turn off email.
        client.post(_ENDPOINT, json={"email_on_run_complete": False})
        # Second call: change only digest_frequency.
        client.post(_ENDPOINT, json={"digest_frequency": "daily"})

        # Both changes should survive.
        final = client.get(_ENDPOINT).get_json()["preferences"]
        assert final["email_on_run_complete"] is False
        assert final["digest_frequency"] == "daily"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestNotificationValidation:
    def test_invalid_digest_frequency_returns_400(self, app, client):
        seed_login_session(client, app, username="notif_invalid", email="notif_invalid@test.com")
        resp = client.post(_ENDPOINT, json={"digest_frequency": "hourly"})
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["success"] is False
        assert "digest_frequency" in body["error"]

    def test_non_boolean_value_returns_400(self, app, client):
        seed_login_session(client, app, username="notif_nonbool", email="notif_nonbool@test.com")
        resp = client.post(_ENDPOINT, json={"email_on_run_complete": "yes"})
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["success"] is False

    def test_unknown_keys_are_ignored(self, app, client):
        seed_login_session(client, app, username="notif_unknown", email="notif_unknown@test.com")
        resp = client.post(_ENDPOINT, json={"unknown_key": True, "email_on_run_failed": False})
        assert resp.status_code == 200
        prefs = resp.get_json()["preferences"]
        # The known key was applied.
        assert prefs["email_on_run_failed"] is False
        # The unknown key did not sneak into the response.
        assert "unknown_key" not in prefs

    def test_empty_post_is_a_noop(self, app, client):
        """Sending an empty body must return 200 with current (default) prefs."""
        seed_login_session(client, app, username="notif_noop", email="notif_noop@test.com")
        resp = client.post(_ENDPOINT, json={})
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True
