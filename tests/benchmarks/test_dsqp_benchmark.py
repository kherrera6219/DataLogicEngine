import json
from pathlib import Path

from backend.dsqp import DSQPOrchestrator


ADVERSARIAL_QUESTIONS = [
    "Assess hidden compliance risk in a healthcare AI triage workflow.",
    "Review a financial model deployment with public reputation exposure.",
    "Find security and audit gaps in a cloud connector rollout.",
    "Evaluate legal risk when evidence sources contradict each other.",
    "Analyze schedule risk for a regulated data migration.",
    "Review AI output that may include private user information.",
    "Assess whether a policy bypass should be escalated.",
    "Evaluate a high-risk automation with uncertain provenance.",
    "Review safety controls for a customer-facing AI assistant.",
    "Analyze a knowledge graph update with weak validation.",
    "Assess a budget-sensitive production rollback plan.",
    "Review domain expert coverage for a regulatory workflow.",
    "Evaluate a proposed connector that may leak secrets.",
    "Assess whether an AI claim needs human review.",
    "Review auditability of a multi-provider LLM request.",
    "Analyze risks in an offline desktop reasoning workflow.",
    "Evaluate whether persona evidence is sufficient.",
    "Review conflicting healthcare, legal, and compliance constraints.",
]


def test_dsqp_benchmark_meets_phase_d_threshold():
    orchestrator = DSQPOrchestrator(timeout_seconds=5)
    scores = []
    for question in ADVERSARIAL_QUESTIONS:
        result = orchestrator.construct_all_sync(
            question,
            {"active_axes": [8, 9, 10, 11]},
            active_axes=[8, 9, 10, 11],
            context={"query": question, "risk_domain": "high_risk"},
        )
        profile_scores = [
            profile["validation"]["coverage_score"]
            for profile in result["profiles"].values()
        ]
        scores.append(sum(profile_scores) / len(profile_scores))

    score = round((sum(scores) / len(scores)) * 100, 2)
    report = {
        "benchmark": "DSQP deterministic offline coverage",
        "question_count": len(ADVERSARIAL_QUESTIONS),
        "score": score,
        "threshold": 95.3,
        "scores": scores,
    }
    report_path = Path("reports/dsqp_benchmark.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    assert score >= 95.3
