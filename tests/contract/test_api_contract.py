import pytest
try:
    import schemathesis
    SCHEMATHESIS_INSTALLED = True
except ImportError:
    schemathesis = None
    SCHEMATHESIS_INSTALLED = False

# Only import app and initialize schema if schemathesis is available
if SCHEMATHESIS_INSTALLED:
    from app import app
    schema = schemathesis.from_wsgi("/openapi.json", app)

    @schema.parametrize()
    def test_api_compliance(case):
        """
        Property-based testing to verify API compliance.
        Schemathesis will generate random queries based on the OpenAPI spec
        and ensure the server responds with matching status codes and schemas.
        """
        response = case.call_wsgi()
        case.validate_response(response)
        assert response.status_code < 500, f"Server error on {case.method} {case.formatted_path}"
else:
    @pytest.mark.skip(reason="Schemathesis not installed")
    def test_api_compliance():
        """Placeholder when schemathesis is not installed."""
        pass
