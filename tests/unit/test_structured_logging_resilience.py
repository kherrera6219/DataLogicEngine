import importlib
import json
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
    payload = json.loads(rendered)

    assert payload["schema_version"] == "dle.log.v1"
    assert payload["component"] == "test"
    assert payload["event"] == "log"
    assert payload["correlation_id"] == "startup"
    assert "REDACTED" in payload["message"]

    if original_module is not None:
        sys.modules["backend.logging_config"] = original_module
    else:
        sys.modules.pop("backend.logging_config", None)


def test_custom_json_formatter_redacts_structured_extras():
    from backend.logging_config import CustomJsonFormatter

    formatter = CustomJsonFormatter("%(message)s")
    record = logging.LogRecord(
        name="provider.gateway",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="provider request failed token=raw-secret-value",
        args=(),
        exc_info=None,
    )
    record.event = "provider.failure"
    record.error_code = "PROVIDER_TIMEOUT"
    record.private_key = "not-for-logs"

    payload = json.loads(formatter.format(record))

    assert payload["severity"] == "ERROR"
    assert payload["event"] == "provider.failure"
    assert payload["error_code"] == "PROVIDER_TIMEOUT"
    assert payload["private_key"] == "[REDACTED_SECRET]"
    assert "raw-secret-value" not in payload["message"]
