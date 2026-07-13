"""Phase 1 fail-closed checks for mutation routes found by the live manifest."""

from __future__ import annotations

import re

import pytest


ANONYMOUS_DENIAL_CASES = [
    ("/api/v1/csp-report", {"csp-report": {}}),
    ("/api/methods", {}),
    ("/api/methods/cross-pillar", {}),
    ("/api/methods/cross-sector", {}),
    ("/api/methods/hierarchy", {}),
    ("/api/pillar/", {}),
    ("/api/pillar/test/expand", {}),
    ("/api/pillar/test/sublevels", {}),
    ("/api/pillar/analyze-text", {}),
    ("/api/pillar/export", {}),
    ("/api/pillar/mappings", {}),
    ("/api/truth/core/session", {}),
    ("/api/truth/core/session/test/process", {}),
    ("/api/truth/gate/budget/test/reset", {}),
    ("/api/truth/gate/evaluate", {}),
    ("/api/truth/link/publish", {}),
    ("/api/truth/memory/artifacts/test", {}),
    ("/api/v1/pillar/", {}),
    ("/api/v1/pillar/test/expand", {}),
    ("/api/v1/pillar/test/sublevels", {}),
    ("/api/v1/pillar/analyze-text", {}),
    ("/api/v1/pillar/export", {}),
    ("/api/v1/pillar/mappings", {}),
    ("/api/v1/truth/core/session", {}),
    ("/api/v1/truth/core/session/test/process", {}),
    ("/api/v1/truth/gate/budget/test/reset", {}),
    ("/api/v1/truth/gate/evaluate", {}),
    ("/api/v1/truth/link/publish", {}),
    ("/api/v1/truth/memory/artifacts/test", {}),
    ("/graphql", {"query": "mutation { createSimulation(input: {}) { success } }"}),
]


@pytest.mark.parametrize(("path", "payload"), ANONYMOUS_DENIAL_CASES)
def test_anonymous_mutation_is_denied_before_validation(client, path, payload):
    response = client.post(path, json=payload)

    assert response.status_code in {401, 403}, (
        f"{path} reached validation or execution without authentication: "
        f"status={response.status_code}, body={response.get_data(as_text=True)[:300]}"
    )


def _sample_route_path(rule: str) -> str:
    def replace(match: re.Match[str]) -> str:
        converter = match.group("converter") or "string"
        if converter == "int":
            return "1"
        if converter == "float":
            return "1.0"
        if converter == "uuid":
            return "00000000-0000-0000-0000-000000000001"
        if converter == "path":
            return "phase1/test"
        if converter.startswith("any("):
            return converter.removeprefix("any(").removesuffix(")").split(",", 1)[0]
        return "phase1-test"

    return re.sub(
        r"<(?:(?P<converter>[^:>]+):)?(?P<name>[^>]+)>",
        replace,
        rule,
    )


def test_every_live_mutation_rule_denies_anonymous_access(app, client):
    failures: list[str] = []
    tested = 0
    for rule in app.url_map.iter_rules():
        for method in sorted(set(rule.methods or ()) & {"POST", "PUT", "PATCH", "DELETE"}):
            tested += 1
            path = _sample_route_path(rule.rule)
            response = client.open(path, method=method, json={})
            if response.status_code not in {401, 403}:
                failures.append(
                    f"{method} {rule.rule} ({rule.endpoint}) -> {response.status_code}"
                )

    assert tested > 0
    assert not failures, "Anonymous mutations reached application logic:\n" + "\n".join(failures)
