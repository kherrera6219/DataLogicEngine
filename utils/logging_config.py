"""
Universal Knowledge Graph (UKG) System - Logging Configuration

This module provides logging configuration for the UKG system.
"""

import os

def get_logging_config():
    """
    Get the logging configuration dictionary.
    
    Returns:
        Dict with logging configuration
    """
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.FileHandler",
                "level": log_level,
                "formatter": "standard",
                "filename": "logs/ukg_system.log",
                "mode": "a",
            }
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": True
            }
        }
    }