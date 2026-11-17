"""Legacy breach lookups fail before any external request is made."""

import pytest
import requests

from backend.security.password_security import PasswordSecurity
from core.security.egress_guard import EgressDenied


def test_breach_lookup_raises_typed_denial_without_network(monkeypatch):
    def fail_if_called(*_args, **_kwargs):
        pytest.fail("breach lookup reached requests networking")

    monkeypatch.setattr(requests.sessions.Session, "request", fail_if_called)
    with pytest.raises(EgressDenied, match="password-breach lookup is disabled"):
        PasswordSecurity.check_password_breach("temporary-test-password")
