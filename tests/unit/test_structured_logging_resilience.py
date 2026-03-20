import importlib
import logging
import sys


def test_custom_json_formatter_falls_back_without_python_json_logger(monkeypatch):
    original_module = sys.modules.pop("backend.logging_config", None)
    original_find_spec = importlib.util.find_spec

    def fake_find_spec(name):
        if name == "pythonjsonlogger":
            return None
        return original_find_spec(name)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)

    logging_config = importlib.import_module("backend.logging_config")
    logging_config = importlib.reload(logging_config)

    formatter = logging_config.CustomJsonFormatter("%(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="user email foo@example.com",
        args=(),
        exc_info=None,
    )

    rendered = formatter.format(record)

    assert "datalogicengine" in rendered
    assert "REDACTED" in rendered

    if original_module is not None:
        sys.modules["backend.logging_config"] = original_module
    else:
        sys.modules.pop("backend.logging_config", None)
