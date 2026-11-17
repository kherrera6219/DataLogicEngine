"""Unapproved OIDC networking must not be initialized."""

import pytest
from flask import Flask

from backend.auth.sso import configure_sso, oauth
from core.security.egress_guard import EgressDenied


def test_unconfigured_sso_remains_disabled(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(oauth, "init_app", lambda *_: pytest.fail("SSO initialized"))
    assert configure_sso(app) is None


def test_configured_sso_is_rejected_before_initialization(monkeypatch):
    app = Flask(__name__)
    app.config.update(
        OIDC_CLIENT_ID="configured-client",
        OIDC_DISCOVERY_URL="https://identity.example/.well-known/openid-configuration",
    )
    monkeypatch.setattr(oauth, "init_app", lambda *_: pytest.fail("SSO initialized"))
    with pytest.raises(EgressDenied, match="Remove OIDC_CLIENT_ID"):
        configure_sso(app)
