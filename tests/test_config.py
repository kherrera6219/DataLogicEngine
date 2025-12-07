import importlib
import os

import pytest


def reload_config(monkeypatch, env_value=None, env_overrides=None):
    """Reload the config module with controlled environment settings."""
    if env_value is None:
        monkeypatch.delenv("FLASK_ENV", raising=False)
    else:
        monkeypatch.setenv("FLASK_ENV", env_value)

    env_overrides = env_overrides or {}
    for key, value in env_overrides.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)

    import config

    return importlib.reload(config)


def test_development_config_defaults(monkeypatch):
    config_module = reload_config(
        monkeypatch,
        env_value=None,
        env_overrides={"SECRET_KEY": None, "JWT_SECRET_KEY": None},
    )

    config = config_module.get_config()

    assert config.__class__.__name__ == "DevelopmentConfig"
    assert config.DEBUG is True
    assert isinstance(config.SECRET_KEY, str)
    assert isinstance(config.JWT_SECRET_KEY, str)
    assert config.SESSION_COOKIE_SECURE is False
    assert config.REMEMBER_COOKIE_SECURE is False
    assert config.MAX_SIMULATION_LAYERS == 5
    assert config.CORS_ORIGINS == ["http://localhost:3000", "http://localhost:8080"]


def test_testing_config_isolated_database(monkeypatch):
    config_module = reload_config(monkeypatch, env_value="testing")

    config = config_module.get_config()

    assert config.__class__.__name__ == "TestingConfig"
    assert config.TESTING is True
    assert config.DEBUG is False
    assert config.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"
    assert config.MAX_SIMULATION_LAYERS == 3
    assert config.DEFAULT_REFINEMENT_STEPS == 3
    assert config.JWT_ACCESS_TOKEN_EXPIRES == 300


def test_production_config_security_overrides(monkeypatch):
    config_module = reload_config(
        monkeypatch,
        env_value="production",
        env_overrides={
            "SECRET_KEY": "super-secret",
            "JWT_SECRET_KEY": "jwt-secret",
            "CORS_ORIGINS": "https://app.example.com,https://admin.example.com",
        },
    )

    config = config_module.get_config()

    assert config.__class__.__name__ == "ProductionConfig"
    assert config.DEBUG is False
    assert config.SESSION_COOKIE_SECURE is True
    assert config.REMEMBER_COOKIE_SECURE is True
    assert config.JWT_ACCESS_TOKEN_EXPIRES == 30 * 60
    assert config.QUANTUM_SIMULATION_ENABLED is True
    assert config.RECURSIVE_PROCESSING_ENABLED is True
    assert config.CORS_ORIGINS == [
        "https://app.example.com",
        "https://admin.example.com",
    ]
    assert os.environ["SECRET_KEY"] == "super-secret"
    assert os.environ["JWT_SECRET_KEY"] == "jwt-secret"


@pytest.mark.parametrize(
    "env,expected_class",
    [("production", "ProductionConfig"), ("testing", "TestingConfig"), ("development", "DevelopmentConfig")],
)
def test_get_config_environment_switching(monkeypatch, env, expected_class):
    config_module = reload_config(monkeypatch, env_value=env)

    config = config_module.get_config()

    assert config.__class__.__name__ == expected_class
