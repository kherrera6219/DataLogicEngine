"""
Structured Logging Configuration for DataLogicEngine

Provides centralized logging with JSON format for log aggregation.
"""

import os
import sys
import logging
import socket
import re
from datetime import datetime, UTC
from typing import Optional
from flask import Flask
from pythonjsonlogger.json import JsonFormatter


from backend.security.pii_redaction import pii_redactor


def _redact_text_for_logging(text: str) -> str:
    """
    Redact PII without emitting additional logs.

    This avoids formatter recursion where redaction logs would re-enter logging.
    """
    if not isinstance(text, str):
        return text

    redacted = text
    patterns = getattr(pii_redactor, "patterns", {})
    for pii_type, pattern in patterns.items():
        replacement = f"[REDACTED_{str(pii_type).upper()}]"
        try:
            redacted = re.sub(pattern, replacement, redacted)
        except re.error:
            # Ignore malformed patterns in logging path; preserve availability.
            continue
    return redacted


def _redact_value_for_logging(value):
    if isinstance(value, str):
        return _redact_text_for_logging(value)
    if isinstance(value, dict):
        return {key: _redact_value_for_logging(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_value_for_logging(item) for item in value]
    return value


class CustomJsonFormatter(JsonFormatter):
    """Custom JSON formatter with additional fields and PII redaction."""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Redact message if it's a string
        message = log_record.get('message')
        if not isinstance(message, str):
            # Some call sites pass a pre-built dict or raw LogRecord message.
            fallback_msg = getattr(record, 'msg', None)
            if isinstance(fallback_msg, str):
                message = fallback_msg
                log_record['message'] = fallback_msg
        if isinstance(message, str):
            log_record['message'] = _redact_text_for_logging(message)
        
        # Add timestamp
        log_record['timestamp'] = datetime.now(UTC).isoformat()
        
        # Add level
        log_record['level'] = getattr(record, 'levelname', 'INFO')
        
        # Add service name
        log_record['service'] = 'datalogicengine'
        
        # Add environment
        log_record['environment'] = os.environ.get('FLASK_ENV', 'production')
        
        # Add request context if available (ultra-defensive)
        try:
            from flask import has_request_context
            if has_request_context():
                from flask import request, g
                log_record['request_id'] = getattr(g, 'correlation_id', '')
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
            pass
        
        # Deep redaction for all fields (excluding structural ones)
        for key in list(log_record.keys()):
            value = log_record[key]
            if key in ('timestamp', 'level', 'environment', 'service', 'request_id'):
                continue
                
            log_record[key] = _redact_value_for_logging(value)


def _resolve_log_level() -> int:
    return logging.DEBUG if os.environ.get("FLASK_ENV") == "development" else logging.INFO


def _build_formatter(log_format: str):
    if str(log_format).lower() == "json":
        return CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
    return logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def _configure_root_handlers(*, log_level: int, log_format: str, log_file: str) -> None:
    # Create logs directory
    os.makedirs("logs", exist_ok=True)

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
    log_format = os.environ.get("LOG_FORMAT", "json")
    log_file = os.environ.get("LOG_FILE", "logs/app.log")
    _configure_root_handlers(log_level=log_level, log_format=log_format, log_file=log_file)
    formatter = _build_formatter(log_format)
    
    # Security log (separate file)
    security_logger = logging.getLogger('security')
    security_handler = logging.handlers.RotatingFileHandler(
        'logs/security.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    security_handler.setFormatter(formatter)
    security_logger.addHandler(security_handler)
    
    # Audit log (separate file)
    audit_logger = logging.getLogger('audit')
    audit_handler = logging.handlers.RotatingFileHandler(
        'logs/audit.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=30  # Keep more audit logs
    )
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
