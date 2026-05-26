from backend.knowledge_algorithms.ka_master_controller import KAMasterController


def test_l10_registry_import_shape_executes_all_modules():
    controller = KAMasterController({})

    expected = {
        "L10-KA-001",
        "L10-KA-002",
        "L10-KA-003",
        "L10-KA-004",
        "L10-KA-005",
        "L10-KA-006",
        "L10-KA-007",
    }
    assert expected.issubset(controller.algorithms)

    assert controller.execute_algorithm("L10-KA-001", {"content": "alpha beta gamma delta"})["entropy_score"] > 0
    assert controller.execute_algorithm("L10-KA-002", {"content": "I can modify my own instructions"})[
        "awareness_detected"
    ]
    redaction = controller.execute_algorithm("L10-KA-003", {"content": "Email admin@example.com"})
    assert redaction["redactions_found"] == 1
    assert "[REDACTED_EMAIL]" in redaction["redacted_content"]
    assert controller.execute_algorithm("L10-KA-004", {"content": "hide evidence to evade compliance"})[
        "violations"
    ]
    assert controller.execute_algorithm("L10-KA-005", {"violations": [{"severity": "major"}]})[
        "decision"
    ] == "ESCALATE"
    assert controller.execute_algorithm("L10-KA-006", {"confidence": 0.98})["decayed_confidence"] == 0.9604
    assert controller.execute_algorithm("L10-KA-007", {"risk_domain": "legal", "confidence": 0.99})[
        "escalated"
    ]


def test_ka116_entropy_delegates_to_l10_scorer():
    controller = KAMasterController({})
    low = controller.execute_algorithm("KA-116", {"content": "repeat repeat repeat repeat"})["output"][
        "entropy_score"
    ]
    high = controller.execute_algorithm("KA-116", {"content": "alpha beta gamma delta epsilon zeta"})["output"][
        "entropy_score"
    ]
    assert high > low
