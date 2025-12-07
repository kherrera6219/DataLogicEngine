"""
Backend middleware package for Universal Knowledge Graph system.

This package provides middleware components for request handling,
rate limiting, and other cross-cutting concerns.
"""

from .request_limits import configure_request_limits

__all__ = ['configure_request_limits']
