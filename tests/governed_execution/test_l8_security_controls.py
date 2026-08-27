from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

from backend.governed_execution.l8_security_controls import (
    evaluate_model_screening,
    evaluate_opa_policy,
)
from backend.truth_engine.truth_gate.opa_policy import OPAPolicyEvaluator


def test_product_l8_model_screening_failure_blocks_without_detail_leak():
    sentinel = "secret-model-screening-path"
    with patch(
        "backend.governed_execution.l8_security_controls.TruthGateModelScreening.screen",
        side_effect=RuntimeError(sentinel),
    ):
        result = evaluate_model_screening("candidate")

    assert result["allowed"] is False
    assert result["action"] == "block"
    assert result["error"] == "model_screening_failed"
    assert sentinel not in repr(result)


def test_product_l8_opa_failure_denies_without_detail_leak():
    sentinel = "secret-opa-policy-path"
    with patch(
        "backend.governed_execution.l8_security_controls.OPAPolicyEvaluator.evaluate",
        side_effect=RuntimeError(sentinel),
    ):
        result = evaluate_opa_policy(
            risk_domain="standard",
            overall_confidence=0.99,
            minimum_confidence=0.95,
        )

    assert result["allow"] is False
    assert result["violations"] == ["opa_evaluation_error"]
    assert result["error"] == "opa_evaluation_failed"
    assert sentinel not in repr(result)


def test_configured_opa_process_failure_denies_instead_of_allowing_fallback(tmp_path):
    binary = tmp_path / "opa.exe"
    policy = tmp_path / "truthgate.rego"
    binary.write_bytes(b"test")
    policy.write_text("package datalogicengine.truthgate", encoding="utf-8")
    evaluator = OPAPolicyEvaluator(binary_path=str(binary), policy_path=policy)

    with patch(
        "backend.truth_engine.truth_gate.opa_policy.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, [str(binary)]),
    ):
        result = evaluator.evaluate(
            {
                "risk_domain": "standard",
                "overall_confidence": 1.0,
                "minimum_confidence": 0.95,
            }
        )

    assert result == {
        "available": False,
        "backend": "error",
        "allow": False,
        "violations": ["opa_evaluation_error"],
        "error": "opa_evaluation_failed",
    }


def test_configured_opa_malformed_output_denies(tmp_path):
    binary = tmp_path / "opa.exe"
    policy = tmp_path / "truthgate.rego"
    binary.write_bytes(b"test")
    policy.write_text("package datalogicengine.truthgate", encoding="utf-8")
    evaluator = OPAPolicyEvaluator(binary_path=str(binary), policy_path=policy)

    completed = subprocess.CompletedProcess(
        args=[str(binary)],
        returncode=0,
        stdout=json.dumps({"result": []}),
        stderr="",
    )
    with patch(
        "backend.truth_engine.truth_gate.opa_policy.subprocess.run",
        return_value=completed,
    ):
        result = evaluator.evaluate(
            {
                "risk_domain": "standard",
                "overall_confidence": 1.0,
                "minimum_confidence": 0.95,
            }
        )

    assert result["allow"] is False
    assert result["error"] == "opa_evaluation_failed"
