"""Published dle-gateway.v1 compatibility baseline."""

import json
from pathlib import Path

import yaml

from scripts.check_gateway_openapi_compatibility import find_breaking_changes


ROOT = Path(__file__).resolve().parents[2]


def test_gateway_v1_has_no_unversioned_breaking_contract_change() -> None:
    spec = yaml.safe_load((ROOT / 'docs' / 'openapi.yaml').read_text(encoding='utf-8'))
    baseline = json.loads(
        (ROOT / 'docs' / 'contracts' / 'gateway-v1-compatibility.json').read_text(encoding='utf-8')
    )
    assert find_breaking_changes(spec, baseline) == []
