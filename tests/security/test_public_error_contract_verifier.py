"""Regression coverage for public exception-boundary scanning."""

from pathlib import Path

from scripts.verify_public_error_contracts import findings_for


ROOT = Path(__file__).resolve().parents[2]


def test_model_lifecycle_routes_do_not_return_raw_exception_values():
    assert findings_for(ROOT / "backend/routes/dataset_routes.py") == []


def test_ka_workflow_routes_use_the_typed_public_error_boundary():
    assert findings_for(ROOT / "backend/routes/ka_routes.py") == []
