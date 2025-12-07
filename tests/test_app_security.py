import importlib

import pytest


def test_password_policy_accepts_strong_password(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    app_module = importlib.import_module("app")
    importlib.reload(app_module)

    assert app_module.password_meets_policy("ValidPassw0rd!!") is True


def test_password_policy_rejects_weak_inputs(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    app_module = importlib.import_module("app")
    importlib.reload(app_module)

    weak_passwords = [
        "short",
        "nouppercase123!",
        "NOLOWERCASE123!",
        "NoNumber!!!",
        "NoSymbol1234",
    ]

    for candidate in weak_passwords:
        assert app_module.password_meets_policy(candidate) is False
