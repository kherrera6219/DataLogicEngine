"""Report bounded failure details for the intermittent Windows gateway test.

This is a pytest plugin, not application code. It preserves the test outcome
and reports only fixed-contract fields from the mocked test response.
"""

from __future__ import annotations

import json
import re

import pytest

TARGET = "test_gateway_persists_full_governed_trace_when_legacy_bypass_is_requested"
GATEWAY_TARGETS = {
    TARGET,
    "test_gateway_does_not_cross_provider_failover",
}
KA_TARGET = "test_ka_1046_owning_path"


def _text(value: object) -> str | None:
    return value[:120] if isinstance(value, str) else None


def _symbol(value: object) -> str | None:
    value = getattr(value, "value", value)
    return (
        value
        if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value)
        else None
    )


def _ka_diagnostic(call):
    for entry in call.excinfo.traceback:
        report = entry.frame.f_locals.get("report")
        if not hasattr(report, "required_failure") or not hasattr(report, "traces"):
            continue
        traces = getattr(report, "traces", {})
        results = getattr(report, "results", {})
        if not isinstance(traces, dict) or not isinstance(results, dict):
            continue
        nodes = []
        for name, trace in list(traces.items())[:64]:
            if not isinstance(name, str) or not re.fullmatch(r"KA-\d{3,4}", name):
                continue
            result = results.get(name)
            error = getattr(result, "error", None)
            nodes.append(
                {
                    "id": name,
                    "states": [
                        _symbol(getattr(event, "state", None))
                        for event in getattr(trace, "events", [])[:32]
                    ],
                    "error_code": _symbol(getattr(error, "code", None)),
                }
            )
        return {
            "status": _symbol(getattr(report, "status", None)),
            "required_failure": _symbol(getattr(report, "required_failure", None)),
            "nodes": nodes,
        }
    return {"status": "report_unavailable"}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if (
        item.name not in GATEWAY_TARGETS | {KA_TARGET}
        or call.when != "call"
        or call.excinfo is None
    ):
        return

    if item.name == KA_TARGET:
        report.sections.append(
            ("KA failure diagnostic", json.dumps(_ka_diagnostic(call)))
        )
        return

    response = None
    for entry in call.excinfo.traceback:
        candidate = entry.frame.f_locals.get("response")
        if candidate is not None and hasattr(candidate, "failure"):
            response = candidate
    if response is None:
        report.sections.append(("Gateway failure diagnostic", "Response unavailable"))
        return

    failure = getattr(response, "failure", None)
    failure = failure if isinstance(failure, dict) else {}
    trace = getattr(response, "trace", None)
    trace = trace if isinstance(trace, list) else []
    diagnostic = {
        "status": _text(getattr(response, "status", None)),
        "failure": {key: _text(failure.get(key)) for key in ("kind", "code", "stage")},
        "stages": [
            {key: _text(stage.get(key)) for key in ("name", "status", "error_code")}
            for stage in trace[:64]
            if isinstance(stage, dict)
        ],
    }
    report.sections.append(("Gateway failure diagnostic", json.dumps(diagnostic)))
