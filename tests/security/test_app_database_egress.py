"""Application database configuration cannot select a remote destination."""

import pytest
from sqlalchemy.engine import make_url

from core.security.egress_guard import EgressDenied, local_database_url


@pytest.mark.parametrize(
    "target",
    [
        "postgresql://user:password@outside.example:5432/app",
        "postgresql://user:password@192.0.2.1:5432/app",
        "postgresql://user:password@127.0.0.1:5432/app?host=outside.example",
        "postgresql://user:password@127.0.0.1:5432/app?hostaddr=192.0.2.1",
        "postgresql://user:password@127.0.0.1:5432/app?service=remote",
        "sqlite://///outside.example/share/app.db",
        "sqlite:///file://outside.example/share/app.db?uri=true",
    ],
)
def test_database_configuration_rejects_remote_or_ambiguous_destinations(target):
    with pytest.raises(EgressDenied):
        local_database_url(target)


def test_local_database_configuration_pins_loopback_and_keeps_credentials():
    url = make_url(local_database_url("postgresql://user:secret@localhost:5432/app"))
    assert url.host == "127.0.0.1"
    assert url.query["hostaddr"] == "127.0.0.1"
    assert url.password == "secret"
    assert local_database_url("sqlite:///:memory:") == "sqlite:///:memory:"


def test_legacy_app_rejects_remote_database_before_startup(monkeypatch, tmp_path):
    from app import create_app

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    with pytest.raises(EgressDenied):
        create_app(
            "testing",
            {
                "DLE_RUNTIME_ROOT": str(tmp_path),
                "DLE_DATA_PLANE_DRIVER": "legacy",
                "SQLALCHEMY_DATABASE_URI": "postgresql://user:password@outside.example/app",
            },
            start_runtime=False,
        )
