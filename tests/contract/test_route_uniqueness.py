"""Phase 2: Flask URL map must not register overlapping method+path pairs."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="module")
def uniqueness_app():
    os.environ["DLE_LEGACY_API_PREFIXES"] = "false"
    from scripts.verify_route_uniqueness import _build_app, find_collisions

    app = _build_app()
    return app, find_collisions(app)


def test_no_route_collisions_on_default_v1_surface(uniqueness_app):
    app, collisions = uniqueness_app
    assert app.config.get("DLE_LEGACY_API_PREFIXES") in (False, None) or (
        app.config.get("DLE_LEGACY_API_PREFIXES") is False
    )
    assert collisions == [], (
        "Overlapping Flask routes detected:\n"
        + "\n".join(
            f"{c['method']} {c['path']} -> {c['endpoints']}" for c in collisions
        )
    )


def test_compliance_prefix_owned_by_compliance_api_only(uniqueness_app):
    app, _ = uniqueness_app
    compliance_endpoints = {
        rule.endpoint
        for rule in app.url_map.iter_rules()
        if rule.rule.startswith("/api/v1/compliance")
    }
    # Must not include regulatory_api endpoints under /api/v1/compliance
    assert all(
        not ep.startswith("regulatory_api") for ep in compliance_endpoints
    ), compliance_endpoints


def test_gateway_admin_namespaced_under_admin_gateway(uniqueness_app):
    app, _ = uniqueness_app
    gateway_admin_rules = [
        rule.rule
        for rule in app.url_map.iter_rules()
        if rule.endpoint.startswith("gateway_admin")
    ]
    assert gateway_admin_rules, "gateway_admin blueprint not registered"
    assert all(r.startswith("/api/v1/admin/gateway") for r in gateway_admin_rules)
    # Ops admin health remains outside gateway namespace
    ops_health = [
        rule.rule
        for rule in app.url_map.iter_rules()
        if rule.endpoint == "admin_api.admin_health_check"
        or (rule.rule == "/api/v1/admin/health")
    ]
    assert any(r == "/api/v1/admin/health" for r in ops_health)
