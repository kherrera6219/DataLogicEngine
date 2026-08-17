from __future__ import annotations

import asyncio
import json
import logging
import sys
from types import SimpleNamespace

import pytest
from flask import Flask, g


def test_structured_formatter_redacts_context_extras_and_exceptions():
    from backend.logging_config import CustomJsonFormatter

    app = Flask(__name__)
    formatter = CustomJsonFormatter()
    try:
        raise ValueError("test failure")
    except ValueError:
        exc_info = sys.exc_info()
    record = logging.LogRecord(
        "component", logging.ERROR, __file__, 10, "User email test@example.com", (), exc_info,
    )
    record.event = "contract_test"
    record.api_key = "secret-key"
    record.payload = {"email": "person@example.com"}
    record.duration_ms = 12
    with app.test_request_context("/users/test@example.com", headers={"User-Agent": "agent"}):
        g.correlation_id = "corr-1"
        parsed = json.loads(formatter.format(record))
    assert parsed["correlation_id"] == "corr-1"
    assert parsed["api_key"] == "[REDACTED_SECRET]"
    assert "test@example.com" not in parsed["message"]
    assert "exception" in parsed and parsed["method"] == "GET"

    target = {}
    formatter.add_fields(target, record, {"custom": "value"})
    assert target["custom"] == "value"


def test_logging_format_levels_root_handlers_and_service(monkeypatch, tmp_path):
    import backend.logging_config as module

    root = logging.getLogger()
    old_handlers = list(root.handlers)
    old_level = root.level
    try:
        monkeypatch.setenv("FLASK_ENV", "development")
        assert module._resolve_log_level() == logging.DEBUG
        assert isinstance(module._build_formatter("text"), logging.Formatter)
        module._configure_root_handlers(
            log_level=logging.DEBUG,
            log_format="text",
            log_file=str(tmp_path / "dev.log"),
        )
        assert len(root.handlers) == 1

        monkeypatch.setenv("FLASK_ENV", "production")
        monkeypatch.setenv("LOG_AGGREGATION_HOST", "127.0.0.1")
        monkeypatch.setenv("LOG_AGGREGATION_PORT", "5514")
        monkeypatch.setenv("LOG_AGGREGATION_PROTOCOL", "tcp")

        class Syslog(logging.Handler):
            def __init__(self, **values):
                super().__init__()
                self.values = values

            def emit(self, _record):
                return None

        monkeypatch.setattr(module.logging.handlers, "SysLogHandler", Syslog)
        module._configure_root_handlers(
            log_level=logging.INFO,
            log_format="json",
            log_file=str(tmp_path / "production.log"),
        )
        assert len(root.handlers) == 3

        monkeypatch.delenv("LOG_AGGREGATION_HOST", raising=False)
        monkeypatch.setenv("LOG_FILE", str(tmp_path / "service.log"))
        logger = module.configure_service_logging("coverage-service")
        assert logger.name == "coverage-service"
    finally:
        for handler in list(root.handlers):
            if handler not in old_handlers:
                handler.close()
        root.handlers = old_handlers
        root.setLevel(old_level)


def test_configure_structured_logging_replaces_managed_handlers(monkeypatch, tmp_path):
    import backend.logging_config as module

    app = Flask(__name__)
    app.config.update(
        LOG_FORMAT="json",
        LOG_FILE=str(tmp_path / "app.log"),
        SECURITY_LOG_FILE=str(tmp_path / "security.log"),
        AUDIT_LOG_FILE=str(tmp_path / "audit.log"),
    )
    security = logging.getLogger("security")
    audit = logging.getLogger("audit")
    stale_security = logging.NullHandler()
    stale_security._dle_managed_handler = True
    stale_audit = logging.NullHandler()
    stale_audit._dle_managed_handler = True
    security.addHandler(stale_security)
    audit.addHandler(stale_audit)
    module.configure_structured_logging(app)
    assert any(getattr(handler, "_dle_managed_handler", False) for handler in security.handlers)
    assert any(getattr(handler, "_dle_managed_handler", False) for handler in audit.handlers)
    for logger in (security, audit):
        for handler in list(logger.handlers):
            if getattr(handler, "_dle_managed_handler", False):
                logger.removeHandler(handler)
                handler.close()


def test_persona_enhancement_synthesis_metadata_and_specialists(monkeypatch):
    from backend.truth_engine.truth_core.personas import PersonaEnhancer

    enhancer = PersonaEnhancer()
    enhancer.integration_function = SimpleNamespace(
        integrate_text=lambda outputs, context: ("Integrated response", {**context, "count": len(outputs)})
    )
    monkeypatch.setattr(enhancer, "_get_persona_response", lambda name, config, query, context: {
        "persona": name, "role": config["role"], "response": f"{name}: {query}", "confidence": 0.8,
    })
    result = enhancer.enhance_query("Question", {"context": True}, ["knowledge_expert", "unknown"])
    assert result["synthesized_response"]["content"] == "Integrated response"
    assert list(result["persona_responses"]) == ["knowledge_expert"]
    assert enhancer.get_persona_info("knowledge_expert")["axis_alignment"] == 8
    assert "sector_expert" in enhancer.get_persona_info()
    assert enhancer.spawn_specialists("unknown", 2) == []
    specialists = enhancer.spawn_specialists("sector_expert", 2)
    assert len(specialists) == 2 and "Specialist 1" in specialists[0]["role"]
    assert enhancer.map_to_axis("regulatory_expert") == 10
    assert enhancer.map_to_axis("unknown") == 8
    assert enhancer._synthesize_responses({}, {}) == {"content": "", "confidence": 0}


def test_persona_quad_and_ka_response_paths(monkeypatch):
    import backend.truth_engine.truth_core.personas as module

    config = module.PersonaEnhancer.TRUTH_PERSONAS["knowledge_expert"]

    class Quad:
        async def process_with_persona(self, *_args):
            return {"response": "Quad answer", "confidence": 0.9}

    enhancer = module.PersonaEnhancer(Quad())
    quad = asyncio.run(enhancer._get_persona_response("knowledge_expert", config, "Q", {}))
    assert quad["source"] == "quad_persona_engine"

    class BrokenQuad:
        async def process_with_persona(self, *_args):
            raise RuntimeError("quad unavailable")

    result = SimpleNamespace(
        trace_id="trace-1",
        output={"persona_results": []},
    )
    monkeypatch.setattr(module, "get_controller", lambda: object())
    monkeypatch.setattr(module, "execute_required_ka", lambda *_args, **_kwargs: result)
    monkeypatch.setattr(module, "require_output_field", lambda *_args: [
        {"persona_type": "knowledge", "response": "KA answer", "confidence": 0.7, "measurement_status": "measured"},
    ])
    enhancer = module.PersonaEnhancer(BrokenQuad())
    ka = asyncio.run(enhancer._get_persona_response("knowledge_expert", config, "Q", {}))
    assert ka["source"] == "KA-012" and ka["trace_id"] == "trace-1"

    monkeypatch.setattr(module, "require_output_field", lambda *_args: [])
    failed = asyncio.run(enhancer._get_persona_response("knowledge_expert", config, "Q", {}))
    assert failed["source"] == "ka_failure"
    monkeypatch.setattr(module, "require_output_field", lambda *_args: [
        {"persona_type": "knowledge", "response": "", "confidence": "unknown"},
    ])
    failed = asyncio.run(enhancer._get_persona_response("knowledge_expert", config, "Q", {}))
    assert failed["measurement_status"] == "failed"


def test_persona_async_resolution_and_synthesis_fallback():
    from backend.truth_engine.truth_core.personas import PersonaEnhancer

    async def value():
        return {"resolved": True}

    assert PersonaEnhancer._resolve_maybe_async({"sync": True}) == {"sync": True}
    assert PersonaEnhancer._resolve_maybe_async(value()) == {"resolved": True}

    enhancer = PersonaEnhancer()
    enhancer.integration_function = SimpleNamespace(
        integrate_text=lambda *_args: (_ for _ in ()).throw(RuntimeError("integration failed"))
    )
    synthesized = enhancer._synthesize_responses({
        "knowledge_expert": {"role": "Knowledge", "response": "One", "confidence": 2.0},
        "sector_expert": {"role": "Sector", "response": "Two", "confidence": 0.5},
    }, {"knowledge_expert": 1.0, "sector_expert": 0.5})
    assert "**Knowledge**" in synthesized["content"]
    assert synthesized["confidence"] == 1.0


def test_persona_pod_parallel_execution_and_synthesis(monkeypatch):
    from backend.truth_engine.truth_core.personas import PersonaPod

    class Enhancer:
        async def _get_persona_response(self, name, config, *_args):
            if "Broken" in name:
                raise RuntimeError("specialist failed")
            return {"role": name, "response": "answer", "confidence": 0.8}

    pod = PersonaPod("sector", [
        {"role": "Working Specialist"}, {"role": "Broken Specialist"},
    ])
    asyncio.run(pod.execute("Q", {}, SimpleNamespace(persona_enhancer=Enhancer())))
    assert len(pod.results) == 1
    synthesis = pod.synthesize()
    assert synthesis["lane"] == "sector" and synthesis["confidence"] == 0.8
    assert PersonaPod("empty", []).synthesize() == {}
