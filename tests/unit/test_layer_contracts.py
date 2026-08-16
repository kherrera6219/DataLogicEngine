import pytest

from backend.governed_execution.layer_contracts import (
    LAYER_CONTRACTS,
    all_layer_ids,
    layer_contract,
)
from backend.governed_execution.ten_layers import LAYER_NAMES


def test_ten_layer_contracts_present():
    assert all_layer_ids() == list(range(1, 11))
    assert len(LAYER_CONTRACTS) == 10
    assert {
        f"L{layer}": layer_contract(layer)["name"] for layer in all_layer_ids()
    } == LAYER_NAMES
    for layer in range(1, 11):
        c = layer_contract(layer)
        assert c["name"]
        assert "reads" in c
        assert "writes" in c
        assert c["side_effects"] == []

    assert "provider_execution" not in {
        contract["name"] for contract in LAYER_CONTRACTS.values()
    }
    assert layer_contract(9)["name"] == "convergence"


def test_layer_contract_unknown_raises():
    with pytest.raises(KeyError, match="unknown_layer:99"):
        layer_contract(99)
