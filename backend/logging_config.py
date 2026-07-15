# ruff: noqa: E402
"""
Structured Logging Configuration for DataLogicEngine

Provides centralized logging with JSON format for log aggregation.
"""

import importlib
import importlib.util
import os
import sys
import logging
import socket
import json
from datetime import datetime, UTC
from flask import Flask


from backend.observability.redaction import is_sensitive_key, redact_text, redact_value


_PYTHON_JSON_LOGGER_SPEC = importlib.util.find_spec("pythonjsonlogger")
_HAS_PYTHON_JSON_LOGGER = _PYTHON_JSON_LOGGER_SPEC is not None
JsonFormatter = None
if _HAS_PYTHON_JSON_LOGGER:
    JsonFormatter = importlib.import_module("pythonjsonlogger.json").JsonFormatter


def _redact_text_for_logging(text: str) -> str:
    """
    Redact PII without emitting additional logs.

    This avoids formatter recursion where redaction logs would re-enter logging.
    """
    return redact_text(text)


def _redact_value_for_logging(value):
    return redact_value(value)


class CustomJsonFormatter(logging.Formatter):
    """Custom JSON formatter with additional fields and PII redaction."""

    def __init__(self, fmt: str | None = None):
        super().__init__(fmt)
        self._json_formatter = None
        if JsonFormatter is not None:
            self._json_formatter = JsonFormatter(fmt)

    def _build_log_record(self, record: logging.LogRecord, message_dict: dict | None = None) -> dict:
        try:
            rendered_message = record.getMessage()
        except Exception:
            rendered_message = str(getattr(record, "msg", "log-message-unavailable"))

        log_record = {
            "schema_version": "dle.log.v1",
            "timestamp": datetime.now(UTC).isoformat(),
            "severity": getattr(record, "levelname", "INFO"),
            "level": getattr(record, "levelname", "INFO"),
            "service": "datalogicengine",
            "component": getattr(record, "name", "unknown"),
            "event": getattr(record, "event", "log"),
            "message": rendered_message,
            "environment": os.environ.get("FLASK_ENV", "production"),
            "redaction_classification": getattr(
                record,
                "redaction_classification",
                "best_effort_redacted",
            ),
            "error_code": getattr(record, "error_code", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "state_transition": getattr(record, "state_transition", None),
        }
        if message_dict:
            log_record.update(message_dict)

        standard_fields = set(logging.makeLogRecord({}).__dict__)
        standard_fields.update({"message", "asctime"})
        for key, value in record.__dict__.items():
            if key not in standard_fields and not key.startswith("_"):
                log_record[key] = value

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Add request context if available (ultra-defensive)
        try:
            from flask import has_request_context
            if has_request_context():
                from flask import request, g
                correlation_id = getattr(g, 'correlation_id', '')
                log_record['correlation_id'] = correlation_id
                log_record['request_id'] = correlation_id
                log_record['path'] = getattr(request, 'path', '')
                log_record['method'] = getattr(request, 'method', '')

                # Safe header access
                headers = getattr(request, 'headers', {})
                log_record['user_agent'] = str(headers.get('User-Agent', ''))[:100]
                log_record['ip'] = getattr(request, 'remote_addr', '')

                # Redact PII from request path if present
                if log_record.get('path'):
                    log_record['path'] = _redact_text_for_logging(log_record['path'])
        except Exception:
            # Formatter errors should never break request handling, but capture
            # a minimal signal for operator visibility.
            log_record.setdefault('logging_context_error', 'request-context-enrichment-failed')

        # Deep redaction for all fields (excluding structural ones)
        log_record.setdefault("correlation_id", "startup")
        log_record.setdefault("request_id", log_record["correlation_id"])
        for key in list(log_record.keys()):
            value = log_record[key]
            if key in (
                'schema_version', 'timestamp', 'severity', 'level', 'environment',
                'service', 'component', 'event', 'correlation_id', 'request_id',
                'redaction_classification', 'error_code', 'duration_ms',
                'state_transition',
            ):
                continue
            if is_sensitive_key(key):
                log_record[key] = "[REDACTED_SECRET]"
            else:
                log_record[key] = _redact_value_for_logging(value)
        return log_record

    def add_fields(self, log_record, record, message_dict):
        built_record = self._build_log_record(record, message_dict)
        log_record.update(built_record)

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(self._build_log_record(record), default=str, ensure_ascii=True)


def _resolve_log_level() -> int:
    return logging.DEBUG if os.environ.get("FLASK_ENV") == "development" else logging.INFO


def _build_formatter(log_format: str):
    if str(log_format).lower() == "json":
        return CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
    return logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def _configure_root_handlers(*, log_level: int, log_format: str, log_file: str) -> None:
    log_parent = os.path.dirname(os.path.abspath(log_file))
    os.makedirs(log_parent, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = []

    formatter = _build_formatter(log_format)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if os.environ.get("FLASK_ENV") != "development":
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    log_aggregation_host = os.environ.get("LOG_AGGREGATION_HOST")
    if log_aggregation_host:
        log_aggregation_port = int(os.environ.get("LOG_AGGREGATION_PORT", 514))
        log_aggregation_protocol = os.environ.get("LOG_AGGREGATION_PROTOCOL", "udp").lower()
        sock_type = socket.SOCK_DGRAM if log_aggregation_protocol == "udp" else socket.SOCK_STREAM

        syslog_handler = logging.handlers.SysLogHandler(
            address=(log_aggregation_host, log_aggregation_port),
            socktype=sock_type,
        )
        syslog_handler.setLevel(log_level)
        syslog_handler.setFormatter(formatter)
        root_logger.addHandler(syslog_handler)


def configure_structured_logging(app: Flask) -> None:
    """
    Configure structured JSON logging for the application.
    
    Supports:
    - Console output (development)
    - File output (production)
    - JSON format for log aggregation
    """
    log_level = _resolve_log_level()
    log_format = app.config.get("LOG_FORMAT") or os.environ.get("LOG_FORMAT", "json")
    log_file = app.config.get("LOG_FILE") or os.environ.get("LOG_FILE", "logs/app.log")
    _configure_root_handlers(log_level=log_level, log_format=log_format, log_file=log_file)
    formatter = _build_formatter(log_format)
    security_log_file = app.config.get("SECURITY_LOG_FILE", "logs/security.log")
    audit_log_file = app.config.get("AUDIT_LOG_FILE", "logs/audit.log")
    os.makedirs(os.path.dirname(os.path.abspath(security_log_file)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(audit_log_file)), exist_ok=True)
    
    # Security log (separate file)
    security_logger = logging.getLogger('security')
    for existing_handler in list(security_logger.handlers):
        if getattr(existing_handler, "_dle_managed_handler", False):
            security_logger.removeHandler(existing_handler)
            existing_handler.close()
    security_handler = logging.handlers.RotatingFileHandler(
        security_log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    security_handler._dle_managed_handler = True
    security_handler.setFormatter(formatter)
    security_logger.addHandler(security_handler)
    
    # Audit log (separate file)
    audit_logger = logging.getLogger('audit')
    for existing_handler in list(audit_logger.handlers):
        if getattr(existing_handler, "_dle_managed_handler", False):
            audit_logger.removeHandler(existing_handler)
            existing_handler.close()
    audit_handler = logging.handlers.RotatingFileHandler(
        audit_log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=30  # Keep more audit logs
    )
    audit_handler._dle_managed_handler = True
    audit_handler.setFormatter(formatter)
    audit_logger.addHandler(audit_handler)
    
    app.logger.info("Structured logging configured", extra={
        'log_level': logging.getLevelName(log_level),
        'log_format': log_format
    })


def configure_service_logging(service_name: str) -> logging.Logger:
    """
    Configure structured logging for non-Flask service entrypoints.
    """
    log_level = _resolve_log_level()
    log_format = os.environ.get("LOG_FORMAT", "json")
    log_file = os.environ.get("LOG_FILE", f"logs/{service_name}.log")
    _configure_root_handlers(log_level=log_level, log_format=log_format, log_file=log_file)

    logger = logging.getLogger(service_name)
    logger.info(
        "Structured service logging configured",
        extra={
            "service_name": service_name,
            "log_level": logging.getLevelName(log_level),
            "log_format": log_format,
        },
    )
    return logger


# Import for rotating file handler
import logging.handlers
