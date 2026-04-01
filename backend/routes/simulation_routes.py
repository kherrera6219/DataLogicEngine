"""
Compatibility shim for the canonical simulation API blueprint.

The supported implementation lives in ``routes/simulation_routes.py``.
This module preserves the historical import path while avoiding a second,
divergent definition of the same HTTP surface.
"""

from routes.simulation_routes import simulation_bp

__all__ = ["simulation_bp"]
