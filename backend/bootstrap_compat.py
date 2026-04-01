"""
Runtime compatibility patches for legacy dependencies.

These patches must be applied before importing modules that rely on
older Flask/GraphQL integration packages so every entrypoint boots with
the same compatibility behavior.
"""

from __future__ import annotations

import collections as collections_module
from collections import abc as collections_abc


def apply_runtime_compatibility_patches() -> None:
    """Apply process-wide compatibility patches required by legacy packages."""
    if not hasattr(collections_module, "MutableMapping"):
        collections_module.MutableMapping = collections_abc.MutableMapping
        collections_module.Mapping = collections_abc.Mapping
        collections_module.Sequence = collections_abc.Sequence
        collections_module.Iterable = collections_abc.Iterable
        collections_module.Callable = collections_abc.Callable

    try:
        import graphql
        import graphql.error
    except ImportError:
        return

    if not hasattr(graphql, "get_default_backend"):
        def get_default_backend():
            return None

        graphql.get_default_backend = get_default_backend

    if not hasattr(graphql.error, "format_error"):
        graphql.error.format_error = lambda e: str(e)
