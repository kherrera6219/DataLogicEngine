from __future__ import annotations

import json

from scripts.consolidate_phase17_history import DEFAULT_REPORT, verify
from scripts.generate_documentation_contract_index import DEFAULT_OUTPUT, render
from scripts.verify_docs_references import validate_headings


def test_heading_lint_ignores_shell_comments_inside_fences():
    lines = [
        "# One title",
        "",
        "## Setup",
        "",
        "```powershell",
        "# This is a shell comment, not a heading",
        "```",
        "",
        "### Details",
    ]
    assert validate_headings(lines) == []


def test_phase17_historical_sources_are_retained_outside_active_paths():
    report = json.loads(DEFAULT_REPORT.read_text(encoding="utf-8"))
    result = verify(report)
    assert result["status"] == "pass"
    assert result["summary"]["record_count"] >= 45
    assert result["summary"]["verified_count"] == result["summary"]["record_count"]
    assert result["summary"]["active_historical_count"] == 0


def test_generated_production_contract_index_matches_authorities():
    assert DEFAULT_OUTPUT.read_text(encoding="utf-8") == render()
