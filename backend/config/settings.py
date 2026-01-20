"""
Centralized Configuration Settings Module.

This module provides a single source of truth for all configurable values,
eliminating hardcoded values throughout the codebase.

All settings can be overridden via environment variables.
"""

import os
from typing import Any
from functools import lru_cache


class Settings:
    """Centralized application settings with environment variable support."""

    # ==========================================================================
    # SESSION & AUTHENTICATION
    # ==========================================================================
    SESSION_LIFETIME_MINUTES: int = int(os.getenv('SESSION_LIFETIME_MINUTES', '30'))
    SESSION_COOKIE_SECURE: bool = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE: str = os.getenv('SESSION_COOKIE_SAMESITE', 'Strict')

    # Account lockout settings
    MAX_FAILED_LOGIN_ATTEMPTS: int = int(os.getenv('MAX_FAILED_LOGIN_ATTEMPTS', '5'))
    ACCOUNT_LOCKOUT_MINUTES: int = int(os.getenv('ACCOUNT_LOCKOUT_MINUTES', '30'))

    # Password policy
    PASSWORD_MIN_LENGTH: int = int(os.getenv('PASSWORD_MIN_LENGTH', '12'))
    PASSWORD_EXPIRY_DAYS: int = int(os.getenv('PASSWORD_EXPIRY_DAYS', '90'))
    PASSWORD_HISTORY_COUNT: int = int(os.getenv('PASSWORD_HISTORY_COUNT', '5'))

    # ==========================================================================
    # RATE LIMITING
    # ==========================================================================
    GLOBAL_RATE_LIMIT: str = os.getenv('GLOBAL_RATE_LIMIT', '200 per hour')
    AUTH_RATE_LIMIT: str = os.getenv('AUTH_RATE_LIMIT', '10 per minute')
    ADMIN_RATE_LIMIT: str = os.getenv('ADMIN_RATE_LIMIT', '30 per minute')
    API_RATE_LIMIT: str = os.getenv('API_RATE_LIMIT', '100 per minute')
    GATEWAY_RATE_LIMIT: str = os.getenv('GATEWAY_RATE_LIMIT', '60 per minute')

    # ==========================================================================
    # CIRCUIT BREAKER (LLM Gateway)
    # ==========================================================================
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = int(os.getenv('CIRCUIT_BREAKER_FAILURE_THRESHOLD', '5'))
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = int(os.getenv('CIRCUIT_BREAKER_RECOVERY_TIMEOUT', '60'))
    CIRCUIT_BREAKER_HALF_OPEN_REQUESTS: int = int(os.getenv('CIRCUIT_BREAKER_HALF_OPEN_REQUESTS', '3'))

    # ==========================================================================
    # REQUEST HANDLING
    # ==========================================================================
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv('REQUEST_TIMEOUT_SECONDS', '30'))
    MAX_CONTENT_LENGTH: int = int(os.getenv('MAX_CONTENT_LENGTH', str(16 * 1024 * 1024)))  # 16MB

    # ==========================================================================
    # CACHING
    # ==========================================================================
    DEFAULT_CACHE_TTL: int = int(os.getenv('DEFAULT_CACHE_TTL', '300'))  # 5 minutes
    UKG_CACHE_TTL: int = int(os.getenv('UKG_CACHE_TTL', '300'))
    STATS_CACHE_TTL: int = int(os.getenv('STATS_CACHE_TTL', '60'))  # 1 minute for dashboard stats

    # ==========================================================================
    # PAGINATION
    # ==========================================================================
    DEFAULT_PAGE_SIZE: int = int(os.getenv('DEFAULT_PAGE_SIZE', '50'))
    MAX_PAGE_SIZE: int = int(os.getenv('MAX_PAGE_SIZE', '100'))

    # ==========================================================================
    # DATABASE
    # ==========================================================================
    DB_POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '20'))
    DB_POOL_MAX_OVERFLOW: int = int(os.getenv('DB_POOL_MAX_OVERFLOW', '30'))
    DB_POOL_TIMEOUT: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    DB_POOL_RECYCLE: int = int(os.getenv('DB_POOL_RECYCLE', '300'))

    # ==========================================================================
    # LLM GATEWAY
    # ==========================================================================
    LLM_DEFAULT_MAX_TOKENS: int = int(os.getenv('LLM_DEFAULT_MAX_TOKENS', '4096'))
    LLM_DEFAULT_TEMPERATURE: float = float(os.getenv('LLM_DEFAULT_TEMPERATURE', '0.7'))
    LLM_REQUEST_TIMEOUT: int = int(os.getenv('LLM_REQUEST_TIMEOUT', '120'))

    # ==========================================================================
    # UKG SIMULATION
    # ==========================================================================
    UKG_MAX_SIMULATION_LAYERS: int = int(os.getenv('UKG_MAX_SIMULATION_LAYERS', '10'))
    UKG_DEFAULT_CONFIDENCE_THRESHOLD: float = float(os.getenv('UKG_DEFAULT_CONFIDENCE_THRESHOLD', '0.85'))
    UKG_ENABLE_QUANTUM_SIMULATION: bool = os.getenv('UKG_ENABLE_QUANTUM_SIMULATION', 'False').lower() == 'true'

    # ==========================================================================
    # SECURITY
    # ==========================================================================
    ALLOWED_ROLES: frozenset = frozenset({'owner', 'super_admin', 'admin', 'security_officer',
                                          'auditor', 'data_scientist', 'developer', 'analyst',
                                          'user', 'guest', 'viewer'})
    PROTECTED_ROLES: frozenset = frozenset({'owner', 'super_admin'})  # Cannot be assigned via API

    # ==========================================================================
    # OBSERVABILITY
    # ==========================================================================
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1'))
    SENTRY_PROFILES_SAMPLE_RATE: float = float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1'))

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a setting value by key name."""
        return getattr(cls, key, default)

    @classmethod
    def to_dict(cls) -> dict:
        """Export all settings as dictionary (for debugging, excludes secrets)."""
        return {
            key: value for key, value in vars(cls).items()
            if not key.startswith('_') and not callable(value)
            and 'SECRET' not in key and 'KEY' not in key and 'PASSWORD' not in key
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get singleton Settings instance."""
    return Settings()


# Convenience exports
settings = get_settings()
