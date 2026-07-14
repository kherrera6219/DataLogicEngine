from backend.evaluation import (
    detect_provider_model_drift,
    load_provider_model_matrix,
    provider_matrix_release_ready,
)
from backend.llm_gateway.model_defaults import GOOGLE_PRIMARY_MODEL, OPENAI_LATEST_MODEL


def test_provider_model_rows_are_separate_and_match_current_product_defaults():
    matrix = load_provider_model_matrix()
    defaults = {"openai": OPENAI_LATEST_MODEL, "google": GOOGLE_PRIMARY_MODEL}
    rows = matrix["combinations"]

    assert len({(row["provider"], row["model"], row["workflow"]) for row in rows}) == len(rows)
    assert detect_provider_model_drift(matrix, defaults) == []


def test_pending_installed_and_human_evidence_cannot_approve_release():
    matrix = load_provider_model_matrix()

    assert provider_matrix_release_ready(matrix) is False
    assert matrix["release_ready"] is False
    for row in matrix["combinations"]:
        if row["provider"] in {"openai", "google"}:
            assert row["quarantined"] is True
            assert row["owner_approval"] is False
