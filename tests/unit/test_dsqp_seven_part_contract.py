"""G-DSQP: freeze the seven-part persona contract."""

from __future__ import annotations

from backend.dsqp import (
    COMPONENT_KEYS,
    DSQP_PART_LABELS,
    DSQP_SEVEN_PART_KEYS,
    dsqp_contract_summary,
)
from backend.dsqp.dsqp_validator import DSQPValidator


def test_dsqp_contract_is_exactly_seven_parts():
    assert len(COMPONENT_KEYS) == 7
    assert tuple(COMPONENT_KEYS) == DSQP_SEVEN_PART_KEYS
    assert len(DSQP_PART_LABELS) == 7
    assert "related_jobs" in COMPONENT_KEYS  # Related Roles
    assert "skills" in COMPONENT_KEYS  # Traits / Skills label


def test_dsqp_contract_summary_stable():
    summary = dsqp_contract_summary()
    assert summary["part_count"] == 7
    assert summary["keys"] == list(COMPONENT_KEYS)


def test_dsqp_validator_requires_all_seven_components():
    validator = DSQPValidator()
    incomplete = {
        "components": {key: {"value": "x"} for key in COMPONENT_KEYS[:-1]},
        "dsqp_chain": [
            {"component": key, "question": "q?", "answer": "a"}
            for key in COMPONENT_KEYS[:-1]
        ],
    }
    result = validator.validate(incomplete)
    assert result.get("missing_components") or not result.get("coverage_ok", True)
