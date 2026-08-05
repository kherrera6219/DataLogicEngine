from typing import Any

import pytest

from backend.knowledge_algorithms.contracts import (
    KAExecutionResult,
    KAExecutionState,
    KAOutcomeType,
)
from backend.truth_engine.truth_core.emergence_controller import (
    EmergenceDetectionController,
)
from backend.truth_engine.truth_core.l10_schemas import (
    EmergenceLevel,
    L10Decision,
    L10Input,
)


def _typed_result(ka_id: str, output: dict[str, Any]) -> KAExecutionResult:
    return KAExecutionResult(
        canonical_id=ka_id,
        ka_version="1.0.0",
        manifest_version="test",
        state=KAExecutionState.SUCCEEDED,
        outcome_type=KAOutcomeType.VALUE,
        success=True,
        output=output,
        request_id="request-test",
        run_id="run-test",
        trace_id=f"trace-{ka_id}",
    )


class MockKAController:
    def execute_typed(
        self,
        ka_id: str,
        inputs: dict[str, Any],
    ) -> KAExecutionResult:
        content = str(inputs.get("content", ""))

        # Lane A: Emergence
        if ka_id == "KA-021":
            observations = inputs["observations"]
            return _typed_result(
                ka_id,
                {
                    "is_emergent": any(
                        abs(row["observed_value"] - row["baseline_value"])
                        > row["tolerance"]
                        and bool(row["corroborating_trace_ids"])
                        for row in observations
                    )
                },
            )
        if ka_id == "KA-1108":
            interaction = inputs["interactions"][0]
            return _typed_result(
                ka_id,
                {
                    "escalation_detected": interaction["crossed_privilege_boundary"],
                    "alerts": [],
                },
            )

        # Lane A: Safety
        if ka_id == "L10-KA-003":
            pii_found = "@" in content
            return _typed_result(
                ka_id,
                {
                    "redactions_found": 1 if pii_found else 0,
                    "redacted_content": (
                        "Contact us at [REDACTED_EMAIL]" if pii_found else content
                    ),
                    "sensitive_values_returned": False,
                },
            )
        if ka_id == "L10-KA-001":
            return _typed_result(ka_id, {"entropy_score": 0.2})
        if ka_id == "L10-KA-002":
            return _typed_result(ka_id, {"awareness_detected": False})
        if ka_id == "L10-KA-004":
            violations = (
                [
                    {
                        "type": "ethical_breach",
                        "severity": "major",
                        "message": "Unethical content detected",
                    }
                ]
                if "unethical" in content
                else []
            )
            return _typed_result(ka_id, {"violations": violations})
        if ka_id == "L10-KA-006":
            original = float(inputs["confidence"])
            decayed = round(original * float(inputs.get("decay_factor", 0.98)), 6)
            threshold = float(inputs.get("threshold", 0.95))
            return _typed_result(
                ka_id,
                {
                    "status": ("pass" if decayed >= threshold else "fail"),
                    "passed": decayed >= threshold,
                    "decayed_confidence": decayed,
                },
            )
        if ka_id == "L10-KA-007":
            return _typed_result(
                ka_id,
                {
                    "escalation_required": False,
                    "reviews_dispatched": 0,
                },
            )
        if ka_id == "L10-KA-005":
            dependencies = inputs.get("dependency_results", {})
            trust_passed = dependencies["L10-KA-006"]["passed"]
            pii_found = dependencies["L10-KA-003"]["redactions_found"] > 0
            ethics = dependencies["L10-KA-004"]["violations"]
            decision = (
                "ESCALATE"
                if not trust_passed or ethics
                else "MODIFY"
                if pii_found
                else "RELEASE"
            )
            return _typed_result(ka_id, {"decision": decision})
        if ka_id == "KA-1095":
            return _typed_result(
                ka_id,
                {
                    "decisions": [
                        {
                            "escalation_required": True,
                            "review_level": "specialist",
                        }
                    ],
                    "reviews_dispatched": 0,
                },
            )

        # Lane B: Commit
        if ka_id == "KA-1109":
            return _typed_result(
                ka_id,
                {
                    "decisions": [
                        {
                            "containment_class": "restricted",
                            "persistence_rule": "restricted_store_only",
                        }
                    ],
                    "persistence_actions_applied": 0,
                },
            )
        if ka_id == "KA-1079":
            return _typed_result(
                ka_id,
                {
                    "decision": "reject",
                    "promotion_applied": False,
                },
            )

        return _typed_result(ka_id, {"status": "success", "passed": True})


@pytest.fixture
def l10_controller():
    return EmergenceDetectionController(ka_controller=MockKAController())


@pytest.fixture
def base_l10_input():
    return L10Input(
        simulation_id="test-sim-123",
        l9_result={
            "readiness_score": 0.98,
            "epistemic_report": {
                "current_output": "The solution is safe and effective.",
                "review_conducted": "full_meta_analysis",
            },
        },
        risk_domain="standard",
        reasoning_trace={"steps": ["L1", "L2", "L3"]},
    )


class TestLayer10Controller:
    def test_authorize_standard_release(self, l10_controller, base_l10_input):
        """Test release path for clean input."""
        result = l10_controller.authorize(base_l10_input)

        assert result.decision == L10Decision.RELEASE
        assert result.final_answer == "The solution is safe and effective."
        assert not result.requires_human_signoff
        assert not result.emergence_report.emergence_detected
        assert set(l10_controller.L10_KAS).issubset(result.kas_invoked)
        assert "KA-1109" in result.kas_invoked
        assert "KA-1079" in result.kas_invoked
        assert "KA-108" not in result.kas_invoked
        assert "KA-109" not in result.kas_invoked
        assert "KA-079" not in result.kas_invoked

    def test_authorize_pii_modification(self, l10_controller, base_l10_input):
        """Test modification path when PII is detected and redacted."""
        base_l10_input.l9_result["epistemic_report"]["current_output"] = (
            "Contact us at admin@example.com"
        )

        result = l10_controller.authorize(base_l10_input)

        assert result.decision == L10Decision.MODIFY
        assert "[REDACTED EMAIL]" in result.final_answer
        assert any(a.action_type == "redact" for a in result.containment_actions)

    def test_authorize_emergence_flagged(self, l10_controller, base_l10_input):
        """Test emergence detection via KA-021."""
        base_l10_input.l9_result["epistemic_report"]["current_output"] = (
            "This is an emergent pattern."
        )
        base_l10_input.l9_result["emergence_observations"] = [
            {
                "observation_id": "measured-deviation",
                "metric_name": "reasoning_path_deviation",
                "baseline_value": 0.1,
                "observed_value": 0.8,
                "tolerance": 0.2,
                "corroborating_trace_ids": ["trace-1"],
            }
        ]

        result = l10_controller.authorize(base_l10_input)

        assert result.emergence_report.emergence_detected
        assert result.emergence_report.overall_level == EmergenceLevel.MODERATE

    def test_trust_gate_belief_decay_pass(self, l10_controller, base_l10_input):
        """Test trust gate with 98% belief decay (Pass)."""
        # 0.98 * 0.98 = 0.9604 (> 0.95 threshold)
        base_l10_input.l9_result["readiness_score"] = 0.98
        result = l10_controller.authorize(base_l10_input)

        assert result.trust_report.status == "pass"
        assert result.decision == L10Decision.RELEASE

    def test_trust_gate_belief_decay_fail_high_risk(
        self, l10_controller, base_l10_input
    ):
        """Test high-risk trust gate failure leading to escalation."""
        # 0.99 * 0.98 = 0.9702 (< 0.985 threshold)
        base_l10_input.risk_domain = "high_risk"
        base_l10_input.l9_result["readiness_score"] = 0.99

        result = l10_controller.authorize(base_l10_input)

        assert result.trust_report.status == "fail"
        assert result.decision == L10Decision.ESCALATE
        assert result.requires_human_signoff
        assert "KA-1095" in result.kas_invoked

    def test_fail_closed_on_exception(self, l10_controller, base_l10_input):
        """Test that any exception in authorize leads to a HALT (Fail-Closed)."""
        result = l10_controller.authorize(None)

        assert result.decision == L10Decision.HALT
        assert "Final safety gate failed" in result.final_answer

    def test_lane_b_knowledge_commit_authorization(
        self, l10_controller, base_l10_input
    ):
        """Verify Lane B KAs are invoked during successful release."""
        result = l10_controller.authorize(base_l10_input)

        assert "KA-1109" in result.kas_invoked
        assert "KA-1079" in result.kas_invoked
        # Decision was RELEASE, so Lane B logic executed

    def test_lane_b_is_proposal_only_and_does_not_write_stores(
        self, monkeypatch, base_l10_input
    ):
        """Verify the retained controller cannot bypass the effect owner."""
        merged_nodes = []
        merged_relationships = []

        class FakeGraphStore:
            @staticmethod
            def merge_knowledge_node(properties):
                merged_nodes.append(properties)
                return True

            @staticmethod
            def merge_relationship_by_uid(source_uid, target_uid, rel_type, props=None):
                merged_relationships.append((source_uid, target_uid, rel_type, props))
                return True

        monkeypatch.setattr("backend.storage.get_graph_store", lambda: FakeGraphStore())

        controller = EmergenceDetectionController(ka_controller=MockKAController())

        result = controller.authorize(base_l10_input)

        assert result.decision == L10Decision.RELEASE
        assert merged_nodes == []
        assert merged_relationships == []
