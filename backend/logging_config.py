"""
Structured Logging Configuration for DataLogicEngine

Provides centralized logging with JSON format for log aggregation.
"""

import os
import sys
import logging
import json
from datetime import datetime, UTC
from typing import Optional
from flask import Flask, request, g
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.now(UTC).isoformat()
        
        # Add level
        log_record['level'] = record.levelname
        
        # Add service name
        log_record['service'] = 'datalogicengine'
        
        # Add environment
        log_record['environment'] = os.environ.get('FLASK_ENV', 'production')
        
        # Add request context if available
        try:
            if request:
                log_record['request_id'] = g.get('correlation_id', '')
                log_record['path'] = request.path
                log_record['method'] = request.method
                log_record['user_agent'] = request.headers.get('User-Agent', '')[:100]
                log_record['ip'] = request.remote_addr
        except RuntimeError:
            pass  # Outside request context


def configure_structured_logging(app: Flask) -> None:
    """
    Configure structured JSON logging for the application.
    
    Supports:
    - Console output (development)
    - File output (production)
    - JSON format for log aggregation
    """
    log_level = logging.DEBUG if os.environ.get('FLASK_ENV') == 'development' else logging.INFO
    log_format = os.environ.get('LOG_FORMAT', 'json')
    log_file = os.environ.get('LOG_FILE', 'logs/app.log')
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    if log_format == 'json':
        # JSON formatter for log aggregation
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Standard formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (production)
    if os.environ.get('FLASK_ENV') != 'development':
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
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


# Import for rotating file handler
import logging.handlers
