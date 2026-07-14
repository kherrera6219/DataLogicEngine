from __future__ import annotations

import pytest

from ukg_sdk.truth_engine.core import TruthEngine


class FakeClient:
    def __init__(self, response: dict):
        self.response = response
        self.calls: list[tuple[str, dict]] = []

    def post(self, path: str, json: dict) -> dict:
        self.calls.append((path, json))
        return self.response


def test_evaluate_is_thin_canonical_service_call():
    client = FakeClient(
        {
            "data": {
                "contract_version": "governed.v1",
                "status": "completed",
                "response": "measured answer",
                "run_id": "run-1",
                "confidence_score": None,
            }
        }
    )
    engine = TruthEngine(client=client)

    result = engine.evaluate("Is this governed?", {"purpose": "test"})

    assert result.ok is True
    assert result.verdict == "completed"
    assert result.answer == "measured answer"
    assert result.confidence is None
    assert client.calls[0][0] == "/gateway/chat"
    assert client.calls[0][1]["meta"]["purpose"] == "test"


def test_failure_is_not_converted_to_a_local_answer():
    failure = {"code": "POLICY_BLOCK", "message": "blocked"}
    engine = TruthEngine(
        client=FakeClient(
            {"status": "blocked", "run_id": "run-2", "failure": failure}
        )
    )

    result = engine.evaluate("blocked input")

    assert result.ok is False
    assert result.verdict == "blocked"
    assert result.failure == failure
    assert result.answer == ""


def test_removed_client_side_components_fail_explicitly():
    with pytest.raises(TypeError, match="removed in SDK 0.6"):
        TruthEngine(truthgate=object())
