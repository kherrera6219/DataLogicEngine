"""API health must report the product-versions authority, not a hardcode."""

from __future__ import annotations

import inspect

from backend.product_version import PRODUCT_VERSION
from backend.routes.api_routes import api_health


def test_api_health_uses_product_version_constant():
    source = inspect.getsource(api_health)
    assert "PRODUCT_VERSION" in source
    assert '"1.0.0"' not in source
    assert PRODUCT_VERSION  # authority loaded
