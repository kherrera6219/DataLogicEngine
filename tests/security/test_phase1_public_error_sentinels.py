"""Prove internal exception sentinels cannot reach public response bodies."""

from __future__ import annotations

from types import SimpleNamespace
import inspect


SENTINEL = "PHASE1_INTERNAL_EXCEPTION_SENTINEL_DO_NOT_EXPOSE"


def test_graphql_execution_error_is_normalized(authenticated_client, monkeypatch):
    from backend import graphql_schema

    monkeypatch.setattr(
        graphql_schema.schema,
        "execute",
        lambda *_args, **_kwargs: SimpleNamespace(
            data=None,
            errors=[RuntimeError(SENTINEL)],
        ),
    )

    response = authenticated_client.post("/graphql", json={"query": "query { users { id } }"})

    assert response.status_code == 200
    assert SENTINEL not in response.get_data(as_text=True)


def test_compliance_exception_is_normalized(app, monkeypatch):
    from backend.routes import compliance_routes

    manager = SimpleNamespace(
        get_compliance_hierarchy=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError(SENTINEL)
        )
    )
    monkeypatch.setattr(compliance_routes, "_get_compliance_manager", lambda: manager)

    view = app.view_functions["compliance_api.get_compliance_standards"]
    with app.test_request_context("/api/v1/compliance/standards"):
        response = app.make_response(inspect.unwrap(view)())

    assert response.status_code == 500
    assert SENTINEL not in response.get_data(as_text=True)


def test_methods_exception_is_normalized(app):
    class BrokenAxisSystem:
        @property
        def axis_managers(self):
            raise RuntimeError(SENTINEL)

    app.config["AXIS_SYSTEM"] = BrokenAxisSystem()

    view = app.view_functions["methods_api.get_methods"]
    with app.test_request_context("/api/methods"):
        response = app.make_response(inspect.unwrap(view)())

    assert response.status_code == 500
    assert SENTINEL not in response.get_data(as_text=True)
