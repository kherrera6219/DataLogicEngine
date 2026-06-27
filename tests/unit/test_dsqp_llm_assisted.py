"""LLM-assisted DSQP construction (A2-2).

Exercises the LLM-assisted answer path with an injected stub client (no network),
covering query-derived construction, per-component fallback to the deterministic
scaffold, provenance recording, the kill switch, and schema preservation.
"""

import json

from backend.dsqp import COMPONENT_KEYS, DSQPAnswerGenerator, DSQPChain, DSQPValidator


class _StubClient:
    """Stand-in for OllamaClient that returns a canned generation."""

    def __init__(self, response: str, ok: bool = True):
        self._response = response
        self._ok = ok
        self.calls: list[dict] = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return {"ok": self._ok, "response": self._response, "error": None if self._ok else "boom"}


_FULL_LLM_JSON = json.dumps({
    "job_role": {"title": "FDA Medical-Device Regulatory Lead", "level": "Principal", "focus_area": "cardiac implants"},
    "education": {"degree": "JD with biomedical engineering background", "focus": "device law"},
    "certifications": {"list": ["RAC (Devices)", "ISO 13485 Lead Auditor"], "required_for": "healthcare"},
    "skills": {"items": ["510(k) submission", "predicate analysis", "design controls"], "domain_focus": "medical devices"},
    "training": {"modules": ["FDA 510(k) Pathway", "Class III PMA"], "risk_domain": "healthcare"},
    "career_path": {"stages": ["Reg Affairs Associate", "Device Reg Manager", "Reg Lead"], "years_in_field": 14},
    "related_jobs": {"overlapping_roles": ["Clinical Affairs Lead", "Quality Systems Manager"], "blind_spot_coverage": ["post-market surveillance"]},
})


def _gen(client, model="cloud-test"):
    # Injecting a client routes generation through it (no network / cloud call).
    return DSQPAnswerGenerator(client=client, model=model)


def test_llm_assisted_construction_is_query_derived(monkeypatch):
    monkeypatch.setenv("DSQP_LLM_ASSISTED", "true")
    chain = DSQPChain(answer_generator=_gen(_StubClient(_FULL_LLM_JSON)))

    persona = chain.construct(
        "Assess FDA 510(k) clearance pathway for a cardiac implant",
        {"active_axes": [10]},
        axis_number=10,
        coordinate_path="healthcare.medical_device",
        context={"risk_domain": "healthcare"},
    ).to_dict()

    # The job title is the model's query-specific answer, not the deterministic
    # "Lead Regulatory Analyst" scaffold.
    assert persona["components"]["job_role"]["title"] == "FDA Medical-Device Regulatory Lead"
    assert persona["metadata"]["construction_mode"] == "llm_assisted"
    assert persona["metadata"]["llm_component_count"] == 7
    assert all(step["source"] == "llm" for step in persona["dsqp_chain"])
    # Deterministic context fields are still backfilled onto LLM answers.
    assert persona["components"]["job_role"]["query_mission"].startswith("Assess FDA 510(k)")
    assert persona["components"]["education"]["domain"] == "healthcare"
    # Still passes the (process-aware) validator.
    assert DSQPValidator().validate(persona)["valid"] is True


def test_partial_llm_output_falls_back_per_component(monkeypatch):
    monkeypatch.setenv("DSQP_LLM_ASSISTED", "true")
    # Only two valid components; the rest missing/malformed → deterministic fill.
    partial = json.dumps({
        "job_role": {"title": "Securities Enforcement Counsel", "level": "Senior"},
        "certifications": {"list": []},  # invalid: empty list → rejected
        "skills": {"items": ["10b-5 analysis", "disclosure review"]},
    })
    chain = DSQPChain(answer_generator=_gen(_StubClient(partial)))

    persona = chain.construct(
        "Evaluate SEC Rule 10b-5 insider trading disclosure controls",
        {"active_axes": [10]},
        axis_number=10,
        coordinate_path="finance.securities",
        context={"risk_domain": "finance"},
    ).to_dict()

    assert persona["metadata"]["construction_mode"] == "hybrid"
    assert persona["metadata"]["llm_component_count"] == 2  # job_role + skills
    by_component = {s["component"]: s["source"] for s in persona["dsqp_chain"]}
    assert by_component["job_role"] == "llm"
    assert by_component["skills"] == "llm"
    assert by_component["certifications"] == "deterministic"  # empty list rejected
    assert by_component["education"] == "deterministic"
    assert persona["components"]["job_role"]["title"] == "Securities Enforcement Counsel"
    assert DSQPValidator().validate(persona)["valid"] is True


def test_kill_switch_forces_deterministic(monkeypatch):
    monkeypatch.setenv("DSQP_LLM_ASSISTED", "false")
    client = _StubClient(_FULL_LLM_JSON)
    chain = DSQPChain(answer_generator=_gen(client))

    persona = chain.construct(
        "Assess FDA clearance",
        {"active_axes": [10]},
        axis_number=10,
        coordinate_path="healthcare.device",
        context={"risk_domain": "healthcare"},
    ).to_dict()

    assert client.calls == []  # model never called
    assert persona["metadata"]["construction_mode"] == "deterministic_offline"
    assert persona["components"]["job_role"]["title"] == "Lead Regulatory Analyst"


def test_model_error_falls_back(monkeypatch):
    monkeypatch.setenv("DSQP_LLM_ASSISTED", "true")
    chain = DSQPChain(answer_generator=_gen(_StubClient("", ok=False)))

    persona = chain.construct(
        "Assess FDA clearance",
        {"active_axes": [10]},
        axis_number=10,
        coordinate_path="healthcare.device",
        context={"risk_domain": "healthcare"},
    ).to_dict()

    assert persona["metadata"]["construction_mode"] == "deterministic_offline"
    assert DSQPValidator().validate(persona)["valid"] is True


def test_no_cloud_model_returns_empty(monkeypatch):
    """With no injected client and no cloud model configured, generate() is a no-op."""
    monkeypatch.setenv("DSQP_LLM_ASSISTED", "true")
    import backend.llm_gateway.active_model as active_model

    monkeypatch.setattr(active_model, "generate_with_active_model", lambda *a, **k: None)
    gen = DSQPAnswerGenerator(client=None, model=None)

    out = gen.generate(
        persona_type="regulatory",
        query="x",
        coordinate_path="a.b",
        keywords=["x"],
        context={},
        questions={k: "q?" for k in COMPONENT_KEYS},
    )
    assert out == {}


def test_validated_components_rejects_malformed():
    raw = json.dumps({
        "job_role": {"title": "Good Role"},     # valid
        "education": {"degree": ""},            # empty primary → rejected
        "skills": {"items": []},                # empty list → rejected
        "training": {"modules": ["M1"]},        # valid
        "career_path": "nope",                  # not a dict → rejected
    })
    out = DSQPAnswerGenerator._validated_components(raw)
    assert set(out) == {"job_role", "training"}
    assert out["training"]["modules"] == ["M1"]


def test_validated_components_coerces_scalar_list_field():
    raw = json.dumps({"certifications": {"list": "Single Cert", "required_for": "finance"}})
    out = DSQPAnswerGenerator._validated_components(raw)
    assert out["certifications"]["list"] == ["Single Cert"]
