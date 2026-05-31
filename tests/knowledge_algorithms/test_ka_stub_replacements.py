from backend.knowledge_algorithms.ka_11_analytical_modeling import KA011AnalyticalModeling, KA011Input
from backend.knowledge_algorithms.ka_33_reserved_expansion_slot import KA033ExtensionSlot, KA033Input
from backend.knowledge_algorithms.ka_39_anomaly_detection import KA039AnomalyDetection, KA039Input
from backend.knowledge_algorithms.ka_48_entity_extraction import KA048EntityExtraction, KA048Input
from backend.knowledge_algorithms.ka_77_data_enrichment import KA077DataEnrichment, KA077EnrichmentInput
from backend.knowledge_algorithms.ka_109_system_health import KA109HealthInput, KA109SystemHealth
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


def test_ka048_extracts_typed_entities():
    text = "NIST 800-53 review for Acme Corporation costs $12,500 on 2026-05-30. Email admin@example.com."
    result = KA048EntityExtraction({}).run(KA048Input(text=text))
    entities = result["output"]["entities"]

    assert result["success"] is True
    assert any(entity["type"] == "REGULATION" and entity["text"].lower().startswith("nist") for entity in entities)
    assert any(entity["type"] == "MONEY" and "12,500" in entity["text"] for entity in entities)
    assert any(entity["type"] == "DATE" and entity["text"] == "2026-05-30" for entity in entities)
    assert any(entity["type"] == "EMAIL" and entity["text"] == "admin@example.com" for entity in entities)


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


def test_ka109_reports_real_local_health_components():
    result = KA109SystemHealth({}).run(KA109HealthInput(check_mode="deep"))

    assert result["success"] is True
    assert result["output"]["overall_status"] in {"HEALTHY", "DEGRADED"}
    assert result["output"]["sub_component_health"]["python_runtime"]["status"] == "ok"
    assert result["output"]["sub_component_health"]["ka_registry"]["exists"] is True
    assert result["output"]["uptime_seconds"] > 0


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
