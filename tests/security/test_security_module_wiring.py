"""Security controls must be live-path authorities or explicitly retired."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_retired_fail_open_supervisor_is_not_shipped():
    assert not (ROOT / "backend/security/defense_supervisor.py").exists()
    assert not (
        ROOT / "backend/security/prompts/defense_supervisor.txt"
    ).exists()
    payload_verifier = (ROOT / "scripts/verify_release_payload.py").read_text(
        encoding="utf-8"
    )
    assert "defense_supervisor" not in payload_verifier
    assert "ukg_api_v3_2" not in payload_verifier
    backend_spec = (ROOT / "backend.spec").read_text(encoding="utf-8")
    assert "backend/security/prompts" not in backend_spec
    assert "backend/api/specs" not in backend_spec


def test_gateway_governance_imports_both_live_input_controls():
    governance_path = ROOT / "backend/llm_gateway/governance.py"
    tree = ast.parse(governance_path.read_text(encoding="utf-8"))
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert "backend.security.prompt_injection_shield" in imports
    assert "backend.security.ai_guardrail" in imports
