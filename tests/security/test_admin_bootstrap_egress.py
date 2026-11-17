"""Interactive bootstrap does not perform an external password lookup."""

from contextlib import nullcontext
from types import SimpleNamespace

import pytest


def test_manual_password_warns_without_external_breach_lookup(monkeypatch, capsys):
    from scripts import create_admin_user as bootstrap

    class Query:
        def first(self):
            return None

        def filter_by(self, **_kwargs):
            return self

    class User:
        query = Query()

        def set_password(self, password):
            self.password = password

    saved = []
    session = SimpleNamespace(add=saved.append, commit=lambda: None)
    monkeypatch.setattr(bootstrap, "app", SimpleNamespace(app_context=nullcontext))
    monkeypatch.setattr(bootstrap, "db", SimpleNamespace(session=session))
    monkeypatch.setattr(bootstrap, "User", User)
    answers = iter(["localowner", "owner@example.test", "no"])
    monkeypatch.setattr("builtins.input", lambda *_args: next(answers))
    monkeypatch.setattr(
        bootstrap.getpass, "getpass", lambda *_args: "Uniqu3!SecurePhrase"
    )

    def forbidden_lookup(*_args, **_kwargs):
        pytest.fail("admin bootstrap attempted external password lookup")

    monkeypatch.setattr(
        bootstrap.PasswordSecurity, "check_password_breach", forbidden_lookup
    )
    bootstrap.create_admin_user()

    assert len(saved) == 1
    assert "not checked against a breach database" in capsys.readouterr().out
