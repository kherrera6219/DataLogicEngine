from app import app


def test_service_routes_are_registered_in_main_app():
    """Guard against unwired blueprints in the primary Flask app path."""
    rules = {str(rule.rule) for rule in app.url_map.iter_rules()}

    expected_rules = {
        "/api/methods",
        "/api/methods/cross-sector",
        "/api/contextual/experts",
        "/api/honeycomb/generate",
        "/api/search/global",
    }

    missing = sorted(route for route in expected_rules if route not in rules)
    assert not missing, f"Expected wired service routes were missing: {missing}"


def test_removed_server_rendered_page_routes_are_not_registered():
    """Chat and knowledge graph UI are owned by Electron/Next, not Flask templates."""
    rules = {str(rule.rule) for rule in app.url_map.iter_rules()}

    assert "/chat" not in rules
    assert "/knowledge-graph" not in rules
