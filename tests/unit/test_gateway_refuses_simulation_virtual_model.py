"""Chat gateway must not accept simulation as a virtual model (isolation)."""

from __future__ import annotations

import pytest

from backend.llm_gateway.external_contract import apply_virtual_model


def test_apply_virtual_model_rejects_simulation_ids():
    for bad in ("simulation", "dle-simulation", "dle-simulation.v1", "sim"):
        with pytest.raises(ValueError, match="Unsupported governed virtual model"):
            apply_virtual_model({"virtual_model": bad, "messages": []})
    with pytest.raises(ValueError, match="Unsupported governed virtual model"):
        apply_virtual_model({"mode": "simulation", "messages": []})


def test_apply_virtual_model_accepts_product_models():
    for good in ("dle-standard", "dle-enhanced", "dle-local-review"):
        payload = {"virtual_model": good}
        policy = apply_virtual_model(payload)
        assert payload["virtual_model"] == good
        assert policy.id == good
