import importlib


def test_auto_create_schema_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AUTO_CREATE_SCHEMA", raising=False)
    app_module = importlib.import_module("app")
    importlib.reload(app_module)

    assert app_module._should_auto_create_schema() is False


def test_auto_create_schema_enabled_when_opted_in(monkeypatch):
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "true")
    app_module = importlib.import_module("app")
    importlib.reload(app_module)

    assert app_module._should_auto_create_schema() is True
