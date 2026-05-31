from backend.knowledge_algorithms.ka_11_analytical_modeling import KA011AnalyticalModeling, KA011Input
from backend.knowledge_algorithms.ka_33_reserved_expansion_slot import KA033ExtensionSlot, KA033Input
from backend.knowledge_algorithms.ka_37_resource_allocator import KA037Input, KA037ResourceAllocator
from backend.knowledge_algorithms.ka_39_anomaly_detection import KA039AnomalyDetection, KA039Input
from backend.knowledge_algorithms.ka_43_causal_inference import KA043CausalInference, KA043Input
from backend.knowledge_algorithms.ka_48_entity_extraction import KA048EntityExtraction, KA048Input
from backend.knowledge_algorithms.ka_50_summarization import KA050Input, KA050Summarization
from backend.knowledge_algorithms.ka_77_data_enrichment import KA077DataEnrichment, KA077EnrichmentInput
from backend.knowledge_algorithms.ka_79_data_retrieval import KA079DataRetrieval, KA079RetrievalInput
from backend.knowledge_algorithms.ka_106_fault_tolerance import KA106FaultInput, KA106FaultTolerance
from backend.knowledge_algorithms.ka_109_system_health import KA109HealthInput, KA109SystemHealth
from backend.knowledge_algorithms.ka_111_api_gateway import KA111APIGateway, KA111Input
from backend.knowledge_algorithms.ka_master_controller import KAMasterController


def test_ka011_supports_structural_and_bayesian_models():
    ka = KA011AnalyticalModeling({})

    structural = ka.run(KA011Input(model_type="structural", data=[{"a": 1}, {"a": 2, "b": 3}, [1, 2]]))
    assert structural["success"] is True
    assert structural["output"]["results"]["field_frequency"]["a"] == 2
    assert structural["output"]["results"]["nested_collection_count"] == 1

    bayesian = ka.run(KA011Input(model_type="bayesian", data=[8, 10, 12, 14]))
    assert bayesian["success"] is True
    assert bayesian["output"]["results"]["posterior_mean"] > 0
    assert "implementation stubbed" not in str(bayesian["output"]).lower()


def test_ka033_extension_slot_summarizes_payload():
    result = KA033ExtensionSlot({}).run(KA033Input(operation="summarize", payload={"query": "x", "empty": ""}))

    assert result["success"] is True
    assert result["output"]["operation"] == "summarize"
    assert result["output"]["result_payload"]["summary"]["field_count"] == 2
    assert result["output"]["result_payload"]["summary"]["empty_fields"] == ["empty"]


def test_ka039_detects_numeric_outlier_with_zscore():
    result = KA039AnomalyDetection({}).run(KA039Input(data=[10, 11, 12, 10, 100], threshold=1.5))

    assert result["success"] is True
    assert result["output"]["count"] == 1
    assert result["output"]["anomalies"][0]["value"] == 100
    assert result["output"]["baseline"]["count"] == 5


def test_ka037_allocates_resources_from_workload_shape():
    ka = KA037ResourceAllocator({})

    normal = ka.run(KA037Input(priority="normal", task_type="general", complexity="low", input_size=100))
    critical = ka.run(
        KA037Input(
            priority="critical",
            task_type="orchestration",
            complexity="high",
            input_size=4000,
            expected_steps=6,
        )
    )

    assert normal["success"] is True
    assert critical["success"] is True
    assert critical["output"]["token_budget"] > normal["output"]["token_budget"]
    assert critical["output"]["execution_queue"] in {"priority", "batch"}
    assert critical["output"]["allocation_factors"]["expected_steps"] == 6


def test_ka043_ranks_causes_from_evidence_and_mechanism():
    result = KA043CausalInference({}).run(
        KA043Input(
            effect="Ground is wet",
            candidates=[
                {"name": "Sprinklers were on", "mechanism": "water spray can wet ground", "precedes_effect": True},
                {"name": "Heavy rain", "mechanism": "rainfall can wet ground", "precedes_effect": True},
            ],
            evidence=["Weather station reported heavy rain before the ground was wet."],
        )
    )

    assert result["success"] is True
    assert result["output"]["likely_cause"] == "Heavy rain"
    assert result["output"]["ranked_causes"][0]["confidence"] > result["output"]["ranked_causes"][1]["confidence"]
    assert "implementation stubbed" not in str(result["output"]).lower()


def test_ka048_extracts_typed_entities():
    text = "NIST 800-53 review for Acme Corporation costs $12,500 on 2026-05-30. Email admin@example.com."
    result = KA048EntityExtraction({}).run(KA048Input(text=text))
    entities = result["output"]["entities"]

    assert result["success"] is True
    assert any(entity["type"] == "REGULATION" and entity["text"].lower().startswith("nist") for entity in entities)
    assert any(entity["type"] == "MONEY" and "12,500" in entity["text"] for entity in entities)
    assert any(entity["type"] == "DATE" and entity["text"] == "2026-05-30" for entity in entities)
    assert any(entity["type"] == "EMAIL" and entity["text"] == "admin@example.com" for entity in entities)


def test_ka050_extractively_summarizes_important_sentences():
    text = (
        "Status noise is low. "
        "The incident response plan reduces outage risk for local services. "
        "Backups are validated daily and recovery evidence is retained. "
        "Unrelated cosmetic updates can wait."
    )
    result = KA050Summarization({}).run(KA050Input(text=text, max_length=140, focus_terms=["backups", "recovery"]))

    assert result["success"] is True
    assert "Backups are validated daily" in result["output"]["summary"]
    assert result["output"]["compression_ratio"] < 1
    assert result["output"]["method"] == "extractive_frequency_rank"


def test_ka077_enriches_records_locally():
    ka = KA077DataEnrichment({})
    result = ka.run(
        KA077EnrichmentInput(
            records=[
                {
                    "company": "Acme Health",
                    "location": "Seattle, WA",
                    "description": "HIPAA compliance audit",
                }
            ]
        )
    )
    enriched = result["output"]["enriched_records"][0]

    assert result["success"] is True
    assert enriched["industry"] == "healthcare"
    assert enriched["geo_coords"] == KA077DataEnrichment._deterministic_coordinates("Seattle, WA")
    assert "privacy" in enriched["entity_topics"]
    assert result["output"]["enrichment_summary"]["local_only"] is True


def test_ka079_retrieves_ranked_local_records_with_filters():
    records = [
        {"id": "a", "title": "Payroll export", "category": "finance", "body": "CSV delivery"},
        {"id": "b", "title": "HIPAA audit packet", "category": "compliance", "body": "Evidence for privacy audit"},
        {"id": "c", "title": "SOX audit packet", "category": "compliance", "body": "Financial control evidence"},
    ]
    result = KA079DataRetrieval({}).run(
        KA079RetrievalInput(
            query={"text": "privacy audit evidence", "filters": {"category": "compliance"}},
            records=records,
            max_results=2,
        )
    )

    assert result["success"] is True
    assert result["output"]["results_count"] == 2
    assert result["output"]["results"][0]["id"] == "b"
    assert result["output"]["results"][0]["relevance"] > result["output"]["results"][1]["relevance"]
    assert result["output"]["local_only"] is True


def test_ka106_uses_deterministic_circuit_breaker_policy():
    ka = KA106FaultTolerance({})

    open_result = ka.run(KA106FaultInput(operation="vector_search", failures=3, successes=3))
    half_open_result = ka.run(
        KA106FaultInput(operation="vector_search", failures=3, successes=3, last_failure_age_s=15)
    )

    assert open_result["success"] is True
    assert open_result["output"]["circuit_state"] == "OPEN"
    assert open_result["output"]["circuit_reason"] == "failure_rate_threshold_exceeded"
    assert open_result["output"]["fallback_engaged"] is True
    assert half_open_result["output"]["circuit_state"] == "HALF_OPEN"


def test_ka109_reports_real_local_health_components():
    result = KA109SystemHealth({}).run(KA109HealthInput(check_mode="deep"))

    assert result["success"] is True
    assert result["output"]["overall_status"] in {"HEALTHY", "DEGRADED"}
    assert result["output"]["sub_component_health"]["python_runtime"]["status"] == "ok"
    assert result["output"]["sub_component_health"]["ka_registry"]["exists"] is True
    assert result["output"]["uptime_seconds"] > 0


def test_ka111_authorizes_routes_and_rate_limits_locally():
    ka = KA111APIGateway({})

    allowed = ka.run(KA111Input(headers={"X-API-Key": "local-dev-key"}, path="/search/documents", request_count=3))
    denied = ka.run(KA111Input(headers={}, path="/search/documents"))
    limited = ka.run(KA111Input(headers={"X-API-Key": "local-dev-key"}, path="/search/documents", request_count=99))

    assert allowed["success"] is True
    assert allowed["output"]["route_target"] == "retrieval_service"
    assert allowed["output"]["rate_limit_remaining"] >= 0
    assert denied["success"] is False
    assert denied["output"]["status_code"] == 401
    assert limited["success"] is False
    assert limited["output"]["status_code"] == 429


def test_ka_master_dispatches_selected_flow(monkeypatch):
    controller = KAMasterController({})
    controller.algorithms = {
        "KA-004": {"metadata": {"Implementation": "unused"}},
        "KA-005": {"metadata": {"Implementation": "unused"}},
        "KA-048": {"metadata": {"Implementation": "unused"}},
    }
    calls = []

    def fake_execute(ka_id, payload):
        calls.append((ka_id, payload))
        return {"success": True, "output": {"ka_id": ka_id}}

    monkeypatch.setattr(controller, "execute_algorithm", fake_execute)

    result = controller.run({"data": {"query": "Extract entities from NIST control owner Alice Smith"}})

    assert result["success"] is True
    assert result["output"]["orchestrated_flow"] == ["KA-004", "KA-005", "KA-048"]
    assert [ka_id for ka_id, _payload in calls] == ["KA-004", "KA-005", "KA-048"]
    assert result["output"]["system_state"] == "NOMINAL"
