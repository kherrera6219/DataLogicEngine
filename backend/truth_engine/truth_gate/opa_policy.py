"""Local OPA/Rego policy evaluation with a deterministic Python fallback."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from typing import Any


class OPAPolicyEvaluator:
    """Evaluate TruthGate policy offline through OPA when available."""

    def __init__(self, *, binary_path: str | None = None, policy_path: str | Path | None = None):
        self.binary_path = binary_path or os.environ.get("DLE_OPA_BINARY") or os.environ.get("OPA_BINARY")
        self.policy_path = Path(policy_path or os.environ.get("DLE_TRUTHGATE_POLICY") or "policies/truthgate.rego")

    def evaluate(self, input_data: dict[str, Any]) -> dict[str, Any]:
        if self.binary_path and Path(self.binary_path).exists() and self.policy_path.exists():
            try:
                completed = subprocess.run(
                    [
                        self.binary_path,
                        "eval",
                        "--format=json",
                        "--data",
                        str(self.policy_path),
                        "--input",
                        "-",
                        "data.datalogicengine.truthgate.decision",
                    ],
                    input=json.dumps(input_data),
                    text=True,
                    capture_output=True,
                    timeout=5,
                    check=True,
                )
                parsed = json.loads(completed.stdout)
                result = parsed.get("result", [{}])[0].get("expressions", [{}])[0].get("value", {})
                if isinstance(result, dict):
                    return {"available": True, "backend": "opa", **result}
            except Exception as exc:  # Fall back fail-closed below.
                return {"available": False, "backend": "python", **self._fallback(input_data), "error": str(exc)}
        return {"available": False, "backend": "python", **self._fallback(input_data)}

    @staticmethod
    def _fallback(input_data: dict[str, Any]) -> dict[str, Any]:
        risk_domain = str(input_data.get("risk_domain") or "standard").lower()
        confidence = float(input_data.get("overall_confidence") or 0.0)
        violations = []
        if risk_domain in {"healthcare", "finance", "legal", "safety"} and confidence < 0.995:
            violations.append("critical_domain_confidence_below_0_995")
        if input_data.get("axis_17_requires_human") and not input_data.get("human_reviewed"):
            violations.append("human_review_required")
        return {
            "allow": not violations,
            "violations": violations,
        }
