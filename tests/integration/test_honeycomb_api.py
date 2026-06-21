"""Honeycomb API endpoint tests.

Regression coverage for audit item N4 (2026-06-10): honeycomb_api looked up
the Honeycomb manager at legacy Axis 5 while AxisSystem registers it at
canonical Axis 3, so every endpoint returned 500 "Honeycomb system not
initialized". Also covers the auth decorators added in the same fix.
"""

import pytest
from unittest.mock import MagicMock, patch
from flask import Flask

from backend.honeycomb_api import honeycomb_api


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['AXIS_SYSTEM'] = MagicMock()
    app.register_blueprint(honeycomb_api)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_user():
    with patch("backend.auth.api_decorators.current_user") as mock_user:
        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_user.is_admin = True
        mock_user.role = "admin"
        with patch(
            "backend.auth.api_decorators.check_api_auth",
            return_value=(True, mock_user),
        ):
            yield mock_user


def test_generate_resolves_honeycomb_at_canonical_axis_3(client, app, auth_user):
    """The manager registered at Axis 3 (as AxisSystem does) must be found."""
    honeycomb = MagicMock()
    honeycomb.generate_multi_axis_honeycomb.return_value = {"status": "success"}
    app.config['AXIS_SYSTEM'].axis_managers = {3: honeycomb}

    response = client.post('/api/honeycomb/generate', json={"node_uid": "n1"})

    assert response.status_code == 200
    assert response.get_json()["status"] == "success"
    honeycomb.generate_multi_axis_honeycomb.assert_called_once_with("n1", 50)


def test_sector_crosswalk_resolves_honeycomb_at_canonical_axis_3(client, app, auth_user):
    honeycomb = MagicMock()
    honeycomb.generate_sector_pillar_crosswalk.return_value = {"status": "success"}
    app.config['AXIS_SYSTEM'].axis_managers = {3: honeycomb}

    response = client.post('/api/honeycomb/sector-crosswalk', json={"sector_id": "s1"})

    assert response.status_code == 200
    honeycomb.generate_sector_pillar_crosswalk.assert_called_once_with("s1")


def test_find_paths_resolves_honeycomb_at_canonical_axis_3(client, app, auth_user):
    honeycomb = MagicMock()
    honeycomb.find_crosswalk_paths.return_value = {"status": "success"}
    app.config['AXIS_SYSTEM'].axis_managers = {3: honeycomb}

    response = client.post(
        '/api/honeycomb/find-paths',
        json={"source_uid": "a", "target_uid": "b"},
    )

    assert response.status_code == 200
    honeycomb.find_crosswalk_paths.assert_called_once_with("a", "b", 3)


def test_connect_resolves_honeycomb_at_canonical_axis_3(client, app, auth_user):
    honeycomb = MagicMock()
    honeycomb.create_honeycomb_connection.return_value = {"status": "success"}
    app.config['AXIS_SYSTEM'].axis_managers = {3: honeycomb}

    response = client.post(
        '/api/honeycomb/connect',
        json={"source_uid": "a", "target_uid": "b", "connection_type": "related"},
    )

    assert response.status_code == 200
    honeycomb.create_honeycomb_connection.assert_called_once_with(
        "a", "b", "related", 1.0, None
    )


def test_generate_reports_uninitialized_without_axis_system(client, app, auth_user):
    app.config['AXIS_SYSTEM'] = None

    response = client.post('/api/honeycomb/generate', json={"node_uid": "n1"})

    assert response.status_code == 500
    assert "not initialized" in response.get_json()["message"]


def test_generate_requires_authentication(client, app):
    honeycomb = MagicMock()
    app.config['AXIS_SYSTEM'].axis_managers = {3: honeycomb}

    with patch(
        "backend.auth.api_decorators.check_api_auth",
        return_value=(False, None),
    ):
        response = client.post('/api/honeycomb/generate', json={"node_uid": "n1"})

    assert response.status_code == 401
    honeycomb.generate_multi_axis_honeycomb.assert_not_called()


def test_connect_requires_auth(client, app):
    # Single-mode / OS-level auth: there is no admin vs non-admin distinction
    # (roles were removed in the auth deprecation). The real security boundary is
    # that the endpoint requires authentication — an unauthenticated request is
    # rejected and never reaches the handler.
    honeycomb = MagicMock()
    app.config['AXIS_SYSTEM'].axis_managers = {3: honeycomb}

    with patch(
        "backend.auth.api_decorators.check_api_auth",
        return_value=(False, None),
    ):
        response = client.post(
            '/api/honeycomb/connect',
            json={"source_uid": "a", "target_uid": "b", "connection_type": "related"},
        )

    assert response.status_code in (401, 403)
    honeycomb.create_honeycomb_connection.assert_not_called()
