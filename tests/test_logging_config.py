import importlib


def test_logging_config_respects_environment(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    import utils.logging_config as logging_config

    reloaded = importlib.reload(logging_config)
    config = reloaded.get_logging_config()

    assert config["version"] == 1
    assert config["handlers"]["console"]["level"] == "DEBUG"
    assert config["handlers"]["file"]["level"] == "DEBUG"
    assert config["handlers"]["file"]["filename"].endswith("logs/ukg_system.log")
    assert "standard" in config["formatters"]
    assert config["loggers"][""]["handlers"] == ["console", "file"]
