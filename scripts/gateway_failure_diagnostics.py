"""Report bounded failure details for the intermittent Windows gateway test.

This is a pytest plugin, not application code. It preserves the test outcome
and reports only fixed-contract fields from the mocked test response.
"""

from __future__ import annotations

import json

import pytest

TARGET = "test_gateway_persists_full_governed_trace_when_legacy_bypass_is_requested"


def _text(value: object) -> str | None:
    return value[:120] if isinstance(value, str) else None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if item.name != TARGET or call.when != "call" or call.excinfo is None:
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
