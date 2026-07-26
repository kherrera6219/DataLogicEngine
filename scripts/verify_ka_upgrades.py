"""Verify retained KA upgrade behavior through the canonical implementations.

This compatibility command used to exercise a retired, provider-backed
``KA-117 Threat Model`` prototype. Threat modeling is canonically KA-136 and
KA-117 is the knowledge-integrity validator. The checks below intentionally use
the public deterministic KA boundary so this verifier cannot introduce a
second provider or execution authority.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.knowledge_algorithms.ka_05_query_classification import (
    KA005QueryClassification,
)
from backend.knowledge_algorithms.ka_136_threat_model_agent import (
    KA136ThreatModelAgent,
)


class VerificationFailure(RuntimeError):
    """Raised when a canonical KA upgrade contract does not hold."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationFailure(message)


def verify_ka136_threat_model() -> dict[str, Any]:
    """Verify deterministic threat findings at the canonical KA-136 boundary."""
    result = KA136ThreatModelAgent({}).run(
        {
            "assets": [
                {
                    "asset_id": "gateway",
                    "criticality": "critical",
                    "privileged": True,
                },
                {
                    "asset_id": "store",
                    "criticality": "critical",
                    "stores_sensitive_data": True,
                },
            ],
            "data_flows": [
                {
                    "flow_id": "gateway-store",
                    "source_asset_id": "gateway",
                    "target_asset_id": "store",
                    "crosses_trust_boundary": True,
                    "authenticated": True,
                    "encrypted": False,
                    "integrity_protected": True,
                }
            ],
        }
    )
    output = dict(result.get("output") or {})
    _require(result.get("ka_id") == "KA-136", "KA-136 returned the wrong identity")
    _require(result.get("success") is True, "KA-136 did not complete successfully")
    _require(output.get("deterministic") is True, "KA-136 is not deterministic")
    _require(
        output.get("findings")
        == [
            {
                "flow_id": "gateway-store",
                "threat": "information_disclosure",
                "severity": "critical",
                "proposed_mitigation": "require_encryption",
            }
        ],
        "KA-136 did not return the expected bounded threat finding",
    )
    return result


def verify_ka005_classification() -> dict[str, Any]:
    """Verify local classification without recursive provider delegation."""
    algorithm = KA005QueryClassification({})
    result = algorithm.run({"query": "Review the regulatory compliance rules"})
    output = dict(result.get("output") or {})
    _require(result.get("ka_id") == "KA-005", "KA-005 returned the wrong identity")
    _require(result.get("success") is True, "KA-005 did not complete successfully")
    _require(
        output.get("category") == "REGULATORY",
        "KA-005 did not select the regulatory category",
    )
    _require(
        output.get("suggested_tier") == "high_stakes",
        "KA-005 did not bind regulatory work to the high-stakes tier",
    )
    _require(
        output.get("metadata", {}).get("sdk_response") == {},
        "KA-005 attempted recursive provider delegation",
    )
    return result


def main() -> int:
    checks = (
        ("KA-136 canonical threat model", verify_ka136_threat_model),
        ("KA-005 deterministic classification", verify_ka005_classification),
    )
    failures: list[str] = []
    for label, check in checks:
        try:
            check()
            print(f"[PASS] {label}")
        except Exception as exc:  # noqa: BLE001 - verification boundary
            failures.append(f"{label}: {exc}")
            print(f"[FAIL] {label}: {exc}")
    if failures:
        print(f"KA upgrade verification: FAIL errors={len(failures)}")
        return 1
    print(f"KA upgrade verification: PASS checks={len(checks)}/{len(checks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
