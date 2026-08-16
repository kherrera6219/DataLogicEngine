from backend.runtime.startup_contract import (
    DEFAULT_GENERATIVE_LOCALITY,
    legacy_api_prefixes_enabled,
    startup_contract_summary,
)


def test_startup_contract_summary_product_defaults():
    summary = startup_contract_summary()
    assert summary["entry"] == "app.create_app"
    assert summary["generative_locality"] == DEFAULT_GENERATIVE_LOCALITY
    assert summary["gateway_admin_prefix"] == "/api/v1/admin/gateway"


def test_legacy_api_prefixes_default_off(monkeypatch):
    monkeypatch.delenv("DLE_LEGACY_API_PREFIXES", raising=False)
    assert legacy_api_prefixes_enabled() is False
